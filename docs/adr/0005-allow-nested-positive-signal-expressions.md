# Allow nested positive signal expressions without NOT

Accepted. Momentum Trader will allow Signal Rule Expressions to combine Signal Conditions with nested positive AND/OR logic, because some disciplined ETF momentum rules need more structure than a single flat group. We will not support NOT-style negation in the signal language, because the project favors explainable rules about what is present and wants to avoid ambiguous "not X therefore act" logic, especially when data sufficiency or warmup state is unknown.

**Considered Options**

- Keep Signal Rule Expressions limited to one flat all/any group.
- Support nested AND/OR while excluding NOT-style negation.
- Support a full boolean expression language including NOT.

**Consequences**

The current implementation only supports flat all/any groups, so nested AND/OR is a future signal-layer capability rather than current behavior. Future config and report explanations should preserve positive rule language and make Unknown Condition Results visible instead of relying on negation to express missing or failed evidence. Not-equal comparisons are treated as NOT-style negation and should not be used in formal Signal Conditions; price and indicator comparisons should use directional operators, while equality is reserved for explicit discrete market states.
