# Four-round adaptive synchrony experiment

`v.adaptive_synchrony_experiment(...)` separates a maximum observation domain
from an estimated empirical synchrony scale. It consumes the reusable sparse
relationships produced by `v.local_synchrony_pairs(...)`; it does not recompute
the underlying time-series correlation.

The four rounds are:

1. Estimate independent cold and warm first local-to-regional breaks inside a
   standardized physical-distance domain.
2. When both breaks are valid, form one configurable common radius and reduce
   cold, warm, and pairwise Delta over the same neighbors.
3. Compare those adaptive reductions with a fixed-radius control from the same
   relationships.
4. Retain the cold, warm, common, cold-minus-warm distance, uncertainty, and
   categorical status fields as scientific outputs.

The default common rule is `max(cold_break, warm_break)`. A discovery limit is
never substituted for an unresolved break. Primary Delta remains the robust
reduction of pairwise `cold_synchrony - warm_synchrony`, not a difference of
marginal medians.

## Sampling contract

`v.local_synchrony_pairs(...)` accepts an optional `distance_sampling` plan.
Successive `(upper_km, maximum_pairs_per_focal)` strata are sampled uniformly
before the expensive synchrony kernel runs; `None` retains a dense stratum.
Every retained relationship carries `sampling_probability`, and the adaptive
reducer uses its inverse as a design weight. Validate sampled break placement
and status against exhaustive focal pixels before spatial scale-up.

## Current real-data gate

The bounded 2023-11-01 through 2024-01-30 PRISM experiment evaluated five
exhaustive 1000 km focal domains. Exhaustive common breaks resolved at two of
five representative pixels; the distance-stratified version resolved one of
five, and tail-status agreement was 30%. Fixed 500 km pairwise Delta was much
more stable under sampling (mean absolute error 0.00065). The predeclared
representative gate therefore stopped the workflow before the 25-site Colorado,
statewide Colorado, or CONUS stages. This is an implementation and evidence
boundary, not a missing-value imputation opportunity.

## Temporal extension

Outputs retain `time_window_id` and `time_window_end`. Repeating the bounded
method over independent windows can later support median, IQR, and trend of
`R*(x,y,t)`. That extension should wait until spatial break identifiability and
far-field sampling stability pass their gates.
