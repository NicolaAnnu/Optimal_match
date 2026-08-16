from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict
from functools import partial
from pathlib import Path
import math
import time

import numpy as np
import pandas as pd

from .config import ExperimentConfig
from .markets import MARKETS, DensityScenario, density_scenarios, generate_market
from .metrics import match_rate, optimal_welfare, welfare
from .protocols import (
    both_sides_search,
    centralized_matching,
    customers_search,
    providers_search,
)

STRATEGIES = (
    "Customers search",
    "Providers search",
    "Both sides search",
    "Centralized matching",
)


def _centralized_sufficient_condition(n: int, d_i: float, d_j: float) -> bool:
    threshold = min(1.0, 3.0 * math.log(n) / n)
    return d_i * d_j >= threshold


def _strategy_record(
    *,
    market_key: str,
    scenario: DensityScenario,
    n: int,
    replication: int,
    strategy: str,
    result,
    b: np.ndarray,
    c: np.ndarray,
    w_star: float,
    elapsed_ms: float,
    epsilon: float,
) -> dict:
    w = welfare(result.match, b, c)
    welfare_ratio = w / w_star if w_star > 0 else 1.0
    return {
        "market_key": market_key,
        "market": MARKETS[market_key].label,
        "scenario_id": scenario.scenario_id,
        "scenario": scenario.label,
        "is_baseline": scenario.is_baseline,
        "sensitivity_parameter": MARKETS[market_key].sensitivity_parameter,
        "sensitivity_value": scenario.sensitivity_value,
        "n": n,
        "epsilon": epsilon,
        "d_I": scenario.d_i,
        "d_J": scenario.d_j,
        "replication": replication,
        "strategy": strategy,
        "interactions_total": int(result.interactions),
        "interactions_per_customer": result.interactions / n,
        "welfare": w,
        "optimal_welfare": w_star,
        "welfare_ratio": welfare_ratio,
        "welfare_regret": 1.0 - welfare_ratio,
        "match_rate": match_rate(result.match),
        "runtime_ms": elapsed_ms,
        "baseline_prediction": MARKETS[market_key].baseline_prediction,
        "centralized_sufficient_condition": _centralized_sufficient_condition(
            n, scenario.d_i, scenario.d_j
        ),
        "z": result.metadata.get("z", np.nan),
        "rejections": result.metadata.get("rejections", np.nan),
        "acceptances": result.metadata.get("acceptances", np.nan),
        "displacements": result.metadata.get("displacements", np.nan),
        "provider_initiated_contacts": result.metadata.get(
            "provider_initiated_contacts", np.nan
        ),
        "recommendations_per_customer": result.metadata.get(
            "recommendations_per_customer", np.nan
        ),
        "accepted_recommendations": result.metadata.get(
            "accepted_recommendations", np.nan
        ),
    }


def _run_one_market_draw(
    task: tuple,
    config: ExperimentConfig,
) -> list[dict]:
    market_key, n, scenario, replication, seed = task

    rng = np.random.default_rng(seed)
    b, c = generate_market(n, scenario.d_i, scenario.d_j, rng)
    w_star = optimal_welfare(b, c)
    out: list[dict] = []

    runners = [
        ("Customers search", lambda: customers_search(b, c, config.epsilon)),
        ("Providers search", lambda: providers_search(b, c, config.epsilon)),
        (
            "Both sides search",
            lambda: both_sides_search(b, c, scenario.d_j, config.epsilon),
        ),
        (
            "Centralized matching",
            lambda: centralized_matching(
                b, c, scenario.d_i, scenario.d_j, rng, config.epsilon
            ),
        ),
    ]

    for strategy, runner in runners:
        t0 = time.perf_counter()
        result = runner()
        elapsed_ms = 1000.0 * (time.perf_counter() - t0)
        out.append(
            _strategy_record(
                market_key=market_key,
                scenario=scenario,
                n=n,
                replication=replication,
                strategy=strategy,
                result=result,
                b=b,
                c=c,
                w_star=w_star,
                elapsed_ms=elapsed_ms,
                epsilon=config.epsilon,
            )
        )
    return out


def _build_tasks(
    config: ExperimentConfig,
    market_keys: tuple[str, ...],
) -> list[tuple]:

    for key in market_keys:
        if key not in MARKETS:
            raise ValueError(f"Unknown market: {key}")

    n_base_draws = len(market_keys) * len(config.market_sizes) * config.replications
    base_seeds = iter(
        np.random.SeedSequence(config.seed)
        .generate_state(n_base_draws, dtype=np.uint32)
        .tolist()
    )

    tasks: list[tuple] = []
    for market_key in market_keys:
        scenarios = density_scenarios(market_key)
        for n in config.market_sizes:
            for replication in range(config.replications):
                seed = next(base_seeds)
                for scenario in scenarios:
                    tasks.append((market_key, n, scenario, replication, seed))
    return tasks


def _execute_tasks(tasks: list[tuple], config: ExperimentConfig) -> pd.DataFrame:
    worker = partial(_run_one_market_draw, config=config)
    if config.workers <= 1:
        rows = [row for task in tasks for row in worker(task)]
    else:
        with ProcessPoolExecutor(max_workers=config.workers) as pool:
            rows = [row for chunk in pool.map(worker, tasks) for row in chunk]
    return pd.DataFrame(rows)


def _ci95(mean: pd.Series, sd: pd.Series, reps: pd.Series) -> tuple[pd.Series, pd.Series]:
    se = sd.fillna(0.0) / np.sqrt(reps)
    return mean - 1.96 * se, mean + 1.96 * se


def summarize_raw(
    raw: pd.DataFrame,
    welfare_threshold: float = 0.95,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    group_cols = [
        "market_key",
        "market",
        "scenario_id",
        "scenario",
        "is_baseline",
        "sensitivity_parameter",
        "sensitivity_value",
        "n",
        "epsilon",
        "d_I",
        "d_J",
        "strategy",
        "baseline_prediction",
        "centralized_sufficient_condition",
    ]

    summary = (
        raw.groupby(group_cols, dropna=False, as_index=False)
        .agg(
            replications=("replication", "nunique"),
            mean_interactions=("interactions_per_customer", "mean"),
            sd_interactions=("interactions_per_customer", "std"),
            p05_interactions=("interactions_per_customer", lambda s: s.quantile(0.05)),
            median_interactions=("interactions_per_customer", "median"),
            p95_interactions=("interactions_per_customer", lambda s: s.quantile(0.95)),
            mean_welfare_ratio=("welfare_ratio", "mean"),
            sd_welfare_ratio=("welfare_ratio", "std"),
            p05_welfare_ratio=("welfare_ratio", lambda s: s.quantile(0.05)),
            median_welfare_ratio=("welfare_ratio", "median"),
            p95_welfare_ratio=("welfare_ratio", lambda s: s.quantile(0.95)),
            mean_match_rate=("match_rate", "mean"),
            sd_match_rate=("match_rate", "std"),
            mean_runtime_ms=("runtime_ms", "mean"),
        )
    )

    summary["se_interactions"] = summary["sd_interactions"].fillna(0.0) / np.sqrt(
        summary["replications"]
    )
    (
        summary["ci95_low_interactions"],
        summary["ci95_high_interactions"],
    ) = _ci95(
        summary["mean_interactions"],
        summary["sd_interactions"],
        summary["replications"],
    )
    (
        summary["ci95_low_welfare_ratio"],
        summary["ci95_high_welfare_ratio"],
    ) = _ci95(
        summary["mean_welfare_ratio"],
        summary["sd_welfare_ratio"],
        summary["replications"],
    )
    (
        summary["ci95_low_match_rate"],
        summary["ci95_high_match_rate"],
    ) = _ci95(
        summary["mean_match_rate"],
        summary["sd_match_rate"],
        summary["replications"],
    )

    draw_cols = ["market_key", "scenario_id", "n", "replication"]
    eligible = raw[raw["welfare_ratio"] >= welfare_threshold].copy()
    if eligible.empty:
        efficiency = pd.DataFrame()
    else:
        min_cost = (
            eligible.groupby(draw_cols, as_index=False)["interactions_per_customer"]
            .min()
            .rename(columns={"interactions_per_customer": "min_eligible_interactions"})
        )
        eligible = eligible.merge(min_cost, on=draw_cols, how="left")
        winners = eligible[
            np.isclose(
                eligible["interactions_per_customer"],
                eligible["min_eligible_interactions"],
                atol=1e-12,
                rtol=0.0,
            )
        ].copy()
        winners["tie_count"] = winners.groupby(draw_cols)["strategy"].transform("size")
        winners["efficiency_credit"] = 1.0 / winners["tie_count"]

        credits = (
            winners.groupby(
                [
                    "market_key",
                    "market",
                    "scenario_id",
                    "scenario",
                    "is_baseline",
                    "sensitivity_value",
                    "n",
                    "strategy",
                ],
                as_index=False,
            )["efficiency_credit"]
            .sum()
        )
        eligible_draws = (
            winners[draw_cols]
            .drop_duplicates()
            .groupby(["market_key", "scenario_id", "n"], as_index=False)
            .size()
            .rename(columns={"size": "eligible_replications"})
        )
        efficiency = credits.merge(
            eligible_draws,
            on=["market_key", "scenario_id", "n"],
            how="left",
        )
        efficiency["efficient_share"] = (
            efficiency["efficiency_credit"] / efficiency["eligible_replications"]
        )

    return summary, efficiency


def save_results(
    raw: pd.DataFrame,
    summary: pd.DataFrame,
    efficiency: pd.DataFrame,
    output_dir: Path,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    raw.to_csv(output_dir / "experiment_raw.csv", index=False)
    summary.to_csv(output_dir / "experiment_summary.csv", index=False)
    efficiency.to_csv(output_dir / "experiment_efficiency.csv", index=False)


def run_experiment(
    config: ExperimentConfig,
    output_dir: str | Path = "results",
    market_keys: tuple[str, ...] = ("airbnb", "care"),
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Run the single unified Monte Carlo experiment.

    The same output supports both analyses used in the report:
      1. market-size scaling at the fixed baseline calibration;
      2. sensitivity to preference density at any fixed market size.
    """
    tasks = _build_tasks(config, market_keys)
    raw = _execute_tasks(tasks, config)
    summary, efficiency = summarize_raw(raw, config.welfare_threshold)
    save_results(raw, summary, efficiency, Path(output_dir))
    return raw, summary, efficiency


def config_as_dict(config: ExperimentConfig) -> dict:
    return asdict(config)
