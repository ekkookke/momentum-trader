from __future__ import annotations

import pandas as pd


def make_portfolio_value_analyzer():
    import backtrader as bt

    class PortfolioValueAnalyzer(bt.Analyzer):
        def start(self) -> None:
            self.values = []

        def next(self) -> None:
            current_date = self.strategy.datas[0].datetime.date(0)
            self.values.append({"date": current_date, "equity": self.strategy.broker.getvalue()})

        def get_analysis(self):
            return self.values

    return PortfolioValueAnalyzer


def analyzer_to_frame(rows: list[dict]) -> pd.DataFrame:
    if not rows:
        return pd.DataFrame(columns=["date", "equity"])
    df = pd.DataFrame(rows)
    df["date"] = pd.to_datetime(df["date"])
    return df.sort_values("date").reset_index(drop=True)

