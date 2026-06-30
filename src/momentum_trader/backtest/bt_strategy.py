from __future__ import annotations

from math import floor

from momentum_trader.config import AppConfig
from momentum_trader.strategy.position_state import PositionState
from momentum_trader.strategy.rules import is_pyramid_complete, next_pyramid_step


def make_etf_pandas_data():
    import backtrader as bt

    class ETFPandasData(bt.feeds.PandasData):
        lines = ("entry_signal", "open_limit_up", "ma_short", "ma_long", "breakout_high")
        params = (
            ("datetime", None),
            ("open", "open"),
            ("high", "high"),
            ("low", "low"),
            ("close", "close"),
            ("volume", "volume"),
            ("openinterest", -1),
            ("entry_signal", "entry_signal"),
            ("open_limit_up", "open_limit_up"),
            ("ma_short", "ma_short"),
            ("ma_long", "ma_long"),
            ("breakout_high", "breakout_high"),
        )

    return ETFPandasData


def make_momentum_strategy():
    import backtrader as bt

    class MomentumPyramidStrategy(bt.Strategy):
        params = (("app_config", None),)

        def __init__(self) -> None:
            if self.p.app_config is None:
                raise ValueError("app_config is required")
            self.config: AppConfig = self.p.app_config
            self.position_states = {data: PositionState() for data in self.datas}
            self.order_records = []
            self.closed_trade_records = []

        def prenext_open(self) -> None:
            self.next_open()

        def nextstart_open(self) -> None:
            self.next_open()

        def next_open(self) -> None:
            # 成交时点风险点：启用 backtrader cheat_on_open 后，next_open 在 T+1 开盘前触发；
            # 此处只读取 [-1] 的 T 日收盘信号并用 [0] 的 T+1 开盘价下单。
            for data in self.datas:
                if not self._can_trade_current_bar(data):
                    continue
                self._maybe_exit(data)

            entry_slots = self.config.backtest.max_positions - self._open_position_count()
            for data in self.datas:
                if not self._can_trade_current_bar(data):
                    continue
                submitted_new_entry = self._maybe_enter_or_add(data, entry_slots)
                if submitted_new_entry and not self.getposition(data).size:
                    # 同日多个 ETF 入场信号按配置顺序优先，提交首仓订单后即占用一个名额。
                    entry_slots -= 1

        def prenext(self) -> None:
            self.next()

        def nextstart(self) -> None:
            self.next()

        def next(self) -> None:
            for data, state in self.position_states.items():
                if self.getposition(data).size and self._is_current_bar(data):
                    state.update_peak(float(data.close[0]))

        def _can_trade_current_bar(self, data) -> bool:
            # ETF 上市日期/停牌处理风险点：多标的回测中，backtrader 在所有数据都
            # 就绪前会进入 prenext_open。这里允许已上市且有足够历史的 ETF 交易，
            # 但只处理当前日期同步的数据，避免未上市或停牌数据沿用旧 bar。
            return len(data) >= 2 and self._is_current_bar(data)

        def _is_current_bar(self, data) -> bool:
            current_date = self._current_data_date()
            return (
                current_date is not None
                and len(data) > 0
                and data.datetime.date(0) == current_date
            )

        def _current_data_date(self):
            dates = [data.datetime.date(0) for data in self.datas if len(data) > 0]
            return max(dates) if dates else None

        def _maybe_exit(self, data) -> None:
            position = self.getposition(data)
            if not position.size:
                return

            state = self.position_states[data]
            prev_close = float(data.close[-1])
            prev_ma_short = float(data.ma_short[-1])
            reason = None

            if not is_pyramid_complete(self.config.strategy, state.pyramid_level):
                if prev_close < prev_ma_short:
                    reason = "break_ma_short"
            elif state.peak_price is not None:
                stop_price = state.peak_price * (1 - self.config.strategy.trailing_stop_pct)
                if prev_close <= stop_price:
                    reason = "trailing_stop"

            if reason:
                order = self.sell(data=data, size=abs(position.size))
                order.addinfo(reason=reason)

        def _maybe_enter_or_add(self, data, entry_slots: int) -> bool:
            position = self.getposition(data)
            state = self.position_states[data]

            if bool(data.open_limit_up[0]):
                # 涨跌停风险点：T+1 开盘一字涨停时，买入/加仓订单直接跳过。
                return False

            if not position.size:
                if not bool(data.entry_signal[-1]):
                    return False
                if entry_slots <= 0:
                    return False
                return self._buy_pyramid_step(data, "entry")

            step = next_pyramid_step(self.config.strategy, state.pyramid_level)
            if step is None or state.entry_price is None:
                return False

            prev_close = float(data.close[-1])
            if prev_close >= state.entry_price * (1 + step.trigger_pct):
                return self._buy_pyramid_step(data, f"pyramid_{state.pyramid_level + 1}")
            return False

        def _buy_pyramid_step(self, data, reason: str) -> bool:
            state = self.position_states[data]
            step = next_pyramid_step(self.config.strategy, state.pyramid_level)
            if step is None:
                return False

            open_price = float(data.open[0])
            if open_price <= 0:
                return False

            intent_value = self.broker.getvalue() * self.config.backtest.intent_position_pct
            order_value = intent_value * step.allocation_pct
            size = floor(order_value / open_price)
            if size <= 0:
                return False

            order = self.buy(data=data, size=size)
            order.addinfo(reason=reason, allocation_pct=step.allocation_pct)
            return True

        def _open_position_count(self) -> int:
            return sum(1 for data in self.datas if self.getposition(data).size)

        def notify_order(self, order) -> None:
            if order.status != order.Completed:
                return

            from momentum_trader.backtest.trade_log import OrderRecord

            side = "BUY" if order.isbuy() else "SELL"
            executed_date = bt.num2date(order.executed.dt).date()
            self.order_records.append(
                OrderRecord(
                    date=executed_date,
                    symbol=order.data._name,
                    side=side,
                    size=float(order.executed.size),
                    price=float(order.executed.price),
                    value=float(order.executed.value),
                    commission=float(order.executed.comm),
                    reason=order.info.get("reason", ""),
                )
            )

            state = self.position_states[order.data]
            if order.isbuy():
                state.mark_entry(
                    executed_date,
                    float(order.executed.price),
                    float(order.info.get("allocation_pct", 0.0)),
                )
            elif not self.getposition(order.data).size:
                state.reset()

        def notify_trade(self, trade) -> None:
            if not trade.isclosed:
                return

            from momentum_trader.backtest.trade_log import ClosedTradeRecord

            self.closed_trade_records.append(
                ClosedTradeRecord(
                    symbol=trade.data._name,
                    entry_date=bt.num2date(trade.dtopen).date() if trade.dtopen else None,
                    exit_date=bt.num2date(trade.dtclose).date()
                    if trade.dtclose
                    else trade.data.datetime.date(0),
                    pnl=float(trade.pnl),
                    pnl_after_cost=float(trade.pnlcomm),
                    holding_bars=int(trade.barlen),
                )
            )

    return MomentumPyramidStrategy
