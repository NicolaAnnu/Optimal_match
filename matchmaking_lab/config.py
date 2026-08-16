from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class ExperimentConfig:
    epsilon: float = 0.10
    replications: int = 100
    market_sizes: Tuple[int, ...] = (25, 50, 100, 150, 200)
    seed: int = 2026
    workers: int = 1
    welfare_threshold: float = 0.95


def preset_config(name: str, workers: int = 1) -> ExperimentConfig:
    name = name.lower()
    if name == "quick":
        return ExperimentConfig(
            replications=10,
            market_sizes=(25, 50, 100),
            workers=workers,
        )
    if name == "standard":
        return ExperimentConfig(
            replications=100,
            market_sizes=(25, 50, 100, 150, 200),
            workers=workers,
        )
    if name == "full":
        return ExperimentConfig(
            replications=300,
            market_sizes=(25, 50, 100, 150, 200, 300),
            workers=workers,
        )
    raise ValueError(f"Unknown preset: {name}")
