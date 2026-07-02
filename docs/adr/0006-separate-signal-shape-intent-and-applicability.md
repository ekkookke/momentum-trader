# Separate signal condition shape, intent, and applicability

Accepted. Momentum Trader's signal language separates three concerns: condition `type` names the calculation shape, condition `name` carries the trading intent, and the condition's entry/exit placement plus Signal Applicability Scope define the review context for the market signal. Future condition types may be added only when the system needs a new calculation shape, such as volume-based comparison or Benchmark-relative comparison, not merely because a new trading intent appears.

**Considered Options**

- Add a new condition type for each trading intent, such as separate moving-average-break and trend-filter types.
- Keep condition type focused on calculation shape and express intent through names, placement, and applicability scope.

**Consequences**

The existing `ma_break` and `price_vs_ma` split should be treated as a cleanup candidate rather than a precedent for future type proliferation. Configuration authors should use descriptive condition names to preserve user-facing explanation, and condition names must be unique across all entry and exit signal conditions within a Strategy Run so reports and exported columns do not merge different rule meanings. Condition names may include parameter hints, but the mechanical rule expression and archived configuration remain the source of truth for calculation parameters. The core signal engine should keep condition types small and mechanically meaningful. Non-price market inputs such as volume, amount, turnover, or Benchmark-relative series may justify new condition types only when they introduce a new calculation shape with clear data semantics. Applicability that depends on holdings, portfolio state, Pyramiding state, cooldown, or risk state belongs to Strategy Execution Filters rather than new Signal Condition types.
