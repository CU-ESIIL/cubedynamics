# Spatial synchrony stacks: Phase 1.5 diagnostic design

Status: scientific representation study. This phase reuses the validated Phase
1 PRISM stack and stops before the 100 by 100 scaling benchmark.

## Traceability and preserved objects

The primary input is the Phase 1 checkpoint
`artifacts/synchrony-stack-phase1/prism_20x20_synchrony_stack.nc`, fingerprint
`sha256:4b4a3c30fbd5ccb2a4f8b5cefc2ca2b127e7bf31d646b27091b354b447df9acb`.
It contains observed PRISM `tmin` and `tmax` synchrony for 2023-11-01 through
2024-01-30, an inclusive 90-day coordinate interval with 91 daily labels,
`min_t=10`, per-series median thresholds, 400 centers, and a 20 by 20 focal
grid. Phase 1.5 does not recalculate those climate correlations.

The implementation continues to distinguish pair synchrony `S(i,j)`, a center
landscape `M_i=S(i,.)`, a focal stack over centers, panel similarity
`Q(i,j)`, and a reduced stack map. Cold, warm, and `Delta S = cold - warm`
remain separate. A median Delta product is always the median of pairwise Delta
values, not the difference of separately reduced cold and warm products.

## Panel-change representation

`panel_change_diagnostics` compares adjacent center landscapes independently
for cold, warm, and Delta S. For each variable it records:

- Spearman and Pearson correlation;
- RMSE and MAE;
- normalized RMSE, defined as RMSE divided by the pooled 5th-to-95th percentile
  range, with undefined output when that range is zero;
- Wasserstein distance, explicitly a distribution-only comparison that ignores
  spatial arrangement;
- gradient-vector RMSE and gradient-magnitude RMSE on the common raster;
- shared valid count, panel standard deviations, robust ranges, exact unique
  counts, and near-tie fractions.

For Delta S it also records sign-disagreement fraction. Values within a
configurable absolute deadband are assigned a neutral sign class, so numerical
noise around zero is not silently interpreted as a regime flip.

No universal panel-change scalar is introduced. The working panel-change
signature has four interpretable axes:

1. magnitude change: RMSE/MAE and normalized RMSE;
2. rank structure: Spearman, supported by near-tie and dynamic-range context;
3. sign/asymmetry change: deadbanded sign disagreement;
4. spatial reorganization: gradient-vector difference.

Pearson and Wasserstein remain supporting diagnostics. This preserves cases in
which a low rank correlation coexists with small absolute differences.

## Radius-growth representation

`stack_radius_diagnostics` applies nested distance masks to the existing full
stack. At every requested radius it records center count and, separately for
cold, warm, and Delta S, mean, median, standard deviation, IQR, MAD, and the
5th, 25th, 50th, 75th, and 95th percentiles.

Radius sensitivity is descriptive. Step changes and derivatives are retained;
an experimental stable-radius field is allowed only with its complete rule in
metadata. The default exploratory rule is the first radius having at least 25
centers for which the remaining median or IQR range is no greater than 0.02.
It is not called a universal synchrony radius.

## Distance, direction, and spatial partitioning

`stack_structure_diagnostics` characterizes each focal stack without fitting a
large spatial model. It records:

- Spearman association between Delta S and center distance;
- variance explained descriptively by distance bins and by eight compass bins;
- residual IQR after subtracting distance-bin medians;
- one-dimensional KDE mode count over a fixed evaluation grid at 0.75, 1.0,
  and 1.25 times Scott's bandwidth, plus a conservative all-bandwidth
  multimodality-consensus flag;
- deterministic two-group separation and balance;
- neighbor agreement, agreement above the class-balance expectation, and
  largest connected-component coverage after mapping groups back to center
  geography.

KDE mode count and two-group fields are experimental. A two-group split is not
evidence of climate regimes: spatial coherence and direct maps are mandatory,
and even coherent groups remain candidate structure in this single observed
window.

## Public API boundary

Phase 1.5 adds three pipe-friendly diagnostics:

- `v.panel_change_diagnostics(...)`;
- `v.stack_radius_diagnostics(...)`;
- `v.stack_structure_diagnostics(...)`.

They accept a Phase 1 stack Dataset and return ordinary xarray Datasets.
Analysis-table and figure production remain in the reusable Phase 1.5 example
script. The runtime functions do not read files, write checkpoints, classify
climate regions, or trigger synchrony recomputation.

## Candidate production signature

The proposed schema is evidence-ranked rather than automatically adopted.
Candidate fields are cold magnitude, warm magnitude, Delta asymmetry, stack
heterogeneity, radius sensitivity, directional structure, and spatial
partitioning. The report and machine-readable decision table must classify each
as `KEEP`, `KEEP AS DIAGNOSTIC`, `EXPERIMENTAL`, or `DROP`, document redundancy,
and state what pairwise information must survive aggregation.

## Failure and interpretation rules

- Inputs must be a complete Phase 1 stack with center and two focal dimensions.
- Panel metrics use the same shared finite pixels; insufficient overlap returns
  NaN plus the observed count.
- Radius masks are nested and never extrapolate beyond the block's support.
- Constant panels make correlation and normalized metrics undefined rather than
  inventing a perfect comparison, while identity distance metrics remain zero.
- Edge pixels are labeled as incomplete-support examples, not regional types.
- A histogram, KDE mode, mixture split, or p-value never establishes a regime.
- National computation and the 100 by 100 benchmark remain out of scope until
  the Phase 1.5 decision gate is complete.
