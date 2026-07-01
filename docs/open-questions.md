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
