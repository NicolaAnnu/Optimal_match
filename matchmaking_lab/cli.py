from __future__ import annotations

import argparse
from dataclasses import replace
from pathlib import Path

from .config import preset_config
from .experiments import run_experiment


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Unified Monte Carlo sensitivity experiment for the matchmaking "
            "protocols studied in Shi (2023)."
        )
    )
    parser.add_argument("--preset", choices=["quick", "standard", "full"], default="standard")
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--replications", type=int, default=None)
    parser.add_argument("--epsilon", type=float, default=None)
    parser.add_argument("--markets", nargs="+", choices=["airbnb", "care"], default=["airbnb", "care"])
    parser.add_argument("--output-dir", default="results")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    config = preset_config(args.preset, workers=args.workers)

    if args.replications is not None:
        if args.replications <= 0:
            raise SystemExit("--replications must be positive.")
        config = replace(config, replications=args.replications)

    if args.epsilon is not None:
        if not (0 < args.epsilon < 0.4):
            raise SystemExit("For this two-point calibration use 0 < epsilon < 0.4.")
        config = replace(config, epsilon=args.epsilon)

    _, summary, efficiency = run_experiment(
        config,
        Path(args.output_dir),
        market_keys=tuple(args.markets),
    )

    baseline = summary[summary["is_baseline"]].copy()
    print("\nBASELINE MARKET-SIZE SCALING (fixed d_I and d_J)\n")
    print(
        baseline[
            [
                "market",
                "n",
                "d_I",
                "d_J",
                "strategy",
                "mean_interactions",
                "mean_welfare_ratio",
                "mean_match_rate",
            ]
        ].to_string(index=False)
    )

    print("\nUnified sensitivity experiment completed.")
    print("Results: experiment_raw.csv, experiment_summary.csv, experiment_efficiency.csv")
    if not efficiency.empty:
        print(f"Tie-aware efficiency rows: {len(efficiency)}")


if __name__ == "__main__":
    main()
