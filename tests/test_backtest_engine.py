from __future__ import annotations

import pandas as pd

from momentum_trader.backtest.engine import run_backtest
from momentum_trader.config import ETFConfig, load_config


def _trend_breakout_frame(start: str, periods: int) -> pd.DataFrame:
    dates = pd.bdate_range(start, periods=periods)
    close = pd.Series([100 + idx * 0.12 for idx in range(periods)], dtype=float)
    return pd.DataFrame(
        {
            "date": dates,
            "open": close,
            "high": close,
            "low": close - 0.5,
            "close": close,
            "volume": [10000] * periods,
            "amount": close * 10000,
        }
    )


def test_backtest_trades_early_data_before_late_data_starts() -> None:
    cfg = load_config("configs/default.yaml")
    cfg.universe = [
        ETFConfig(symbol="EARLY", name="Early ETF"),
        ETFConfig(symbol="LATE", name="Late ETF"),
    ]

    early = _trend_breakout_frame("2020-01-01", 420)
    late = _trend_breakout_frame(str(early.loc[320, "date"].date()), 80)
    benchmark = early.copy()

    result = run_backtest(
        cfg,
        etf_frames={"EARLY": early, "LATE": late},
        benchmark_frame=benchmark,
    )

    assert not result.orders.empty
    first_order = result.orders.sort_values("date").iloc[0]
    assert first_order["symbol"] == "EARLY"
    assert pd.Timestamp(first_order["date"]) < late["date"].min()

