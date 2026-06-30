from __future__ import annotations

import pandas as pd

from momentum_trader.config import PyramidStepConfig, StrategyConfig
from momentum_trader.strategy.signals import add_execution_flags, add_momentum_signals


def make_strategy_config() -> StrategyConfig:
    return StrategyConfig(
        breakout_window=120,
        short_ma_window=60,
        long_ma_window=250,
        trailing_stop_pct=0.15,
        pyramid=[
            PyramidStepConfig(trigger_pct=0.0, allocation_pct=0.5),
            PyramidStepConfig(trigger_pct=0.1, allocation_pct=0.3),
            PyramidStepConfig(trigger_pct=0.2, allocation_pct=0.2),
        ],
    )


def base_frame(rows: int = 260) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "date": pd.date_range("2020-01-01", periods=rows, freq="B"),
            "open": [100.0] * rows,
            "high": [100.0] * rows,
            "low": [99.0] * rows,
            "close": [100.0] * rows,
            "volume": [10000] * rows,
            "amount": [1000000.0] * rows,
        }
    )


def test_entry_signal_uses_prior_breakout_high_only() -> None:
    df = base_frame()
    df.loc[df.index[-1], "high"] = 200.0
    df.loc[df.index[-1], "close"] = 150.0

    result = add_momentum_signals(df, make_strategy_config())

    assert result.loc[result.index[-1], "breakout_high"] == 100.0
    assert bool(result.loc[result.index[-1], "entry_signal"]) is True


def test_entry_signal_requires_ma_trend_filter() -> None:
    df = base_frame()
    df.loc[df.index[-80] :, "close"] = 80.0
    df.loc[df.index[-1], "close"] = 120.0
    df.loc[df.index[-1], "high"] = 121.0

    result = add_momentum_signals(df, make_strategy_config())

    last = result.index[-1]
    assert bool(result.loc[last, "close"] > result.loc[last, "breakout_high"])
    assert bool(result.loc[last, "ma_short"] > result.loc[last, "ma_long"]) is False
    assert bool(result.loc[result.index[-1], "entry_signal"]) is False


def test_entry_signal_false_before_long_ma_warmup() -> None:
    df = base_frame(rows=200)
    df.loc[df.index[-1], "close"] = 150.0
    df.loc[df.index[-1], "high"] = 151.0

    result = add_momentum_signals(df, make_strategy_config())

    assert bool(result["ma_long"].isna().all())
    assert not result["entry_signal"].any()


def test_open_limit_up_flag_marks_one_price_limit_open() -> None:
    df = base_frame(rows=3)
    df.loc[1, ["open", "high", "low", "close"]] = [110.0, 110.0, 110.0, 110.0]

    result = add_execution_flags(df, limit_up_threshold=0.095)

    assert bool(result.loc[1, "open_limit_up"]) is True
    assert bool(result.loc[2, "open_limit_up"]) is False
