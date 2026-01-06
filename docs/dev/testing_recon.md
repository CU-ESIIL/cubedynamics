# Testing Reconnaissance

## 1. Overview
This report inventories the existing test suite, core APIs, and testing conventions in the repository to guide upcoming test redesigns. It captures what is currently tested (and how), highlights network versus offline expectations, and surfaces risks around fire_plot/gridmet/prism/sentinel coverage.

## 2. Repo structure
- `src/` – primary package source for `cubedynamics` (verbs, data loaders, streaming, plotting, viewers, ops, utils).  See [src/cubedynamics/__init__.py](../../src/cubedynamics/__init__.py).
- `climate_cube_math/` – legacy package shims and dataset loaders kept for backward compatibility. See [climate_cube_math/](../../climate_cube_math/).
- `tests/` – pytest suite covering verbs, loaders, viewers, and streaming. See inventory below.
- `docs/` – MkDocs documentation (concepts, datasets, recipes, design, dev notes).
- `.github/workflows/` – CI configurations for unit/integration/online tests and docs builds.

## 3. Package & API map (selected fire/loader entrypoints)
- `cubedynamics.verbs.fire.fire_plot(da=None, *, fired_event=None, fired_daily=None, event_id=None, climate_variable="vpd", freq=None, time_buffer_days=1, n_ring_samples=200, n_theta=296, color_limits=None, show_hist=False, verbose=False, save_prefix=None, fast=False, allow_synthetic=False, prefer_streaming=True) -> Dict[str, Any]`
  - Hybrid cube-first or legacy FIRED-first entrypoint that builds a `FireEventDaily`, computes a `TimeHull`, loads a climate cube (gridMET/PRISM unless a cube is supplied), samples inside/outside climate values, and plots a filled hull plus optional histogram. [Source](../../src/cubedynamics/verbs/fire.py).
- `cubedynamics.fire_time_hull.FireEventDaily` (dataclass) and `TimeHull`
  - Encapsulate FIRED perimeters over time (`event_id`, `t0`/`t1`, centroid coords, geometries) and derived hull geometry/metrics. Created via `build_fire_event_daily`. [Source](../../src/cubedynamics/fire_time_hull.py).
- `cubedynamics.fire_time_hull.load_fired_conus_ak(which="daily", prefer="gpkg", cache_dir=None, *, download=False, dataset_page=..., download_id=..., timeout=180) -> gpd.GeoDataFrame`
  - Loads FIRED CONUS/AK daily or event polygons from cache with optional download/extract fallback; requires EPSG:4326 reprojection. [Source](../../src/cubedynamics/fire_time_hull.py).
- `cubedynamics.fire_time_hull.pick_event_with_joint_support(fired_daily, *, climate_support, time_buffer_days=0, min_days=3, id_col="id", date_col="date")`
  - Scans FIRED events to find one whose date range (with buffer) fits a provided climate support window; raises if none match. [Source](../../src/cubedynamics/fire_time_hull.py).
- `cubedynamics.fire_time_hull.load_climate_cube_for_event(event, *, time_buffer_days=14, variable="tmmx", prefer_synthetic=False, freq=None, prefer_streaming=True, allow_synthetic=False, verbose=False) -> ClimateCube`
  - Determines climate source from `variable` (`gridmet`, `prism`, or error for sentinel NDVI), fetches buffered cube via corresponding loader, and wraps the target variable as `ClimateCube`. [Source](../../src/cubedynamics/fire_time_hull.py).
- `cubedynamics.data.gridmet.load_gridmet_cube(*legacy_args, lat=None, lon=None, bbox=None, aoi_geojson=None, aoi=None, start=None, end=None, variable=None, variables=None, freq=None, time_res=None, chunks=None, prefer_streaming=True, show_progress=True, allow_synthetic=False) -> xr.Dataset`
  - Streaming-first GRIDMET loader supporting modern AOI keyword API plus legacy positional form; falls back to synthetic dataset with provenance/`is_synthetic` attrs when streaming/download fail. [Source](../../src/cubedynamics/data/gridmet.py).
- `cubedynamics.data.prism.load_prism_cube(*legacy_args, lat=None, lon=None, bbox=None, aoi_geojson=None, start=None, end=None, variable="ppt", variables=None, time_res="ME", freq=None, chunks=None, prefer_streaming=True, show_progress=True, allow_synthetic=False) -> xr.Dataset`
  - PRISM loader mirroring GRIDMET semantics (keyword-first, streaming fallback, synthetic option, legacy positional support). [Source](../../src/cubedynamics/data/prism.py).
- `cubedynamics.data.sentinel2.load_s2_cube(lat, lon, start, end, edge_size=1028, resolution=10, cloud_lt=40, bands=None, chunks=None) -> xr.DataArray`
  - Streams Sentinel-2 L2A data via `cubo`, returning dask-backed bands arranged as `(time, band, y, x)` or `(time, y, x)`; used by NDVI computations. [Source](../../src/cubedynamics/data/sentinel2.py).
- `cubedynamics.data.sentinel2.load_s2_ndvi_cube(...) -> xr.DataArray`
  - Loads Sentinel-2 bands then computes NDVI (`ndvi` named, `(time, y, x)`), ensuring required bands are present. [Source](../../src/cubedynamics/data/sentinel2.py).

## 4. Test inventory (grouped)
| Topic | Test files (relative) | What they cover | Markers/notes |
| --- | --- | --- | --- |
| GRIDMET loaders & safety | `tests/test_gridmet_api.py`, `tests/test_gridmet_online.py`, `tests/test_gridmet_safety.py` | Modern vs legacy signatures, streaming vs fallback warnings, synthetic handling, default freq for fire_plot | `online`/`integration` on networked cases; safety test parametrizes `allow_synthetic` |
| PRISM loaders | `tests/test_prism_loader.py`, `tests/test_prism_online.py` | Keyword/legacy API, freq handling, streaming path smoke tests | Online tests marked `online`/`integration` |
| Sentinel/NDVI/STAC | `tests/test_sentinel2_ndvi.py`, `tests/test_sentinel2_online.py`, `tests/test_sentinel_loader_helper.py`, `tests/test_landsat_vis_ndvi.py`, `tests/verbs/test_landsat_mpc.py` | Sentinel-2 cube/NDVI streaming smoke, helper fallbacks, Landsat MPC visualization | Online marked; helper tests cover offline behaviors |
| Fire time hull / fire_plot | `tests/test_fire_plot_cube_first.py`, `tests/test_gridmet_safety.py` (freq defaults), `tests/test_fire_time_hull_loader.py`, `tests/test_verbs_fire_extract.py`, `tests/test_climate_hull_extract.py` | Cube-first fire_plot avoids fetching, hull geometry inference, FIRED download caching, event sampling utilities | Mostly offline; loader uses temp dirs and monkeypatching |
| Streaming / VirtualCube / IO | `tests/test_virtual_cube_streaming.py`, `tests/test_no_eager_compute_or_io.py`, `tests/test_no_eager_values_in_plotting.py`, `tests/test_virtual_cube_core.py`, `tests/test_virtual_cube_streaming.py` | Streaming tilers vs materialized cubes, ensuring no eager compute/IO, virtual cube behavior | No explicit markers; synthetic data |
| Plotting & viewers | `tests/test_plot_cube_viewer.py`, `tests/test_cube_viewer*.py`, `tests/test_plotting_*`, `tests/test_plot_verb.py`, `tests/test_vase*.py`, `tests/test_vase_viz.py`, `tests/test_lexcube_viz.py`, `tests/test_demo_vase.py` | Grammar-based plotting verbs, viewer interactivity/IDs, vase plots, lexicographic viewer; check lazy behavior | Visualization tests rely on synthetic cubes |
| Stats/verbs/core contracts | `tests/test_verbs_*`, `tests/test_ops_stats_virtual.py`, `tests/test_anomalies.py`, `tests/test_correlation.py`, `tests/test_variables_api.py`, `tests/test_public_api_smoke.py`, `tests/test_dependencies.py` | Pipe grammar, variance/anomaly/tail dependence, public API exposure, dependency checks | Mostly fast unit tests |

## 5. Pytest conventions & markers
- Markers declared: `online` (cubo/network), `streaming`, `integration`. [pytest.ini](../../pytest.ini).
- Default options: `pythonpath = src .` and disable `zarr` plugin; markers applied in tests (gridmet/prism/sentinel). [pytest.ini](../../pytest.ini).
- Repository-level `conftest.py` ensures `src` importability, shims `plotly` if missing, and loads `cubedynamics` via importlib. [conftest.py](../../conftest.py).
- Test fixtures: `tiny_cube`, `monotone_series`, and helper `assert_is_lazy_xarray` to enforce dask-backed objects when dask is available. [tests/conftest.py](../../tests/conftest.py).

## 6. CI test execution (GitHub Actions)
- `.github/workflows/tests.yml` runs unit tests on pushes/PRs with Python 3.11: installs `requirements.txt`, installs package editable, runs `pytest -m "not integration" -q`, then (conditionally via `RUN_INTEGRATION=1`) runs full integration suite. [Workflow](../../.github/workflows/tests.yml).
- `.github/workflows/online-tests.yml` schedules/dispatches online integration runs executing `pytest -m "integration"`. [Workflow](../../.github/workflows/online-tests.yml).
- Docs build via `.github/workflows/tests.yml` `docs` job runs `mkdocs build --strict`. [Workflow](../../.github/workflows/tests.yml).

## 7. Existing fixtures and helpers
- Synthetic cube fixtures (`tiny_cube`, `monotone_series`) and laziness assertion for dask-backed arrays are centralized in `tests/conftest.py` for reuse across verbs/viewers/plotting tests. [tests/conftest.py](../../tests/conftest.py).
- Fire/loader tests extensively monkeypatch external calls (e.g., GRIDMET streaming, FIRED downloads) to keep tests offline while exercising fallback paths. Examples: gridmet safety test overrides loader; FIRED loader test swaps download and geopandas readers. [tests/test_gridmet_safety.py](../../tests/test_gridmet_safety.py), [tests/test_fire_time_hull_loader.py](../../tests/test_fire_time_hull_loader.py).

## 8. Network vs offline testing strategy (current)
- Network-dependent tests are marked `online` and `integration`; they cover streaming gridMET/PRISM/Sentinel behavior and are skipped in default CI. [pytest.ini](../../pytest.ini), [tests/test_gridmet_online.py](../../tests/test_gridmet_online.py), [tests/test_prism_online.py](../../tests/test_prism_online.py), [tests/test_sentinel2_online.py](../../tests/test_sentinel2_online.py).
- Offline tests rely on synthetic data or monkeypatched loaders to validate APIs, shape/dim invariants, and fallback behavior (e.g., synthetic GRIDMET cubes when streaming fails). [tests/test_gridmet_safety.py](../../tests/test_gridmet_safety.py), [src/cubedynamics/data/gridmet.py](../../src/cubedynamics/data/gridmet.py).
- CI default (`-m "not integration"`) executes offline/fast coverage; integration/online require explicit opt-in. [tests workflow](../../.github/workflows/tests.yml).

## 9. Design principles implied by code/tests/docs
- Grammar-of-cubes API: verbs operate on dask-friendly cubes with pipeable transformations and plotting grammar. [src/cubedynamics/__init__.py](../../src/cubedynamics/__init__.py).
- Spatial dataset contract: two spatial dims, EPSG inference priority, boundary-inclusive membership, and optional rasterize fast-path; used by fire_plot helpers and intended for shared tests. [docs/design/spatial_dataset_contract.md](../../docs/design/spatial_dataset_contract.md).
- Streaming-first loaders with synthetic fallbacks (gridMET/PRISM) encode resilience to offline environments while preserving provenance via attrs (`source`, `is_synthetic`, `backend_error`). [src/cubedynamics/data/gridmet.py](../../src/cubedynamics/data/gridmet.py), [src/cubedynamics/data/prism.py](../../src/cubedynamics/data/prism.py).
- Fire workflow contract: `fire_plot` expects EPSG inference, time-buffered climate cubes, and differentiates cube-first vs legacy FIRED-first modes. [src/cubedynamics/verbs/fire.py](../../src/cubedynamics/verbs/fire.py), [src/cubedynamics/fire_time_hull.py](../../src/cubedynamics/fire_time_hull.py).

## 10. Gaps / risks for upcoming changes
- Fire plotting coverage is mainly synthetic and focuses on cube-first no-fetch and gridMET freq defaults; no integration tests combine `fire_plot` with real GRIDMET/PRISM/Sentinel streams, leaving cross-dataset behavior unvalidated. [tests/test_fire_plot_cube_first.py](../../tests/test_fire_plot_cube_first.py), [tests/test_gridmet_safety.py](../../tests/test_gridmet_safety.py).
- Changes to `fire_plot` defaults (`freq`, `allow_synthetic`, buffer days) could alter gridmet/prism loader calls without existing assertions beyond freq fallback to daily; hist/plot outputs are largely mocked. [tests/test_gridmet_safety.py](../../tests/test_gridmet_safety.py).
- Sentinel NDVI is only covered by online smoke tests; offline abstractions or fixtures are missing, making deterministic testing difficult and hindering regression coverage without network access. [tests/test_sentinel2_ndvi.py](../../tests/test_sentinel2_ndvi.py), [src/cubedynamics/data/sentinel2.py](../../src/cubedynamics/data/sentinel2.py).
- Streaming/VirtualCube tests validate variance/strategy but do not assert IO boundaries for loader integrations with actual remote sources; risk if streaming interfaces change. [tests/test_virtual_cube_streaming.py](../../tests/test_virtual_cube_streaming.py).

## 11. Recommended test architecture
- **Contract tests (offline, fast):** Cover shared spatial/temporal contracts (EPSG inference, spatial dims, boundary semantics) using synthetic gridMET/PRISM/Sentinel-like cubes per the spatial dataset contract. Expand fire_plot contract tests to assert loader selection, freq defaults, and buffer handling without network.
- **Verb-level tests (offline with fixtures):** Add deterministic fixtures for NDVI/PRISM/GRIDMET subsets to exercise fire_plot, variance/anomaly verbs, and plotting aesthetics without mocking plotting internals; preserve `streaming` marker for streaming-first behaviors.
- **Integration tests (opt-in `integration`/`online`):** Maintain lightweight streaming smoke tests for gridMET/PRISM/Sentinel but add scenario-based fire_plot end-to-end runs across datasets when network available. Keep CI default excluding these markers; add synthetic-recorded responses if feasible to reduce flakiness.
