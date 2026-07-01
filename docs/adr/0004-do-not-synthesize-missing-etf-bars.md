# Do not synthesize missing ETF daily bars

Accepted. Momentum Trader treats missing ETF daily bars as absence of tradable data, not as flat prices to be forward-filled or placeholder bars to be generated before listing. This keeps Signal Scan and Backtest from trading on synthetic prices, while requiring future data-quality checks to surface suspicious Data Gaps for human review instead of silently treating every missing bar as a legitimate suspension.

**Considered Options**

- Align every ETF to a shared trading calendar and forward-fill missing prices.
- Preserve only returned Tradable Daily Bars and make unexplained gaps visible.

**Consequences**

Multi-ETF alignment and reporting must tolerate missing bars. Data Gap checks should warn on suspicious gaps, but they should not rely only on a naive calendar-day threshold because Chinese market holidays can create legitimate gaps longer than an ordinary weekend.
