from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
import math
from typing import Any

import numpy as np
from scipy.optimize import linear_sum_assignment

from .markets import B_HIGH, C_LOW, C_HIGH


@dataclass
class ProtocolResult:
    match: np.ndarray
    interactions: int
    metadata: dict[str, Any] = field(default_factory=dict)


def _assert_matching(match: np.ndarray) -> None:
    used = match[match >= 0]
    if used.size != np.unique(used).size:
        raise RuntimeError("error")


def customers_search(
    b: np.ndarray,
    c: np.ndarray,
    epsilon: float,
    initial_cost_estimates: np.ndarray | None = None,
) -> ProtocolResult:
    n = b.shape[0]
    customer_match = np.full(n, -1, dtype=int)
    provider_match = np.full(n, -1, dtype=int)
    required_provider_surplus = np.zeros(n)

    if initial_cost_estimates is None:
        cost_estimates = np.full((n, n), C_LOW + epsilon)
    else:
        cost_estimates = initial_cost_estimates.copy()

    active = deque(range(n))
    interactions = 0
    rejections = 0
    acceptances = 0
    displacements = 0

    while active:
        i = active.popleft()
        while True:
            estimated_surplus = b[i] - required_provider_surplus - cost_estimates[i]
            j = int(np.argmax(estimated_surplus))

            if estimated_surplus[j] < 0:
                break

            interactions += 1
            if c[i, j] <= cost_estimates[i, j] + 1e-12:
                acceptances += 1
                previous_customer = provider_match[j]
                if previous_customer != -1:
                    displacements += 1
                    customer_match[previous_customer] = -1
                    active.append(previous_customer)

                customer_match[i] = j
                provider_match[j] = i
                required_provider_surplus[j] += epsilon
                break

            rejections += 1
            cost_estimates[i, j] = c[i, j]

    _assert_matching(customer_match)
    return ProtocolResult(
        match=customer_match,
        interactions=interactions,
        metadata={
            "rejections": rejections,
            "acceptances": acceptances,
            "displacements": displacements,
        },
    )


def providers_search(b: np.ndarray, c: np.ndarray, epsilon: float) -> ProtocolResult:
    n = b.shape[0]
    customer_match = np.full(n, -1, dtype=int)
    provider_match = np.full(n, -1, dtype=int)
    required_customer_surplus = np.zeros(n)
    benefit_estimates = np.full((n, n), B_HIGH - epsilon)

    active = deque(range(n))
    interactions = 0
    rejections = 0
    acceptances = 0
    displacements = 0

    while active:
        j = active.popleft()
        while True:
            estimated_surplus = benefit_estimates[:, j] - required_customer_surplus - c[:, j]
            i = int(np.argmax(estimated_surplus))

            if estimated_surplus[i] < 0:
                break

            interactions += 1
            if b[i, j] >= benefit_estimates[i, j] - 1e-12:
                acceptances += 1
                previous_provider = customer_match[i]
                if previous_provider != -1:
                    displacements += 1
                    provider_match[previous_provider] = -1
                    active.append(previous_provider)

                provider_match[j] = i
                customer_match[i] = j
                required_customer_surplus[i] += epsilon
                break

            rejections += 1
            benefit_estimates[i, j] = b[i, j]

    _assert_matching(customer_match)
    return ProtocolResult(
        match=customer_match,
        interactions=interactions,
        metadata={
            "rejections": rejections,
            "acceptances": acceptances,
            "displacements": displacements,
        },
    )


def choose_z(n: int, d_j: float, epsilon: float) -> float:
    increments = math.ceil(1.0 / epsilon)
    bound_z0 = increments / max(d_j, 1e-12)
    bound_z04 = n * d_j + increments
    return 0.0 if bound_z0 <= bound_z04 else C_HIGH


def both_sides_search(
    b: np.ndarray,
    c: np.ndarray,
    d_j: float,
    epsilon: float,
) -> ProtocolResult:
    n = b.shape[0]
    z = choose_z(n, d_j, epsilon)

    cost_estimates = np.full((n, n), z + epsilon)
    provider_initiates = c < z - 1e-12
    initial_interactions = int(provider_initiates.sum())
    cost_estimates[provider_initiates] = c[provider_initiates]

    later = customers_search(
        b,
        c,
        epsilon=epsilon,
        initial_cost_estimates=cost_estimates,
    )
    metadata = dict(later.metadata)
    metadata.update(
        {
            "z": z,
            "provider_initiated_contacts": initial_interactions,
        }
    )
    return ProtocolResult(
        match=later.match,
        interactions=initial_interactions + later.interactions,
        metadata=metadata,
    )


def centralized_matching(
    b: np.ndarray,
    c: np.ndarray,
    d_i: float,
    d_j: float,
    rng: np.random.Generator,
    epsilon: float,
) -> ProtocolResult:
    n = b.shape[0]
    density_product = max(d_i * d_j, 1e-12)
    k = min(n, max(1, math.ceil(3.0 * math.log(n) / density_product)))

    accepted = np.zeros((n, n), dtype=bool)
    for i in range(n):
        recommended = rng.choice(n, size=k, replace=False)
        accepted[i, recommended] = (
            (b[i, recommended] >= B_HIGH - epsilon)
            & (c[i, recommended] <= C_LOW + epsilon)
        )

    assignment_cost = np.concatenate(
        [np.where(accepted, 0.0, 1000.0), np.ones((n, n))],
        axis=1,
    )
    rows, cols = linear_sum_assignment(assignment_cost)

    match = np.full(n, -1, dtype=int)
    for i, j in zip(rows, cols):
        if j < n and accepted[i, j]:
            match[i] = j

    _assert_matching(match)
    return ProtocolResult(
        match=match,
        interactions=n * k,
        metadata={
            "recommendations_per_customer": k,
            "accepted_recommendations": int(accepted.sum()),
        },
    )
