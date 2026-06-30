from __future__ import annotations

from dataclasses import dataclass
from datetime import date

import pandas as pd


@dataclass
class OrderRecord:
    date: date
    symbol: str
    side: str
    size: float
    price: float
    value: float
    commission: float
    reason: str


@dataclass
class ClosedTradeRecord:
    symbol: str
    entry_date: date | None
    exit_date: date | None
    pnl: float
    pnl_after_cost: float
    holding_bars: int


def orders_to_frame(records: list[OrderRecord]) -> pd.DataFrame:
    columns = ["date", "symbol", "side", "size", "price", "value", "commission", "reason"]
    return pd.DataFrame([record.__dict__ for record in records], columns=columns)


def closed_trades_to_frame(records: list[ClosedTradeRecord]) -> pd.DataFrame:
    columns = [
        "symbol",
        "entry_date",
        "exit_date",
        "pnl",
        "pnl_after_cost",
        "holding_bars",
    ]
    return pd.DataFrame([record.__dict__ for record in records], columns=columns)
