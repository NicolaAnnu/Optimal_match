# Two-Sided Matchmaking Lab

A reproducible Monte Carlo project inspired by Peng Shi (2023), *Optimal Matchmaking Strategy in Two-Sided Marketplaces*.

The project uses two **real-market archetypes discussed in the paper**:

1. **Airbnb / short-term rentals** — the baseline treats provider preferences as relatively easy to describe and customer preferences as more idiosyncratic.
2. **Care.com / childcare** — the baseline treats both sides as having substantial hard-to-describe preferences.

> The platform names identify real economic settings, but the numerical values of `d_I` and `d_J` are transparent **stylized simulation calibrations**, not empirical estimates from Airbnb or Care.com proprietary data.

## What changed in this version

There is now **one unified sensitivity experiment** rather than a separate baseline experiment plus a second sensitivity run.

For every density calibration, the same market-size grid is simulated. The baseline is simply one marked calibration on each path. This solves an important identification problem in the earlier version: `d_I` and `d_J` no longer change automatically with `n`.

Therefore:

- **market-size scaling** holds preference densities fixed and varies only `n`;
- **sensitivity analysis** holds `n` fixed and varies the relevant preference density;
- both views come from the **same Monte Carlo output**.

## Preference-density paths

### Airbnb / short-term rentals

`d_I = 0.10` is fixed and:

```text
d_J = 0.20, 0.40, 0.60, 0.80, 1.00
```

Baseline:

```text
d_I = 0.10, d_J = 0.80
```

### Care.com / childcare

Both sides become progressively easier to describe together:

```text
d_I = d_J = 0.02, 0.05, 0.10, 0.20, 0.40
```

Baseline:

```text
d_I = d_J = 0.02
```

These values are defined explicitly in `matchmaking_lab/markets.py`.

## Monte Carlo design

All four strategies are evaluated on the **same market realization**:

- Customers search;
- Providers search;
- Both sides search;
- Centralized matching.

The sensitivity comparison also uses **common random numbers**. For a given market, market size, and replication, the same underlying uniform random matrices are reused across density levels and thresholded at different `d_I` / `d_J` values. This creates paired/nested sensitivity draws and reduces Monte Carlo noise.

Main outcomes:

- interactions per customer;
- welfare ratio relative to a perfect-information maximum-welfare assignment;
- welfare regret;
- match rate;
- 95% confidence intervals for communication and welfare;
- protocol diagnostics;
- a **tie-aware efficient share**: among strategies with welfare ratio >= 0.95, the least-communication strategy receives efficiency credit; exact ties split the credit equally.

## Numerical presets

Because each market is now evaluated at five density levels, the experiment is numerically larger than the earlier baseline-only design.

- `quick`: 10 replications × n = 25, 50, 100
- `standard`: 100 replications × n = 25, 50, 100, 150, 200
- `full`: 300 replications × n = 25, 50, 100, 150, 200, 300

For the standard preset:

```text
2 markets × 5 density scenarios × 5 market sizes × 100 replications
= 5,000 scenario-specific market instances
= 20,000 protocol evaluations
```

These 5,000 scenario-specific instances come from **1,000 independent base draws**
(2 markets × 5 market sizes × 100 replications). Each base draw is reused across
the five density levels through common random numbers, so sensitivity comparisons
are paired rather than independent.

## Project structure

```text
matchmaking_project/
├── matchmaking_lab/
│   ├── config.py
│   ├── markets.py
│   ├── protocols.py
│   ├── metrics.py
│   ├── experiments.py
│   └── cli.py
├── frontend/
│   └── app.py
├── scripts/
│   └── run_experiments.py
├── tests/
│   └── test_protocols.py
├── results/
├── requirements.txt
└── pyproject.toml
```

## Run the experiment

From the project root:

```powershell
python -m matchmaking_lab.cli --preset quick
```

For the main experiment:

```powershell
python -m matchmaking_lab.cli --preset standard --workers 4
```

For a heavier robustness run:

```powershell
python -m matchmaking_lab.cli --preset full --workers 4
```

You can override the number of replications:

```powershell
python -m matchmaking_lab.cli --preset standard --replications 250 --workers 4
```

Or run a single market:

```powershell
python -m matchmaking_lab.cli --preset standard --markets airbnb --workers 4
```

## Output files

One run creates only three main CSV files:

```text
results/experiment_raw.csv
results/experiment_summary.csv
results/experiment_efficiency.csv
```

There are no separate `baseline_*` and `sensitivity_*` files anymore.

## Frontend

After generating the results:

```powershell
streamlit run frontend/app.py
```

The dashboard contains only views that map directly to the experimental design:

1. **Market-size scaling** — baseline densities fixed, `n` varies;
2. **Sensitivity analysis** — `n` fixed, preference density varies;
3. **Efficiency comparison** — tie-aware communication efficiency conditional on welfare >= 0.95;
4. **Methodology**.

The previous live-scenario/demo view and Monte Carlo scatter frontier were removed because they were not necessary for the report's main experimental argument.

## Tests

```powershell
pytest -q
```

## Methodological scope

This project is a numerical illustration of Shi's mechanisms, not a numerical proof of the communication-complexity lower bounds. The Monte Carlo analysis studies interaction cost and matching quality; the lower and upper bounds in bits remain theoretical results from the paper.
