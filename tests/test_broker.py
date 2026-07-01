from __future__ import annotations

import pytest

from momentum_trader.backtest.broker import make_percent_commission_info


def test_percent_commission_info_uses_absolute_percent_rate() -> None:
    commission = make_percent_commission_info(0.0015)

    assert commission.getcommission(size=100, price=10.0) == pytest.approx(1.5)
