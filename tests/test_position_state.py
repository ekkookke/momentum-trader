from __future__ import annotations

from datetime import date

from momentum_trader.strategy.position_state import PositionState


def test_mark_entry_tracks_first_entry_and_pyramid_levels() -> None:
    state = PositionState()

    state.mark_entry(date(2024, 1, 2), price=10.0, allocation_pct=0.6)
    state.mark_entry(date(2024, 1, 5), price=11.0, allocation_pct=0.25)

    assert state.is_open
    assert state.entry_date == date(2024, 1, 2)
    assert state.entry_price == 10.0
    assert state.peak_price == 10.0
    assert state.pyramid_level == 2
    assert state.filled_intent_pct == 0.85


def test_update_peak_only_moves_up_and_reset_clears_state() -> None:
    state = PositionState()

    state.update_peak(10.0)
    state.update_peak(9.0)
    state.update_peak(12.0)
    assert state.peak_price == 12.0

    state.reset()
    assert not state.is_open
    assert state.entry_date is None
    assert state.entry_price is None
    assert state.peak_price is None
    assert state.pyramid_level == 0
    assert state.filled_intent_pct == 0.0
