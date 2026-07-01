from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from momentum_trader.config import AppConfig


@dataclass(frozen=True)
class OutputLocations:
    root_dir: Path
    tag: str
    run_dir: Path
    latest_dir: Path
    index_path: Path


def build_output_locations(root_dir: Path, tag: str) -> OutputLocations:
    safe_tag = normalize_tag(tag)
    return OutputLocations(
        root_dir=root_dir,
        tag=safe_tag,
        run_dir=root_dir / "runs" / safe_tag,
        # latest_dir intentionally remains the configured root so existing
        # localhost URLs such as /report.html keep working.
        latest_dir=root_dir,
        index_path=root_dir / "index.csv",
    )


def normalize_tag(tag: str) -> str:
    normalized = re.sub(r"[^A-Za-z0-9._-]+", "_", tag.strip())
    normalized = normalized.strip("._-")
    return normalized or "default"


def config_with_output_dir(config: AppConfig, output_dir: Path) -> AppConfig:
    report = config.report.model_copy(update={"output_dir": output_dir})
    return config.model_copy(update={"report": report})


def append_run_index(config: AppConfig, locations: OutputLocations) -> Path:
    row = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "tag": locations.tag,
        "run_dir": str(locations.run_dir),
        "config_path": str(config.config_path or ""),
        "config_sha1": _file_sha1(config.config_path),
        "project": config.project.name,
        "source": config.data.source,
        "adjust": config.data.adjust,
        "start_date": config.backtest.start_date,
        "end_date": config.backtest.end_date,
        "universe": ",".join(etf.symbol for etf in config.universe),
        "initial_cash": config.backtest.initial_cash,
        "final_equity": _final_equity(locations.run_dir / "reports" / "equity_curve.csv"),
    }
    row.update(_metrics(locations.run_dir / "reports" / "metrics.csv"))

    index = pd.DataFrame([row])
    if locations.index_path.exists():
        existing = pd.read_csv(locations.index_path)
        index = pd.concat([existing, index], ignore_index=True)

    locations.index_path.parent.mkdir(parents=True, exist_ok=True)
    index.to_csv(locations.index_path, index=False)
    return locations.index_path


def _metrics(path: Path) -> dict[str, float | int | str]:
    if not path.exists():
        return {}
    metrics = pd.read_csv(path)
    if metrics.empty:
        return {}
    return metrics.iloc[0].to_dict()


def _final_equity(path: Path) -> float | None:
    if not path.exists():
        return None
    equity = pd.read_csv(path)
    if equity.empty:
        return None
    return float(equity["equity"].iloc[-1])


def _file_sha1(path: Path | None) -> str:
    if path is None or not path.exists():
        return ""
    return hashlib.sha1(path.read_bytes()).hexdigest()
