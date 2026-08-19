# Two-Sided Matchmaking Lab

A reproducible Monte Carlo simulation project inspired by Peng Shi (2023), *Optimal Matchmaking Strategy in Two-Sided Marketplaces*.

The project numerically studies the trade-off between **communication cost** and **matching quality** in two-sided marketplaces. It implements and compares four matchmaking strategies under different market sizes and different levels of preference describability.

Two real-market archetypes are used:

1. **Airbnb / short-term rentals** — provider-side preferences are modeled as relatively easier to describe, while customer preferences remain more idiosyncratic.
2. **Care.com / childcare** — both sides are modeled as having relatively hard-to-describe preferences.

> The platform names identify real economic settings used as market archetypes. The numerical values of `d_I` and `d_J` are **stylized experimental calibrations**, not empirical estimates derived from proprietary Airbnb or Care.com data.

---

## Experimental objective

The experiment asks:

> How do communication requirements and matching quality change with market size and with the describability of preferences?

The design separates these two effects:

* **market-size scaling:** preference densities are fixed while `n` varies;
* **sensitivity analysis:** market size is fixed while preference densities vary.

Both analyses are obtained from the **same unified Monte Carlo experiment**.

This avoids changing market size and preference density simultaneously and allows the effects of the two dimensions to be interpreted separately.

---

## Market generation

Each simulated market contains `n` customers and `n` providers.

For every customer-provider pair `(i, j)`, the model generates:

* a customer benefit `b_ij`;
* a provider cost `c_ij`.

The implementation uses the two-point calibration:

```text
b_ij ∈ {1.0, 0.6}
c_ij ∈ {0.0, 0.4}
```

with:

```text
P(b_ij = 1.0) = d_I
P(c_ij = 0.0) = d_J
```

Therefore:

* `d_I` measures how frequently customer-side high-value matches are easy to identify;
* `d_J` measures how frequently provider-side low-cost matches are easy to identify.

The default approximation parameter is:

```text
epsilon = 0.10
```

The experiment uses a fixed default random seed:

```text
seed = 2026
```

---

## Preference-density paths

### Airbnb / short-term rentals

The customer-side density is fixed:

```text
d_I = 0.10
```

while provider-side describability varies over:

```text
d_J = 0.20, 0.40, 0.60, 0.80, 1.00
```

The baseline calibration is:

```text
d_I = 0.10
d_J = 0.80
```

This baseline is associated with the model prediction:

```text
Customers search
```

---

### Care.com / childcare

Both preference densities vary together:

```text
d_I = d_J = 0.02, 0.05, 0.10, 0.20, 0.40
```

The baseline calibration is:

```text
d_I = d_J = 0.02
```

This baseline is associated with the model prediction:

```text
Both sides search
```

The density grids and baseline configurations are defined explicitly in:

```text
matchmaking_lab/markets.py
```

---

## Matchmaking strategies

Each generated market is evaluated using the same four strategies.

### 1. Customers search

Customers sequentially contact providers using initially estimated provider costs.

Rejected interactions reveal additional information and update the customer's estimate of that provider's cost.

The protocol records:

* interactions;
* acceptances;
* rejections;
* displacements.

---

### 2. Providers search

This is the provider-side counterpart of the customer-search protocol.

Providers search among customers using initial estimates of customer benefits and update those estimates as information is revealed.

The protocol also records:

* interactions;
* acceptances;
* rejections;
* displacements.

---

### 3. Both sides search

The hybrid protocol allows information acquisition from both sides of the market.

A threshold `z` is selected according to the market parameters. Some providers initiate communication first, after which the customer-search mechanism continues using the information already revealed.

The simulation records both the initial provider contacts and subsequent customer-search interactions.

---

### 4. Centralized matching

The platform recommends a subset of providers to each customer.

The number of recommendations is determined by:

```text
k = min(n, ceil(3 log(n) / (d_I d_J)))
```

Customers accept recommendations satisfying the high-benefit and low-cost conditions, and a one-to-one assignment is then constructed using the accepted edges.

The simulation also evaluates whether the corresponding sufficient-density condition holds for each scenario.

---

## Perfect-information benchmark

Matching quality is evaluated relative to a centralized benchmark with full information.

For each generated market, the code computes the maximum possible total surplus using a maximum-weight one-to-one assignment.

If:

```text
W*
```

denotes optimal perfect-information welfare and:

```text
W
```

denotes the welfare achieved by a matchmaking strategy, the main quality measure is:

```text
welfare_ratio = W / W*
```

The corresponding regret is:

```text
welfare_regret = 1 - welfare_ratio
```

---

## Unified Monte Carlo design

There is a **single unified experiment** rather than separate baseline and sensitivity experiments.

For every market, every preference-density scenario is evaluated over the same market-size grid.

The baseline is therefore simply one marked point within each density path.

All four matchmaking strategies are evaluated on the **same generated market realization**, so differences between strategies are not caused by different random markets.

---

## Common random numbers

The sensitivity analysis uses **common random numbers**.

For a given:

```text
market × n × replication
```

the same base random seed is reused across all five density scenarios.

The underlying uniform random matrices are therefore the same and are thresholded using different values of `d_I` and `d_J`.

As a result, the density scenarios are paired.

For example, in the Airbnb experiment:

```text
d_I = 0.10
```

remains unchanged, so the generated customer-benefit matrix is identical across the five `d_J` values, while increasing `d_J` can progressively transform high provider costs into low provider costs.

This design reduces unnecessary Monte Carlo noise and makes the sensitivity comparisons easier to interpret.

---

## Main metrics

For each strategy and simulation draw, the raw experiment records:

* total interactions;
* interactions per customer;
* welfare;
* optimal perfect-information welfare;
* welfare ratio;
* welfare regret;
* match rate;
* runtime;
* protocol-specific diagnostics.

Depending on the protocol, diagnostics include:

* rejections;
* acceptances;
* displacements;
* provider-initiated contacts;
* recommendations per customer;
* accepted recommendations;
* hybrid threshold `z`.

The aggregated results additionally report:

* mean;
* standard deviation;
* 5th percentile;
* median;
* 95th percentile;
* 95% confidence intervals.

Confidence intervals are calculated for:

* interactions per customer;
* welfare ratio;
* match rate.

---

## Communication efficiency

The project also constructs a **tie-aware communication-efficiency measure**.

For every individual Monte Carlo realization, a strategy is first considered eligible if:

```text
welfare_ratio >= 0.95
```

Among the eligible strategies, the strategy requiring the smallest number of interactions per customer receives the efficiency credit.

If multiple strategies have exactly the same minimum communication cost, the credit is divided equally among them.

For example:

```text
1 winner       -> credit = 1
2 tied winners -> credit = 0.5 each
3 tied winners -> credit = 1/3 each
```

Aggregating this credit across replications produces the reported:

```text
efficient_share
```

This measure therefore compares communication efficiency **conditional on achieving sufficiently high matching quality**.

---

## Numerical presets

Three presets are available.

### Quick

```text
10 replications
n = 25, 50, 100
```

Useful for testing the code and dashboard.

### Standard

```text
100 replications
n = 25, 50, 100, 150, 200
```

This is the configuration used for the main experiment.

### Full

```text
300 replications
n = 25, 50, 100, 150, 200, 300
```

Intended for a heavier robustness run.

---

## Main experiment used in the project

The results used for the main analysis were generated with:

```powershell
python -m matchmaking_lab.cli --preset standard --workers 4
```

With the standard preset, this corresponds to:

```text
2 markets
× 5 density scenarios per market
× 5 market sizes
× 100 Monte Carlo replications
= 5,000 scenario-specific market instances
```

Each scenario is evaluated with all four matchmaking strategies:

```text
5,000 market instances
× 4 strategies
= 20,000 protocol evaluations
```

Because the five density scenarios reuse the same base random draw for each market size and replication, the 5,000 scenario-specific instances originate from:

```text
2 markets
× 5 market sizes
× 100 replications
= 1,000 independent base Monte Carlo draws
```

The five density scenarios associated with each base draw are therefore **paired rather than independent**.

The generated `experiment_raw.csv` contains one row for each protocol evaluation, giving **20,000 rows** for the standard experiment.

---

## Project structure

```text
optimal_matchmaking/
├── matchmaking_lab/
│   ├── __init__.py
│   ├── config.py
│   ├── markets.py
│   ├── protocols.py
│   ├── metrics.py
│   ├── experiments.py
│   └── cli.py
│
├── frontend/
│   └── app.py
│
├── scripts/
│   └── run_experiments.py
│
├── tests/
│   └── test_protocols.py
│
├── results/
│   ├── experiment_raw.csv
│   ├── experiment_summary.csv
│   └── experiment_efficiency.csv
│
├── EXPERIMENT_DESIGN.md
├── README.md
├── requirements.txt
├── pyproject.toml
└── .gitignore
```

### Main modules

* `config.py` — experiment configuration and numerical presets;
* `markets.py` — market archetypes, density grids and random market generation;
* `protocols.py` — implementation of the four matchmaking strategies;
* `metrics.py` — welfare, optimal-welfare and matching metrics;
* `experiments.py` — Monte Carlo execution, aggregation and CSV generation;
* `cli.py` — command-line interface;
* `frontend/app.py` — Streamlit dashboard;
* `EXPERIMENT_DESIGN.md` — concise description of the experimental methodology.

---

## Installation

The project requires Python 3.10 or later.

Install the dependencies from the project root:

```powershell
python -m pip install -r requirements.txt
```

The main dependencies are:

```text
NumPy
pandas
SciPy
Streamlit
Plotly
pytest
```

---

## Running the experiment

All commands should be executed from the project root.

### Quick test

```powershell
python -m matchmaking_lab.cli --preset quick
```

### Main experiment

```powershell
python -m matchmaking_lab.cli --preset standard --workers 4
```

### Full robustness run

```powershell
python -m matchmaking_lab.cli --preset full --workers 4
```

---

## CLI options

The command-line interface supports the following main options:

```text
--preset
--workers
--replications
--epsilon
--markets
--output-dir
```

### Override the number of replications

```powershell
python -m matchmaking_lab.cli --preset standard --replications 250 --workers 4
```

### Change epsilon

For the two-point calibration implemented in the project:

```text
0 < epsilon < 0.4
```

Example:

```powershell
python -m matchmaking_lab.cli --preset standard --epsilon 0.15 --workers 4
```

### Run only Airbnb

```powershell
python -m matchmaking_lab.cli --preset standard --markets airbnb --workers 4
```

### Run only Care.com

```powershell
python -m matchmaking_lab.cli --preset standard --markets care --workers 4
```

### Specify a different output directory

```powershell
python -m matchmaking_lab.cli --preset standard --workers 4 --output-dir my_results
```

---

## Parallel execution

The experiment supports multiprocessing through Python's `ProcessPoolExecutor`.

For example:

```powershell
python -m matchmaking_lab.cli --preset standard --workers 4
```

uses up to four worker processes to execute the Monte Carlo tasks.

The number of workers affects execution speed but does not change the experimental design.

---

## Output files

Every run generates three main CSV files:

```text
results/experiment_raw.csv
results/experiment_summary.csv
results/experiment_efficiency.csv
```

Existing files with the same names in the selected output directory are overwritten.

### `experiment_raw.csv`

Contains one row for every:

```text
market
× density scenario
× market size
× replication
× strategy
```

It includes raw communication, welfare, matching, runtime and protocol-diagnostic measures.

### `experiment_summary.csv`

Contains aggregated statistics for each:

```text
market
× density scenario
× market size
× strategy
```

It includes means, dispersion measures, percentiles and confidence intervals.

### `experiment_efficiency.csv`

Contains the tie-aware communication-efficiency comparison among strategies satisfying:

```text
welfare_ratio >= 0.95
```

There are no separate `baseline_*` and `sensitivity_*` result files. Both analyses are derived from these same unified experiment outputs.

---

## Streamlit dashboard

After generating the experiment results, launch the frontend with:

```powershell
streamlit run frontend/app.py
```

The dashboard reads:

```text
results/experiment_summary.csv
results/experiment_efficiency.csv
```

and provides four sections.

### 1. Market-size scaling

Uses only the baseline density configuration of each market.

Preference densities remain fixed while:

```text
n
```

changes.

This isolates the effect of market size on communication requirements and matching quality.

### 2. Sensitivity analysis

Keeps market size fixed while varying the appropriate preference-density parameter.

For Airbnb:

```text
d_J varies
d_I = 0.10
```

For Care.com:

```text
d_I = d_J varies
```

### 3. Efficiency comparison

Displays the tie-aware efficient share of each strategy conditional on:

```text
welfare_ratio >= 0.95
```

### 4. Methodology

Summarizes the experimental design, density calibrations, common-random-numbers approach and interpretation of the main metrics.

---

## Tests

Run the test suite from the project root with:

```powershell
python -m pytest -q
```

The tests verify that:

* all protocols produce valid one-to-one matchings;
* achieved welfare does not exceed the perfect-information optimum;
* each market has the intended five fixed density scenarios;
* each market has exactly one baseline scenario;
* the common-random-numbers construction creates the intended nested density draws.

---

## Reproducibility

The default experiment configuration is:

```text
epsilon = 0.10
seed = 2026
welfare threshold = 0.95
```

Together with the fixed density grids and Monte Carlo presets, this makes the experiment reproducible.

The main reported experiment uses:

```powershell
python -m matchmaking_lab.cli --preset standard --workers 4
```

---

## Methodological scope

This project is a **numerical illustration of the matchmaking mechanisms studied by Shi (2023)**.

The Monte Carlo experiment investigates how:

* preference density;
* market size;
* decentralized versus centralized search;
* communication requirements;
* and matching quality

interact across different two-sided market configurations.

The simulation does **not** constitute a numerical proof of the theoretical communication-complexity lower or upper bounds established in the paper.

In particular, the code measures communication operationally through the number of customer-provider interactions, while the theoretical communication-complexity results in Shi (2023) are expressed in terms of information transmitted in bits.

The numerical results should therefore be interpreted as an experimental illustration of the mechanisms and comparative predictions of the theoretical framework, rather than as a replacement for its formal results.

---

## Reference

Peng Shi (2023), *Optimal Matchmaking Strategy in Two-Sided Marketplaces*.
