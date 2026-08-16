import numpy as np

from matchmaking_lab.markets import baseline_scenario, density_scenarios, generate_market
from matchmaking_lab.metrics import optimal_welfare, welfare
from matchmaking_lab.protocols import (
    both_sides_search,
    centralized_matching,
    customers_search,
    providers_search,
)


def _check_one_to_one(match):
    assigned = match[match >= 0]
    assert len(assigned) == len(set(assigned.tolist()))


def test_protocols_produce_valid_matchings_and_respect_welfare_benchmark():
    rng = np.random.default_rng(123)
    b, c = generate_market(30, 0.10, 0.80, rng)
    optimum = optimal_welfare(b, c)
    results = [
        customers_search(b, c, 0.1),
        providers_search(b, c, 0.1),
        both_sides_search(b, c, 0.8, 0.1),
        centralized_matching(b, c, 0.10, 0.80, rng, 0.1),
    ]
    for result in results:
        _check_one_to_one(result.match)
        assert result.interactions >= 0
        assert welfare(result.match, b, c) <= optimum + 1e-9


def test_density_scenarios_are_fixed_and_have_one_baseline():
    airbnb = density_scenarios("airbnb")
    care = density_scenarios("care")

    assert len(airbnb) == 5
    assert len(care) == 5
    assert all(np.isclose(s.d_i, 0.10) for s in airbnb)
    assert [round(s.d_j, 2) for s in airbnb] == [0.20, 0.40, 0.60, 0.80, 1.00]
    assert all(np.isclose(s.d_i, s.d_j) for s in care)
    assert [round(s.d_i, 2) for s in care] == [0.02, 0.05, 0.10, 0.20, 0.40]
    assert np.isclose(baseline_scenario("airbnb").d_j, 0.80)
    assert np.isclose(baseline_scenario("care").d_i, 0.02)


def test_common_random_numbers_create_nested_density_draws():
    seed = 999
    low_rng = np.random.default_rng(seed)
    high_rng = np.random.default_rng(seed)
    b_low, c_low = generate_market(40, 0.10, 0.20, low_rng)
    b_high, c_high = generate_market(40, 0.10, 0.80, high_rng)

    # d_I is unchanged, so customer-benefit draws are exactly identical.
    assert np.array_equal(b_low, b_high)
    # Raising d_J can only turn high costs into low costs, never the reverse.
    assert np.all(c_high <= c_low)
