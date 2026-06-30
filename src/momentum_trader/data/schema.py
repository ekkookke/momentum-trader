from __future__ import annotations

from collections.abc import Iterable

import pandas as pd

REQUIRED_COLUMNS = ["date", "open", "high", "low", "close", "volume"]
STANDARD_COLUMNS = [*REQUIRED_COLUMNS, "amount"]

AKSHARE_COLUMN_MAP = {
    "日期": "date",
    "开盘": "open",
    "最高": "high",
    "最低": "low",
    "收盘": "close",
    "成交量": "volume",
    "成交额": "amount",
    "振幅": "amplitude",
    "涨跌幅": "pct_change",
    "涨跌额": "change",
    "换手率": "turnover",
}


def normalize_ohlcv(raw: pd.DataFrame) -> pd.DataFrame:
    df = raw.rename(columns=AKSHARE_COLUMN_MAP).copy()
    missing = [column for column in REQUIRED_COLUMNS if column not in df.columns]
    if missing:
        raise ValueError(f"missing required OHLCV columns: {missing}")
    if "amount" not in df.columns:
        df["amount"] = pd.NA

    df["date"] = pd.to_datetime(df["date"]).dt.normalize()
    numeric_columns = [column for column in df.columns if column != "date"]
    for column in numeric_columns:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    df = df.sort_values("date").drop_duplicates(subset=["date"], keep="last")
    return df.reset_index(drop=True)


def assert_columns(df: pd.DataFrame, columns: Iterable[str]) -> None:
    missing = [column for column in columns if column not in df.columns]
    if missing:
        raise ValueError(f"dataframe missing columns: {missing}")
