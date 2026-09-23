# Reproduce the spatial synchrony stack Phase 1.5 analysis

Phase 1.5 analyzes the exact observed-PRISM stack produced and validated in
Phase 1. It does not recalculate the climate correlations, run the 100 by 100
benchmark, or create a national product.

## Required input

Run Phase 1 first if this ignored checkpoint is not already present:

`artifacts/synchrony-stack-phase1/prism_20x20_synchrony_stack.nc`

The Phase 1.5 script refuses any checkpoint whose analysis fingerprint is not:

`sha256:4b4a3c30fbd5ccb2a4f8b5cefc2ca2b127e7bf31d646b27091b354b447df9acb`

That checkpoint represents observed PRISM `tmin` and `tmax` from 2023-11-01
through 2024-01-30 (91 daily coordinate labels), a 20 by 20 grid, 400 moving
centers, 80,200 canonical pairs including self-pairs, a 90-day inclusive
window, `min_t=10`, and a per-series median split (`q=0.5`).

## Run

From the repository root with the Python 3.11 development environment:

```bash
MPLCONFIGDIR=/tmp/cubedynamics-mpl \
XDG_CACHE_HOME=/tmp/cubedynamics-cache \
.venv/bin/python examples/prism_synchrony_stack_phase15.py
```

To use non-default locations, pass `--stack`, `--output`, or `--report`.

## Outputs

The ignored evidence directory `artifacts/synchrony-stack-phase15/` receives:

- a tidy adjacent-panel CSV and its full NetCDF diagnostic Dataset;
- nested radius diagnostics as NetCDF;
- separate cold, warm, and Delta structure diagnostics as NetCDF;
- a candidate `SynchronySignature` Dataset;
- JSON/CSV decision, typology, disagreement, runtime, and provenance records;
- 14 required teaching figures plus six standardized typology figures.

The figure-heavy report is written to
`output/pdf/cubedynamics_synchrony_stack_phase15_report.pdf`.

The candidate data-model contract is
`schemas/synchrony_signature_phase15.schema.json`. It labels stable-radius and
spatial-partition fields as experimental; it is not a production schema.

## Validate

```bash
.venv/bin/python -m pytest \
  tests/test_synchrony_stack_diagnostics.py \
  tests/test_synchrony_stacks.py -q

python scripts/build_reference_docs.py --check
git diff --check
```

The report's decision is **GO WITH CHANGES** for the bounded 100 by 100
benchmark: test nested 25, 50, 75, and 100 km support with halos and retain the
multidimensional diagnostics. It is not authorization for a national run or a
climate-regime product.
