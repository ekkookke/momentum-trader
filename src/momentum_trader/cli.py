from __future__ import annotations

from pathlib import Path
from typing import Annotated

import pandas as pd
import typer

from momentum_trader.backtest.engine import BacktestResult
from momentum_trader.config import load_config
from momentum_trader.data.loader import MarketDataLoader
from momentum_trader.utils.logging import console

app = typer.Typer(help="A-share ETF momentum backtest CLI.")
DEFAULT_CONFIG = Path("configs/default.yaml")
ConfigOption = Annotated[Path, typer.Option("--config", "-c")]


@app.command("fetch-data")
def fetch_data(config: ConfigOption = DEFAULT_CONFIG) -> None:
    cfg = load_config(config)
    loader = MarketDataLoader(cfg)
    market_data = loader.load_all()
    console.print(f"Loaded {len(market_data.etfs)} ETFs and benchmark data.")


@app.command("run-backtest")
def run_backtest_cmd(config: ConfigOption = DEFAULT_CONFIG) -> None:
    from momentum_trader.backtest.engine import run_backtest, save_backtest_result

    cfg = load_config(config)
    market_data = MarketDataLoader(cfg).load_all()
    result = run_backtest(cfg, market_data.etfs, market_data.benchmark)
    save_backtest_result(result, cfg.report.output_dir)
    console.print(f"Backtest outputs saved under {cfg.report.output_dir}.")


@app.command("report")
def report_cmd(config: ConfigOption = DEFAULT_CONFIG) -> None:
    from momentum_trader.report.exports import export_report

    cfg = load_config(config)
    reports_dir = cfg.report.output_dir / "reports"
    trades_dir = cfg.report.output_dir / "trades"
    equity_path = reports_dir / "equity_curve.csv"
    orders_path = trades_dir / "orders.csv"
    closed_trades_path = trades_dir / "closed_trades.csv"

    missing = [path for path in [equity_path, orders_path, closed_trades_path] if not path.exists()]
    if missing:
        missing_text = ", ".join(str(path) for path in missing)
        raise typer.BadParameter(f"missing backtest output files: {missing_text}")

    result = BacktestResult(
        equity_curve=pd.read_csv(equity_path, parse_dates=["date"]),
        orders=pd.read_csv(orders_path),
        closed_trades=pd.read_csv(closed_trades_path),
        benchmark=MarketDataLoader(cfg).load_benchmark(),
    )
    paths = export_report(cfg, result)
    for name, path in paths.items():
        console.print(f"{name}: {path}")


@app.command("run")
def run(config: ConfigOption = DEFAULT_CONFIG) -> None:
    from momentum_trader.backtest.engine import run_backtest, save_backtest_result
    from momentum_trader.report.exports import export_report

    cfg = load_config(config)
    market_data = MarketDataLoader(cfg).load_all()
    result = run_backtest(cfg, market_data.etfs, market_data.benchmark)
    save_backtest_result(result, cfg.report.output_dir)
    paths = export_report(cfg, result)
    for name, path in paths.items():
        console.print(f"{name}: {path}")


if __name__ == "__main__":
    app()
