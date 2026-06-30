from __future__ import annotations

from momentum_trader.config import PyramidConfig, PyramidStepConfig


def is_pyramid_complete(pyramid: PyramidConfig, level: int) -> bool:
    return level >= len(_effective_steps(pyramid))


def next_pyramid_step(pyramid: PyramidConfig, level: int) -> PyramidStepConfig | None:
    steps = _effective_steps(pyramid)
    if level >= len(steps):
        return None
    return steps[level]


def _effective_steps(pyramid: PyramidConfig) -> list[PyramidStepConfig]:
    if pyramid.enabled:
        return pyramid.steps
    return [PyramidStepConfig(trigger_pct=0.0, allocation_pct=1.0)]
