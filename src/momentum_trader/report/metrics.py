from __future__ import annotations

import numpy as np
import pandas as pd


def compute_equity_metrics(
    equity_curve: pd.DataFrame,
    risk_free_rate: float = 0.0,
    trading_days_per_year: int = 252,
) -> dict[str, float]:
    if equity_curve.empty:
        return {
            "annual_return": np.nan,
            "sharpe": np.nan,
            "max_drawdown": np.nan,
            "calmar": np.nan,
        }

    equity = equity_curve["equity"].astype(float)
    returns = equity.pct_change().dropna()
    total_return = equity.iloc[-1] / equity.iloc[0] - 1
    years = max(len(equity) / trading_days_per_year, 1 / trading_days_per_year)
    annual_return = (1 + total_return) ** (1 / years) - 1

    excess_daily = returns - risk_free_rate / trading_days_per_year
    sharpe = np.nan
    if excess_daily.std(ddof=1) > 0:
        sharpe = excess_daily.mean() / excess_daily.std(ddof=1) * np.sqrt(trading_days_per_year)

    running_max = equity.cummax()
    drawdown = equity / running_max - 1
    max_drawdown = drawdown.min()
    calmar = np.nan if max_drawdown == 0 else annual_return / abs(max_drawdown)

    return {
        "annual_return": float(annual_return),
        "sharpe": float(sharpe),
        "max_drawdown": float(max_drawdown),
        "calmar": float(calmar),
    }


def compute_trade_metrics(orders: pd.DataFrame, closed_trades: pd.DataFrame) -> dict[str, float]:
    total_fees = float(orders["commission"].sum()) if not orders.empty else 0.0
    total_orders = int(len(orders))

    if closed_trades.empty:
        return {
            "win_rate": np.nan,
            "profit_loss_ratio": np.nan,
            "avg_holding_bars": np.nan,
            "total_trades": 0,
            "total_orders": total_orders,
            "total_fees": total_fees,
        }

    pnl = closed_trades["pnl_after_cost"].astype(float)
    wins = pnl[pnl > 0]
    losses = pnl[pnl < 0]
    win_rate = len(wins) / len(pnl)
    profit_loss_ratio = np.nan
    if not losses.empty:
        profit_loss_ratio = wins.mean() / abs(losses.mean()) if not wins.empty else 0.0

    return {
        "win_rate": float(win_rate),
        "profit_loss_ratio": float(profit_loss_ratio),
        "avg_holding_bars": float(closed_trades["holding_bars"].mean()),
        "total_trades": int(len(closed_trades)),
        "total_orders": total_orders,
        "total_fees": total_fees,
    }


def compute_symbol_pnl(closed_trades: pd.DataFrame) -> pd.DataFrame:
    if closed_trades.empty:
        return pd.DataFrame(columns=["symbol", "pnl_after_cost", "trade_count"])

    return (
        closed_trades.groupby("symbol", as_index=False)
        .agg(pnl_after_cost=("pnl_after_cost", "sum"), trade_count=("symbol", "size"))
        .sort_values("pnl_after_cost", ascending=False)
    )

