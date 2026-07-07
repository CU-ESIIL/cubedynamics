# CI and Testing

CubeDynamics tests are split into small, fast unit suites and opt-in integration/online checks that hit live services. This page explains how to run them locally and how GitHub Actions orchestrates them.

## Quick start (local)

- Install development dependencies with the repo Makefile:

  ```bash
  make install
  ```

- Run the default offline suite:

  ```bash
  make test
  ```

- Run focused fire/VASE and streaming guardrails:

  ```bash
  make test-fire
  make test-streaming
  ```

- Or run the underlying commands directly:
  
  ```bash
  pip install -e ".[dev]"
  ```

- Run unit tests (skips integration/online):
  
  ```bash
  pytest -m "not integration" -q
  ```
  Runs fast, offline-safe checks that cover verbs, cube plumbing, and viewer helpers.

- Run the full suite (unit + integration/online):
  
  ```bash
  pytest -q
  ```
  Executes everything, including networked and large-data exercises. Expect longer runtimes and external dependencies.

- Run only integration tests (external backends, larger data):
  
  ```bash
  pytest -m "integration" -q
  ```

- Run only online tests (explicit network/cubo access):
  
  ```bash
  pytest -m "online" -q
  ```

## Test markers and what they mean

Markers are declared in `pytest.ini` and gate which suites run where:

- **`integration`** – hits external services (e.g., PRISM/gridMET downloads, FIRED fetches) or large cached datasets. Excluded from the default CI job.
- **`online`** – requires cubo or other network access. Use when tests must reach live endpoints. Also excluded from the default CI job.
- **`streaming`** – exercises streaming-first code paths and expectations (lazy Dask/xarray behavior). Included in the unit runs unless combined with other markers.

If you see "`PytestUnknownMarkWarning`" locally, ensure you are running from the repo root so `pytest.ini` is discovered.

## How GitHub Actions runs tests

### tests.yml (push / PR)
- Matrix: Python **3.9, 3.10, 3.11, and 3.12** on `ubuntu-latest`.
- Setup: `actions/setup-python` with pip caching enabled.
- Install: `python -m pip install --upgrade pip`, then `pip install -e ".[dev]"`.
- Unit pass: `pytest -m "not integration and not online" --maxfail=1 --disable-warnings -q`.
- Streaming contract pass: a focused Python 3.11 job runs the PRISM NcSS,
  gridMET, global-climate, median-split synchrony, spatial block, and streaming
  signature tests. This keeps streaming-first regressions visible without
  multiplying those checks across the full Python matrix.
- Optional integration pass: `pytest -m "integration"` (only when `RUN_INTEGRATION=1` is present in the environment, and only on Python 3.11).
- Packaging pass: `python -m build`, `python -m twine check dist/*`, then install the built wheel in a clean virtualenv and smoke-import `cubedynamics`.
- Docs build: `mkdocs build --strict` (separate job in the same workflow, installed from `.[docs]`).
- Timeouts: unit matrix jobs have a 30-minute timeout; streaming, package, and
  docs jobs have 20-minute timeouts.

### online-tests.yml (scheduled / manual)
- Triggers: manual **workflow_dispatch** and a weekly cron (**`0 6 * * 1`** / Mondays at 06:00 UTC).
- Setup: Python 3.11 with pip caching enabled.
- Install: `python -m pip install --upgrade pip`, then `pip install -e ".[dev]"`.
- Command: `pytest -m "integration or online" --maxfail=1 -q` with
  `PYTEST_ADDOPTS` cleared for full output.
- Timeout: 45 minutes.

### Enabling integration in CI
- Default push/PR runs **exclude** `integration` and `online` suites to stay offline and fast.
- Set `RUN_INTEGRATION=1` in GitHub Actions (e.g., via workflow dispatch or repository/env secrets) to execute the integration step in `tests.yml`.
- Online tests run both `integration` and `online` marker sets and are limited to
  the scheduled/manual workflow above.

## Repo testing philosophy

- **Offline by default** – unit tests must pass without network access; integration/online are explicitly marked and opt-in.
- **Integration is opt-in** – expensive or flaky external dependencies stay behind `integration`/`online` markers and the `RUN_INTEGRATION` gate.
- **Streaming-first** – prefer lazy Dask/xarray flows; `streaming` tests assert we do not accidentally force eager computation.
- **Contract tests** – spatial/CRS/time/provenance rules follow the [Spatial & CRS Dataset Contract](../design/spatial_dataset_contract.md). Reconstruction and QA guidance is outlined in [testing_recon](testing_recon.md) for deeper checks on derived cubes.

## New focused coverage

Recent climate synchrony, block-comparison, streaming, and fire/VASE work added
focused tests instead of large default data jobs:

| Area | Tests | What they protect |
| --- | --- | --- |
| Climate median-split synchrony | `tests/test_median_split_synchrony_verb.py` | `v.rolling_median_split_synchrony` output variables, quantile splitting, Dataset lower/upper variable behavior, pipe compatibility, and bounded output-time selection. |
| Spatial block grammar | `tests/test_spatial_units.py` | `v.block_signature`, `v.collect_blocks`, and `v.compare_blocks` semantics, block coordinates, pairwise metrics, and AOI compatibility aliases. |
| PRISM streaming | `tests/test_prism_ncss_streaming.py`, `tests/test_prism_online.py` | Daily NcSS request construction, catalog/alias handling, lazy AOI-cropped PRISM behavior, empty-time failures, and online smoke coverage. |
| gridMET streaming | `tests/test_gridmet_streaming_contract.py`, `tests/test_gridmet_api.py` | Streaming-first gridMET loader contracts, AOI/date normalization, chunk/laziness expectations, and public loader signatures. |
| Global climate adapter | `tests/test_global_climate_streaming.py` | Lazy xarray/Zarr-style global climate normalization to `(time, y, x)`, CRS-neutral bbox slicing, and strict failures for ambiguous dimensions or dateline cases. |
| Fire VASE real-data workflow | `tests/test_real_fire_vase_gridmet_smoke.py` | Offline mocked real-workflow smoke test for FIRED + streamed gridMET, artifact-writing paths, and prescribed-fire detection when a usable field exists. |
| Static fire VASE coloring | `tests/test_real_fire_vase_gridmet_smoke.py` | Regression coverage that static PNG day bands use one scalar per time layer instead of triangle-averaged tessellation colors. |
| Fire VASE panel verb | `tests/test_fire_vase_panel.py` | `v.fire_vase_panel` prescribed-event selection, explicit event IDs, climate-loader use, per-event result collection, and failure reporting. |
| Fire loader calls | `tests/test_fire_plot_loader_calls.py` | `v.fire_plot` PRISM/gridMET streaming calls, Kelvin labels for gridMET temperature, empty-time errors, and explicit synthetic fallback behavior. |
| Streaming public contracts | `src/cubedynamics/tests/test_streaming_contracts.py`, `src/cubedynamics/tests/test_imports.py` | Public streaming helper imports, `chunks` keyword availability, and clear `NotImplementedError` behavior for stubs. |

These tests are intentionally offline by default. Real PRISM/gridMET/FIRED
artifact generation remains an example or manual/scheduled workflow because it
depends on live services and can take long enough to make normal PR checks
noisy.

## Common failure modes

- **Markers not recognized**: run `pytest` from the repository root so `pytest.ini` is picked up; upgrade `pytest` if using a system copy.
- **Missing optional deps**: integration/online tests may require `cubo`, `rasterio`/`GDAL`, or Plotly extras. Install from `.[dev]` or add the missing packages.
- **Network unavailable**: `online` or integration tests that fetch remote data will fail offline; rerun without those markers or provide cached data.
- **Lazy compute expectations**: some `streaming` tests expect Dask-backed objects to remain lazy. Avoid calling `.compute()` in code paths covered by those tests unless explicitly needed.

## Reproducing CI locally

Run the same sequence as CI:

```bash
python -m pip install -e ".[dev]"
pytest -m "not integration and not online" --maxfail=1 --disable-warnings -q
pytest -m "integration"  # if you want to mirror RUN_INTEGRATION=1
mkdocs build --strict
python -m build
python -m twine check dist/*
```

Use `pytest -m "online"` if you also want to mirror the scheduled online workflow.
