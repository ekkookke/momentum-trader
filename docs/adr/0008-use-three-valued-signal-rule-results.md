# Use three-valued signal rule results

Accepted. Signal Rule Expressions will evaluate to True, False, or Unknown rather than collapsing unknown data sufficiency into False. AND returns False if any child is False, Unknown if no child is False and at least one child is Unknown, and True only when all children are True; OR returns True if any child is True, Unknown if no child is True and at least one child is Unknown, and False only when all children are False.

**Considered Options**

- Treat Unknown as False during signal evaluation.
- Use three-valued logic for Signal Rule Expressions and only trigger Entry Signals or Exit Signals on True.

**Consequences**

Unknown never creates an Entry Signal or Exit Signal, but it remains explainable as data insufficiency, warmup, listing-boundary, missing required input on an otherwise valid rule, or input-quality uncertainty rather than being reported as a failed rule. Unsupported fields, invalid parameters, and violated data contracts are not Unknown; they should fail the Run before signal evaluation or block formal interpretation. Strategy evaluation should preserve the affected dates instead of clipping them away solely to hide warmup; future nested AND/OR implementation, report explanations, and tests should preserve this distinction.

For explainability, formal signal evaluation should prefer calculating every child condition over short-circuit optimization. If a future implementation does short-circuit, unevaluated children must be labeled as not evaluated and must not be collapsed into False or Unknown.

Report Packages should preserve condition-level explanations for signal-present rows, such as Entry Signals, Exit Signals, Action Candidates, skipped executions, and material Unknown results, instead of leaving them only in logs or transient data frames. A full Signal Result Matrix keyed by instrument, Signal Date, and Signal Condition Name may remain an audit/export artifact, but it should not be the default user-facing view. Signal Result Matrix dates are signal observation dates, not next executable dates or filled trade dates. Supporting diagnostic values, such as breakout thresholds and moving averages, should be keyed by Signal Condition Name as well so multiple similar conditions cannot overwrite each other's explanations.
