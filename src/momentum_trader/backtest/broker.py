from __future__ import annotations


def make_percent_commission_info(commission_rate: float):
    import backtrader as bt

    class PercentCommissionInfo(bt.CommInfoBase):
        params = (
            ("commission", commission_rate),
            ("stocklike", True),
            ("commtype", bt.CommInfoBase.COMM_PERC),
            ("percabs", True),
        )

    return PercentCommissionInfo()

