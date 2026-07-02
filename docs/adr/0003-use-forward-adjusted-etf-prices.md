# Use forward-adjusted ETF prices for formal strategy evaluation

Accepted. Momentum Trader uses Forward-adjusted Price as the official price meaning for tradable ETF Signal Scan and Backtest, because breakout, moving-average, pyramiding, and drawdown rules are not comparable when raw and adjusted histories are mixed. Unadjusted sources may remain useful for engineering demonstrations or data-source troubleshooting, but they should not be used to explain formal strategy performance.

**Considered Options**

- Allow raw and adjusted ETF histories to both count as formal backtest inputs.
- Require formal ETF strategy evaluation to use forward-adjusted historical prices.

**Consequences**

Market Data Sources that cannot provide forward-adjusted ETF history should not be used as formal strategy-evaluation inputs.

Fallback Market Data Sources are not automatically lower quality than the Formal Market Data Source. They can support formal strategy evaluation when they preserve the same Forward-adjusted Price semantics; otherwise they are limited to connectivity checks, engineering troubleshooting, or temporary sanity checks.

Formal Signal Conditions must not mix raw and adjusted ETF price fields inside one Signal Rule Expression. Raw price diagnostics may help data-source troubleshooting, but they are not formal Signal Inputs for breakout, moving-average, momentum, or other tradable ETF signal rules.
