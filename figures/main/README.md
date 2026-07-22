# Fire VASE Main Figure Suite

This directory contains a publication-oriented five-figure suite for the manuscript **Wildfire Occupies a Continuous Developmental Morphospace**.

## Regenerate

Run from the repository root:

```bash
.venv/bin/python scripts/figures/render_all.py
```

Use `--force-validation` to recompute cached validation tables. Use `--bootstrap-reps 500` for a heavier Science-review validation run.

## Inputs

- `scratch/fire_vase_developmental_morphology/developmental_morphospace_features.parquet`
- `scratch/fire_vase_developmental_morphology/developmental_morphospace_medoids.parquet`
- `scratch/fire_vase_developmental_morphology/developmental_morphospace_loadings.csv`
- `scratch/fire_vase_developmental_morphology/developmental_stage_table.parquet`
- `scratch/fire_vase_developmental_morphology/developmental_climate_coupling.parquet`
- `scratch/fire_vase_developmental_morphology/developmental_matched_pairs.parquet`
- `scratch/fire_vase_run_full/tables/vase_slices.parquet`
- `scratch/fire_vase_run_full/tables/fire_traits.parquet`

## Outputs

Each main figure is exported as PDF, PNG, and SVG: `Figure_1` through `Figure_5`.
Supplementary validation output is written under `figures/supplement/`.

## Statistical Analyses

The pipeline performs geometry-only PCA recomputation, stratified bootstrap PCA stability, feature-permutation and within-fire growth-profile nulls, duration sensitivity, feature ablation, medoid coverage, neighborhood label-overlap analysis, random/blocked predictive climate coupling, matched-neighborhood diagnostics, and a leakage-audited fixed-day stage prediction analysis.

## Runtime

The default run uses `60` bootstrap replicates and caches validation tables under `figures/main/derived_stats/`. Increase `--bootstrap-reps` for a final slow run.

## Style

Typography, palette, figure dimensions, and output resolution are controlled in `scripts/figures/style.py`.

## Robust Conclusions

- Geometry-only Fire VASE features occupy a strongly concentrated low-dimensional linear subspace.
- The result persists under duration sensitivity and reduced feature sets.
- Medoids are real observed fires and provide a compact atlas of occupied regions.
- Climate aligns with morphology but does not uniquely determine developmental form.

## Provisional Conclusions

- Climate prediction and matched-neighborhood inference should be expanded with richer spatial blocking, nonlinear models, and public archived covariates.
- Stage-wise prediction has been leakage-audited here; it should replace the older fractional-stage table in future manuscript language unless the original stage features are redesigned.
