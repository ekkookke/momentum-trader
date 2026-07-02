# Split ETF backtest trading costs

Accepted. Momentum Trader will model ETF Backtest Trading Cost as separate per-fill components instead of a single `per_side_cost_rate`, because exchange-traded ETFs do not pay A-share stamp tax or transfer fees and a stock-style 0.15% single-side assumption would systematically understate backtested ETF returns.

The first-version configuration is:

```yaml
commission_rate: 0.0001
min_commission: 5
slippage_rate: 0.001
stamp_tax_rate: 0
```

Per-fill cost is calculated as:

```text
fee = max(amount * commission_rate, min_commission)
    + amount * slippage_rate
    + amount * stamp_tax_rate
```

**Considered Options**

- Keep one blended `per_side_cost_rate`.
- Split costs into commission, minimum commission, slippage, and explicit stamp tax.
- Build a broker-specific settlement model with more fee categories.

**Consequences**

Splitting the components keeps the ETF tax treatment visible, makes `min_commission` affect small fills correctly, and allows reports to show both `total_fees` and commission/slippage/tax breakdowns for auditability. For fills of at least roughly 50,000 CNY, the configured one-way blended cost is about 0.11%; small staged-entry fills can be higher because the minimum commission is charged per order.

This is still a Backtest Trading Cost model, not a promise of real trading fees. Real execution can differ by broker, order size, market depth, and user behavior.
