from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field, model_validator


class ProjectConfig(BaseModel):
    name: str


class DataConfig(BaseModel):
    source: str = "tencent"
    raw_dir: Path
    processed_dir: Path
    adjust: str = "qfq"
    etf_period: str = "daily"
    benchmark_symbol: str = "sh000300"
    benchmark_name: str = "沪深300指数"
    fetch_date_format: str = "%Y%m%d"


class ETFConfig(BaseModel):
    symbol: str
    name: str


class BacktestConfig(BaseModel):
    start_date: str
    end_date: str
    initial_cash: float = Field(gt=0)
    commission_rate: float = Field(ge=0)
    max_positions: int = Field(gt=0)
    intent_position_pct: float = Field(gt=0, le=1)
    cash_interest_rate: float = 0.0
    limit_up_threshold: float = Field(default=0.095, gt=0)


class PyramidStepConfig(BaseModel):
    trigger_pct: float = Field(ge=0)
    allocation_pct: float = Field(gt=0, le=1)


class StrategyConfig(BaseModel):
    breakout_window: int = Field(gt=1)
    short_ma_window: int = Field(gt=1)
    long_ma_window: int = Field(gt=1)
    trailing_stop_pct: float = Field(gt=0, lt=1)
    pyramid: list[PyramidStepConfig]

    @model_validator(mode="after")
    def validate_windows_and_pyramid(self) -> StrategyConfig:
        if self.short_ma_window >= self.long_ma_window:
            raise ValueError("short_ma_window must be smaller than long_ma_window")
        allocation_sum = sum(step.allocation_pct for step in self.pyramid)
        if abs(allocation_sum - 1.0) > 1e-8:
            raise ValueError("pyramid allocation_pct values must sum to 1.0")
        triggers = [step.trigger_pct for step in self.pyramid]
        if triggers != sorted(triggers):
            raise ValueError("pyramid trigger_pct values must be sorted ascending")
        return self


class ReportConfig(BaseModel):
    output_dir: Path
    risk_free_rate: float = 0.0
    trading_days_per_year: int = 252
    font_candidates: list[str] = Field(default_factory=list)


class AppConfig(BaseModel):
    project: ProjectConfig
    data: DataConfig
    universe: list[ETFConfig]
    backtest: BacktestConfig
    strategy: StrategyConfig
    report: ReportConfig
    config_path: Path | None = None
    root_dir: Path = Field(default_factory=Path.cwd)

    @model_validator(mode="after")
    def resolve_paths(self) -> AppConfig:
        root = self.root_dir
        self.data.raw_dir = _resolve(root, self.data.raw_dir)
        self.data.processed_dir = _resolve(root, self.data.processed_dir)
        self.report.output_dir = _resolve(root, self.report.output_dir)
        return self


def _resolve(root: Path, path: Path) -> Path:
    return path if path.is_absolute() else root / path


def load_config(path: str | Path) -> AppConfig:
    config_path = Path(path).resolve()
    with config_path.open("r", encoding="utf-8") as file:
        payload: dict[str, Any] = yaml.safe_load(file)

    root_dir = config_path.parent.parent
    return AppConfig(**payload, config_path=config_path, root_dir=root_dir)
