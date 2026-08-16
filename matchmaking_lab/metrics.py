from __future__ import annotations

import numpy as np
from scipy.optimize import linear_sum_assignment


def welfare(match: np.ndarray, b: np.ndarray, c: np.ndarray) -> float:
    return float(sum(b[i, j] - c[i, j] for i, j in enumerate(match) if j >= 0))


def optimal_welfare(b: np.ndarray, c: np.ndarray) -> float:
    n = b.shape[0]
    surplus = b - c
    cost = np.concatenate([-surplus, np.zeros((n, n))], axis=1)
    rows, cols = linear_sum_assignment(cost)
    return float(
        sum(surplus[i, j] for i, j in zip(rows, cols) if j < n and surplus[i, j] > 0)
    )

def match_rate(match: np.ndarray) -> float:
    return float(np.mean(match >= 0))

def summarize_distribution(values: np.ndarray) -> dict[str, float]:
    x = np.asarray(values, dtype=float)
    n = x.size
    mean = float(np.mean(x))
    sd = float(np.std(x, ddof=1)) if n > 1 else 0.0
    se = sd / np.sqrt(n) if n > 0 else float("nan")
    return {
        "mean": mean,
        "sd": sd,
        "p05": float(np.quantile(x, 0.05)),
        "median": float(np.quantile(x, 0.50)),
        "p95": float(np.quantile(x, 0.95)),
        "ci95_low": mean - 1.96 * se,
        "ci95_high": mean + 1.96 * se,
    }
