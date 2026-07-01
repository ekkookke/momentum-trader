# Keep real trade execution manual

Accepted. Momentum Trader supports signal scanning, backtesting, reporting, and disciplined manual execution, but it will not place real orders or integrate with broker-side automated trading. Retail A-share investors generally do not have a stable, appropriate automated brokerage interface for this use case, and keeping execution manual preserves the project's emphasis on understandable discipline rather than automation.

**Considered Options**

- Integrate broker-side automated execution as part of the trading system.
- Keep real trade execution outside the system and require manual user action.

**Consequences**

Signals and reports may indicate rule-based actions, but any real order remains a user action outside the system.
