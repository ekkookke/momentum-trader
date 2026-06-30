from __future__ import annotations

import pandas as pd

from momentum_trader.config import StrategyConfig
from momentum_trader.data.schema import assert_columns


def add_momentum_signals(df: pd.DataFrame, strategy: StrategyConfig) -> pd.DataFrame:
    assert_columns(df, ["date", "open", "high", "low", "close"])
    result = df.copy()

    # 未来函数风险点：突破高点使用 shift(1)，即 T 日收盘价只和 T-1 及以前的
    # 120 个交易日最高价比较；当前 K 线最高价不会进入突破阈值。
    result["breakout_high"] = (
        result["high"]
        .shift(1)
        .rolling(strategy.breakout_window, min_periods=strategy.breakout_window)
        .max()
    )

    # 未来函数风险点：均线在 T 日收盘后计算，允许使用 T 日收盘价，但不会使用 T+1 数据。
    result["ma_short"] = result["close"].rolling(
        strategy.short_ma_window, min_periods=strategy.short_ma_window
    ).mean()
    result["ma_long"] = result["close"].rolling(
        strategy.long_ma_window, min_periods=strategy.long_ma_window
    ).mean()
    result["entry_signal"] = (
        (result["close"] > result["breakout_high"]) & (result["ma_short"] > result["ma_long"])
    )
    result["entry_signal"] = result["entry_signal"].fillna(False).astype(bool)
    return result


def add_execution_flags(df: pd.DataFrame, limit_up_threshold: float) -> pd.DataFrame:
    assert_columns(df, ["date", "open", "high", "low", "close"])
    result = df.copy()
    prev_close = result["close"].shift(1)
    limit_price = prev_close * (1 + limit_up_threshold)

    # 涨跌停风险点：买入/加仓在 T+1 开盘执行；如果执行日开盘一字涨停，
    # 即 open/high/low 基本相同且开盘接近涨停价，则跳过该笔买入。
    same_price_bar = (
        result["open"].sub(result["high"]).abs().le(1e-8)
        & result["open"].sub(result["low"]).abs().le(1e-8)
    )
    result["open_limit_up"] = (result["open"] >= limit_price) & same_price_bar
    result["open_limit_up"] = result["open_limit_up"].fillna(False).astype(bool)
    return result


def prepare_strategy_frame(
    df: pd.DataFrame, strategy: StrategyConfig, limit_up_threshold: float
) -> pd.DataFrame:
    return add_execution_flags(add_momentum_signals(df, strategy), limit_up_threshold)
