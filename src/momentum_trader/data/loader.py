from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from momentum_trader.config import AppConfig, ETFConfig
from momentum_trader.data.akshare_client import AkShareClient
from momentum_trader.data.cache import ParquetCache


@dataclass
class MarketData:
    etfs: dict[str, pd.DataFrame]
    benchmark: pd.DataFrame


class MarketDataLoader:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.client = AkShareClient()
        self.cache = ParquetCache(config.data.raw_dir, config.data.fetch_date_format)

    def load_all(self) -> MarketData:
        etfs = {etf.symbol: self.load_etf(etf) for etf in self.config.universe}
        benchmark = self.load_benchmark()
        return MarketData(etfs=etfs, benchmark=benchmark)

    def load_etf(self, etf: ETFConfig) -> pd.DataFrame:
        start = self.config.backtest.start_date
        end = self.config.backtest.end_date
        key = self.cache.key(
            f"{self.config.data.source}_etf", etf.symbol, start, end, self.config.data.adjust
        )

        df = self.cache.read_or_fetch(
            key,
            lambda: self.client.fetch_etf_daily(
                symbol=etf.symbol,
                start_date=start,
                end_date=end,
                period=self.config.data.etf_period,
                adjust=self.config.data.adjust,
                source=self.config.data.source,
            ),
        )
        return self._clip_valid_history(df, start, end)

    def load_benchmark(self) -> pd.DataFrame:
        start = self.config.backtest.start_date
        end = self.config.backtest.end_date
        symbol = self.config.data.benchmark_symbol
        key = self.cache.key(f"{self.config.data.source}_index", symbol, start, end, "none")
        df = self.cache.read_or_fetch(
            key,
            lambda: self.client.fetch_index_daily(
                symbol=symbol,
                start_date=start,
                end_date=end,
                source=self.config.data.source,
            ),
        )
        return self._clip_valid_history(df, start, end)

    @staticmethod
    def _clip_valid_history(df: pd.DataFrame, start_date: str, end_date: str) -> pd.DataFrame:
        start = pd.Timestamp(start_date)
        end = pd.Timestamp(end_date)
        clipped = df.loc[(df["date"] >= start) & (df["date"] <= end)].copy()

        # 停牌处理风险点：不做交易日补齐、不 forward fill，AkShare 缺失的停牌日不会参与信号或成交。
        # ETF 上市日期风险点：若回测起点早于上市日，数据自然从首个有效交易日开始。
        return clipped.sort_values("date").reset_index(drop=True)
