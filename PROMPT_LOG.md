# Prompt Log

This log records substantial user goals, decisions, outputs, and validation for
CubeDynamics development sessions. Keep entries concise and factual. Do not add
secrets, credentials, private tokens, or unrelated transcript text.

## 2026-07-07 — Website Panel Example Smoke Tests

### User Goal
- Decide whether the new VASE-panel and climate synchrony cube-panel website
  examples need tests.

### Implementation Summary
- Added `tests/test_docs_example_panels.py`.
- The tests run both offline docs examples into temporary output paths and
  verify the generated HTML contains expected panel labels/content.
- The tests also verify the VASE and climate synchrony website pages reference
  the embedded assets, rebuild scripts, and public API patterns.
- Updated `docs/dev/ci_testing.md` to list the new website panel example
  coverage.

### Validation
- `python3 -m py_compile tests/test_docs_example_panels.py` passed.
- `git diff --check` passed.
- Focused test passed:
  `uv run --python 3.11 --with-editable . --with pytest pytest tests/test_docs_example_panels.py -q`
  (`4 passed`).

## 2026-07-07 — Climate Synchrony Cube Panel Website Sample

### User Goal
- Add a climate synchrony website section showing how to compare multiple
  synchrony cubes in a panel of interactive cubes.

### Implementation Summary
- Added `examples/climate_synchrony_cube_panel_demo.py`, an offline synthetic
  multi-block example that computes one median-split synchrony cube per block,
  concatenates them along `block`, and renders a faceted `CubePlot`.
- Generated `docs/assets/figures/climate_synchrony_cube_panel.html` for the
  embedded website sample output.
- Updated `docs/recipes/climate_tail_dep_center.md` with a dedicated
  interactive panel section, iframe embed, rebuild command, and copy-pasteable
  code showing the `xr.concat(..., dim="block")` plus `.facet_wrap("block")`
  pattern.

### Validation
- Regenerated the HTML sample with:
  `uv run --python 3.11 --with-editable . python examples/climate_synchrony_cube_panel_demo.py --output docs/assets/figures/climate_synchrony_cube_panel.html`.
- `python3 -m py_compile examples/climate_synchrony_cube_panel_demo.py` passed.
- `git diff --check` passed.
- Focused facet tests passed:
  `uv run --python 3.11 --with-editable . --with pytest pytest tests/test_plotting_facets_export.py tests/test_plotting_grammar.py::test_facets_render_multiple_panels -q`
  (`5 passed`).
- Strict docs build passed with:
  `uv run --python 3.11 --extra docs mkdocs build --strict --site-dir /tmp/cubedynamics-mkdocs-check`.

## 2026-07-07 — Website VASE Panel Sample

### User Goal
- Add a separate website section for panels of VASEs showing sample output and
  a copy-pasteable code chunk for users to recreate it.

### Implementation Summary
- Added `examples/fire_vase_panel_demo.py`, an offline synthetic prescribed-burn
  example that builds a small climate cube and runs the public
  `v.fire_vase_panel(...)` verb.
- Generated `docs/assets/figures/fire_vase_panel_sample.html` as the embedded
  website sample output.
- Updated `docs/capabilities/fire-vase.md` with a dedicated prescribed-burn
  VASE panel section, iframe embed, rebuild command, and the underlying
  `v.fire_vase_panel(...)` code pattern.

### Validation
- Regenerated the HTML sample with:
  `uv run --python 3.11 --with-editable . python examples/fire_vase_panel_demo.py --output docs/assets/figures/fire_vase_panel_sample.html`.
- `python3 -m py_compile examples/fire_vase_panel_demo.py` passed.
- `git diff --check` passed.
- Focused test passed:
  `uv run --python 3.11 --with-editable . --with pytest pytest tests/test_fire_vase_panel.py -q`
  (`3 passed`).
- Strict docs build passed with:
  `uv run --python 3.11 --extra docs mkdocs build --strict --site-dir /tmp/cubedynamics-mkdocs-check`.

## 2026-07-06 — Climate Synchrony, PRISM Streaming, Median Split

### User Goals
- Find and understand the existing climate synchrony function.
- Add tests and plots showing a synchrony cube and a flat time plot.
- Ensure the analysis uses climate data, not NDVI.
- Split climate synchrony by the median: lower-half `tmin` events and
  upper-half `tmax` events.
- Keep PRISM support, but add a general verb for these median-split sets.
- Run small examples, then a real full-resolution PRISM example over the full
  available time record.
- Stream data rather than downloading PRISM archives.
- Clarify whether the run wrote/downloaded a large amount of data, and identify
  future cloud-optimized or parallel streaming improvements.

### Implementation Summary
- Added/updated `v.rolling_median_split_synchrony` for DataArray/Dataset inputs.
  For PRISM temperature datasets, `lower_var="tmin"` computes below-median cold
  synchrony and `upper_var="tmax"` computes above-median hot synchrony.
- Added `output_stride` and explicit `output_times` support so long daily
  records can produce monthly-scale outputs and bounded batches.
- Updated PRISM loading to stream real daily AOI subsets through NCSCO THREDDS
  NcSS with `freq="D"` and no silent synthetic fallback.
- Added handling for PRISM catalog aliases, THREDDS daily-file encoding quirks,
  OPeNDAP ASCII fallback for NcSS `unknown DataType == long` failures, and
  coordinate snapping to the PRISM 1/24-degree grid.
- Added a full-record real-data example:
  `examples/real_prism_median_split_synchrony.py`.
- Added checkpointed batch computation in the example so long runs can resume
  without recomputing completed windows.
- Added/updated docs for PRISM streaming and the climate tail-dependence recipe.

### Artifacts Created
- `artifacts/prism-full-record/real_prism_synchrony_cube.html`
- `artifacts/prism-full-record/real_prism_synchrony_timeseries.png`
- `artifacts/prism-full-record/real_prism_synchrony.nc`
- `artifacts/prism-full-record/real_prism_manifest.json`
- `artifacts/prism-full-record/batches/synchrony_batch_*.nc`
- Earlier exploratory artifacts remain under `artifacts/prism-real/`,
  `artifacts/prism-real-cache/`, and `artifacts/prism-stream-smoke/`.

### Real PRISM Run
- Source: real PRISM streamed via NCSCO THREDDS NcSS.
- AOI: `[-105.75, 39.5, -104.75, 40.5]`.
- Input period: `1981-01-01` through `2025-12-31`.
- Input size: `16,436` daily timesteps on a `25 x 25` PRISM grid.
- Output: `547` rolling windows on a `25 x 25` grid.
- Window: `90` days.
- Output stride: `30` days.
- Batch size: `60` output windows.
- Approximate streamed run time observed: `16.72` minutes.
- Disk written for the full-record output: about `8.2 MB`, mostly final outputs
  plus small NetCDF batch checkpoints. The older direct-download experiment
  cache under `artifacts/prism-real-cache/` is separate and about `153 MB`.

### Result Interpretation
- Both cold and hot climate synchrony were high across this small AOI.
- Hot-side synchrony was usually slightly higher than cold-side synchrony.
- Median spatial synchrony:
  - below-median `tmin`: about `0.861`
  - above-median `tmax`: about `0.918`
  - `bottom_minus_top`: about `-0.022`
- About `29%` of rolling-window spatial medians had cold-side synchrony greater
  than hot-side synchrony.
- No strong long-term trend was apparent in `bottom_minus_top`; a simple linear
  summary was about `+0.004` per decade.

### Validation
- Syntax checks passed for edited modules and the real PRISM example with
  `python3 -m py_compile`.
- `git diff --check` passed.
- Focused Docker tests passed:
  `pytest tests/test_prism_ncss_streaming.py tests/test_median_split_synchrony_verb.py -q -p no:cacheprovider`
  (`12 passed`, one third-party pydantic deprecation warning).
- Short real-data streaming smoke passed for `2024-01-01` through `2024-03-31`.
- Full real-data PRISM run completed and generated the artifacts listed above.

### Caveats and Follow-Ups
- PRISM is not global. For whole-globe climate synchrony, add a global source
  such as ERA5/TerraClimate or another cloud-native gridded climate backend.
- The current PRISM path is server-side AOI streaming, not true cloud-optimized
  chunked storage. It avoids full archive downloads, but full records still
  require many daily HTTP requests.
- Best next performance step: add a ring-buffer streaming runner that fetches
  each daily AOI subset once, keeps only the 90-day window in memory, emits
  every requested output timestep, and optionally prefetches daily requests in
  parallel.

## 2026-07-06 — AOI Spatial Units and Pairwise Synchrony Comparison

### User Goals
- Move from one AOI synchrony cube toward spatial comparison across places.
- Start with pairwise comparisons between two AOI cubes.
- Preserve a path toward small arrays of AOIs and eventually global
  meta-analysis with specific spatial comparisons and richer spatial
  operations.

### Implementation Summary
- Added `cubedynamics.stats.spatial_units` with:
  - `aoi_signature(...)`: summarize an AOI cube into a named unit time
    signature.
  - `compare_aoi_signatures(...)`: compare two signatures over shared time with
    Pearson correlation, mean difference, RMSE, and finite sample count.
- Added pipe-ready verbs:
  - `v.aoi_signature(unit_id=...)`
  - `v.compare_aoi_signature(other)`
- Added docs recipe `docs/recipes/spatial_synchrony_units.md`.
- Updated public API docs, stats verb reference, function inventory, recipe
  index, and MkDocs nav.

### Design Notes
- The first abstraction is intentionally small: each AOI becomes one named
  `unit` with a time signature per variable.
- Pairwise comparison is the first unit of analysis. Many-unit arrays can build
  on the same signature representation without changing the synchrony cube
  calculation.
- The spatial arena should eventually preserve unit geometry/centroids and
  support distance-aware joins, selected comparison sets, and global backends.

### Validation
- Added `tests/test_spatial_units.py`.
- Updated `tests/test_public_api_smoke.py`.
- Focused Docker test passed:
  `pytest tests/test_spatial_units.py tests/test_public_api_smoke.py -q -p no:cacheprovider`
  (`6 passed`, one third-party pydantic deprecation warning).
- Real-artifact smoke passed by converting
  `artifacts/prism-full-record/real_prism_synchrony.nc` to an AOI signature and
  comparing it to itself (`pearson_r = 1`, `mean_difference = 0`, `rmse = 0`).

## 2026-07-06 — Block Grammar for Spatial Arena Workflows

### User Goals
- Replace AOI-as-the-main-term with a more general building unit.
- Use **block** for each local cube/signature so AOIs, tiles, regions, and
  sampled neighborhoods can all become comparable units.
- Add a verb for groups of blocks and begin a grammar of building and comparing
  block collections.

### Implementation Summary
- Added block-first helpers in `cubedynamics.stats.spatial_units`:
  - `block_signature(...)`
  - `collect_blocks(...)`
  - `compare_blocks(...)`
- Added pipe-ready verbs:
  - `v.block_signature(block_id=...)`
  - `v.collect_blocks(block_b, block_c, ...)`
  - `v.compare_blocks()`
- Kept `v.aoi_signature(...)` and `v.compare_aoi_signature(...)` available as
  compatibility names for early AOI notebooks.
- Rewrote the spatial recipe around block grammar and updated public API docs,
  stats verb reference, function inventory, and MkDocs navigation.

### Design Notes
- A block is any local cube footprint used as spatial building material: AOI,
  tile, region, sampled pixel neighborhood, or named comparison site.
- `block_signature` reduces local cube space but keeps time.
- `collect_blocks` stacks one-block signatures along a `block` dimension.
- `compare_blocks` returns all unique pairwise comparisons with dimensions
  `(pair, variable)` and coordinates `left_block`/`right_block`.

### Validation
- Focused Docker test passed:
  `pytest tests/test_spatial_units.py tests/test_public_api_smoke.py -q -p no:cacheprovider`
  (`9 passed`, one third-party pydantic deprecation warning).
- Real-artifact smoke passed by converting the full PRISM synchrony NetCDF into
  two block signatures, collecting them, and comparing the collection
  (`pearson_r = 1`, `mean_difference = 0`, `rmse = 0` for the copy pair).

## 2026-07-06 — gridMET/Global Streaming Pathways and CI Audit

### User Goals
- Make sure gridMET and global alternative climate pathways work through
  streaming/lazy interfaces.
- Audit CI/CD and keep tests current without overwhelming the suite.
- Prefer test-first guardrails for the new streaming/block direction.

### Implementation Summary
- Added `cubedynamics.stream_global_climate_cube(...)` for already-open lazy
  global xarray/Zarr-style climate sources. It normalizes dimensions to
  `(time, y, x)`, supports bbox/AOI cropping, handles 0-360 longitude subsets
  when possible, preserves chunks, and avoids package-managed downloads/cache.
- Added offline tests for the global adapter and gridMET streaming contracts.
- Tightened `load_gridmet_cube` so Dask-backed streaming values are not computed
  by the all-NaN safety check, while preserving the guard for eager in-memory
  fallback/stub datasets.
- Updated public exports and streaming contract imports to include the global
  adapter.
- Updated GitHub Actions with pip caching, job timeouts, a focused Python 3.11
  streaming-contract job, and scheduled/manual online tests that run both
  `integration` and `online` markers.
- Cleaned CI hygiene issues found by the broader offline suite:
  - made `cubedynamics.viewers.simple_cube_widget` import `ipywidgets` lazily;
  - removed optional `cftime` use from unit tests that did not test calendars;
  - made `CubePlot.to_html()` avoid writing `cube_da.html` by default while
    preserving explicit `out_html` writes;
  - made viewer iframe HTML fall back to the system temp directory when the
    current directory is read-only;
  - moved a viewer test's scratch output into `tmp_path`.
- Updated streaming/backend/CI docs to explain PRISM, gridMET, and global
  xarray-backed pathways honestly.

### Design Notes
- gridMET's lower-level real-data helper streams yearly NetCDF files over HTTP
  without writing archives, but it is not yet true cloud-optimized byte-range
  access. Global-scale gridMET work should still be tiled by space/time until a
  more cloud-native backend exists.
- The global alternative pathway intentionally starts from an xarray object
  supplied by the caller. CubeDynamics owns cube semantics and downstream verbs,
  not credentials, catalogs, or remote-store authentication.
- The new CI streaming-contract job is intentionally narrow: it protects PRISM
  NcSS, gridMET streaming, global xarray streaming, median-split synchrony, and
  block comparison behavior without multiplying those checks across every
  Python version.

### Validation
- Exact new streaming-contract job passed in Docker:
  `pytest tests/test_prism_ncss_streaming.py tests/test_gridmet_streaming_contract.py tests/test_global_climate_streaming.py tests/test_median_split_synchrony_verb.py tests/test_spatial_units.py src/cubedynamics/tests/test_streaming_contracts.py --maxfail=1 --disable-warnings -q -p no:cacheprovider`
  (`29 passed`, one third-party pydantic deprecation warning).
- Broad offline CI command passed in Docker with the repo mounted read-only:
  `pytest -m "not integration and not online" --maxfail=1 --disable-warnings -q -p no:cacheprovider`
  (`252 passed`, `5 skipped`, `8 deselected`, `40 warnings`).
- Static checks passed:
  `git diff --check`, workflow YAML parsing, and targeted `py_compile`.

## 2026-07-06 — Real FIRED + gridMET Fire Vase Smoke Test

### User Goals
- Run a real-data test of the fire/VASE path with gridMET climate.
- Produce a static plot and an interactive artifact.
- Evaluate how close the current fire workflow is to one-vase-per-prescribed
  burn across the western US.

### Implementation Summary
- Added `examples/real_fire_vase_gridmet_smoke.py`.
- The example loads FIRED daily and event layers into
  `artifacts/fire-vase-gridmet-real/fired-cache/`.
- It filters to a western-US bounding box, looks for prescribed-fire evidence
  in FIRED event attributes, chooses a duration-bounded event, streams real
  gridMET yearly NetCDF data through `stream_gridmet_to_cube`, and passes the
  real gridMET cube into `v.fire_plot` in cube-first mode.
- Added `h5netcdf` to package dependencies because real gridMET yearly files are
  NetCDF4 and the SciPy NetCDF3 backend cannot open them.

### Artifacts
- Static PNG:
  `artifacts/fire-vase-gridmet-real/real_fire_vase_gridmet_static.png`
- Interactive Plotly HTML:
  `artifacts/fire-vase-gridmet-real/real_fire_vase_gridmet_interactive.html`
- Manifest:
  `artifacts/fire-vase-gridmet-real/manifest.json`
- Candidate event table:
  `artifacts/fire-vase-gridmet-real/candidate_events.csv`

### Result
- Selected FIRED event: `2445`
- Event window: `2001-03-16` to `2001-03-29`
- Centroid: `39.0754, -122.0293`
- gridMET variable: `tmmx`
- gridMET cube shape: `time=16`, `lat=5`, `lon=5`
- Hull duration layers: `8`
- Inside/outside samples: `29` / `346`

### Caveat
- The FIRED event attributes available in this run did not expose a reliable
  prescribed-burn flag. The artifact is therefore a real western FIRED event
  with real gridMET climate, not a confirmed prescribed burn. A production
  western prescribed-burn workflow needs an explicit prescribed-fire source or
  a documented FIRED field mapping before claiming prescribed status.

## 2026-07-06 — Fire VASE/gridMET CI Guardrails

### User Goals
- Check whether the new real FIRED + streamed gridMET fire VASE path has good
  CI/CD coverage.
- Keep tests useful and focused rather than turning CI into a large external
  data job.

### Implementation Summary
- Added `tests/test_real_fire_vase_gridmet_smoke.py`, an offline smoke test for
  the example workflow. It mocks FIRED and gridMET services but exercises event
  selection, prescribed-fire detection when the field exists, streaming call
  parameters, fire_plot invocation, and artifact writing.
- Added a regression test that keeps gridMET `tmmx` labels in Kelvin for
  `fire_plot`.
- Added the new fire/gridMET smoke test to the focused GitHub Actions
  `streaming-contracts` job.

### Validation
- Focused Docker tests passed:
  `pytest tests/test_real_fire_vase_gridmet_smoke.py tests/test_fire_plot_loader_calls.py tests/test_gridmet_streaming_contract.py -q -p no:cacheprovider`
  (`11 passed`, one third-party pydantic deprecation warning).
- Exact focused CI command passed:
  `pytest tests/test_prism_ncss_streaming.py tests/test_gridmet_streaming_contract.py tests/test_global_climate_streaming.py tests/test_median_split_synchrony_verb.py tests/test_spatial_units.py tests/test_real_fire_vase_gridmet_smoke.py src/cubedynamics/tests/test_streaming_contracts.py --maxfail=1 --disable-warnings -q -p no:cacheprovider`
  (`30 passed`, one third-party pydantic deprecation warning).

### Caveat
- This deliberately does not run a full FIRED/gridMET network artifact job on
  every PR. The real-data dependencies are too slow and failure-prone for normal
  CI. Online CI still covers gridMET access separately; a future manual or
  scheduled fire-VASE artifact workflow can be added once the prescribed-fire
  source/field mapping is pinned down.

## 2026-07-07 — Static Fire VASE Daily-Band Coloring Fix

### User Goals
- Fix the mismatch between the static PNG and interactive HTML fire VASE plots.
- Remove misleading vertical triangle color striping from the PNG so daily
  climate bands are interpreted as bands rather than mesh tessellation.

### Implementation Summary
- Reworked the static PNG renderer in
  `examples/real_fire_vase_gridmet_smoke.py` to assign one scalar per explicit
  hull time layer/day band instead of averaging vertex colors per triangle.
- Disabled visible triangle edge lines in the static `Poly3DCollection`.
- Added a regression test proving both triangles in one side-wall day band get
  the same scalar value.
- Made the example's heavy plotting/geospatial imports lazy where possible.
- Added `h5py` as an explicit dependency because `h5netcdf` needs it for the
  real gridMET NetCDF4 stream.

### Validation
- Focused uv test passed:
  `uv run --python 3.11 --with-editable . --with pytest pytest tests/test_real_fire_vase_gridmet_smoke.py -q`
  (`2 passed`, one third-party pydantic deprecation warning).
- Lightweight direct band-mapping assertion passed with values `[100.0, 100.0]`.
- `py_compile` and `git diff --check` passed.
- Regenerated the real FIRED/gridMET artifacts in
  `artifacts/fire-vase-gridmet-real/`.

## 2026-07-07 — Prescribed-Burn Fire VASE Panel Verb

### User Goals
- Keep the existing single-event fire VASE verb stable.
- Add a new verb for building a panel of VASEs across the full prescribed-burn
  list.

### Implementation Summary
- Added `v.fire_vase_panel(...)` in the canonical fire verb module.
- The new verb selects prescribed events from `fired_events` using either
  explicit `event_ids`, `prescribed_column`/`prescribed_values`, or an automatic
  text pattern for prescribed-burn labels.
- It supports pipe-first usage with an already-open climate cube, custom
  per-event `climate_loader(event)` functions, or explicit per-event climate
  loading via `load_climate=True`.
- It assembles per-event `fire_plot` outputs into a Plotly subplot figure
  returned as `fig_panel`, while also returning event records, individual
  results, failures, and prescribed-field evidence.
- Updated API docs and function inventory with the new verb.

### Validation
- Focused uv test passed:
  `uv run --python 3.11 --with-editable . --with pytest pytest tests/test_fire_vase_panel.py tests/test_fire_hull_api.py -q`
  (`9 passed`, two third-party/legacy warnings).

## 2026-07-07 — Repository Python Developer Harness

### User Goals
- Add Python support directly to the repository workflow so local development,
  fire/VASE tests, streaming checks, and docs checks can run without ad hoc
  per-session commands.

### Implementation Summary
- Added `.python-version` with Python 3.11 as the preferred repo runtime.
- Added a `Makefile` that creates a local `.venv/`, installs CubeDynamics in
  editable dev mode, and exposes focused targets for offline tests,
  fire/VASE tests, streaming tests, and docs builds.
- Updated `README.md` and `INSTALL.md` with the new local Python workflow while
  keeping the conda-forge install path for geospatial dependency stability.

### Validation
- Dry-run Make targets passed:
  `make -n install test-fire test-streaming docs`.
- `git diff --check` passed.

### Notes
- The local `.venv/` remains ignored by git. The repository now records the
  desired Python version and commands, not a committed interpreter or virtual
  environment.

## 2026-07-07 — Website Verb and Test Documentation Refresh

### User Goals
- Update the website so the new verbs are discoverable.
- Describe the focused tests added for climate synchrony, spatial blocks,
  streaming pathways, and fire/VASE workflows.

### Implementation Summary
- Expanded the Verbs API with `v.rolling_median_split_synchrony`,
  `v.block_signature`, `v.collect_blocks`, and `v.compare_blocks` examples and
  semantics.
- Added `v.fire_plot` and `v.fire_vase_panel` workflow guidance to the Fire
  VASE / FireHull capability page and the fire event recipe.
- Updated the capability and recipe overviews so the new synchrony, block, and
  prescribed-burn panel workflows are findable from the website navigation.
- Added a focused coverage table to the CI/testing page describing the tests
  added for median-split synchrony, block grammar, PRISM/gridMET/global
  streaming, real fire VASE smoke workflow, PNG day-band coloring, and the
  fire VASE panel verb.

### Validation
- `git diff --check` passed for the updated docs and prompt log.
- Targeted `rg` checks confirmed the new verb names and test references are
  present in the updated website pages.
- `python3 -m mkdocs build --strict` could not run in the current default
  Python environment because `mkdocs` is not installed there.

## 2026-07-07 — Lexcube CI Smoke Fix

### User Goals
- Fix the offline CI failure in `tests/test_lexcube_viz.py` where Lexcube
  raised `KeyError: 'source'` for an in-memory cube with integer time
  coordinates.

### Implementation Summary
- Added a small Lexcube preparation helper that validates `(time, y, x)`,
  transposes into canonical order, and adds an empty `encoding["source"]` on a
  shallow copy when integer time coordinates look day-of-year-like.
- Moved Lexcube import until after validation/preparation so dimension tests can
  run without the optional widget dependency.
- Added regression coverage that the source placeholder is added only to the
  prepared copy, leaving the caller's cube unchanged.

### Validation
- `python3 -m py_compile src/cubedynamics/viz/lexcube_viz.py` passed.
- `python3 -m py_compile tests/test_lexcube_viz.py` passed.
- `git diff --check` passed for the touched files.
- Local pytest could not run in the default Python environment because `pytest`
  and `xarray` are not installed there.

### Follow-up
- CI on Python 3.9 showed Lexcube itself is installed but not importable because
  it uses runtime `float | int` annotations. The Lexcube widget smoke test now
  skips when the optional dependency raises during import, while wrapper
  validation/preparation tests still run.

## 2026-07-07 — Website Interactive Plot Embeds

### User Goals
- Add interactive plots to the website docs for the fire VASE page and the
  climate synchrony page.

### Implementation Summary
- Copied the real fire VASE Plotly HTML artifact into
  `docs/assets/figures/fire_vase_gridmet_interactive.html`.
- Copied the compact median-split climate synchrony cube HTML into
  `docs/assets/figures/climate_median_split_synchrony_cube.html`.
- Embedded both assets with the existing `interactive-embed` iframe pattern and
  new-tab fallback links.

### Validation
- `git diff --check` passed for the updated docs and prompt log.
- Confirmed both embedded HTML assets exist under `docs/assets/figures/`.
- Asset sizes are small enough for the docs site:
  `fire_vase_gridmet_interactive.html` is 55 KB and
  `climate_median_split_synchrony_cube.html` is 40 KB.

### Follow-up
- Added copy-paste reproduction command blocks to both pages. The fire VASE page
  points to `examples/real_fire_vase_gridmet_smoke.py`; the climate synchrony
  page points to the offline `examples/median_split_synchrony_demo.py`.

## 2026-07-07 — Diagnostic PNG Panel Verb

### User Goals
- Add PNG versions of the interactive fire VASE and climate synchrony outputs.
- Make the static output a rich panel: flat cube/schematic perspectives plus
  data plots and summary diagnostics.
- Prefer a single verb if it can reasonably handle different inputs.

### Implementation Summary
- Added `v.diagnostic_panel(...)`, a Matplotlib-based verb that accepts
  `CubePlot`, `DataArray`, synchrony `Dataset`, or `v.fire_plot` result
  dictionaries.
- Cube panels show three flat cube perspectives, a time-series summary,
  variance map, and value distribution.
- Synchrony Dataset panels plot cold synchrony, hot synchrony, and cold-minus-hot
  traces through time while using the difference cube for the flat faces and
  variance map.
- Fire/VASE panels show the 3D hull, footprint/time projections, available
  climate traces such as `tmmx`, `tmmn`, and `vpd`, inside/outside samples, and
  hull metrics.
- Updated the median-split synchrony and real fire/gridMET examples to write
  diagnostic PNG outputs alongside the interactive HTML outputs.

### Validation
- `python3 -m py_compile` passed for the new verb, tests, examples, and verb
  namespace.
- `git diff --check` passed for touched files.
- Focused uv tests passed:
  `uv run --python 3.11 --with-editable . --with pytest pytest tests/test_diagnostic_panel.py -q`
  (`4 passed`).
- Fire smoke regression passed:
  `uv run --python 3.11 --with-editable . --with pytest pytest tests/test_real_fire_vase_gridmet_smoke.py -q`
  (`2 passed`).
