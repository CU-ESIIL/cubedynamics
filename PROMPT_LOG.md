# Prompt Log

This log records substantial user goals, decisions, outputs, and validation for
CubeDynamics development sessions. Keep entries concise and factual. Do not add
secrets, credentials, private tokens, or unrelated transcript text.

## 2026-07-21 — Real Climate-colored Non-prescribed Fire VASE PDF Panel

### User Goals
- Create a static PDF panel of VASE thumbnails and metrics using real fire and
  real climate data.
- Treat the cached real FIRED candidate events as non-prescribed for this panel.
- Include climate coloring.

### Implementation Summary
- Added `examples/fire_vase_pdf_panel_demo.py`, a real-data static PDF
  contact-sheet generator for cached FIRED candidate events and gridMET climate.
- The PDF renders FireHull/VASE thumbnails colored by gridMET `tmmx` and
  annotates each event with space, time, volume, and an OT-v proxy.
- The cached FIRED event table does not contain a prescribed-fire attribute, so
  the generated artifact treats all cached candidates as non-prescribed by
  assumption.
- Corrected the static renderer to color whole between-date quadrilateral bands
  with one date/layer value instead of averaging colors independently over the
  two triangles in each side-wall quad.
- Replaced the normalized `cubedynamics.data.gridmet` mock-streaming path with
  cached real gridMET `tmmx_YYYY.nc` files and converted Kelvin values to
  Celsius/Fahrenheit for the PDF colorbars.
- Updated the real gridMET helper to accept CF variable names such as
  `air_temperature` inside `tmmx` NetCDF files.

### Files Changed or Created
- `examples/fire_vase_pdf_panel_demo.py`
- `output/pdf/fire_vase_real_non_prescribed_tmmx_c_static_panel.pdf`
- `output/pdf/fire_vase_real_non_prescribed_tmmx_f_static_panel.pdf`
- `artifacts/fire-vase-gridmet-real/gridmet-cache/tmmx_2001.nc`
- `artifacts/fire-vase-gridmet-real/gridmet-cache/tmmx_2002.nc`
- `artifacts/fire-vase-gridmet-real/gridmet-cache/tmmx_2003.nc`
- `src/cubedynamics/fire_time_hull.py`

### Validation
- Generated the real panel with `env MPLCONFIGDIR=/private/tmp/mplconfig
  .venv/bin/python examples/fire_vase_pdf_panel_demo.py --temperature-units c
  --output output/pdf/fire_vase_real_non_prescribed_tmmx_c_static_panel.pdf`.
- Generated the Fahrenheit companion with the same command and
  `--temperature-units f`.
- Rendered both PDFs with `pdftoppm` and visually inspected the colorbars and
  ring-band coloring. Celsius range is about 5-35 C; Fahrenheit range is about
  40-100 F.
- Ran `.venv/bin/python -m py_compile examples/fire_vase_pdf_panel_demo.py
  src/cubedynamics/fire_time_hull.py`.
- Ran `.venv/bin/python -m pytest tests/test_fire_vase_panel.py
  tests/test_fire_hull_api.py -q` with 9 passing tests and 2 warnings.
- Follow-up render visually confirmed climate color now appears as horizontal
  date bands rather than diagonal triangle artifacts.

### 2026-07-21 Follow-up: Minimum Temperature and VPD Panels
- Downloaded cached real gridMET `tmmn_2001.nc`-`tmmn_2003.nc` and
  `vpd_2001.nc`-`vpd_2003.nc` into
  `artifacts/fire-vase-gridmet-real/gridmet-cache/`.
- Generated
  `output/pdf/fire_vase_real_non_prescribed_tmmn_c_static_panel.pdf` and
  `output/pdf/fire_vase_real_non_prescribed_vpd_static_panel.pdf`.
- Updated the static panel label helper so VPD colorbars are labeled
  `vpd (kPa)` from the real gridMET metadata.
- Rendered both PDFs with `pdftoppm` and visually inspected the first-page PNGs
  for readable colorbars and horizontal date-band coloring.
- Ran `.venv/bin/python -m py_compile examples/fire_vase_pdf_panel_demo.py`.

### 2026-07-21 Follow-up: Simple Wind-speed Panel
- Used gridMET `vs` as the simplest wind representation: daily mean scalar wind
  speed only, with no wind direction, gust, or vector decomposition.
- Downloaded cached real gridMET `vs_2001.nc`-`vs_2003.nc` into
  `artifacts/fire-vase-gridmet-real/gridmet-cache/`.
- Generated
  `output/pdf/fire_vase_real_non_prescribed_wind_speed_vs_static_panel.pdf`.
- Updated the static panel label helper so `vs` colorbars are labeled
  `wind speed (m/s)`.
- Rendered the PDF with `pdftoppm` and visually inspected the first-page PNG for
  readable labels and horizontal date-band coloring.

## 2026-07-21 — Fire VASE Observed-ending Exploratory Report

### User Goals
- Build a real-data exploratory PDF/HTML report and CSV table set for the
  cached non-prescribed FIRED candidate events.
- Treat "fire death" only as shorthand for observed cessation of detectable
  spatial growth, not physical extinction.
- Avoid synthetic data and avoid prescribed-vs-non-prescribed claims.

### Implementation Summary
- Added `examples/fire_vase_death_exploratory_report.py`, a reproducible
  report generator that reads cached FIRED daily/event GeoPackages, cached
  candidate IDs, and cached real gridMET `tmmx` NetCDF files.
- Wrote a fire-by-time analysis table with geometry, growth, centroid,
  nearest-grid-cell daily maximum temperature in Celsius, and explicit
  unavailable climate-support columns for newly burned/cumulative/boundary
  climate estimates.
- Wrote fire-level terminal features, summary statistics, data availability,
  and QC tables.
- Generated a 15-page PDF, embedded-figure HTML companion, and 10 figure PNGs
  under `outputs/fire_vase_figures/`.
- The report frames terminal observations cautiously because 24 of 25 cached
  candidate fires have sequence gaps near the observed ending and only 1 fire
  passes the primary QC rule.

### Files Changed or Created
- `examples/fire_vase_death_exploratory_report.py`
- `outputs/fire_vase_death_exploratory_report.pdf`
- `outputs/fire_vase_death_exploratory_report.html`
- `outputs/fire_vase_analysis_table.csv`
- `outputs/fire_vase_summary_table.csv`
- `outputs/fire_vase_terminal_features.csv`
- `outputs/fire_vase_quality_control.csv`
- `outputs/fire_vase_data_availability.csv`
- `outputs/fire_vase_figures/*.png`
- `outputs/README_fire_vase_death_report.md`
- `outputs/fire_vase_report_manifest.json`

### Validation
- Ran `MPLCONFIGDIR=/private/tmp/mplconfig .venv/bin/python
  examples/fire_vase_death_exploratory_report.py`; output manifest reports 25
  fires and 229 fire-time rows.
- Rendered the PDF with `pdftoppm` and visually inspected the intro, data
  availability, QC, VASE gallery, temperature trajectory, and conclusion pages
  for clipped text, overlap, and readable Celsius temperature scales.
- Ran `pdfinfo outputs/fire_vase_death_exploratory_report.pdf`; the final PDF
  has 15 landscape letter pages.
- Ran `.venv/bin/python -m py_compile
  examples/fire_vase_death_exploratory_report.py`.
- Ran `.venv/bin/python -m pytest tests/test_fire_vase_panel.py
  tests/test_fire_hull_api.py -q` with 9 passing tests and 2 warnings.

## 2026-07-17 — FIRED vs Classic Model Scaling Overlay

### User Goals
- Compare real FIRED fire-event scaling against classic model-output scaling.
- Show observed data aligning with the blue `2/3` line and classic non-level-set
  model outputs aligning with the red `1/2` line.
- Exclude the level-set / amplified-front model family for this plot.

### Implementation Summary
- Added `artifacts/fire-area-perimeter/make_real_vs_classic_model_scaling_plot.py`.
- Read observed FIRED events from the cached CONUS+AK GeoPackage, converted
  stored sinusoidal ignition coordinates back to lon/lat, and applied the CONUS
  bbox used by the existing reference plot.
- Read only `model_runs_other_models.csv` from the provided model handoff zip,
  leaving `model_runs_level_set.csv` out of the rendered data.
- Generated a white-background log-log hexbin overlay with cornflower-blue
  observed density and `P ∝ A^(2/3)` reference, and firebrick-red classic-model
  density and `P ∝ A^(1/2)` reference.
- Parameterized the plotting script with `--mode level-set` and generated a
  companion plot where the red layer is only the level-set / amplified-front
  model family and the red line is the level-set OLS fit.

### Files Changed or Created
- `artifacts/fire-area-perimeter/real-vs-classic-model-scaling.png`
- `artifacts/fire-area-perimeter/real-vs-classic-model-scaling.pdf`
- `artifacts/fire-area-perimeter/real_vs_classic_model_scaling_manifest.json`
- `artifacts/fire-area-perimeter/real-vs-level-set-model-scaling.png`
- `artifacts/fire-area-perimeter/real-vs-level-set-model-scaling.pdf`
- `artifacts/fire-area-perimeter/real_vs_level_set_model_scaling_manifest.json`
- `artifacts/fire-area-perimeter/make_real_vs_classic_model_scaling_plot.py`

### Validation
- Rendered the plot with `uv run --with matplotlib --with numpy python
  artifacts/fire-area-perimeter/make_real_vs_classic_model_scaling_plot.py`.
- Visually inspected the PNG for alignment, axis readability, and separation of
  observed versus classic-model density.
- Manifest confirms 237,235 observed CONUS events and 15,666 valid classic
  non-level-set model outputs; fitted slopes are 0.662 for observed data and
  0.506 for classic models.
- The level-set companion manifest confirms 7,920 level-set model outputs and a
  red fitted slope of 0.639.

## 2026-07-17 — Two-Panel Fire Geometry Animation

### User Goals
- Create a clean 1920x1080, 30 fps, 12-15 second scientific animation on a pure
  white background.
- Compare a smooth firebrick-red classic perimeter sliding across a flat plane
  with a cornflower-blue wrinkled dome whose ground-plane intersection creates
  a longer perimeter.
- Keep the two panels area-matched through time, with no text, labels, axes,
  particles, flames, smoke, terrain, people, logos, sound, camera motion, cuts,
  or transitions.

### Implementation Summary
- Added `artifacts/fire-area-perimeter/make_two_panel_geometry_animation.py`.
- Rendered deterministic geometry frame-by-frame with fixed isometric
  projection: the left panel uses a smooth low-frequency closed curve; the right
  panel uses a semi-transparent wrinkled dome and its projected ground
  intersection.
- Added subtle nested history rings based on the user's sketch, with current
  boundaries drawn thickest.
- Normalized red and blue footprints to the same target area at each frame while
  increasing the blue boundary wrinkle amplitude through time.

### Files Changed or Created
- `artifacts/fire-area-perimeter/two-panel-fire-geometry-animation.mp4`
- `artifacts/fire-area-perimeter/two-panel-fire-geometry-animation-final.png`
- `artifacts/fire-area-perimeter/two-panel-fire-geometry-animation-mid.png`
- `artifacts/fire-area-perimeter/two-panel-fire-geometry-animation-start.png`
- `artifacts/fire-area-perimeter/two_panel_fire_geometry_animation_manifest.json`
- `artifacts/fire-area-perimeter/make_two_panel_geometry_animation.py`

### Validation
- `python3 -m py_compile artifacts/fire-area-perimeter/make_two_panel_geometry_animation.py`
  passed.
- Rendered the MP4 with `uv run --with numpy --with pillow --with
  imageio-ffmpeg python artifacts/fire-area-perimeter/make_two_panel_geometry_animation.py`.
- Visually inspected the mid and final PNG frames.
- Manifest confirms 1920x1080, 30 fps, 360 frames, 12 seconds. Final red and
  blue areas match numerically while the blue perimeter is 1.71 times the red
  perimeter.

## 2026-07-17 — Spread/Growth Style-Matched Animation

### User Goals
- Use `/Users/tuff/Downloads/spread_vs_growth_with_metrics.mp4` as a style
  reference.
- Make the fire geometry animation match the reference style: flat white
  two-column layout, bold red/blue titles, formulas, pale filled footprints, and
  live area/perimeter metrics.

### Implementation Summary
- Added `artifacts/fire-area-perimeter/make_spread_growth_style_match_animation.py`.
- Rendered a 1920x1080, 30 fps, 12-second MP4 using deterministic area-matched
  red and blue boundaries.
- Matched the reference visual language with Arial typography, firebrick red
  and cornflower blue styling, pale fills, and large metric readouts.
- The blue boundary becomes increasingly wrinkled while preserving matched area
  with the smooth red boundary.

### Files Changed or Created
- `artifacts/fire-area-perimeter/spread-growth-style-match-animation.mp4`
- `artifacts/fire-area-perimeter/spread-growth-style-match-animation-final.png`
- `artifacts/fire-area-perimeter/spread-growth-style-match-animation-mid.png`
- `artifacts/fire-area-perimeter/spread_growth_style_match_animation_manifest.json`
- `artifacts/fire-area-perimeter/make_spread_growth_style_match_animation.py`

### Validation
- `python3 -m py_compile artifacts/fire-area-perimeter/make_spread_growth_style_match_animation.py`
  passed.
- Rendered with `uv run --with numpy --with pillow --with imageio-ffmpeg python
  artifacts/fire-area-perimeter/make_spread_growth_style_match_animation.py`.
- Visually inspected the middle and final frames against the reference styling.
- Manifest confirms final matched area of 1.20 and blue-to-red perimeter ratio
  of 1.59.
- Added an enhanced membrane version with stronger blue fill, internal
  oscillating ripple contours, and more pronounced blue boundary oscillation:
  `spread-growth-style-match-animation-membrane.mp4`. The enhanced final
  blue-to-red perimeter ratio is 1.75.
- Added a perspective storyboard version matching the user's later reference
  image: central metrics, perspective planes, red advancing line with arrows,
  translucent blue dome, blue footprint intersection, mini scaling plots, and a
  bottom takeaway panel. Output:
  `perspective-growth-explainer-animation.mp4`.
- Replaced the central `P / A^b` ratio numbers in the perspective explainer
  with directional indicators: horizontal arrows for stable ratios, up arrows
  for increasing ratios, and down arrows for decreasing ratios.

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

## 2026-07-10 — Synchrony Grammar Verbs

### User Goals
- Implement the PDF prompt requesting a reusable synchrony grammar for
  CubeDynamics: state cubes, event detection, occurrence/severity/timing/duration
  synchrony, spatial comparison modes, biological cube alignment, and
  climate-biology coupling.

### Implementation Summary
- Added state constructors that produce standard `state`, `magnitude`, and
  `threshold` Datasets from threshold, quantile, binary, or change rules.
- Added an event representation with `EventResult(dataset, catalog)` and
  contiguous-run event detection with duration, peak, mean, integral, sequence,
  and recurrence diagnostics.
- Added a shared spatial pair layer for reference, neighbor, all-pairs,
  regional, and block-oriented synchrony outputs.
- Added occurrence, severity, timing, and duration synchrony primitives with
  audit counts and match diagnostics.
- Added biological observation rasterization, cube alignment, relative/absolute
  change states, and same-pixel lagged occurrence coupling via `v.sync_with`.
- Kept `v.rolling_median_split_synchrony` public and behaviorally unchanged;
  the new docs now describe it as a center-reference convenience recipe.
- Added docs and examples for state cubes, four synchrony types, biological
  coupling, and the synchrony grammar concept.

### Files Changed or Created
- New runtime modules under `src/cubedynamics/synchrony/`,
  `src/cubedynamics/events/`, and `src/cubedynamics/biology/`.
- New verb wrappers in `src/cubedynamics/verbs/states.py`,
  `src/cubedynamics/verbs/events.py`, `src/cubedynamics/verbs/synchrony.py`,
  and `src/cubedynamics/verbs/biology.py`; exports added to
  `src/cubedynamics/verbs/__init__.py`.
- Added `tests/test_synchrony_grammar.py` and extended
  `tests/test_public_api_smoke.py`.
- Added docs pages under `docs/concepts/`, `docs/howto/`, and
  `docs/reference/`; linked them from `mkdocs.yml`,
  `docs/recipes/index.md`, and `docs/project/public_api.md`.
- Added `examples/four_synchrony_types.py` and
  `examples/climate_biology_sync_demo.py`.

### Validation
- Installed the project test extra into the existing `.venv` with
  `uv pip install --python .venv/bin/python '.[test]'` after sandbox approval.
- Focused pytest against the live source tree passed:
  `PYTHONPATH=src MPLCONFIGDIR=/private/tmp .venv/bin/python -m pytest tests/test_synchrony_grammar.py tests/test_public_api_smoke.py tests/test_median_split_synchrony_verb.py tests/test_tails.py -q`
  (`21 passed`, one upstream `planetary_computer` pydantic deprecation warning).
- Eager-compute guardrails passed:
  `PYTHONPATH=src MPLCONFIGDIR=/private/tmp .venv/bin/python -m pytest tests/test_no_eager_compute_or_io.py tests/test_no_eager_values_in_plotting.py -q`
  (`2 passed`, same upstream warning).
- New examples ran successfully with `PYTHONPATH=src`.
- `PYTHONPATH=src MPLCONFIGDIR=/private/tmp .venv/bin/mkdocs build --strict`
  passed; warnings were limited to the Material for MkDocs notice, pre-existing
  non-nav page notices, and new-file revision-date notices.
- Broader offline suite was interrupted after a matplotlib backend stall:
  `PYTHONPATH=src MPLCONFIGDIR=/private/tmp .venv/bin/python -m pytest -m 'not integration' -q`
  reached `248 passed, 3 skipped, 8 deselected` before interruption.

### Known Caveats / Follow-ups
- Timing and duration event detection currently materialize event arrays and
  catalogs; this is appropriate for the first reviewable phase but not yet a
  bounded streaming implementation.
- `v.sync_with` supports same-pixel lagged occurrence coupling first; cross-
  location coupling, richer null diagnostics, and complex event sequence verbs
  remain deferred.
- Neighbor outputs summarize incident edge metrics back to pixels; all-pairs
  outputs should be used when edge-level detail is required.

## 2026-07-10 — Synchrony Literature and Design Roadmap PDFs

### User Goals
- Incorporate the additional PDF context:
  `CubeDynamics_Synchrony_Literature_and_Codex_Roadmap.pdf` and
  `CubeDynamics_Synchrony_Design_Specification_v0.1.pdf`.

### Implementation Summary
- Added `docs/project/synchrony_roadmap.md` as a repo-native design roadmap for
  the synchrony framework.
- Linked the roadmap from `docs/concepts/synchrony_grammar.md` and `mkdocs.yml`.
- Captured the literature foundations, canonical data model, primitive
  operators, spatial modes, QA diagnostics, synthetic truth cases, phased
  development plan, and manuscript path from the PDFs.

### Validation
- `PYTHONPATH=src MPLCONFIGDIR=/private/tmp .venv/bin/mkdocs build --strict`
  passed; warnings were limited to the Material for MkDocs notice, pre-existing
  non-nav page notices, and new-file revision-date notices.
- `git diff --check` passed.

### Known Caveats / Follow-ups
- The PDFs recommend future public verbs such as `followed_by`, `recurrence`,
  and `lagged_response`. These were documented as deferred design space rather
  than exposed as stubs, to avoid creating public APIs before their statistical
  contracts are settled.

## 2026-07-10 — Dedicated Synchrony Website Section

### User Goals
- Reorganize the website so synchrony has a dedicated, user-friendly section
  with clean navigation, interactive cubes whenever possible, visible plots, and
  enough theory to keep the complex scientific framing coherent.

### Implementation Summary
- Added a top-level `Synchrony` section to `mkdocs.yml` with pages for overview,
  theory, state/event construction, four primitive operators, biology coupling,
  the center-pixel compatibility recipe, roadmap/validation, and verb reference.
- Added section pages under `docs/synchrony/` and a homepage card linking to the
  new section.
- Generated website assets with `examples/synchrony_section_assets.py`:
  interactive occurrence and severity cubes, a timing/duration cube panel,
  rolling metric comparison plot, matched-event diagnostic plot, and
  climate-biology lag curve.
- Added synchrony-specific docs styling for navigation cards, pills, and figure
  notes.
- Fixed `sync_with` lag semantics so positive lags mean the right-hand cube
  responds after the left-hand climate cube, then added a regression test.

### Files Changed or Created
- New docs pages under `docs/synchrony/`.
- New asset generator: `examples/synchrony_section_assets.py`.
- New generated docs assets under `docs/assets/figures/synchrony_*`.
- Updated `mkdocs.yml`, `docs/index.md`, `docs/recipes/index.md`, and
  `docs/stylesheets/extra.css`.
- Updated `src/cubedynamics/synchrony/coupling.py` and
  `tests/test_synchrony_grammar.py` for corrected positive-lag coupling
  semantics.

### Validation
- `PYTHONPATH=src MPLCONFIGDIR=/private/tmp .venv/bin/python examples/synchrony_section_assets.py --output-dir docs/assets/figures` passed.
- Visually inspected generated PNGs for metric comparison, event diagnostics,
  and coupling lag curve.
- `PYTHONPATH=src MPLCONFIGDIR=/private/tmp .venv/bin/python -m pytest tests/test_synchrony_grammar.py -q`
  passed (`6 passed`, one upstream `planetary_computer` pydantic deprecation
  warning).
- `PYTHONPATH=src MPLCONFIGDIR=/private/tmp .venv/bin/mkdocs build --strict`
  passed; warnings were limited to the Material for MkDocs notice, pre-existing
  non-nav page notices, and new-file revision-date notices.

### Known Caveats / Follow-ups
- The generated interactive cubes are synthetic offline examples. Real PRISM,
  gridMET, FIRED, or biological observation examples should be added as
  benchmark artifacts once the analysis contracts are stable.
- The timing/duration panel currently shows event-level outputs for one
  detected event result, while occurrence/severity examples show rolling-window
  cubes.

## 2026-07-13 — Ghosh-Style Tail Association Figure

### User Goals
- Add a reusable Matplotlib workflow for Ghosh-style copula/tail-association
  plots from two climate-synchrony series.
- Support normalized ranks, diagonal tail bands, lower/upper partial Spearman
  annotations, cube extraction helpers, synthetic demonstration data, and PNG
  plus PDF outputs.

### Implementation Summary
- Added `src/cubedynamics/plotting/tail_association.py` with normalized-rank
  helpers, Ghosh diagonal-band partial Spearman statistics, a one-row triptych,
  a multi-row grid plot, preprocessing modes, and a strict cube extraction
  helper.
- Re-exported the new plotting helpers from `cubedynamics.plotting`.
- Added `examples/ghosh_tail_association_demo.py`, which generates mirrored
  synthetic left-tail and right-tail dominant pairs and writes the demonstration
  figure to `docs/assets/figures/`.
- Added `docs/recipes/ghosh_tail_association.md` and linked it from the Recipes
  nav and overview.
- Generated `docs/assets/figures/ghosh_tail_association_climate_sync_demo.png`
  and `.pdf`.

### Validation
- `PYTHONPATH=src MPLCONFIGDIR=/private/tmp .venv/bin/python -m pytest
  tests/test_tail_association_plot.py tests/test_no_eager_values_in_plotting.py
  -q` passed (`7 passed`, one upstream `planetary_computer` pydantic
  deprecation warning).
- `PYTHONPATH=src MPLCONFIGDIR=/private/tmp .venv/bin/mkdocs build --strict`
  passed; warnings were limited to the Material for MkDocs notice, pre-existing
  non-nav page notices, and the new recipe page's revision-date fallback.
- Rendered the generated PDF with `pdftoppm` and visually checked the PNG and
  PDF render for legibility, spacing, and unclipped labels.

### Known Caveats / Follow-ups
- `event_binary` and `event_intensity` preprocessing modes are reserved names
  that raise a clear `NotImplementedError` until the event threshold contract is
  wired into the synchrony pipeline.
- The example uses deterministic synthetic data. Real climate-synchrony cube
  examples should replace or supplement it once representative cube outputs are
  available in the example environment.

## 2026-07-17 — Minimal Perspective Spread vs Growth Animation

### User Goals
- Simplify the perspective fire-growth explainer after the ratio arrows proved
  distracting.
- Keep the focus on the two growing geometries: classic smooth perimeter in
  firebrick and wrinkled dome footprint in cornflower blue.
- Retain only area and perimeter metrics; remove the lower scaling plots and
  ratio rows.

### Implementation Summary
- Updated
  `artifacts/fire-area-perimeter/make_perspective_growth_explainer_animation.py`
  to remove the title blocks, bottom mini-plots, conclusion box, outward arrows,
  and `P / A^b` ratio indicators.
- Enlarged and lowered the perspective planes and moved the central area and
  perimeter readout into the upper white space.
- Re-rendered
  `artifacts/fire-area-perimeter/perspective-growth-explainer-animation.mp4`,
  `perspective-growth-explainer-animation-final.png`,
  `perspective-growth-explainer-animation-mid.png`, and the manifest.

### Validation
- Rendered the MP4 with `uv run --with numpy --with pillow --with imageio-ffmpeg
  python artifacts/fire-area-perimeter/make_perspective_growth_explainer_animation.py`.
- Visually inspected the midpoint and final poster frames for overlap, focus,
  and color consistency.

### 2026-07-17 Follow-up
- Increased the blue dome opacity while keeping it semi-transparent.
- Added firebrick arrows constrained to the ground plane and cornflower-blue
  arrows with outward/upward components from the dome surface.
- Re-rendered and visually inspected the midpoint and final poster frames.

## 2026-07-17 — Corrected Level-Set Scaling Reference Line

### User Goals
- Fix the red guide line in the real-vs-level-set scaling plot; it was using
  the fitted level-set slope and appeared nearly parallel to the blue 2/3 line.
- Show the red guide as an explicit 1/2-scaling reference instead.

### Implementation Summary
- Updated `artifacts/fire-area-perimeter/make_real_vs_classic_model_scaling_plot.py`
  so `--mode level-set` uses `model_line_slope = 0.5` and labels the red line
  as `P ∝ A^1/2`.
- Re-rendered `artifacts/fire-area-perimeter/real-vs-level-set-model-scaling.png`
  and `.pdf`.
- Kept the fitted level-set slope in the manifest for provenance, but no longer
  uses it for the displayed red reference line.

### Validation
- Ran `uv run --with numpy --with matplotlib python
  artifacts/fire-area-perimeter/make_real_vs_classic_model_scaling_plot.py --mode
  level-set`.
- Visually inspected the updated PNG and confirmed the manifest reports the red
  reference-line slope as `0.5`.

## 2026-07-17 — Data-Only Fire Log-Log Plot

### User Goals
- Regenerate the log(area) vs log(perimeter) FIRED hexbin plot without the green,
  red, or blue scaling lines so the data cloud is the focus.

### Implementation Summary
- Added `artifacts/fire-area-perimeter/make_fire_log_log_data_only_plot.py`.
- Reused the same FIRED CONUS+Alaska cache, log-coordinate axes, magma hexbin
  density, colorbar, and largest-fire data callouts from the 3/4-line plot.
- Removed the `A^3/4`, `A^2/3`, `A^1/2`, OLS fit overlays, and line legend.
- Wrote `artifacts/fire-area-perimeter/fire-log-log-data-only.png`, `.pdf`, and
  `fire_log_log_data_only_manifest.json`.

### Validation
- Ran `uv run --with numpy --with matplotlib python
  artifacts/fire-area-perimeter/make_fire_log_log_data_only_plot.py`.
- Visually inspected the PNG to confirm the colored reference lines and line
  legend were removed.
