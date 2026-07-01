from __future__ import annotations

from pathlib import Path
from typing import Annotated

import pandas as pd
import typer

from momentum_trader.backtest.engine import BacktestResult
from momentum_trader.config import load_config
from momentum_trader.data.loader import MarketDataLoader
from momentum_trader.report.run_outputs import (
    append_run_index,
    build_output_locations,
    config_with_output_dir,
)
from momentum_trader.utils.logging import console

app = typer.Typer(help="A-share ETF momentum backtest CLI.")
DEFAULT_CONFIG = Path("configs/default.yaml")
ConfigOption = Annotated[Path, typer.Option("--config", "-c")]
PortOption = Annotated[int, typer.Option("--port", "-p")]
TagOption = Annotated[str, typer.Option("--tag", help="Run tag used under outputs/runs/{tag}.")]
ServeTagOption = Annotated[str | None, typer.Option("--tag", help="Serve an archived run tag.")]


@app.command("fetch-data")
def fetch_data(config: ConfigOption = DEFAULT_CONFIG) -> None:
    cfg = load_config(config)
    loader = MarketDataLoader(cfg)
    market_data = loader.load_all()
    console.print(f"Loaded {len(market_data.etfs)} ETFs and benchmark data.")


@app.command("run-backtest")
def run_backtest_cmd(config: ConfigOption = DEFAULT_CONFIG, tag: TagOption = "default") -> None:
    from momentum_trader.backtest.engine import run_backtest, save_backtest_result

    cfg = load_config(config)
    locations = build_output_locations(cfg.report.output_dir, tag)
    market_data = MarketDataLoader(cfg).load_all()
    result = run_backtest(cfg, market_data.etfs, market_data.benchmark)
    save_backtest_result(result, locations.run_dir)
    save_backtest_result(result, locations.latest_dir)
    console.print(f"Backtest outputs saved under {locations.run_dir}.")
    console.print(f"Latest outputs refreshed under {locations.latest_dir}.")


@app.command("report")
def report_cmd(config: ConfigOption = DEFAULT_CONFIG, tag: TagOption = "default") -> None:
    from momentum_trader.report.exports import export_report

    cfg = load_config(config)
    locations = build_output_locations(cfg.report.output_dir, tag)
    source_dir = (
        locations.run_dir if _has_backtest_outputs(locations.run_dir) else locations.latest_dir
    )
    reports_dir = source_dir / "reports"
    trades_dir = source_dir / "trades"
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
    _write_saved_result(cfg, result, locations.run_dir)
    paths = export_report(config_with_output_dir(cfg, locations.run_dir), result)
    _write_saved_result(cfg, result, locations.latest_dir)
    latest_paths = export_report(config_with_output_dir(cfg, locations.latest_dir), result)
    index_path = append_run_index(cfg, locations)
    for name, path in paths.items():
        console.print(f"{name}: {path}")
    console.print(f"latest_html: {latest_paths['html']}")
    console.print(f"index: {index_path}")


@app.command("run")
def run(config: ConfigOption = DEFAULT_CONFIG, tag: TagOption = "default") -> None:
    from momentum_trader.backtest.engine import run_backtest, save_backtest_result
    from momentum_trader.report.exports import export_report

    cfg = load_config(config)
    locations = build_output_locations(cfg.report.output_dir, tag)
    market_data = MarketDataLoader(cfg).load_all()
    result = run_backtest(cfg, market_data.etfs, market_data.benchmark)
    save_backtest_result(result, locations.run_dir)
    paths = export_report(config_with_output_dir(cfg, locations.run_dir), result)
    save_backtest_result(result, locations.latest_dir)
    latest_paths = export_report(config_with_output_dir(cfg, locations.latest_dir), result)
    index_path = append_run_index(cfg, locations)
    for name, path in paths.items():
        console.print(f"{name}: {path}")
    console.print(f"latest_html: {latest_paths['html']}")
    console.print(f"index: {index_path}")


@app.command("serve-report")
def serve_report(
    config: ConfigOption = DEFAULT_CONFIG,
    port: PortOption = 8765,
    tag: ServeTagOption = None,
) -> None:
    import functools
    from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

    cfg = load_config(config)
    output_dir = (
        build_output_locations(cfg.report.output_dir, tag).run_dir
        if tag is not None
        else cfg.report.output_dir
    )
    if not output_dir.exists():
        raise typer.BadParameter(f"output directory does not exist: {output_dir}")

    handler = functools.partial(SimpleHTTPRequestHandler, directory=str(output_dir))
    server = ThreadingHTTPServer(("127.0.0.1", port), handler)
    console.print(f"Serving report at http://127.0.0.1:{port}/report.html")
    server.serve_forever()


def _has_backtest_outputs(output_dir: Path) -> bool:
    return all(
        path.exists()
        for path in [
            output_dir / "reports" / "equity_curve.csv",
            output_dir / "trades" / "orders.csv",
            output_dir / "trades" / "closed_trades.csv",
        ]
    )


def _write_saved_result(config, result: BacktestResult, output_dir: Path) -> None:
    from momentum_trader.backtest.engine import save_backtest_result

    save_backtest_result(result, output_dir)


if __name__ == "__main__":
    app()
