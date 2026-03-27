# CI and Testing

CubeDynamics tests are split into small, fast unit suites and opt-in integration/online checks that hit live services. This page explains how to run them locally and how GitHub Actions orchestrates them.

## Quick start (local)

- Install development dependencies:
  
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
- Install: `python -m pip install --upgrade pip`, then `pip install -e ".[dev]"`.
- Unit pass: `pytest -m "not integration and not online" --maxfail=1 --disable-warnings -q`.
- Optional integration pass: `pytest -m "integration"` (only when `RUN_INTEGRATION=1` is present in the environment, and only on Python 3.11).
- Packaging pass: `python -m build`, `python -m twine check dist/*`, then install the built wheel in a clean virtualenv and smoke-import `cubedynamics`.
- Docs build: `mkdocs build --strict` (separate job in the same workflow, installed from `.[docs]`).

### online-tests.yml (scheduled / manual)
- Triggers: manual **workflow_dispatch** and a weekly cron (**`0 6 * * 1`** / Mondays at 06:00 UTC).
- Install: `python -m pip install --upgrade pip`, then `pip install -e ".[dev]"`.
- Command: `pytest -m "integration"` with `PYTEST_ADDOPTS` cleared for full output.

### Enabling integration in CI
- Default push/PR runs **exclude** `integration` and `online` suites to stay offline and fast.
- Set `RUN_INTEGRATION=1` in GitHub Actions (e.g., via workflow dispatch or repository/env secrets) to execute the integration step in `tests.yml`.
- Online tests always run the integration marker set and are limited to the scheduled/manual workflow above.

## Repo testing philosophy

- **Offline by default** – unit tests must pass without network access; integration/online are explicitly marked and opt-in.
- **Integration is opt-in** – expensive or flaky external dependencies stay behind `integration`/`online` markers and the `RUN_INTEGRATION` gate.
- **Streaming-first** – prefer lazy Dask/xarray flows; `streaming` tests assert we do not accidentally force eager computation.
- **Contract tests** – spatial/CRS/time/provenance rules follow the [Spatial & CRS Dataset Contract](../design/spatial_dataset_contract.md). Reconstruction and QA guidance is outlined in [testing_recon](testing_recon.md) for deeper checks on derived cubes.

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
