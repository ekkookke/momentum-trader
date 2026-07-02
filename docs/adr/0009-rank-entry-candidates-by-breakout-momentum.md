# Rank entry candidates by breakout momentum

Accepted. When same-Signal-Date Entry Signals compete for limited Position Slots, Momentum Trader ranks candidates by normalized breakout strength:

`score = (close - breakout_high) / ATR_N`

`ATR_N` defaults to 20 and belongs under `strategy.tie_break` so the ranking horizon is visible in configuration. Higher scores receive execution priority. The score must be computed only from data available on the Signal Date, preserving the after-close signal model and avoiding look-ahead through next-day open or fill information.

**Considered Options**

- Keep ETF Universe configuration order as the tie-breaker.
- Rank candidates by normalized breakout strength.
- Rank candidates by a discretionary or optimized performance score.

**Consequences**

Ranking by breakout momentum is more consistent with the project's trend-following thesis than hidden configuration order, while ATR normalization avoids favoring ETFs only because they have larger nominal price moves. Filled orders should carry the score used for selection. Signals skipped only because Position Slots are full should be recorded in the orders output as Skipped Backtest Fills with symbol, score, and reason, rather than silently disappearing from the order trail.

Exact ties still need a deterministic fallback, such as ETF Universe configuration order. Unknown, zero, or otherwise invalid ATR inputs must not be silently treated as high-priority candidates; they should either make the candidate ineligible for this tie-break or be recorded with an explicit unknown-score reason.
