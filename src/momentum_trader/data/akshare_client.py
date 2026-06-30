from __future__ import annotations

import pandas as pd

from momentum_trader.data.schema import normalize_ohlcv


class AkShareClient:
    def fetch_etf_daily(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        period: str = "daily",
        adjust: str = "qfq",
    ) -> pd.DataFrame:
        import akshare as ak

        # 复权处理风险点：ETF 全部使用前复权 qfq，保证信号与成交价格口径一致。
        raw = ak.fund_etf_hist_em(
            symbol=symbol,
            period=period,
            start_date=start_date.replace("-", ""),
            end_date=end_date.replace("-", ""),
            adjust=adjust,
        )
        return normalize_ohlcv(raw)

    def fetch_index_daily(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        import akshare as ak

        start = start_date.replace("-", "")
        end = end_date.replace("-", "")
        try:
            raw = ak.stock_zh_index_daily_em(symbol=symbol, start_date=start, end_date=end)
        except AttributeError:
            raw = ak.stock_zh_index_daily(symbol=symbol)

        df = normalize_ohlcv(raw)
        mask = (df["date"] >= pd.Timestamp(start_date)) & (df["date"] <= pd.Timestamp(end_date))
        return df.loc[mask].reset_index(drop=True)

