from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import date
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
    def __init__(self, raw_dir: Path, fetch_date_format: str = "%Y%m%d") -> None:
        self.raw_dir = raw_dir
        self.fetch_date_format = fetch_date_format

    def key(self, kind: str, symbol: str, start_date: str, end_date: str, adjust: str) -> CacheKey:
        fetch_date = date.today().strftime(self.fetch_date_format)
        return CacheKey(kind, symbol, start_date, end_date, adjust, fetch_date)

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
        return df

