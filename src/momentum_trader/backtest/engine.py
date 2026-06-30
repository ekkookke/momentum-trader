from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from momentum_trader.config import AppConfig
from momentum_trader.strategy.signals import prepare_strategy_frame


@dataclass
class BacktestResult:
    equity_curve: pd.DataFrame
    orders: pd.DataFrame
    closed_trades: pd.DataFrame
    benchmark: pd.DataFrame


def run_backtest(
    config: AppConfig,
    etf_frames: dict[str, pd.DataFrame],
    benchmark_frame: pd.DataFrame,
) -> BacktestResult:
    import backtrader as bt

    from momentum_trader.backtest.analyzers import analyzer_to_frame, make_portfolio_value_analyzer
    from momentum_trader.backtest.broker import make_percent_commission_info
    from momentum_trader.backtest.bt_strategy import make_etf_pandas_data, make_momentum_strategy
    from momentum_trader.backtest.trade_log import closed_trades_to_frame, orders_to_frame

    cerebro = bt.Cerebro(cheat_on_open=True)
    cerebro.broker.setcash(config.backtest.initial_cash)
    cerebro.broker.addcommissioninfo(make_percent_commission_info(config.backtest.commission_rate))

    data_cls = make_etf_pandas_data()
    for etf in config.universe:
        raw = etf_frames[etf.symbol]
        prepared = prepare_strategy_frame(
            raw,
            strategy=config.strategy,
            limit_up_threshold=config.backtest.limit_up_threshold,
        )
        feed_df = prepared.set_index("date")
        cerebro.adddata(data_cls(dataname=feed_df, name=etf.symbol))

    strategy_cls = make_momentum_strategy()
    analyzer_cls = make_portfolio_value_analyzer()
    cerebro.addstrategy(strategy_cls, app_config=config)
    cerebro.addanalyzer(analyzer_cls, _name="portfolio_value")

    strategies = cerebro.run()
    strategy = strategies[0]
    equity = analyzer_to_frame(strategy.analyzers.portfolio_value.get_analysis())

    return BacktestResult(
        equity_curve=equity,
        orders=orders_to_frame(strategy.order_records),
        closed_trades=closed_trades_to_frame(strategy.closed_trade_records),
        benchmark=benchmark_frame,
    )


def save_backtest_result(result: BacktestResult, output_dir: Path) -> None:
    reports_dir = output_dir / "reports"
    trades_dir = output_dir / "trades"
    reports_dir.mkdir(parents=True, exist_ok=True)
    trades_dir.mkdir(parents=True, exist_ok=True)

    result.equity_curve.to_csv(reports_dir / "equity_curve.csv", index=False)
    result.orders.to_csv(trades_dir / "orders.csv", index=False)
    result.closed_trades.to_csv(trades_dir / "closed_trades.csv", index=False)

