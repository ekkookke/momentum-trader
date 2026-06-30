from __future__ import annotations

import pandas as pd

from momentum_trader.config import ConditionConfig, SignalGroupConfig, StrategyConfig
from momentum_trader.data.schema import assert_columns


def add_momentum_signals(df: pd.DataFrame, strategy: StrategyConfig) -> pd.DataFrame:
    assert_columns(df, ["date", "open", "high", "low", "close"])
    result = df.copy()
    for diagnostic_column in ["breakout_high", "ma_short", "ma_long"]:
        result[diagnostic_column] = float("nan")
    result["entry_signal"] = _combine_conditions(
        result,
        strategy.entry,
        prefix="entry",
    )
    result["exit_signal_before_pyramid"] = _combine_exit_conditions(
        result,
        strategy.exit,
        apply_scope="before_pyramid_complete",
        prefix="exit_before",
    )
    result["exit_signal_after_pyramid"] = _combine_exit_conditions(
        result,
        strategy.exit,
        apply_scope="after_pyramid_complete",
        prefix="exit_after",
    )
    return result


def _combine_exit_conditions(
    df: pd.DataFrame,
    group: SignalGroupConfig,
    apply_scope: str,
    prefix: str,
) -> pd.Series:
    scoped = [
        condition
        for condition in group.conditions
        if condition.type != "trailing_stop" and condition.apply in {"always", apply_scope}
    ]
    return _combine_conditions(df, SignalGroupConfig(mode=group.mode, conditions=scoped), prefix)


def _combine_conditions(df: pd.DataFrame, group: SignalGroupConfig, prefix: str) -> pd.Series:
    if not group.conditions:
        return pd.Series(False, index=df.index)

    signals = []
    for idx, condition in enumerate(group.conditions):
        if condition.type == "trailing_stop":
            continue
        signal = _evaluate_condition(df, condition)
        signals.append(signal)
        df[_condition_column(prefix, condition, idx)] = signal.fillna(False).astype(bool)

    if not signals:
        return pd.Series(False, index=df.index)

    combined = signals[0]
    for signal in signals[1:]:
        if group.mode == "all":
            combined = combined & signal
        else:
            combined = combined | signal
    return combined.fillna(False).astype(bool)


def _evaluate_condition(df: pd.DataFrame, condition: ConditionConfig) -> pd.Series:
    if condition.type == "breakout":
        return _breakout_signal(df, condition)
    if condition.type == "ma_relation":
        return _ma_relation_signal(df, condition)
    if condition.type in {"price_vs_ma", "ma_break"}:
        ma = _moving_average(df[condition.field], condition.ma_window, condition.ma_method)
        return _compare(df[condition.field], condition.op, ma)
    if condition.type == "roc":
        roc = df[condition.field].pct_change(condition.window)
        return _compare(roc, condition.op, condition.threshold)
    if condition.type == "rolling_mean_threshold":
        rolling_mean = df[condition.field].rolling(
            condition.window,
            min_periods=condition.window,
        ).mean()
        return _compare(rolling_mean, condition.op, condition.threshold)
    raise ValueError(f"unsupported condition type: {condition.type}")


def _breakout_signal(df: pd.DataFrame, condition: ConditionConfig) -> pd.Series:
    # 未来函数风险点：突破阈值默认使用 shift=1，T 日收盘只比较 T-1 及以前的高点。
    breakout_high = (
        df[condition.breakout_field]
        .shift(condition.shift)
        .rolling(condition.window, min_periods=condition.window)
        .max()
    )
    df["breakout_high"] = breakout_high
    return _compare(df[condition.field], condition.op, breakout_high)


def _ma_relation_signal(df: pd.DataFrame, condition: ConditionConfig) -> pd.Series:
    fast = _moving_average(df[condition.field], condition.fast_window, condition.ma_method)
    slow = _moving_average(df[condition.field], condition.slow_window, condition.ma_method)
    df["ma_short"] = fast
    df["ma_long"] = slow
    return _compare(fast, condition.op, slow)


def _moving_average(series: pd.Series, window: int | None, method: str) -> pd.Series:
    if window is None:
        raise ValueError("moving average window is required")
    if method == "ema":
        return series.ewm(span=window, min_periods=window, adjust=False).mean()
    return series.rolling(window, min_periods=window).mean()


def _compare(left, op: str, right) -> pd.Series:
    if op == ">":
        return left > right
    if op == ">=":
        return left >= right
    if op == "<":
        return left < right
    if op == "<=":
        return left <= right
    if op == "==":
        return left == right
    if op == "!=":
        return left != right
    raise ValueError(f"unsupported comparison operator: {op}")


def _condition_column(prefix: str, condition: ConditionConfig, idx: int) -> str:
    name = condition.name or f"{condition.type}_{idx}"
    return f"{prefix}_{name}"


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
