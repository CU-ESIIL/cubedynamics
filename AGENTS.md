# AGENTS.md — CubeDynamics Repository Operating Guide

This guide describes the current checkout, not a guarantee that every feature
is in the installed PyPI release. Last synchronized: **2026-08-27**.

## 1) Project identity and scope

- Package: `cubedynamics`, formerly `climate_cube_math`. Version sources are
  `pyproject.toml` and `src/cubedynamics/version.py`; both currently say `0.1.0`.
  Packaging declares alpha status and Python `>=3.9`.
- Core: `pipe(cube) | verb() | verb()`, a small composable grammar over labeled
  spatiotemporal objects. xarray/NumPy provide array semantics; Dask supports
  deferred computation; adapters and renderers connect to the grammar.
- Synchrony, biology, tubes, and Fire VASE are project/domain vocabularies
  shipping in the same distribution for compatibility, not competing cores.
- Preserve public imports and warn-first compatibility unless removal is
  explicitly requested. Never infer implementation from an exported name alone.

Start with `README.md`, `src/cubedynamics/piping.py`,
`docs/project/public_api.md`, and `PROMPT_LOG.md`. The log records recent
decisions, validation scope, and outstanding issues; drafts are not API truth.

## 2) Source-of-truth map

| Location | Ownership |
| --- | --- |
| `src/cubedynamics/` | Installed runtime (`package-dir = "src"`) |
| `src/climate_cube_math/` | Legacy import compatibility |
| `code/cubedynamics/` | Legacy/doc mirror; never assume it drives runtime |
| `tests/`, `src/cubedynamics/tests/` | Regression and contract tests |
| `tests/fixtures/real_data/` | Small real observational NetCDF extracts and provenance JSON |
| `docs/`, `mkdocs.yml`, `docs/overrides/` | Website content, navigation, theme overrides |
| `scripts/` | Reference/notebook generators, validation and source QA tools |
| `examples/custom_verb_project/` | Project-owned verb scaffold |
| `paper/` | Software manuscript drafts, bibliography, and supplied citation-map PDF |
| `docs/manuscripts/` | Separate scientific manuscript/audit material |
| `config/`, `schemas/`, `manifests/releases/` | Storage policy/templates, schemas, release records |
| `artifacts/`, `scratch/`, `local-data/`, `lakehouse/` | Ignored generated evidence and data, not package inputs |

Existing tracked legacy outputs are not authorization to add new bulk products
or delete historical evidence. Check `config/repository_policy.yml` and
`docs/project/publication_plan.md` before relocating data. Preserve unrelated
working-tree changes.

## 3) Public API and callable boundaries

- Preferred imports: `from cubedynamics import data, pipe, verbs as v`.
- Core pipe classes/functions: `cubedynamics.piping.Pipe`, `pipe`, and the
  callable/factory protocol. Plain callables can compose without registration.
- `cubedynamics.grammar` holds semantic states, contracts, order rules, and
  report types. `Pipe.explain()`, `suggest()`, `validate()`, `semantic_state`,
  and `semantic_trace` must remain metadata-only and must not rewrite workflows.
- `cubedynamics.data` exposes scientific nouns, discovery, provider loaders,
  schema/QA helpers, serving-history and certification interfaces.
- Top-level provider and streaming convenience exports remain compatible;
  `cubedynamics.variables` contains older variable shortcuts. Prefer `data.*`
  noun loaders in new user-facing examples.
- Treat `ops*`, `streaming*`, `ops_fire*`, `ops_io*`, `plotting*`, `viewers*`,
  `utils*`, and `config` as internal unless a specific documented API is exposed.
  A public re-export does not make its entire implementation module stable.

The verb namespace includes different calling conventions:

- Factory stages such as `v.mean(...)` and `v.plot(...)` compose with `|`.
- Direct helpers such as `v.rasterize_observations(...)`, `v.vase_mask(...)`,
  and `v.fire_plot(...)` consume their documented arguments immediately.
  Do not present them all as factories.
- `v.correlation_cube` and `v.fit_model` are reserved/unimplemented names.
  Other correlation helpers have separate contracts; do not conflate them.
- `aoi_signature`, `compare_aoi_signature`, `exceedance`, and `vase_demo` have
  compatibility guidance. An alias is not necessarily deprecated.
- `v.month_filter` is supported and implemented in `verbs/stats.py`. Legacy
  `ops.transforms.month_filter` (also re-exported through `ops` and the old
  top-level shortcut) warns and forwards to it; do not wire the public verb
  back through the deprecated shim.

Inspect implementations and `scripts/reference_classification.py`; consult the
generated conceptual browser and secondary A–Z inventory under
`docs/reference/verbs/`. Historical prose can lag code: resolve discrepancies
with tests and explicit notes, not invented behavior.

## 4) Pipe, cube, and laziness invariants

- `pipe(value)` wraps the value. `Pipe.__or__` invokes each stage during
  composition and records a semantic trace. Laziness comes from the operation
  and underlying Dask/VirtualCube object, not from postponing Python calls.
- `unwrap()` returns the wrapped value; it does not force computation.
- Preserve pass-through plotting/output behavior and viewer attachments.
  Plotting or explicit output can materialize data; never promise every helper
  is lazy simply because its input has Dask chunks.
- Canonical dimensions in `src/cubedynamics/config.py`: `time`, `y`, `x`, and
  optional `band`. Provider-level adapters may expose native dimension names;
  inspect contracts before assuming normalization.
- Follow `docs/design/spatial_dataset_contract.md`: reliable spatial-dimension
  inference, CRS precedence, boundary-inclusive geometry, and explicit failure
  on ambiguous dimensions or CRS. Never silently guess or reverse coordinates.
- Keep core transformations free of unnecessary `.compute()`, `.values`, or
  disk writes. Preserve deferred VirtualCube work until explicit materialization
  or a documented consuming operation.
- Prefer bounded streaming/batching for long records over huge Dask graphs.
  Examples may checkpoint outputs when users explicitly run that workflow.

## 5) Data catalog, serving, and scientific provenance

Runtime ownership:

- `src/cubedynamics/data/catalog.py`: implemented noun/source metadata;
  `src/cubedynamics/data/nouns.py`: selection, normalization, and provenance.
- `src/cubedynamics/data/gridmet.py`, `src/cubedynamics/data/prism.py`, and
  `src/cubedynamics/data/sentinel2.py`: provider loaders. Underlying adapters
  live in `src/cubedynamics/streaming/` and `src/cubedynamics/prism_streaming.py`.
- Under `src/cubedynamics/data/`, `lifecycle.py`, `revisions.py`,
  `serving_history.json`, `schema.py`, `qa.py`, and `certification.py` own
  lifecycle, schema fingerprints, QA profiles, revision and certification checks.

Use `data.list_sources()`, `data.sources()`, and `data.describe()` to discover
current support. Catalog nouns currently comprise `temperature`,
`precipitation`, `vpd`, `wind`, `humidity`, `radiation`,
`surface_reflectance`, and `vegetation_index`. Sources are gridMET, PRISM,
and Sentinel-2; Landsat/FIRED helpers are separate integrations. Planned nouns
must not appear implemented before their loader, contracts, tests, and QA exist.

Scientific and access constraints:

- Noun loaders reject synthetic fallback. Lower-level PRISM/gridMET loaders
  retain an explicit `allow_synthetic=True` test/demo escape hatch with provenance;
  never enable it for science or publication examples.
- Sharing a noun does not harmonize units, statistics, grids, masks, or revisions.
  gridMET temperature is kelvin with maximum/minimum; PRISM is Celsius and also
  supports mean. Sentinel-2 band scaling/quality must be inspected separately.
- Source selection, provider/product, variable, query, CRS, retrieval details,
  source mode, serving revision, and schema provenance must remain inspectable.
  Revision scientific validity and live endpoint health are independent.
- PRISM and gridMET are CONUS products. `stream_global_climate_cube` accepts an
  already-open xarray object; it does not acquire or certify global datasets.
- PRISM uses NCSCO THREDDS NcSS daily AOI requests (`freq="D"`), with narrow
  historical OPeNDAP fallback/normalization logic. Retain catalog-alias, daily
  laziness, and coordinate/grid regression tests. Initial discovery can access
  metadata/data; Dask backing is not a guarantee of zero network work at load.
- gridMET attempts bounded OPeNDAP when `netCDF4` or `pydap` is available;
  otherwise the HTTPS path retrieves annual files. Keep the common
  `_open_gridmet_year` seam and legacy override signatures in
  `src/cubedynamics/streaming/gridmet.py`; tests must not change meaning when
  optional engines are installed. Annual retrieval is not chunk-level access.

New source work requires catalog/loader alignment, schema and QA checks,
provenance/revision records, generated references, and tests. Live checks use
`scripts/run_live_source_certification.py`; missing credentials or unavailable
services should yield honest blocked/failure evidence, not substitute data.

## 6) Real-data examples and fixture policy

- Supported notebooks are metadata-marked under `docs/vignettes/` (eight core
  lessons) and `docs/decision_vignettes/` (Working Lands). Exploratory
  `notebooks/` files are not automatically supported publication lessons.
- Inputs live in `tests/fixtures/real_data/`, with sibling provenance JSON and
  checksums: PRISM Boulder and Working Lands, gridMET Badlands, Sentinel-2
  Badlands. See that directory's README for exact scope.
- These small NetCDF files are intentional policy-approved exceptions. Do not
  move them to ignored output locations or remove them to satisfy size checks:
  fresh-clone validation and notebooks depend on them.
- A missing or mismatched fixture is an error. Do not silently download a new
  dataset, rewrite expected checksums, skip the test, or invent measurements.
  Rebuilding source fixtures is a deliberate online acquisition/review task.
- Scientific examples use real data and disclose source, units, dates,
  transformations, and limitations. Small synthetic inputs remain appropriate
  for deterministic unit tests and explicitly labeled negative controls only.
- Notebook builders are `scripts/build_vignette_notebooks.py` and
  `scripts/build_decision_vignettes.py`; `scripts/vignette_shell.py` owns shared
  narrative/reproducibility sections. Update builders instead of losing edits
  on regeneration. The runner enforces required static PNG/SVG output counts
  and uses an inline backend without modifying notebook sources.

## 7) Website and generated documentation ownership

Keep the five top-level jobs distinct: **Home / Learn / Library / Documents /
Vignettes**. User reference comes first in Documents; Developer documentation
holds internal contracts, implementation, CI, plans, and audits. Preserve useful
old URLs. Do not add tabs or redesign navigation as a side effect of API work.

- `scripts/build_reference_docs.py` generates noun/source pages and public
  callable pages/indexes from catalog facts, signatures, docstrings, and grammar
  metadata. Never hand-edit files bearing its generated marker.
- `scripts/reference_classification.py` owns a small purpose/type/compatibility
  map plus implementation inspection. Keep implemented operations separate
  from compatibility/deprecated names and reserved placeholders; retain A–Z.
- `scripts/docs_examples.py` supplies reviewed examples and explicit limitations.
  Do not duplicate full argument or scientific source metadata by hand.
- `scripts/visual_examples.py` owns shared executable visual examples, captions,
  and prerequisites. `scripts/build_visual_docs.py` generates/checks the small
  real-data figure cache in `docs/assets/generated/visual/`; regenerate it after
  runtime/example changes, then regenerate references. See
  `docs/dev/visual_documentation.md` for the six-page first-pass boundary.
- `scripts/docs_hooks.py` derives reference navigation and rewrites notebook
  links. Library categories follow generated entries; multi-source noun pages
  explain differences without asserting scientific equivalence.
- `docs/overrides/` contains theme overrides, not published content. The
  homepage viewer is deferred; preserve accessible fallback links and loading.
- Keep noun → verb → Learn/vignette cross-links. Verify links after notebook
  rendering, not just source Markdown. Do not replace missing figures with
  empty/text files wearing image extensions.
- `paper/` drafts and their citation markers are editorial material, not
  evidence of implemented APIs, reviewed claims, or completed citations.
  Preserve supplied originals and keep scientific manuscript work separate.

## 8) Environment and validation commands

Use Python 3.11 for local development (`.python-version`). Install with
`python -m pip install -e ".[dev]"` or `make install`. The `browser` extra is
separate from `dev` and requires Python 3.10+. Core CI tests Python 3.9–3.12.

Markers in `pytest.ini`: `integration`, `online`, `streaming`, `download`, and
`browser` (also integration). **`not integration` alone is not an offline filter.**

Core/targeted checks:

```bash
python -m pytest -m "not integration and not online" --maxfail=1 --disable-warnings -q
python -m pytest tests/test_public_api_smoke.py tests/test_piping_verbs.py tests/test_plot_verb.py -q
```

`make test` uses the offline filter. `make test-streaming` and `make test-fire`
hold focused contract suites; inspect their lists when modifying those areas.
Unfiltered `pytest` can require a built site, browsers, and remote services.

Publication and source evidence (no live provider requests):

```bash
python scripts/run_vignettes.py
python scripts/run_validation.py --run-vignettes
python scripts/run_source_qa.py
python scripts/run_decision_qa.py
```

The validation command already reruns vignettes with that flag; standalone
execution is useful when only notebooks changed. Evidence goes under
`artifacts/validation/`, `artifacts/source_qa/`, and `artifacts/decision_qa/`.
Do not call a fixture pass a live certification or broader scientific review.

Documentation checks:

```bash
python scripts/build_reference_docs.py --check
python -m pytest tests/test_documentation_reference.py tests/test_reference_usability.py tests/test_documentation_links.py tests/test_repository_guides.py -q
python -m mkdocs build --strict
python scripts/check_site_links.py site
```

If references are stale after an intentional API/catalog change, run
`python scripts/build_reference_docs.py`, review the diff, then repeat `--check`.
Use `python -m mkdocs serve` for local preview. Browser checks after site edits:

```bash
python -m pip install -e ".[browser]"
python -m playwright install chromium
python -m pytest tests/browser -m browser --site-dir site --browser chromium \
  --tracing retain-on-failure --output artifacts/browser/playwright -q
python scripts/check_external_links.py site --crawl-report artifacts/browser/crawl.json
```

On Linux CI, install with `python -m playwright install --with-deps chromium`.
The browser suite checks all built HTML pages, links/anchors, decoded images
and CSS backgrounds, deferred frames, console/resource errors, responsive
journeys, cube drag/zoom, and deliberate detector failures. It is not a visual
proof of every scientific figure or coverage of all browser engines.

`.github/workflows/tests.yml` covers offline, streaming, package, and docs QA;
`pages.yml` gates publication on build/link/browser checks. External-link
availability is advisory. `online-tests.yml` handles separate remote checks
and live-source evidence. Consult workflow files before claiming CI coverage.
Use `not browser` when selecting integration tests without installing/running
the website suite.

Repository checks:

```bash
python scripts/check_repository_size.py --mode tracked
git diff --check
```

The size guard checks Git-tracked (or `--mode staged`) paths. Include new
untracked files in your review; a tracked-only pass cannot validate them.

## 9) Safe implementation playbooks

### Add or modify an operation

1. Decide whether it belongs in shared vocabulary or a project-owned extension.
2. Implement its narrow input/output, units, dimension, and laziness contract.
3. Preserve direct/factory conventions, pass-through semantics, and compatibility.
4. Export intended public names and update grammar metadata where relevant.
5. Test direct and piped use, meaningful failure cases, and lazy behavior.
6. Regenerate references, review callable classification and examples, and run
   targeted plus offline checks. Preserve any `code/` guardrail tests affected.

### Modify spatial or fire workflows

Follow the Spatial & CRS contract. Preserve reprojection and boundary semantics;
run spatial, fire/hull, and relevant streaming tests. Keep separate concerns:
(1) event/cube data construction, (2) geometry, (3) scene/adapters, (4) rendering.

### Modify visualization

Read `docs/dev/cube_viewer_invariants.md` and `docs/dev/viewer_backend.md` first.
Use `tools/debug_viewer_pipeline.py` and viewer/plotting tests for diagnosis.

- `v.plot()` is the canonical custom HTML/CSS/JavaScript cube viewer.
  `v.fire_plot()` still uses Plotly for its primary interactive hull output;
  do not claim full migration or silently switch renderers.
- Cube-attached faces, axes, and labels stay under the cube transform node.
  Preserve the documented front/newest time convention and camera semantics.
- Coordinate/axis changes require aligned invariants, runtime, and regression
  tests; screenshots or documentation alone are not a fix.
- Prefer `FireEventDaily` and `FireHull`; preserve `TimeHull` compatibility.
  Keep geometry generation separate from climate/event fusion and rendering.
- Prefer a narrow documented adapter over duplicated geometry logic. Incomplete
  hull-to-cube or attribution support must be disclosed, not hidden in plotting.
- Run viewer-related pytest tests and the built-site browser suite for website
  embeds. Manually inspect affected views at desktop and narrow widths too.

## 10) Data hygiene, records, and release boundaries

- Keep large Parquet/GeoParquet, Zarr, NetCDF, GLB, TIFF, bulk renderings, and
  runtime manifests outside Git. Use `config/storage.example.yml` and explicit
  output roots; never commit local credentials or `config/storage.yml`.
- Policy-approved real fixtures, small documented docs assets, and release
  records are deliberate exceptions. Never broaden an allowlist to hide a
  data-placement error. Do not remove historical artifacts without an explicit
  archival/migration decision.
- Keep `PROMPT_LOG.md` current for substantial work: dated goal, decisions,
  changed files/artifacts, exact validation, and concrete caveats. No secrets,
  unrelated transcript, or unsupported certification claims.
- Keep README, generators, navigation, examples, and actual exports consistent.
  `tests/test_repository_guides.py` checks the README catalog/version/examples
  and local guide links against the checkout.
- `publish.yml` can publish on `v*` tags or manual dispatch. Publishing, pushing,
  release metadata/DOI changes, and manuscript submission require their own
  requested scope; a documentation update does not authorize them.
- When uncertain, prefer minimal composable changes and a focused regression
  over silently expanding scope. Determine the source of a discrepancy before
  changing an API, checksum, scientific assumption, or expected test result.
