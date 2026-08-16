# Experimental design

## Research question

How does the relative communication cost and matching quality of the four matchmaking protocols change with market size and with the describability of preferences?

The numerical study is designed to separate these two effects rather than changing market size and preference density simultaneously.

## Real-market archetypes

### Airbnb / short-term rentals

The customer side is held at `d_I = 0.10`. Provider describability varies over:

`d_J = 0.20, 0.40, 0.60, 0.80, 1.00`.

The marked baseline is `(d_I, d_J) = (0.10, 0.80)`.

### Care.com / childcare

Both sides are varied together to represent progressively less idiosyncratic preferences:

`d_I = d_J = 0.02, 0.05, 0.10, 0.20, 0.40`.

The marked hard-preference baseline is `(0.02, 0.02)`.

The density values are simulation parameters, not platform estimates.

## Identification logic

For scaling plots, a single baseline density pair is fixed and only `n` changes.

For sensitivity plots, `n` is fixed and the relevant density parameter changes.

Both are slices of the same experiment output.

## Monte Carlo pairing

Within a given market, `n`, and replication, all density levels reuse the same random seed. Thus the same underlying uniform matrices are thresholded at different densities. This common-random-numbers design makes sensitivity comparisons paired and reduces simulation noise.

All four protocols are also evaluated on exactly the same generated `b` and `c` matrices within each scenario.

## Main metrics

- interactions per customer;
- welfare ratio relative to perfect-information maximum welfare;
- welfare regret;
- match rate;
- 95% confidence intervals;
- tie-aware efficient share conditional on welfare ratio >= 0.95.

## Main run

`python -m matchmaking_lab.cli --preset standard --workers 4`

This produces 5,000 scenario-specific market instances and 20,000 protocol evaluations from 1,000 independent base Monte Carlo draws.
