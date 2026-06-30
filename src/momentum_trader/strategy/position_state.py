from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass
class PositionState:
    entry_date: date | None = None
    entry_price: float | None = None
    peak_price: float | None = None
    pyramid_level: int = 0
    filled_intent_pct: float = 0.0

    @property
    def is_open(self) -> bool:
        return self.entry_price is not None and self.pyramid_level > 0

    def reset(self) -> None:
        self.entry_date = None
        self.entry_price = None
        self.peak_price = None
        self.pyramid_level = 0
        self.filled_intent_pct = 0.0

    def mark_entry(self, trade_date: date, price: float, allocation_pct: float) -> None:
        if not self.is_open:
            self.entry_date = trade_date
            self.entry_price = price
            self.peak_price = price
        self.pyramid_level += 1
        self.filled_intent_pct += allocation_pct

    def update_peak(self, close_price: float) -> None:
        if self.peak_price is None:
            self.peak_price = close_price
        else:
            self.peak_price = max(self.peak_price, close_price)

