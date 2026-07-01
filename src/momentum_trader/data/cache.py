from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime, timezone
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

import pandas as pd


@dataclass(frozen=True)
class CacheKey:
    kind: str
    symbol: str
    start_date: str
    end_date: str
    adjust: str
    fetch_date: str
    source: str = "unknown"

    def filename(self) -> str:
        parts = [
            self.symbol,
            self.start_date.replace("-", ""),
            self.end_date.replace("-", ""),
            self.adjust or "none",
            self.fetch_date,
        ]
        return "_".join(parts) + ".parquet"


class ParquetCache:
    def __init__(
        self,
        raw_dir: Path,
        fetch_date_format: str = "%Y%m%d",
        today_provider: Callable[[], date] = date.today,
    ) -> None:
        self.raw_dir = raw_dir
        self.fetch_date_format = fetch_date_format
        self.today_provider = today_provider

    def key(
        self,
        kind: str,
        symbol: str,
        start_date: str,
        end_date: str,
        adjust: str,
        source: str = "unknown",
    ) -> CacheKey:
        fetch_date = self._cache_snapshot_date(end_date).strftime(self.fetch_date_format)
        return CacheKey(kind, symbol, start_date, end_date, adjust, fetch_date, source)

    def path_for(self, key: CacheKey) -> Path:
        return self.raw_dir / key.kind / key.filename()

    def read_or_fetch(self, key: CacheKey, fetcher: Callable[[], pd.DataFrame]) -> pd.DataFrame:
        path = self.path_for(key)
        if path.exists():
            return pd.read_parquet(path)

        df = fetcher()
        path.parent.mkdir(parents=True, exist_ok=True)
        df.to_parquet(path, index=False)
        # 缓存风险点：同一标的、同一参数、同一天只拉取一次，避免盘中多次调用导致数据版本混杂。
        self._record_metadata(key, path)
        return df

    def _cache_snapshot_date(self, end_date: str) -> date:
        today = self.today_provider()
        end = date.fromisoformat(end_date)
        # 缓存复现风险点：历史区间固定用 end_date 作为缓存快照日，避免自然日变化导致
        # 同一历史配置生成不同缓存文件；只有包含今天/未来的区间才使用 today。
        if end < today:
            return end
        return today

    def _record_metadata(self, key: CacheKey, path: Path) -> None:
        metadata_path = path.parent / "_metadata.json"
        if metadata_path.exists():
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        else:
            metadata = {"files": {}}

        metadata["files"][path.name] = {
            "kind": key.kind,
            "source": key.source,
            "symbol": key.symbol,
            "start_date": key.start_date,
            "end_date": key.end_date,
            "adjust": key.adjust,
            "fetch_date": key.fetch_date,
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "akshare_version": _package_version("akshare"),
        }
        metadata_path.write_text(
            json.dumps(metadata, ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )


def _package_version(package: str) -> str:
    try:
        return version(package)
    except PackageNotFoundError:
        return "unknown"
