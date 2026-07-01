from __future__ import annotations

from momentum_trader.config import PyramidConfig, PyramidStepConfig
from momentum_trader.strategy.rules import is_pyramid_complete, next_pyramid_step


def test_enabled_pyramid_boundaries() -> None:
    pyramid = PyramidConfig(
        steps=[
            PyramidStepConfig(trigger_pct=0.0, allocation_pct=0.6),
            PyramidStepConfig(trigger_pct=0.03, allocation_pct=0.25),
            PyramidStepConfig(trigger_pct=0.06, allocation_pct=0.15),
        ]
    )

    assert not is_pyramid_complete(pyramid, 0)
    assert next_pyramid_step(pyramid, 0).allocation_pct == 0.6
    assert next_pyramid_step(pyramid, 2).trigger_pct == 0.06
    assert is_pyramid_complete(pyramid, 3)
    assert next_pyramid_step(pyramid, 3) is None


def test_disabled_pyramid_degrades_to_single_full_step() -> None:
    pyramid = PyramidConfig(enabled=False)

    first_step = next_pyramid_step(pyramid, 0)

    assert first_step is not None
    assert first_step.trigger_pct == 0.0
    assert first_step.allocation_pct == 1.0
    assert is_pyramid_complete(pyramid, 1)
    assert next_pyramid_step(pyramid, 1) is None
