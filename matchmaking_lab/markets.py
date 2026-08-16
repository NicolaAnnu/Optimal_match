from __future__ import annotations

from dataclasses import dataclass
import numpy as np

B_HIGH = 1.0
B_LOW = 0.6
C_LOW = 0.0
C_HIGH = 0.4


@dataclass(frozen=True)
class MarketSpec:
    key: str
    label: str
    interpretation: str
    baseline_d_i: float
    baseline_d_j: float
    baseline_prediction: str
    sensitivity_parameter: str


@dataclass(frozen=True)
class DensityScenario:
    scenario_id: str
    label: str
    d_i: float
    d_j: float
    sensitivity_value: float
    is_baseline: bool

MARKETS = {
    "airbnb": MarketSpec(
        key="airbnb",
        label="Airbnb / short-term rentals",
        interpretation=(
        ),
        baseline_d_i=0.10,
        baseline_d_j=0.80,
        baseline_prediction="Customers search",
        sensitivity_parameter="d_J (with d_I fixed at 0.10)",
    ),
    "care": MarketSpec(
        key="care",
        label="Care.com / childcare",
        interpretation=(

        ),
        baseline_d_i=0.02,
        baseline_d_j=0.02,
        baseline_prediction="Both sides search",
        sensitivity_parameter="common density d_I = d_J",
    ),
}
AIRBNB_DJ_GRID = (0.20, 0.40, 0.60, 0.80, 1.00)
CARE_COMMON_DENSITY_GRID = (0.02, 0.05, 0.10, 0.20, 0.40)


def density_scenarios(market_key: str) -> tuple[DensityScenario, ...]:
    """Return the fixed density path for a real-market archetype.
    """
    if market_key == "airbnb":
        spec = MARKETS[market_key]
        return tuple(
            DensityScenario(
                scenario_id=f"airbnb_dj_{d_j:.2f}",
                label=f"d_I={spec.baseline_d_i:.2f}, d_J={d_j:.2f}",
                d_i=spec.baseline_d_i,
                d_j=d_j,
                sensitivity_value=d_j,
                is_baseline=bool(np.isclose(d_j, spec.baseline_d_j)),
            )
            for d_j in AIRBNB_DJ_GRID
        )

    if market_key == "care":
        spec = MARKETS[market_key]
        return tuple(
            DensityScenario(
                scenario_id=f"care_d_{d:.2f}",
                label=f"d_I=d_J={d:.2f}",
                d_i=d,
                d_j=d,
                sensitivity_value=d,
                is_baseline=bool(
                    np.isclose(d, spec.baseline_d_i)
                    and np.isclose(d, spec.baseline_d_j)
                ),
            )
            for d in CARE_COMMON_DENSITY_GRID
        )

    raise ValueError(f"Unknown market: {market_key}")


def baseline_scenario(market_key: str) -> DensityScenario:
    scenarios = [s for s in density_scenarios(market_key) if s.is_baseline]
    if len(scenarios) != 1:
        raise RuntimeError(f"Expected exactly one baseline scenario for {market_key}.")
    return scenarios[0]


def generate_market(
    n: int,
    d_i: float,
    d_j: float,
    rng: np.random.Generator,
) -> tuple[np.ndarray, np.ndarray]:
    """
    For epsilon < 0.4:
        P(b_ij >= B_HIGH - epsilon) = d_I
        P(c_ij <= C_LOW + epsilon) = d_J
    """
    if not (0.0 < d_i <= 1.0 and 0.0 < d_j <= 1.0):
        raise ValueError("d_I and d_J must lie in (0, 1].")
    u_b = rng.random((n, n))
    u_c = rng.random((n, n))
    b = np.where(u_b < d_i, B_HIGH, B_LOW)
    c = np.where(u_c < d_j, C_LOW, C_HIGH)
    return b, c
