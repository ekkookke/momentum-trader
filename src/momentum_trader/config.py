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
    cash_interest_rate: float = 0.0


class ExecutionConfig(BaseModel):
    commission_rate: float = Field(ge=0)
    limit_up_threshold: float = Field(default=0.095, gt=0)


class PyramidStepConfig(BaseModel):
    trigger_pct: float = Field(ge=0)
    allocation_pct: float = Field(gt=0, le=1)


class PyramidConfig(BaseModel):
    enabled: bool = True
    steps: list[PyramidStepConfig] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_pyramid_steps(self) -> PyramidConfig:
        if not self.enabled:
            return self
        if not self.steps:
            raise ValueError("enabled pyramid requires at least one step")
        allocation_sum = sum(step.allocation_pct for step in self.steps)
        if abs(allocation_sum - 1.0) > 1e-8:
            raise ValueError("pyramid allocation_pct values must sum to 1.0")
        triggers = [step.trigger_pct for step in self.steps]
        if triggers != sorted(triggers):
            raise ValueError("pyramid trigger_pct values must be sorted ascending")
        return self


class PositionConfig(BaseModel):
    max_positions: int = Field(gt=0)
    intent_position_pct: float = Field(gt=0, le=1)
    pyramid: PyramidConfig


class ConditionConfig(BaseModel):
    type: str
    name: str | None = None
    apply: str = "always"
    field: str = "close"
    op: str = ">"
    window: int | None = None
    shift: int = 0
    breakout_field: str = "high"
    fast_window: int | None = None
    slow_window: int | None = None
    ma_window: int | None = None
    ma_method: str = "sma"
    threshold: float | None = None
    drawdown_pct: float | None = None

    @model_validator(mode="after")
    def validate_condition(self) -> ConditionConfig:
        allowed_types = {
            "breakout",
            "ma_relation",
            "price_vs_ma",
            "ma_break",
            "roc",
            "rolling_mean_threshold",
            "trailing_stop",
        }
        if self.type not in allowed_types:
            raise ValueError(f"unsupported condition type: {self.type}")
        if self.apply not in {"always", "before_pyramid_complete", "after_pyramid_complete"}:
            raise ValueError(f"unsupported condition apply scope: {self.apply}")
        if self.op not in {">", ">=", "<", "<=", "==", "!="}:
            raise ValueError(f"unsupported comparison operator: {self.op}")
        if self.ma_method not in {"sma", "ema"}:
            raise ValueError(f"unsupported ma_method: {self.ma_method}")
        if self.window is not None and self.window <= 1:
            raise ValueError("window must be greater than 1")
        for attr in ["fast_window", "slow_window", "ma_window"]:
            value = getattr(self, attr)
            if value is not None and value <= 1:
                raise ValueError(f"{attr} must be greater than 1")
        if self.shift < 0:
            raise ValueError("shift must be greater than or equal to 0")
        if self.type == "breakout" and self.window is None:
            raise ValueError("breakout condition requires window")
        if self.type == "ma_relation" and (self.fast_window is None or self.slow_window is None):
            raise ValueError("ma_relation condition requires fast_window and slow_window")
        if self.type in {"price_vs_ma", "ma_break"} and self.ma_window is None:
            raise ValueError(f"{self.type} condition requires ma_window")
        if self.type in {"roc", "rolling_mean_threshold"}:
            if self.window is None or self.threshold is None:
                raise ValueError(f"{self.type} condition requires window and threshold")
        if self.type == "trailing_stop" and self.drawdown_pct is None:
            raise ValueError("trailing_stop condition requires drawdown_pct")
        if self.drawdown_pct is not None and not 0 < self.drawdown_pct < 1:
            raise ValueError("drawdown_pct must be between 0 and 1")
        return self


class SignalGroupConfig(BaseModel):
    mode: str = "all"
    conditions: list[ConditionConfig]

    @model_validator(mode="after")
    def validate_mode(self) -> SignalGroupConfig:
        if self.mode not in {"all", "any"}:
            raise ValueError(f"unsupported signal group mode: {self.mode}")
        return self


class StrategyConfig(BaseModel):
    entry: SignalGroupConfig
    exit: SignalGroupConfig


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
    execution: ExecutionConfig
    position: PositionConfig
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
