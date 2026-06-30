from __future__ import annotations

from pathlib import Path

import pandas as pd

from momentum_trader.backtest.engine import BacktestResult
from momentum_trader.config import AppConfig
from momentum_trader.report.metrics import (
    compute_equity_metrics,
    compute_symbol_pnl,
    compute_trade_metrics,
)
from momentum_trader.report.plots import plot_equity_vs_benchmark


def export_report(config: AppConfig, result: BacktestResult) -> dict[str, Path]:
    output_dir = config.report.output_dir
    reports_dir = output_dir / "reports"
    trades_dir = output_dir / "trades"
    charts_dir = output_dir / "charts"
    reports_dir.mkdir(parents=True, exist_ok=True)
    trades_dir.mkdir(parents=True, exist_ok=True)
    charts_dir.mkdir(parents=True, exist_ok=True)

    equity_metrics = compute_equity_metrics(
        result.equity_curve,
        risk_free_rate=config.report.risk_free_rate,
        trading_days_per_year=config.report.trading_days_per_year,
    )
    trade_metrics = compute_trade_metrics(result.orders, result.closed_trades)
    metrics = pd.DataFrame([{**equity_metrics, **trade_metrics}])
    symbol_pnl = compute_symbol_pnl(result.closed_trades)

    metrics_path = reports_dir / "metrics.csv"
    symbol_pnl_path = reports_dir / "symbol_pnl.csv"
    orders_path = trades_dir / "orders.csv"
    closed_trades_path = trades_dir / "closed_trades.csv"
    chart_path = charts_dir / "equity_vs_hs300.png"

    metrics.to_csv(metrics_path, index=False)
    symbol_pnl.to_csv(symbol_pnl_path, index=False)
    result.orders.to_csv(orders_path, index=False)
    result.closed_trades.to_csv(closed_trades_path, index=False)
    plot_equity_vs_benchmark(
        result.equity_curve,
        result.benchmark,
        chart_path,
        config.report.font_candidates,
    )

    return {
        "metrics": metrics_path,
        "symbol_pnl": symbol_pnl_path,
        "orders": orders_path,
        "closed_trades": closed_trades_path,
        "chart": chart_path,
    }

