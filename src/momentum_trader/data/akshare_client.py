from __future__ import annotations

import pandas as pd

from momentum_trader.data.schema import normalize_ohlcv


def _inject_system_truststore() -> None:
    try:
        import truststore
    except ImportError:
        return
    truststore.inject_into_ssl()


class AkShareClient:
    def fetch_etf_daily(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        period: str = "daily",
        adjust: str = "qfq",
        source: str = "tencent",
    ) -> pd.DataFrame:
        _inject_system_truststore()
        import akshare as ak

        if source == "sina":
            # 演示模式风险点：新浪接口不支持前复权参数，只用于验证回测管线能否跑通。
            raw = ak.fund_etf_hist_sina(symbol=_sina_etf_symbol(symbol))
        elif source == "tencent":
            # 复权处理风险点：腾讯接口支持 adjust="qfq"，作为默认正式前复权 ETF 数据源。
            raw = ak.stock_zh_a_hist_tx(
                symbol=_market_symbol(symbol),
                start_date=start_date.replace("-", ""),
                end_date=end_date.replace("-", ""),
                adjust=adjust,
                timeout=20,
            )
        else:
            # EastMoney 前复权接口保留为备选；在部分网络环境下可能被本机代理返回 502。
            raw = ak.fund_etf_hist_em(
                symbol=symbol,
                period=period,
                start_date=start_date.replace("-", ""),
                end_date=end_date.replace("-", ""),
                adjust=adjust,
            )
        return normalize_ohlcv(raw)

    def fetch_index_daily(
        self, symbol: str, start_date: str, end_date: str, source: str = "tencent"
    ) -> pd.DataFrame:
        _inject_system_truststore()
        import akshare as ak

        start = start_date.replace("-", "")
        end = end_date.replace("-", "")
        if source == "sina":
            raw = ak.stock_zh_index_daily(symbol=symbol)
        elif source == "tencent":
            raw = ak.stock_zh_index_daily_tx(
                symbol=_market_symbol(symbol),
                start_date=start,
                end_date=end,
            )
        else:
            try:
                raw = ak.stock_zh_index_daily_em(symbol=symbol, start_date=start, end_date=end)
            except AttributeError:
                raw = ak.stock_zh_index_daily(symbol=symbol)

        df = normalize_ohlcv(raw)
        mask = (df["date"] >= pd.Timestamp(start_date)) & (df["date"] <= pd.Timestamp(end_date))
        return df.loc[mask].reset_index(drop=True)


def _sina_etf_symbol(symbol: str) -> str:
    if symbol.startswith(("sh", "sz")):
        return symbol
    if symbol.startswith(("5", "6", "9")):
        return f"sh{symbol}"
    return f"sz{symbol}"


def _market_symbol(symbol: str) -> str:
    if symbol.startswith(("sh", "sz")):
        return symbol
    if symbol.startswith(("5", "6", "9")):
        return f"sh{symbol}"
    return f"sz{symbol}"
