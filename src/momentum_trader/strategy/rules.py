from __future__ import annotations

from momentum_trader.config import StrategyConfig


def is_pyramid_complete(strategy: StrategyConfig, level: int) -> bool:
    return level >= len(strategy.pyramid)


def next_pyramid_step(strategy: StrategyConfig, level: int):
    if level >= len(strategy.pyramid):
        return None
    return strategy.pyramid[level]

