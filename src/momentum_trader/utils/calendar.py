from __future__ import annotations

import pandas as pd


def trading_days_from_frame(df: pd.DataFrame) -> pd.Series:
    return pd.to_datetime(df["date"]).drop_duplicates().sort_values()

