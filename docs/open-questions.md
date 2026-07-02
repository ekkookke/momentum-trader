# Open Questions

## Benchmark and Baseline Curves

The user wants reports to compare the strategy against multiple curves:

- HS300 index
- HS300 ETF buy-and-hold
- HS300 ETF monthly contribution plan
- equal-weight buy-and-hold of the configured ETF Universe

Resolved naming direction: reserve **Benchmark Series** for non-tradable market indexes and use **Baseline Strategy** for tradable buy-and-hold, monthly contribution, and equal-weight comparison curves.

Remaining implementation question: which Baseline Strategies belong in the first report implementation, and should monthly contribution assume a fixed cash amount, a fixed percentage of initial cash, or a configurable schedule?

This spans data semantics, backtest portfolio construction, and report presentation, so it should be resolved with the backtest/report sessions before implementation.

## Processed Market Data Directory

`configs/default.yaml` contains `data.processed_dir`, but the current data layer does not define a stable processed-data lifecycle beyond raw cached snapshots, schema normalization, and date clipping.

Open question: should `processed_dir` remain part of the configuration, and if so, is it a derived cache, a stable input for Signal Scan and Backtest, or a future optimization detail that should stay outside the shared domain language until implemented?

## Data Gap Detection

The glossary distinguishes Data Gaps from legitimate non-trading days, ETF suspension, and pre-listing periods, but the current system does not yet classify or report these cases explicitly.

Open question: how should Signal Scan and Backtest distinguish source failures from legitimate missing bars, and where should Data Gaps be surfaced in Report Packages?

The first implementation should include data-integrity checks, but not as a naive `date.diff().dt.days <= 7` rule because Chinese market holidays can exceed seven calendar days. Prefer a layered design:

- CI unit tests for the gap classifier using synthetic calendars and known edge cases.
- Runtime warnings or report sections for suspicious gaps in loaded ETF data.
- A market-calendar-aware threshold, or a conservative calendar-day heuristic that explicitly allows known long holiday windows.

Default severity direction: hard errors should block strategy evaluation when required OHLCV fields, parseable dates, numeric prices, or required price semantics are missing. Suspicious issues such as long gaps, zero volume, missing amount, duplicate dates that can be resolved, or unusual jumps should warn and continue first, with the warning visible in the Report Package.

## Unknown Signal Condition Results

The glossary distinguishes an Unknown Condition Result from a Signal Condition that was evaluated and found false. ADR-0008 defines three-valued Signal Rule Expression semantics so Unknown does not trigger Entry Signals or Exit Signals, but also does not disappear into False.

Open question: how should Signal Scan and Report Packages expose material Unknown Condition Results without overwhelming the retail user? Default reports should not explain every false-only non-candidate, but they still need a clear way to surface cases where data sufficiency, warmup, listing boundaries, or input-quality uncertainty affected signal interpretation.

Implementation debt: the current signal implementation collapses condition `NaN` values into boolean `False` for execution columns. Future signal-layer work should preserve condition-level True/False/Unknown results and update `tests/test_signals.py` so warmup, listing boundary, and missing valid inputs assert Unknown rather than only checking that no entry or exit was triggered. Boolean entry/exit columns may remain execution-layer derivatives, but they should not be the only archived signal result.

## Nested Signal Rule Expression Implementation

ADR-0005 accepts nested positive AND/OR Signal Rule Expressions while excluding NOT-style negation, but the current configuration model and signal calculation only support flat all/any groups.

Open question: what should the nested configuration shape be, how should Unknown Condition Results propagate through nested AND/OR expressions, how should Report Packages explain nested rule matches to a retail user, and how should existing flat configurations migrate without breaking prior Run interpretation?

## Reusable Signal Condition Definitions

The glossary allows a long-term model where named Signal Condition Definitions are declared once and referenced by entry, exit, scan, and report expressions. The current implementation keeps conditions inline inside entry and exit groups.

Open question: when nested Signal Rule Expressions are introduced, should configuration migrate to `condition definitions + expression references`, and how should reports preserve historical interpretation for runs that used inline condition lists?

## Signal Diagnostic Value Storage

The glossary requires diagnostic values to be associated with the Signal Condition Name that produced them, but the current signal implementation writes global diagnostic columns such as `breakout_high`, `ma_short`, and `ma_long`.

Open question: should condition diagnostics be exported as nested report data, condition-prefixed columns, or a separate long-form table keyed by instrument, Signal Date, Signal Condition Name, and diagnostic key?

## Price-vs-Moving-Average Condition Type Cleanup

The glossary intentionally does not distinguish `price_vs_ma` and `ma_break` as separate domain concepts. Both represent the same market comparison shape: a configured field compared with a moving average. The business intent should be carried by the condition name and its placement in an Entry Signal or Exit Signal expression.

Open question: should the signal configuration keep `ma_break` as a deprecated alias for one release before consolidating on `price_vs_ma`, and how should existing run configurations be migrated without breaking historical Run interpretation?

## Stateful Exit and Risk Rule Cleanup

ADR-0007 keeps Signal Rule Expressions market-data-only and assigns holdings, portfolio, staged-entry, cooldown, drawdown stops, and risk-state decisions to Strategy Execution Filters. The current implementation still allows exit condition `apply` values such as `before_pyramid_complete` and `after_pyramid_complete`, which makes condition applicability depend on Pyramiding state. It also configures `trailing_stop` under `strategy.exit.conditions`, even though its calculation depends on holding-path state such as entry timing and peak price.

Open question: how should the configuration migrate stateful exit applicability and `trailing_stop` from Signal Conditions into Strategy Execution Filters or risk-exit configuration while preserving existing run interpretation and report explanations?

## Signal Comparison Operator Cleanup

ADR-0005 treats `!=` as NOT-style negation and reserves equality for explicit discrete market states, but the current configuration model still accepts `!=` for all Signal Conditions.

Open question: should the implementation remove `!=` immediately, keep it as a deprecated validation warning for one release, or reject it only for price and indicator calculation shapes once discrete-state conditions exist?

## Breakout Shift Validation

The glossary and ADR-0007 require formal entry breakout thresholds to exclude the current bar, but the current `ConditionConfig.shift` default is `0` and relies on example configuration to set `shift: 1`.

Open question: should breakout `shift` default to `1`, should entry breakout conditions reject `shift: 0`, and should any current-bar-inclusive breakout calculation be represented as a separate diagnostic-only type or scope?

## Signal Trigger Field Validation

ADR-0007 defines first-version formal Entry Signals and Exit Signals as close-confirmed, while the current condition model allows a breakout or comparison condition to use arbitrary configured trigger fields such as `high` or `low`.

Open question: should formal entry and exit conditions reject non-`close` trigger fields by default, allow them only under a diagnostic scope, or introduce explicit intrabar-derived signal semantics in a later version?

## Candidate Priority Semantics

ADR-0007 keeps same-day tie-breaking among multiple true Entry Signals outside the signal layer. The current backtest uses configuration order when multiple ETFs compete for limited position slots.

Open question: should Strategy Execution continue using configuration order, switch to an explicit priority field, or support ranking-based candidate selection while preserving stable Run explanations?
