# Prompt Log

This log records substantial user goals, decisions, outputs, and validation for
CubeDynamics development sessions. Keep entries concise and factual. Do not add
secrets, credentials, private tokens, or unrelated transcript text.

## 2026-09-02 — Reusable release workflow and 0.1.0rc2 preparation

- Prepare `0.1.0rc2` from reviewed main `54e469d6f8c62609a7d111161e82da2c674bad54`
  without changing scientific behavior, tagging, publishing, creating a GitHub
  release, or pushing. Preserve RC1 reports and manifests as historical facts.
- Make the release identity derive from the committed project version and an
  exact `v*` tag, with explicit rejection of dirty sources, branch publication,
  tag/package mismatch, artifact-name mismatch, manifest mismatch, and changed
  bytes. The package version must be committed before tagging; no workflow may
  rewrite it from the tag.
- Keep tag pushes verification-only. A separately authorized dispatch may
  publish to GitHub or PyPI only after rerunning the full gate and Python matrix
  for the selected tag and carrying the exact same-run wheel, sdist, checksum,
  and manifest bundle into the publication job. PyPI continues to use Trusted
  Publisher OIDC and immutable releases; no token or password is introduced.
- Generalize active gate outputs, distribution filenames, candidate manifests,
  prerelease detection, and maintainer documentation so later RC and stable
  versions require a version edit and tag, not YAML surgery.
- A Python 3.9 matrix run exposed older-xarray handling of exact Dask quantiles.
  Keep `quantile_state` lazy while making its exact reduction explicit: gather
  the selected time axis into one chunk, preserve all spatial chunks, document
  the memory boundary, and cover the supported-version behavior directly.
- Post-fix validation: 24 long-record tests passed under both the normal Python
  3.11 environment and the locked Python 3.9 dependency set. The complete
  offline suite passed 895 tests with 5 skips on Python 3.11 and 894 tests with
  10 skips on Python 3.9. Eight visual results and 78 generated references pass
  freshness checks; tracked-size and diff checks pass. The earlier local full
  gate passed before this compatibility fix and is therefore superseded; run a
  fresh non-publishing gate on the final unchanged snapshot before tagging.

## 2026-09-01 — Long-record event grammar and notebook identity hardening

- Treat the new two-year and proposed twenty-year notebook findings as evidence
  to reproduce against current `main`, not as proof that an older imported
  `0.1.0rc1` wheel still describes the checkout. Classify every finding before
  changing runtime behavior and preserve the completed RC1 and temporal-support
  work.
- Make notebook runtime identity inspectable without bumping the release
  version or recommending dependency-breaking `--ignore-installed` installs.
  Make local-cell event instances unambiguous, add an explicit and
  user-controlled transition to regional episodes, and provide a bounded event
  metrics vocabulary without turning the package into a general reporting
  system.
- Correct confirmed metadata defects in block-signature explanations and
  mixed-unit block comparison outputs. Clarify pooled multi-year quantiles,
  positive/negative lag direction, rolling median-split outputs, and the valid
  interpretation of the legacy rolling tail-variance contrast.
- Add deterministic long-record, Dask-laziness, event-consolidation, unit,
  runtime-provenance, and documentation regressions. Document trajectories,
  trend, change-point, event classification, and specialized plotting as
  deliberate grammar gaps when a scientifically defensible bounded API is not
  implemented in this pass.
- Do not publish, tag, push, silently harmonize sources, or weaken spatial,
  temporal-support, xarray, or condition-state contracts.
- Implemented public `version_info()`, explicit local-cell and regional-episode
  event scopes, `v.consolidate_events(...)`, and `v.event_metrics(...)`.
  Consolidation uses user-declared temporal and spatial connectivity; event
  metrics retain the source scope. Fixed seasonal-gap event contiguity,
  metric-specific comparison units, quantile reference-population metadata,
  lag direction metadata, and rolling synchrony/tail interpretation. Event
  life-history alignment, period signatures, trends, change points,
  classification, and specialized event plots remain documented design work.
- Added runtime identity to every supported vignette, safe dedicated-kernel
  installation guidance, local-versus-regional event teaching material, a
  long-record conceptual page, generated verb references, and a classified
  triage record. The live multi-year gridMET check was not run locally because
  no OPeNDAP engine was installed; the available fallback would retrieve whole
  annual files and was not a bounded check. No substitute data were used.
- Pre-snapshot validation: 45 focused temporal/long-record tests passed; the
  complete offline suite passed 881 tests with 5 skips; all 12 supported
  vignettes executed with required figures; five publication modules, source
  QA, and decision QA passed; 78 references, eight visual results, seven noun
  figures, and source notebooks passed freshness checks; strict MkDocs,
  built-site links, 387 Chromium tests, tracked-size policy, and diff checks
  passed. A clean installed-wheel/full release gate is run separately against
  the unchanged prepared snapshot; no publication action is authorized here.

## 2026-09-01 — Make temporal alignment scientifically explicit

- Treat coordinate-label equality, observation temporal-support equality, and
  event-time alignment as three distinct scientific questions. Preserve exact
  coordinate/spatial guardrails and never silently shift, resample,
  interpolate, aggregate, or truncate observations.
- Audit authoritative PRISM and gridMET documentation before assigning source
  conventions; represent verified interval/instant/unknown support as
  source-qualified metadata, propagate it through semantic state, and surface
  cross-source matches, mismatches, and unknowns through `explain()` and
  `validate()`.
- Add explicit label-versus-exact-support alignment choices, maintain xarray
  interoperability and Dask laziness, clarify event/lag semantics, and prove
  the scientific consequence with deterministic offset-window temperature and
  precipitation regressions plus a concise real-data teaching example.
- Do not publish, tag, loosen spatial alignment, infer unverified source
  timing, or attribute all PRISM/gridMET product differences to temporal
  support.
- Implemented `TemporalSupport` and `TemporalAlignmentReport`, public metadata
  inspection and one-dimensional interval derivation, temporal fields in
  `SemanticState`, `v.align_time(mode="labels"|"require_exact_support")`, and
  support-aware `v.overlap`. Known mismatches require an explicit choice;
  unknown support remains a distinct `CHECK`; no policy changes coordinates or
  values. Event and lag outputs now state whether they compare observation
  labels, event anchors, or coordinate-period shifts.
- Verified the source rules from provider documentation: PRISM days span
  12:00–12:00 UTC and use the ending date; gridMET nominal days span
  midnight-to-midnight MST (07:00 UTC). The catalog stores offsets relative to
  each adapter's midnight UTC date coordinate. A bounded live South Dakota
  check (2024-07-01 through 2024-07-31) returned 31 exact labels for PRISM and
  gridMET temperature and precipitation, distinct source identities, different
  declared supports, separate native grids, and lazy arrays. This does not
  attribute numerical product differences solely to timing.
- Added the focused Temporal alignment guide, generated noun/source/verb
  references, and an opt-in live showcase notebook. The website does not
  execute that online notebook during its offline build; readers can run it to
  request the documented real observations. Added deterministic offset-window
  regressions proving changed daily maxima, precipitation dates, threshold
  labels, and event starts from one hourly signal.
- Validation: 117 focused grammar/noun/overlap/synchrony/plot/temporal tests
  passed; the full offline suite passed 854 tests with 5 skips; 32 streaming
  contracts passed; all 12 supported notebooks passed both checkout and exact
  wheel execution; publication validation passed five modules; source and
  decision QA passed; 76 references and eight visual results passed freshness
  checks; strict MkDocs, built-site links, 380 Chromium checks, repository size,
  and diff checks passed. The complete clean temporary-snapshot non-publishing
  gate passed all 35 steps. The direct checkout gate correctly refused the
  uncommitted working tree. No tag, push, upload, or release was performed.

## 2026-09-01 — Naive outside-user first-use acceptance follow-up

- Continued the existing RC1 hardening pass using the independent
  `CU-ESIIL/cubedynamics_test_user` naive-user report as first-use evidence;
  retained the completed semantic, plotting, overlap, Fire, and release-gate
  work as the broad-functional acceptance baseline.
- New P0 blockers to reproduce and resolve: a clean `python:3.11-slim`
  Debian/aarch64 installed-wheel import reaching Rasterio through an eager
  data/Sentinel-2/Cubo import and failing on `libexpat.so.1`; ordinary NetCDF
  export rejecting Boolean CubeDynamics metadata; and a first-discovered PRISM
  example/default selecting monthly semantics while real streaming supports
  daily requests.
- Required outcome: identify causes rather than document workarounds, keep
  optional compiled integrations from blocking the core grammar where
  practical, adopt deterministic NetCDF-safe metadata, make the first PRISM
  path copy-and-run, classify current versus legacy public pages, and add a
  separate installed-wheel first-use gate alongside the existing broad gate.
- Do not publish, tag, push, invent live-source evidence, or treat the bounded
  naive report as exhaustive functional coverage.
- Root cause and fix: core import eagerly reached Cubo -> Rasterio -> Rasterio's
  bundled GDAL, whose aarch64 1.4.4 wheel retained an unresolved
  `libexpat.so.1` dependency on Debian 13. Sentinel/Cubo import is now deferred;
  the exact `python:3.11-slim` arm64 image imports the rebuilt wheel and passes
  the public first-use smoke. Xarray still warns while discovering the broken
  optional Rasterio backend, and Sentinel use on that host remains unsupported.
- Added deterministic NetCDF-safe metadata serialization, Boolean state-file
  encoding without in-memory mutation, daily-only modern PRISM defaults and
  validation, a bounded online PRISM first-use script, an installed-wheel
  acceptance script, clean Debian-slim x86_64/aarch64 CI, and a public
  documentation age/generation audit. Regenerated the output reference,
  visual lesson, and grammar notebook from their owning builders.
- Validation: 831 offline tests passed with 5 skips; 32 streaming contracts
  passed; all 12 supported vignettes executed with required plots; aggregate
  publication validation passed five modules; source and decision QA passed;
  75 references, 8 visual results, noun/source notebooks, source-project
  evidence and 14 homepage examples passed freshness checks; strict MkDocs and
  built-site links passed; the built wheel passed Twine, `pip check`, release
  identity, first-use, and checksum-pinned external quickstart checks. The full
  Chromium run passed 373 checks and exposed four stale wording assertions;
  all 12 affected desktop/mobile journeys passed after correction.
- The monolithic release gate correctly refused to mint hash-bound evidence
  from a dirty, uncommitted checkout. It was not bypassed, and the next
  candidate remains blocked on a reviewed commit plus the configured CI matrix.

## 2026-08-31 — Comprehensive RC1 validation triage and next-RC gate

- Read the supplied 12-page `cubedynamics_codex_rc1_triage_fix_prompt.pdf` and
  reproduced its semantic, plotting, alignment, optional-dependency, and fire
  findings against the current checkout before changing runtime code.
- Wrote the required one-category-per-finding maintainer classification in
  `docs/project/rc1_validation_triage.md`. Genuine defects are condition
  auxiliary-field reduction, variance units, semantic/dimensional plotting,
  canonical overlap representation, alignment diagnostics, and the tested
  release's fire routing. Random invalid chains, missing optional Lexcube, and
  non-overlapping fire/climate dates are not grounds to loosen scientific
  guardrails.
- Decisions: conditions are Datasets with `state`; threshold conditions may
  add meaningful threshold/magnitude fields, overlap must not invent them;
  condition means expose only the state proportion; summaries remain
  thresholdable because the maintained order lesson teaches that path; and the
  preferred fire object route is `FireEventDaily -> FireHull -> environment ->
  plot`, with cube-first `v.fire_plot` as the high-level convenience API.
- Do not publish, tag, push, or describe offline fixture checks as live source
  certification. Record exact gates and remaining caveats after implementation.
- Implemented state-only overlap, state-only condition-frequency reduction,
  deterministic variance units, anomaly/z-score result metadata, dimensional
  plotting for canonical semantic objects, accurate alignment diagnostics,
  optional Lexcube guidance, modern cube-first Fire routing, geometry-only
  FireHull inspection, and overlapping six-variable environmental attribution.
- Added a maintained black-box smoke covering the requested semantic and Fire
  sequences and wired it into the non-publishing release gate. Updated the gate
  checker so numerical xarray parity is tested alongside (not instead of)
  truthful CubeDynamics result metadata.
- Verified through PyPI's official JSON API that `0.1.0rc1` is public; corrected
  the maintained install, quickstart, release-note, and release-process pages.
  The checkout remains versioned rc1 during this engineering pass. A reviewed
  next-candidate version bump is still a release-management action, and no
  package upload, tag, push, or release creation is authorized here.

## 2026-08-31 — Align summary, condition, overlap, and plotting semantics

- Outside-user PyPI/Jupyter validation of `0.1.0rc1` found four connected
  release-candidate issues: `threshold_state` cannot currently consume a
  summary even though the published order lesson teaches that scientifically
  distinct path; reducing a condition produces numerically valid output but
  leaves condition metadata on the xarray value; `overlap` returns a bare
  boolean DataArray rather than the standard state Dataset; and `v.plot()`
  cannot directly select the renderable state variable from semantic Datasets.
- Scope is deliberately narrow: preserve authored order and exact-alignment
  enforcement, make reductions describe summaries in both runtime attrs and
  the semantic trace, keep summary-to-threshold distinct from
  threshold-to-summary, normalize overlap to the existing
  `state`/`magnitude`/`threshold` contract, and give plotting an explicit,
  deterministic Dataset-variable selection rule. Do not broaden unrelated
  verbs or silently harmonize scientific operands.
- Implemented both mean/threshold order paths with machine-readable
  `ORDER_CHANGES_MEANING` notes. Condition means now expose summary metadata
  and a unitless proportion on `state`; `overlap` returns the standard
  condition Dataset; and `v.plot()` selects `state`, `event_active`, a sole
  variable, or an explicitly named Dataset variable without materializing
  Dask data.
- Validation: 65 focused grammar/reduction/overlap/plot tests passed; 141
  reference/usability/link tests passed; the complete offline suite passed
  (795 passed, 5 skipped); all 12 supported real-data vignettes executed with
  required plots; decision QA passed; 75 generated references and 8 visual
  results checked current; strict MkDocs build, built-site links/anchors,
  repository-size policy, and `git diff --check` passed; Chromium audited all
  built pages (375 passed). Jupyter/MkDocs required local kernel sockets, so
  those commands were rerun outside the filesystem sandbox without network
  acquisition.

## 2026-08-31 — Repair DataArray live-source certification

- Reproduced the scheduled live-source result: Daymet was intentionally
  `BLOCKED` without an Earthdata token, while the bounded three-day PRISM sample
  was retrieved successfully but failed only `source_identity_documented`.
- Found that noun provenance was present on the returned `DataArray`, but the
  climate QA profile converted it to a Dataset and inspected source identity
  and synthetic status only in container attrs. Updated those checks to inspect
  both container and data-variable attrs, preserving strict rejection when any
  variable declares synthetic data.
- Added DataArray provenance and synthetic-negative regressions. Enhanced live
  certification console output to name failed gates, failed QA checks, and
  blocker caveats while retaining complete JSON evidence.
- Validation: 24 focused QA/noun/live-certification tests passed; the bounded
  live command exited zero with Daymet `BLOCKED` for the absent local token and
  PRISM `PASS_WITH_CAVEATS`; the complete offline suite passed with 785 tests
  and 5 skips; offline Phase 1 source QA passed for PRISM, gridMET, and
  Sentinel-2. Regenerated visual evidence changed only the manifest's QA-source
  hash and checkout SHA; all 8 visual results (7 figures) and 75 reference pages
  passed freshness checks. `git diff --check` passed.

## 2026-08-30 — Make lazy-iframe browser auditing deterministic

- Investigated the single Chromium crawl failure on the Fire VASE page. The
  published HTML asset was present and valid; the audit could instead observe
  the iframe's already-loaded initial `about:blank` document, then finish and
  close the page while the lazy navigation was still active. Chromium reported
  that teardown as `net::ERR_ABORTED`.
- Updated the shared embed activation check to wait until each nonblank iframe's
  browsing context matches its resolved `src` and that requested document is
  complete. Added a deliberately delayed lazy-iframe detector regression that
  proves content loaded by the requested document is included in the audit.
- Validation: 11 non-browser browser-support tests passed; the focused detector
  and Fire VASE browser checks passed 12/12; the complete Chromium suite passed
  375/375 in 262.69 seconds; `git diff --check` passed.

## 2026-08-30 — Bring the software manuscript framing into the public documentation

- User asked to find the newly added main manuscript PDF and incorporate its
  ideas and language into the documentation and website. Identified
  `docs/documentation/main-17.pdf` as the August 28, 2026 draft, extracted its
  text, rendered all 13 pages, and visually inspected the complete document.
- Adopted the manuscript's distinction between computational repeatability and
  scientific inspectability, its two-level model of readable expression plus
  inspectable foundation, and its source-qualified noun, semantic verb,
  authored-order, state/trace, and evidence-boundary language. Retained the
  design maxim that shorter expressions require stronger evidence underneath.
- Added `docs/concepts/scientific_inspectability.md` and placed it under
  Documents → Pipe and grammar. The page links to the dated manuscript while
  stating that runtime, tests, public API, and generated references—not the
  manuscript—remain implementation truth.
- Reframed Home, Learn, the grammar and pipe references, methods/citation,
  vignettes, README, quickstart, and the xarray comparison around inspectable
  scientific statements. Preserved explicit boundaries: common nouns do not
  establish source equivalence; trace is not complete provenance; `unwrap()`
  does not compute or certify; fixture/live/structural/scientific evidence have
  distinct jobs; many-dataset and full branch-and-join synthesis are not current
  capability claims. No scientific runtime, catalog, source status, release
  metadata, manuscript PDF, generated reference page, or primary navigation tab
  changed.
- Extended the research-focused homepage with an inspectability manifesto and
  statement/state/evidence layer section using the existing editorial design.
  Visual QA found and fixed low-contrast release-status text and a clipped
  mobile wordmark; added a 390 px browser regression for the title.
- Validation: the complete offline suite passed with 783 tests and 5 skips;
  94 focused documentation/reference/repository/release tests passed;
  75 generated reference pages were current; strict MkDocs build and built-site
  file/anchor checks passed; all 374 Chromium browser checks passed. Desktop and
  390 px views of Home and the new framing page were also inspected in the
  in-app browser with no horizontal overflow. During final checks, the reviewed
  documentation change set appeared on `origin/main` as commit `0156d25`
  (`inspect`), created outside this task's tool actions. Read-only requests then
  verified that both the public homepage and `/concepts/scientific_inspectability/`
  served the new framing. No release, tag, DOI, or manuscript-status change was
  performed.

## 2026-08-28 — Prepare an installable 0.1.0rc1

- Independent outside-user acceptance correctly stopped: PyPI had no package
  and GitHub Releases had no wheel/sdist assets. A clone is not a substitute.
  Local main: 862a80aed8a2781b40e6e5293fd6cfbcba887aa4. Public main:
  cb80b6c7d1b1562016b8ae1a1bf7c0221ea392f0, differing only by an added PDF.
  Public prereleases 0.0.1 and build both had empty asset lists.
- Prepared real RC metadata, consistent unpublished installation guidance,
  and a no-checkout public checksum-pinned PRISM quickstart. No science or
  source registration changed. Historical developer installs are labeled.
- Publication workflow now requires explicit destination selection, a matching
  tag, full gate and same-wheel Python 3.9–3.12 checks. GitHub assets include
  wheel, sdist and SHA256SUMS. PyPI trusted-publisher configuration remains
  unverified; exact maintainer steps are in RELEASING.md. No public writes.
- Gate now binds clean source identity and all commit-eligible inputs, checks
  the public quickstart and gallery, and can run from a separate local snapshot.
  A local snapshot is not the eventual public release SHA. Preliminary
  release/docs regressions: 62 passed; final gate and hashes follow below.
- Fresh dependency resolution exposed two VirtualCube failures on pandas 3:
  removed AS frequency aliases. Added a narrow annual-offset compatibility
  translation preserving calendar anchors/multipliers and regression tests.
  Earlier artifacts are diagnostic only; the final RC is rebuilt and re-gated.
- Synchronized `uv.lock` with the RC and the already-declared roads extra;
  no existing dependency versions were upgraded. Added a version-consistency
  regression. The existing lock retains a yanked build-tool version; release
  validation resolves fresh tools with pip, not that development lock.
- The full browser gate exposed missing notebook plots: the release gate's
  global Agg backend suppressed `plt.show()` in MkDocs-Jupyter's own kernels.
  Scoped the inline backend to the docs step; script plots retain Agg. Kept
  the browser image-count checks unchanged and added an environment
  regression. No missing-figure failure is waived.
- Final local evidence was produced from isolated snapshot
  `d6a6c4b44bf295f64bb754a6470bcc67375bb4e6` (base checkout
  `862a80aed8a2781b40e6e5293fd6cfbcba887aa4`). The complete 33-step gate
  passed: 782 offline tests passed with 5 skips; 32 streaming tests, 12
  installed-wheel notebooks, publication/source/decision QA, all generated
  checks, strict docs, links, repository policy and 373 Chromium checks passed.
- Final artifacts: `cubedynamics-0.1.0rc1-py3-none-any.whl`, SHA256
  `6f5b269b64d7ab1d1cfc9651f1cb9e7caee76a6621275ec77c27439302934d26`;
  `cubedynamics-0.1.0rc1.tar.gz`, SHA256
  `e07bd7d1383e56e2a65d215554611b01285479b5113edb7b19118cc4e6ad3b83`.
  Twine, archive contents, exact wheel bytes, package-only use and `pip check`
  passed. External wheel checks passed on local Python 3.9.21, 3.10.16,
  3.11.11 and 3.12.8; the public fixture and bounded three-day live PRISM
  quickstarts passed (the latter is not source certification). All 61 external
  documentation links were available during the advisory check.
- Final verdict remains `NOT READY TO PUBLISH v0.1.0rc1`: no tag, GitHub
  Release or PyPI upload was performed. The prepared changes still require
  review and commit after integrating public main
  `cb80b6c7d1b1562016b8ae1a1bf7c0221ea392f0` (its only newer file at review
  time was `docs/documentation/main-17.pdf`), followed by the configured Linux
  matrix on that public SHA. PyPI project/pending-publisher and GitHub
  environment settings also remain unverified. Exact authorized publication
  steps are recorded in `RELEASING.md`.

## 2026-08-28 — Readable interactive homepage hero

- User requested a polished interactive hero with visible legend text and
  readable cube labels, retaining the real-data HTML viewer.
- Updated `scripts/build_real_data_assets.py` and added the small modular
  `docs/assets/styles/hero-cube.css`: light research-figure styling, distinct
  header/controls/stage/legend regions, explicit Celsius ticks, and responsive
  framing. Rebuilt `docs/assets/figures/prism_boulder_tmax_cube.html` from the
  unchanged, hash-verified PRISM fixture; units and full data range are checked
  against the explicit −25 to 20 °C scale. Deferred loading remains intact.
- Fixed canonical viewer label inverse-rotation order, local time-axis
  cancellation, intermediate 3D preservation, theme inheritance, duplicate
  endpoint labels, and two-dimensional zoom distortion (now uniform 3D zoom).
  Added keyboard rotation/zoom/reset and shared optional button controls.
  Geographic labels retain two decimals; optional short dates preserve the
  existing default format. Cube faces, geometry and newest/front semantics
  are unchanged.
- Added real-fixture and axis regression tests plus desktop/mobile browser
  assertions for legend contrast, stage layout, label rotation matrices and
  controls. Updated viewer invariants and refreshed the visual evidence manifest.
- Validation: 749 offline tests passed (5 skipped); 3 homepage browser checks
  passed; strict MkDocs build, visual evidence check and tracked-size policy
  passed. Browser skill used for visual inspection of the local preview.
  No production deployment, commit or push performed.

### Follow-up — Keep the year on the cube

- At the user's request, changed the homepage generator's date format to
  `%d %b %Y`: both cube endpoint labels now include 2024, not just the heading.
- Rebuilt the asset, aligned the invariant notes, and added regression checks
  for full dates and their fit within desktop/mobile viewports.
- Validation: 7 focused Python tests, 3 homepage browser checks and strict
  MkDocs build passed; visually checked the full labels in the narrow embed.

### Follow-up — Homepage example dropdown

- User requested a dropdown covering the available example cubes. Added 14
  curated choices: 13 raster cubes from reviewed PRISM, gridMET and Sentinel-2
  fixtures and the existing FIRED/gridMET hull, explicitly labeled as a
  specialized Plotly viewer. Included raw variables/bands and existing grammar
  lesson results; historical synthetic or unverified exports remain excluded.
- Added `scripts/hero_examples.py`, deterministic gallery generation and an
  input/output checksum manifest. The build hook renders accessible grouped
  options and no-JavaScript standalone links. Each selection updates its
  description and lesson/source links, retaining full years, native units,
  coordinate labels and Sentinel-2 cloud/scene-count caveats.
- Only one viewer loads at a time. Switching replaces its browsing context to
  cancel stale in-flight navigation; completed loader overlays immediately
  stop intercepting controls. Fixed mobile selector clipping. Initial viewer
  HTML is 57,244 bytes; all 14 HTML exports total 763,063 bytes.
- Added gallery/fixture-integrity and desktop/mobile browser regressions,
  including every choice, rapid switching, controls and no-JavaScript links.
  CI now checks gallery freshness. Updated asset ownership and viewer notes.
- Validation: 765 offline tests passed (5 skipped); final focused browser suite
  passed all 17 checks. Strict MkDocs build, gallery/visual evidence checks,
  built-site links, tracked repository policy and diff checks passed. Local
  preview rebuilt; no commit, push or production deployment performed.

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

## 2026-07-21 — Fire VASE Developmental Decision Atlas

### User Goals
- Revise the exploratory report away from a terminal/death framing and toward a
  scientific decision atlas for wildfire developmental trajectories and
  environmental transitions.
- Use real cached FIRED candidate fires and real cached gridMET `tmmx`, `tmmn`,
  `vpd`, and `vs` data.
- Distinguish final meaningful expansion, terminal observed record, and
  physical extinction.
- Add task-specific QC, event detection, alignment comparisons, geometry-only
  typology, continuous developmental axes, event-centered climate diagnostics,
  state transitions, terminal-observation secondary analysis, outlier checks,
  sample-size diagnostics, and a manuscript decision matrix.

### Implementation Summary
- Added `config/fire_vase_developmental_atlas.yml` with configurable activity
  metric, pulse thresholds, quiescence length, lag window, clustering settings,
  climate variables, and outlier-sensitivity options.
- Added `examples/fire_vase_developmental_atlas.py`, a full real-data atlas
  generator that writes:
  `outputs/fire_vase_developmental_atlas.pdf`,
  `outputs/fire_vase_developmental_atlas.html`,
  `outputs/fire_vase_time_table.csv`,
  `outputs/fire_vase_developmental_traits.csv`,
  `outputs/fire_vase_event_table.csv`,
  `outputs/fire_vase_qc_table.csv`, and
  `outputs/fire_vase_candidate_results.csv`.
- Generated 15 major PNG figures and 15 SVG companions under
  `outputs/fire_vase_developmental_figures/`.
- The PDF contains a one-page scientific decision summary, task-specific QC,
  major diagnostic sections, a two-page final interpretation, and full-page
  developmental profiles for each of the 25 fires.

### Validation
- Ran `MPLCONFIGDIR=/private/tmp/mplconfig .venv/bin/python
  examples/fire_vase_developmental_atlas.py`; manifest reports 25 fires and 229
  fire-time records.
- Confirmed all four climate columns are present and complete in
  `outputs/fire_vase_time_table.csv`: `tmmx_c`, `tmmn_c`, `vpd_kpa`, and
  `wind_speed_m_s`.
- Confirmed first-observation alignment includes 25 fires and that
  `physical_extinction_observed` is `False` for all fire-time rows.
- Rendered the final 50-page PDF with `pdftoppm` and visually inspected the
  executive summary, QC table, observation raster, event sensitivity, alignment
  comparison, manuscript decision matrix, two interpretation pages, and a
  profile page.
- Audited the new atlas outputs for prohibited terminal/death and prescribed
  comparison language.
- Ran `.venv/bin/python -m py_compile
  examples/fire_vase_developmental_atlas.py`.
- Ran `.venv/bin/python -m pytest tests/test_fire_vase_panel.py
  tests/test_fire_hull_api.py -q` with 9 passing tests and 2 warnings.

### 2026-07-21 Follow-up: 100-fire Size-stratified Developmental Atlas
- Created
  `artifacts/fire-vase-gridmet-real/candidate_events_100_size_stratified_2001_2003.csv`
  using random seed 4217.
- Sampling design: eligible FIRED events were constrained to CONUS gridMET
  coverage, cached climate years 2001-2003, at least 5 observed daily records,
  and positive final area. The final sample uses 10 log-area bins with 10 fires
  per bin, spanning about 1.1-229 km2.
- Ran the developmental atlas workflow with
  `--candidates-csv artifacts/fire-vase-gridmet-real/candidate_events_100_size_stratified_2001_2003.csv`
  and `--outputs outputs/fire_vase_developmental_atlas_100_size_sample`.
- Generated a 125-page PDF, HTML companion, fire-time table with 784 rows,
  developmental traits for 100 fires, 730 detected events, task-specific QC,
  manuscript candidate results, and 15 PNG/15 SVG figure files.
- Patched hard-coded "25 fires" text in the atlas generator so summaries and
  compound-condition figures use the actual sample size.

### Validation
- Confirmed the 100-fire sample has 10 fires in each size bin and complete
  cached climate for `tmmx_c`, `tmmn_c`, `vpd_kpa`, and `wind_speed_m_s`.
- Rendered the 125-page PDF with `pdftoppm` and visually inspected the
  executive summary, alignment comparison, and a representative fire profile.
- Confirmed no physical extinction is inferred and no prescribed-fire
  comparison is made.
- Ran `.venv/bin/python -m py_compile
  examples/fire_vase_developmental_atlas.py`.
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

## 2026-07-21 — Fire VASE Lakehouse Scaffolding

### User Goals
- Treat fire VASEs as real scientific data objects rather than synthetic or
  image-first products.
- Design a scalable architecture for many fires while keeping GitHub light.
- Add schemas, storage/config templates, repository-size guardrails, modular
  lakehouse helpers, and a small real-data pilot path.

### Implementation Summary
- Added `src/cubedynamics/fire_vase_lakehouse/` with deterministic cache keys,
  component invalidation, cohort partitioning, manifest transitions, QC helpers,
  schema loading/validation, and cohort/medoid/event-aligned summary helpers.
- Added JSON schemas for raw observations, canonical fire time, geometry,
  traits, events, VASE slices, rendered assets, manifests, runs, catalog,
  failures, and cohort summaries.
- Added `config/fire_vase_pipeline.yml`, `config/storage.example.yml`, and
  `config/repository_policy.yml`; `config/storage.yml` is ignored for real
  local or production storage settings.
- Extended `.gitignore` for lakehouse outputs, scratch roots, Zarr, Parquet,
  NetCDF, GeoParquet, GLB/GLTF, TIFF, and runtime manifests.
- Added repository protection through `scripts/check_repository_size.py`,
  `.pre-commit-config.yaml`, and `.github/workflows/repository-size-check.yml`.
- Added `scripts/fire_vase_lakehouse_pilot.py`, which samples only real rows
  from the configured fire catalog and writes a pilot manifest under an ignored
  output root.
- Added architecture docs in `docs/dev/fire_vase_lakehouse.md` and repository
  boundary notes in README/data/output/manifest READMEs.

### Validation
- Ran `.venv/bin/python -m pytest tests/test_fire_vase_lakehouse.py -q`
  (`10 passed`, one unrelated Planetary Computer pydantic warning).
- Ran `.venv/bin/python scripts/fire_vase_lakehouse_pilot.py --config
  config/fire_vase_pipeline.yml --output-root ./scratch/fire_vase_run
  --sample-size 1000`. The configured real catalog had 100 rows, so the pilot
  wrote 100 real-fire rows and recorded
  `source_catalog_smaller_than_requested_sample` in
  `scratch/fire_vase_run/pilot_report.json`.
- Ran `.venv/bin/python scripts/check_repository_size.py --mode staged`
  successfully. Full tracked-file mode correctly flagged pre-existing tracked
  generated outputs under `artifacts/` and `tmp/`; cleaning those from Git index
  should be a separate explicit cleanup step.

### Caveats
- `pyarrow` and `duckdb` were not installed in the project virtualenv, so the
  pilot wrote CSV fallback tables rather than Parquet and did not run DuckDB
  queries. No full-population 250k fire job was attempted.

### 2026-07-21 Follow-up: All Available Configured Fires
- Installed `pyarrow==25.0.0` and `duckdb==1.5.4` into the project `.venv`
  with `uv pip install --python .venv/bin/python pyarrow duckdb`.
- Re-ran the lakehouse pilot with `--sample-size 100000` and output root
  `./scratch/fire_vase_run_all`. The configured real catalog still contained
  100 rows, so the all-available run wrote 100 real fires to Parquet and
  recorded `source_catalog_smaller_than_requested_sample`.
- DuckDB validation over the Parquet outputs found 100 catalog rows, 100 trait
  rows, and 100 processing manifest rows at `geometry_complete`.
- Ran the broad offline suite with `.venv/bin/python -m pytest -m "not
  integration and not online" -q`; it reached 266 passed, 3 skipped, and 8
  deselected with no failures before being interrupted after a long quiet
  Matplotlib/backend wait.

### 2026-07-21 Follow-up: Full Cached FIRED Event Source
- Corrected the lakehouse pipeline source from the 100-fire stratified CSV to
  the cached full FIRED event GeoPackage:
  `artifacts/fire-vase-gridmet-real/fired-cache/fired_conus-ak_events_nov2001-march2021.gpkg`.
- Updated `scripts/fire_vase_lakehouse_pilot.py` to read GeoPackage/GeoJSON/SHP
  sources, normalize FIRED event columns, compute lon/lat centroids through
  EPSG:5070, and avoid an expensive exact medoid calculation over very large
  cohorts.
- Ran the full cached event manifest/table pass with output root
  `./scratch/fire_vase_run_full`; it processed 278,569 real FIRED event rows and
  wrote Parquet tables under the ignored scratch root.
- DuckDB validation reported 278,569 catalog rows, 278,569 trait rows, 278,569
  `geometry_complete` manifest rows, event years 2000-2021, and a total scratch
  footprint of about 49 MB.

### 2026-07-22 Follow-up: Population Summary PDF Atlas
- Added `scripts/fire_vase_population_atlas_pdf.py` to build a full-population
  summary atlas from the Parquet lakehouse pilot tables using DuckDB,
  matplotlib, and ReportLab.
- Generated `output/pdf/fire_vase_population_summary_atlas.pdf` and
  `output/pdf/fire_vase_population_summary_atlas_manifest.json` from
  `scratch/fire_vase_run_full/tables`.
- The atlas summarizes 278,569 real FIRED event rows with annual counts,
  regional summaries, region-year density, size-duration structure, largest
  events, longest-duration events, processing status, and provenance/limits.
- Rendered all PDF pages to PNG under
  `tmp/pdfs/fire_vase_population_summary_atlas_render/` with Poppler and
  visually checked the layout. Fixed a wrapped year-range callout and rebuilt
  the PDF.

### 2026-07-22 Follow-up: Visual Morphology VASE Atlas
- Added `scripts/fire_vase_morphology_atlas_pdf.py` to build a visual atlas
  from real FIRED daily/event caches, including many VASE profile glyphs,
  morphology categories, category trait fingerprints, and climate-vs-shape
  comparisons.
- Generated `output/pdf/fire_vase_morphology_atlas.pdf` and
  `output/pdf/fire_vase_morphology_atlas_manifest.json`.
- Classified 278,569 real FIRED events using daily area trajectories. Counts:
  single flash 161,073; skinny persistent 38,094; compact steady 31,250;
  multi-pulse complex 24,418; late surge 16,079; front-loaded plateau 7,655.
- The main panel shows 216 real VASE profile glyphs sampled across categories.
  Climate comparisons use a balanced 300-event real gridMET sample from cached
  2001-2003 CONUS event windows.
- Moved generated sidecar CSVs to ignored
  `scratch/fire_vase_morphology_atlas/` rather than `output/pdf/`.
- Rendered atlas pages to PNG under `tmp/pdfs/fire_vase_morphology_atlas_render/`
  and visually checked the main VASE panel, category exemplars, shape summary,
  trait heat map, and climate comparison pages.

### 2026-07-22 Follow-up: Climate-Attributed VASE Slice Tables
- Added `scripts/fire_vase_build_climate_tables.py` to populate durable
  `vase_slices` Parquet rows from real FIRED daily/event caches and cached
  daily gridMET NetCDF files.
- Updated `config/fire_vase_pipeline.yml` to label the current gridMET
  attribution as daily centroid-nearest-grid-cell extraction rather than
  hourly.
- Expanded `schemas/vase_slices.schema.json` with maximum/minimum temperature,
  VPD, wind speed, climate source/resolution/method, climate availability, and
  failure reason fields.
- Built `scratch/fire_vase_run_full/tables/vase_slices.parquet` for all
  supported cached gridMET years (2001-2003): 67,522 VASE slice rows across
  30,544 fires.
- Marked 26,877 fires as `climate_complete` in
  `processing_manifest_climate.parquet`. Recorded retryable failures for 3,667
  cached-year fires with missing gridMET values and 248,025 fires whose slice
  years are not yet cached locally.
- DuckDB validation confirmed available climate ranges and schema validation
  passed on sample records. Focused lakehouse tests pass (`13 passed`).

### 2026-07-22 Follow-up: Full-Span gridMET Climate Attribution
- Cached real daily gridMET NetCDF files for `tmmx`, `tmmn`, `vpd`, and `vs`
  for 2000-2021 under ignored
  `artifacts/fire-vase-gridmet-real/gridmet-cache/` using
  `scripts/cache_gridmet_years.py`.
- Cache manifest:
  `scratch/fire_vase_run_full/gridmet_cache_manifest.json`. The completed
  cache contains 88 NetCDF files, reusing 13 already cached files and
  downloading 75 additional files with 0 failures.
- Rebuilt `scratch/fire_vase_run_full/tables/vase_slices.parquet` across the
  full cached span. The table now contains 626,102 daily VASE slice rows for
  278,569 FIRED events from 2000-11-02 through 2021-05-01.
- Climate attribution is complete for 237,235 fires and 550,961 slice rows.
  The remaining 41,334 fires and 75,141 slice rows have cached-year extraction
  failures because gridMET returned missing values for one or more centroid
  samples, likely outside/near the effective gridMET footprint.
- Validation: sample `vase_slices` records passed JSON schema validation;
  focused lakehouse tests passed (`13 passed`); staged repository size policy
  check passed.

### 2026-07-22 Follow-up: Developmental Morphology Analysis Atlas
- Added `scripts/fire_vase_developmental_morphology_analysis.py` to construct a
  continuous geometry-first VASE morphospace and evaluate climate coupling
  afterward from the full climate-attributed `vase_slices` table.
- Generated `output/pdf/fire_vase_developmental_morphology_atlas.pdf` and
  `output/pdf/fire_vase_developmental_morphology_atlas_manifest.json`.
- The atlas uses all 278,569 FIRED events, 237,235 climate-complete fires, and
  36 real medoid VASE representatives selected by farthest-point coverage in
  PC1-PC3 morphospace.
- Wrote sidecar analysis tables under ignored
  `scratch/fire_vase_developmental_morphology/`: morphospace features, medoids,
  geometry-only developmental events, stage summaries, directional coupling,
  developmental control profile, matched pairs, and PCA loadings.
- First-pass results: geometry PC1-PC5 explain 96.3% of geometry-feature
  variance; mean linear proxy R2 is 0.191 for `P(morphology | climate)` and
  0.020 for `P(climate | morphology)`. Stage-wise control profiles indicate
  geometry-only models carry far more information about final morphospace
  position than climate-only models in this linear baseline.
- Validation: rendered the 10-page PDF to PNG with Poppler and visually checked
  overview, medoid, field-guide, and control-profile pages. The script compiles,
  focused lakehouse tests pass (`13 passed`), and staged repository size policy
  check passes.

### 2026-07-22 Follow-up: Manuscript Stage 1 Narrative
- Created
  `docs/manuscripts/fire_vase_developmental_morphology/manuscript_stage_1_narrative.md`
  as the first manuscript working draft for Fire VASE developmental morphology.
- The draft frames Fire VASE as a scientific representation, not a visualization,
  and organizes the paper around a geometry-first developmental morphospace,
  climate mapped afterward, matched comparisons, and a developmental control
  profile.
- Added a focused citation map covering FIRED/FIREDpy, gridMET, climate/VPD,
  fast daily fire growth, topographic spread constraints, and biological
  morphospace/geometric morphometrics.
- Linked the narrative to current analysis outputs: the developmental morphology
  atlas, morphospace features, medoids, geometry-only events, climate coupling,
  matched pairs, and control-profile tables.

### 2026-07-22 Follow-up: Manuscript Stage 2 Citation-Revised Narrative
- Created
  `docs/manuscripts/fire_vase_developmental_morphology/manuscript_stage_2_citation_revised_narrative.md`
  from the user's opening manuscript thoughts.
- Tightened the central claim from "wildfire lacks a representation of an entire
  fire" to the more citation-defensible claim that wildfire lacks a compact,
  comparable, whole-history developmental representation.
- Revised the abstract and introduction around Fire VASE as an instrument for
  discovering morphospace, not primarily a visualization.
- Folded in current repository results: 278,569 events, 237,235
  climate-complete fires, PC1-PC5 explaining 96.3% of geometry-feature variance,
  36 medoid representatives, directional coupling R2 values, and the
  stage-wise developmental control profile.
- Added a results narrative and figure sequence for a tight six-figure
  manuscript, plus confidence levels and analyses still needed before
  submission.

### 2026-07-22 Follow-up: Science-Paper-Style Manuscript PDF
- Added `scripts/fire_vase_science_manuscript_pdf.py` to generate a compact
  science-paper-style PDF manuscript from the Fire VASE developmental morphology
  narrative and atlas figures.
- Generated
  `output/pdf/fire_vase_developmental_morphology_manuscript.pdf` and
  `output/pdf/fire_vase_developmental_morphology_manuscript_manifest.json`.
- The PDF uses a manuscript title/abstract page, two-column body text,
  numbered references, and full-width figure plates cropped from the real
  developmental morphology atlas outputs.
- Rendered the 8-page manuscript PDF to PNG with Poppler and visually checked
  the title page, two-column body page, morphospace figure plate, and final
  developmental control profile page. Fixed an orphan word and cropped figure
  label issues before finalizing.
- Validation: script compiles, PDF metadata reports 8 letter pages, and staged
  repository size policy check passes.

### 2026-07-22 Follow-up: Formal Reviews And Review-Revised Manuscript PDF
- Created
  `docs/manuscripts/fire_vase_developmental_morphology/formal_reviews_round_1.md`
  with three formal review perspectives: conceptual framing/theory, wildfire
  science/data interpretation, and methods/statistical evidence.
- Revised `scripts/fire_vase_science_manuscript_pdf.py` to expand the manuscript
  toward a 10-page short-paper draft with a clearer representational gap,
  explicit constraint hypothesis, morphospace rationale, fuller Results and
  Methods sections, and a data/code availability note.
- Filled reviewer-requested arguments: climate is framed as state-dependent
  rather than unimportant; centroid gridMET attribution is described as a
  first-pass proxy; short one-day fires are treated as both a result and caveat;
  R2 values are consistently framed as linear baselines; PCA axes and medoid
  labels are interpreted cautiously.
- Improved manuscript figure preparation by auto-cropping nonblank atlas content
  before embedding, which made the matched-comparison plate substantially more
  legible while preserving real atlas-derived figures.
- Regenerated
  `output/pdf/fire_vase_developmental_morphology_manuscript.pdf` and
  `output/pdf/fire_vase_developmental_morphology_manuscript_manifest.json`.
- Validation: script compiles, the revised PDF renders to PNG with Poppler,
  visual QA checked the title/body/figure pages, PDF metadata reports 10 letter
  pages, and staged repository size policy check passes.

### 2026-07-22 Follow-up: Science Author-Guideline Compliance Pass
- Looked up accessible Science.org / AAAS author-guideline material and a
  secondary Science magazine initial-submission format summary after direct
  Science instruction pages were not retrievable from this environment.
- Added
  `docs/manuscripts/fire_vase_developmental_morphology/science_author_guidelines_compliance.md`
  documenting the guideline assumptions, changes made, and remaining
  pre-submission placeholders.
- Revised `scripts/fire_vase_science_manuscript_pdf.py` from a two-column
  print-style PDF to a conservative Science initial-submission-style PDF:
  single column, double spaced, 1-inch margins, 12-point Times-style body text,
  line-numbered pages, <=125-word abstract, short One Sentence Summary,
  ordered figure callouts, "References and Notes," acknowledgments, funding,
  author contributions, competing interests, data/materials availability, and
  supplementary materials statements.
- Regenerated
  `output/pdf/fire_vase_developmental_morphology_manuscript.pdf` and
  `output/pdf/fire_vase_developmental_morphology_manuscript_manifest.json`.
- Validation: abstract is 112 words, One Sentence Summary is 64 characters,
  visual QA checked front matter/body/back matter/figure pages, script compiles,
  PDF metadata reports 17 letter pages, and staged repository size policy check
  passes.

### 2026-07-22 Follow-up: Fire VASE Main Figure Suite
- Created a reproducible five-figure Science-style main suite under
  `figures/main/` with PDF, PNG, and SVG exports for `Figure_1` through
  `Figure_5`, plus `figure_legends.md`, `statistical_validation.md`,
  `figure_data_dictionary.md`, `README.md`, `figure_manifest.json`, and
  derived validation CSV/JSON tables.
- Added figure-generation scripts under `scripts/figures/` for shared style,
  Fire VASE glyph rendering, morphospace data loading/PCA, validation
  statistics, all five main figures, supplementary validation, and full suite
  rendering.
- Generated `figures/supplement/Supplementary_Figure_1_validation.*` as a
  compact validation summary.
- Used only existing real Fire VASE/FIRED/gridMET-derived analysis tables from
  `scratch/fire_vase_developmental_morphology/` and
  `scratch/fire_vase_run_full/tables/`; no synthetic data were introduced.
- Recomputed geometry PCA and validation summaries with 60 stratified bootstrap
  replicates over 12,000-fire subsamples for a fast local pass. Observed
  results: 278,569 fires, 626,102 vase slices, 237,235 climate-complete fires,
  and PC1-PC5 cumulative variance 0.962747.
- Important caveats documented in the validation file: duration sensitivity
  weakens the cumulative variance for long fires, the within-fire
  growth-profile permutation null remains close to observed, and the
  leakage-audited fixed-day prediction benchmark is weak/negative under
  blocked validation compared with older future-normalized stage features.
- Validation: rendered the full suite, visually inspected main PNG exports,
  compiled all `scripts/figures/*.py` files, and confirmed repository size
  policy passes for staged files.

### 2026-07-22 Follow-up: Science Manuscript Updated To New Figure Suite
- Revised `scripts/fire_vase_science_manuscript_pdf.py` so the manuscript uses
  the new standalone `figures/main/Figure_1.png` through `Figure_5.png`
  instead of cropped pages from the earlier exploratory atlas.
- Edited the manuscript abstract, Results, Discussion, and Methods to match the
  recomputed figure evidence: strong geometry-first morphospace structure,
  medoids as real-fire landmarks, interpretable descriptive PC axes, climate
  alignment without equivalence, and weak/provisional leakage-audited fixed-day
  prediction.
- Replaced the older strong stage-wise prediction language tied to
  future-normalized fractional-stage features with an explicit leakage-audited
  benchmark interpretation for Figure 5.
- Expanded the manuscript figure captions into standalone, panel-by-panel
  legends and updated `scripts/figures/render_all.py` so
  `figures/main/figure_legends.md` remains comprehensive on regeneration.
- Regenerated
  `output/pdf/fire_vase_developmental_morphology_manuscript.pdf` and
  `output/pdf/fire_vase_developmental_morphology_manuscript_manifest.json`.
- Validation: manuscript PDF reports 19 letter pages, abstract is 124 words,
  rendered PDF pages to PNG, visually inspected text and figure pages, searched
  for stale old prediction claims, compiled updated scripts, and confirmed the
  repository size policy check passes.

### 2026-07-22 Follow-up: Round-Two Manuscript Review And Figure Polish
- Created
  `docs/manuscripts/fire_vase_developmental_morphology/formal_reviews_round_2.md`
  with three additional formal reviews focused on conceptual framing, validation
  and leakage risk, and figure readability, plus response-to-review notes.
- Revised `scripts/fire_vase_science_manuscript_pdf.py` to answer the reviews:
  sharpened the representation-first manuscript framing, clarified what the
  validation hierarchy supports, separated descriptive climate alignment from
  predictive claims, made fixed-day prediction methods more explicit, and added
  a forward-looking hypothesis paragraph.
- Updated figure scripts in `scripts/figures/` so main axis labels use plain
  language instead of terse technical abbreviations, and moved or removed
  cramped labels/legends that were causing text overlap in Figures 4 and 5.
- Regenerated `figures/main/Figure_1` through `Figure_5` in PDF, PNG, and SVG
  formats, regenerated `figures/main/figure_legends.md`, and rebuilt the
  manuscript PDF and manifest.
- Validation: reran the full figure suite, compiled the changed manuscript and
  figure scripts, rendered the manuscript PDF to PNG with Poppler, visually
  checked key figure pages and overlap-prone panels, confirmed the PDF reports
  19 letter pages, and confirmed the staged repository size policy check passes.

### 2026-07-22 Follow-up: Perimeter-Based Climate Attribution Scaffold
- Started addressing the manuscript caveat that climate attribution was daily
  and centroid-based by adding a companion perimeter-exposure pipeline rather
  than replacing the existing centroid `vase_slices` baseline.
- Extended the shared gridMET variable mapping to support precipitation,
  relative and specific humidity, 100-hr and 1000-hr dead fuel moisture,
  energy release component, burning index, evapotranspiration, and solar
  radiation in addition to maximum temperature, minimum temperature, VPD, and
  wind speed.
- Added `scripts/fire_vase_build_perimeter_climate_tables.py`, which summarizes
  cached daily gridMET over real FIRED daily polygons for active burned area,
  cumulative burned area, and configurable exterior perimeter-extension zones.
  The table records sample-cell counts, mean/min/max/std climate summaries,
  and explicit nearest-cell fallback flags for fires smaller than a gridMET
  cell.
- Added `schemas/vase_climate_exposures.schema.json`, documented the new table
  in `docs/dev/fire_vase_lakehouse.md`, added optional-variable settings to
  `config/fire_vase_pipeline.yml`, and added a `--preset comprehensive` option
  to `scripts/cache_gridmet_years.py` for downloading expanded gridMET inputs.
- Ran a 25-fire real-data pilot extraction against the cached 2000-2021 gridMET
  files and wrote corrected pilot output to
  `scratch/fire_vase_run_full/tables/vase_climate_exposures.parquet` plus
  `scratch/fire_vase_run_full/perimeter_climate_build_report.json`.
- Validation: caught and fixed an initial CRS/buffering bug before finalizing
  the smoke output, compiled the changed scripts, ran
  `pytest tests/test_fire_vase_lakehouse.py -q` with 16 passing tests, and
  confirmed the staged repository size policy check passes.

### 2026-07-22 Follow-up: Manuscript Claim Audit And Conservative Revision
- Read the attached manuscript-audit brief and inspected the current manuscript
  PDF text, figure/statistics scripts, derived tables, and validation outputs.
- Added and ran `scripts/fire_vase_manuscript_claim_audit.py`, a reproducible
  claim-audit workflow that writes PCA ablations, PC1 loading/correlation
  diagnostics, a null-model hierarchy, climate/prediction section decisions,
  a revised manuscript source, an audited figure plan, and a terminal-style
  final report.
- Generated required audit deliverables under `analysis/`, including
  `manuscript_claim_audit.md`, `pc1_robustness_report.md`,
  `null_model_report.md`, `climate_section_decision.md`,
  `prediction_section_decision.md`, `figure_restructure_plan.md`, and
  `final_terminal_report.txt`.
- Revised the manuscript source as
  `docs/manuscripts/fire_vase_developmental_morphology/manuscript_audited_revision.md`
  with the claim level lowered from strong "constrained/restricted possible
  trajectories" language to the strongest supported claim: a reproducible
  low-dimensional developmental coordinate system.
- Updated the audited figure set under `figures/main_audited/`, including a
  new `Figure_3_null_universes` diagnostic figure and revised audited figure
  legends. The recommended main-text structure is now four figures, with
  fixed-day prediction moved to the supplement as a leakage audit.
- Audit conclusion: PC1 survives scale/duration controls but is strongly tied
  to profile/allocation redundancy; observed histories differ clearly from
  feature-permutation nulls but not enough from stricter duration/profile
  nulls to justify Level 4 possible-space constraint language.
- Validation: compiled the changed scripts, ran the audit with 6,000-fire
  samples and 12 null replicates, visually inspected the revised null figure
  for label overlap, ran `pytest tests/test_fire_vase_lakehouse.py -q` with
  16 passing tests, and confirmed the staged repository size policy check
  passes.

### 2026-07-22 Follow-up: Updated Main Figures And Manuscript From New Analyses
- Integrated the claim-audit analyses into the production figure pipeline.
  `scripts/figures/make_figure_3.py` now renders the PC1 ablation and null
  developmental-universe diagnostics from `analysis/claim_audit_stats/`, making
  the audit result the main Figure 3 rather than a sidecar figure.
- Updated `scripts/figures/render_all.py` to generate a four-figure main suite
  and to move the fixed-day prediction benchmark into the supplement as
  `Supplementary_Figure_2_prediction`. Regenerated main figure legends, the
  figure README, validation notes, data dictionary, and manifest.
- Rewrote `scripts/fire_vase_science_manuscript_pdf.py` around the supported
  manuscript claim: Fire VASE provides a reproducible low-dimensional
  coordinate system for observed wildfire histories. Removed unsupported
  restricted-trajectory framing, compressed climate to proof-of-concept
  projection/association, and removed prediction from the main figure sequence.
- Regenerated `figures/main/Figure_1` through `Figure_4` in PDF, PNG, and SVG,
  regenerated supplementary validation and prediction figures, and rebuilt
  `output/pdf/fire_vase_developmental_morphology_manuscript.pdf` as a 15-page
  Science-style draft with four main figures and comprehensive legends.
- Validation: compiled the changed scripts, reran the figure suite with
  60 bootstrap replicates and a 12,000-fire validation sample, rebuilt the
  manuscript PDF, rendered it to PNG pages with Poppler, visually checked the
  title/abstract page and main figure pages for text overlap, ran
  `.venv/bin/python -m pytest tests/test_fire_vase_lakehouse.py -q` with
  16 passing tests, and confirmed the staged repository size policy check
  passes.

### 2026-07-22 Follow-up: Round-Three Panel Review And Edits
- Added
  `docs/manuscripts/fire_vase_developmental_morphology/formal_reviews_round_3.md`
  with three formal reviews focused on inference, null-model interpretation,
  figure readability, and manuscript flow after the audit integration.
- Edited `scripts/fire_vase_science_manuscript_pdf.py` to remove process
  language from the paper, keep the one-sentence summary on the title page,
  make Results/Methods headings more consistent, soften Figure 1 language from
  "collapse into" to "can be organized in," and describe climate matching as
  similar form versus similar climate.
- Updated `scripts/figures/make_figure_4.py` so panel C reads as a
  climate-shape association analysis with the axis label "Held-out variance
  explained (R2)" instead of "Predictive coupling" and "prediction accuracy."
- Regenerated the main and supplementary figure suite, updated figure legends
  and manifests, rebuilt the Science-style manuscript PDF, and rendered the
  final PDF to PNG for visual QA. The manuscript now reports 14 letter pages,
  with the orphan one-sentence-summary page removed.
- Validation: compiled changed scripts by executing the figure/manuscript
  builders, rendered the final PDF with Poppler, visually checked the title
  page and updated Figure 4 page, and reran
  `.venv/bin/python -m pytest tests/test_fire_vase_lakehouse.py -q` with
  16 passing tests.

### 2026-07-22 Follow-up: Citation Audit And Reference Expansion
- Checked the existing manuscript references against external bibliographic
  sources and article pages. The original references were real and broadly
  relevant, but several citation placements were overloaded or uncited in the
  text.
- Added
  `docs/manuscripts/fire_vase_developmental_morphology/citation_audit_2026-07-22.md`
  documenting which citations were verified, which claims they support, where
  better citations were needed, and what remains as a pre-submission caveat.
- Updated `scripts/fire_vase_science_manuscript_pdf.py` with direct citations
  for MODIS burned-area mapping, human-started fires, morphospace/geometric
  morphometrics, PCA, farthest-point/k-center representative selection, and
  bootstrap resampling. The reference list now includes 17 entries with DOIs
  where available.
- Rebuilt `output/pdf/fire_vase_developmental_morphology_manuscript.pdf`,
  rendered it to PNG with Poppler, checked the reference pages for layout, and
  shortened the final Methods paragraph to remove an orphan sentence before
  References.
- Validation: compiled the manuscript PDF generator, rebuilt the manuscript
  PDF, ran `.venv/bin/python -m pytest tests/test_fire_vase_lakehouse.py -q`
  with 16 passing tests, and confirmed the staged repository size policy check
  passes.

## 2026-07-22 - Comprehensive Fire VASE climate rebuild and manuscript refresh

- User goal: rebuild the VASE database and manuscript so the analysis uses the expanded gridMET variables and no longer presents the climate revision as a four-variable product.
- Data decision: cached 22 years each for 15 gridMET variables (`tmmx`, `tmmn`, `vpd`, `vs`, `pr`, `rmax`, `rmin`, `sph`, `fm100`, `fm1000`, `erc`, `bi`, `etr`, `pet`, `srad`) and rebuilt `scratch/fire_vase_run_full/tables/vase_slices.parquet` with all 15 columns retained.
- Perimeter decision: attempted the full 278,569-fire perimeter/active/extension build and a 5,000-fire build, but the current per-zone/per-variable raster extractor is too slow at those scales. Replaced the old pilot with a real 100-fire, 1,095-row, 15-variable perimeter exposure table and documented that full-catalog perimeter attribution needs optimization.
- Created updated analysis reports under `analysis/`, refreshed figures under `figures/climate_revision_main/` and `figures/climate_revision_supplement/`, revised `docs/manuscripts/fire_vase_developmental_morphology/manuscript_climate_revision.md`, and rebuilt `output/pdf/fire_vase_climate_revision_manuscript.pdf`.
- Validation: compiled changed scripts, rebuilt the comprehensive centroid table, verified climate columns/non-null counts, generated reports/figures/PDF with `scripts/fire_vase_climate_revision.py`, rendered the PDF to PNG with Poppler, and visually checked representative text and figure pages.
- Caveats: centroid climate is population-wide; perimeter exposure is expanded but still sampled. True local-normal anomalies, complete active-edge/perimeter attribution, topography, vegetation, suppression, ignition cause, wind direction, and gust products remain future work.

## 2026-07-22 - Science-style climate revision manuscript vetting

- User goal: make the climate-revision manuscript coherent with the five-figure
  narrative, verify citations, improve the scholarly language, check Science
  author-guideline alignment, and deliver a fresh formatted PDF.
- Manuscript decision: rewrote
  `docs/manuscripts/fire_vase_developmental_morphology/manuscript_climate_revision_science_style.md`
  around the figure sequence: life histories, continuous developmental
  gradients, climate redistribution, state dependence, and the limits of
  centroid climate explanation.
- Citation decision: replaced older, loosely connected references with a
  13-reference numbered list tied to the claims actually made in the text:
  climate-fire motivation, MODIS/FIRED/gridMET provenance, morphometrics,
  functional data analysis, PCA, human ignition context, and spatially explicit
  daily fire progression.
- Figure decision: removed embedded storyboard headers/takeaway boxes from the
  main climate figures, moved explanatory detail into comprehensive figure
  legends, promoted panel labels to uppercase, and revised Figure 3 panel E so
  category labels remain readable in the PDF.
- Created
  `docs/manuscripts/fire_vase_developmental_morphology/climate_revision_science_citation_audit_2026-07-22.md`
  and
  `docs/manuscripts/fire_vase_developmental_morphology/climate_revision_science_compliance_2026-07-22.md`.
- Output: rebuilt
  `output/pdf/fire_vase_climate_revision_science_style_manuscript.pdf`, a
  13-page, U.S. letter, single-column, double-spaced, line-numbered
  Science-style draft with figures grouped after the text.
- Validation: compiled `scripts/fire_vase_climate_revision.py`, regenerated the
  manuscript/figures/PDF, rendered the final PDF to 13 PNG pages with Poppler,
  checked title/text/figure pages for layout issues, verified title length
  (61 characters), one-sentence summary length (98 characters), abstract length
  (118 words), and confirmed all 13 references are cited and all citations
  resolve.
- Caveats: live Science instruction pages were attempted but not retrievable
  from the local browsing tool; compliance was checked against accessible
  Science-format guidance and must be confirmed in the submission portal.
  Author, affiliation, funding, contribution, and repository-archive metadata
  remain placeholders.

## 2026-07-22 - Climate revision round-two formal review and edits

- User goal: run another editor-referred review round with three independent
  reviewers and incorporate their feedback into the manuscript.
- Added
  `docs/manuscripts/fire_vase_developmental_morphology/formal_reviews_climate_revision_round_2.md`
  with an editor decision letter and three reviews focused on fire/climate
  attribution, statistical interpretation, and Science-reader narrative.
- Revised `scripts/fire_vase_climate_revision.py` so regenerated manuscript
  text and figure legends distinguish the developmental representation from
  the bounded centroid-climate projection, clarify that expanded climate
  variables can remain scientifically important even when they do not improve
  blocked linear prediction, and describe state models as leakage-safe,
  partly autoregressive associational baselines rather than causal mechanisms.
- Rebuilt
  `docs/manuscripts/fire_vase_developmental_morphology/manuscript_climate_revision_science_style.md`,
  `figures/climate_revision_main/figure_legends.md`, and
  `output/pdf/fire_vase_climate_revision_science_style_manuscript.pdf`.
- Validation: compiled `scripts/fire_vase_climate_revision.py`, regenerated
  the manuscript/figures/PDF, rendered the PDF to 13 PNG pages with Poppler,
  visually checked revised text and Figure 3 pages, confirmed the abstract is
  117 words, title is 61 characters, one-sentence summary is 98 characters,
  and all 13 references remain cited with no missing or uncited references.

## 2026-07-22 - Climate revision round-three optimization review

- User goal: repeat the three-reviewer/editor workflow with an emphasis on
  self-improvement, story quality, claim support, and making the manuscript
  feel solid enough to cite.
- Added
  `docs/manuscripts/fire_vase_developmental_morphology/formal_reviews_climate_revision_round_3.md`
  with an editor letter and three reviews focused on conceptual story,
  statistical guardrails, and citation-worthiness.
- Revised `scripts/fire_vase_climate_revision.py` and regenerated the
  manuscript so "developmental opportunity" is defined as the distribution of
  growth histories made more or less likely under conditions, the modest
  blocked R2 is explicitly framed as a limit on deterministic prediction
  rather than a rejection of the distributional claim, and the state model is
  described as conditional near-term interpretation rather than mechanism.
- Added three references supporting the final landscape-control claims:
  Parisien and Moritz 2009, Holsinger et al. 2016, and Povak et al. 2018.
  Updated the citation audit accordingly.
- Rebuilt
  `output/pdf/fire_vase_climate_revision_science_style_manuscript.pdf`.
  The PDF is now 14 pages because the reference list expanded from 13 to 16
  entries.
- Validation: compiled `scripts/fire_vase_climate_revision.py`, regenerated
  outputs, rendered the PDF to 14 PNG pages with Poppler, visually checked the
  abstract/text/reference/Figure 3 pages, confirmed the abstract is 121 words,
  title is 61 characters, one-sentence summary is 98 characters, and all 16
  references are cited with no missing or uncited references.

## 2026-07-22 - AI transparency statement

- User goal: review the prompt log and write an AI transparency statement that
  credits AI assistance accurately.
- Added
  `docs/manuscripts/fire_vase_developmental_morphology/ai_transparency_statement.md`
  with a manuscript-ready statement, prompt-log-derived inventory of AI-assisted
  work, and responsibility boundary.
- Updated `scripts/fire_vase_climate_revision.py` so the generated
  Science-style climate revision manuscript includes an AI transparency
  paragraph in the acknowledgments/back matter.

## 2026-07-22 - GitHub Actions cleanup for updating-figures checks

- User goal: address failing GitHub Actions screenshots for repository size and
  Python 3.9 tests on the updating-figures run.
- Untracked previously committed generated artifacts under blocked
  repository-policy paths (`artifacts/` and `tmp/pdfs/`) while leaving the
  local files on disk; `scripts/check_repository_size.py --mode tracked` now
  passes.
- Fixed a Python 3.9 import-time type-alias failure in
  `src/cubedynamics/plotting/tail_association.py` by replacing PEP 604
  module-level type aliases with `typing.Optional`/`typing.Union`.
- Validation: reproduced the Python 3.9 failure with `uv run --python 3.9`,
  reran the offline suite successfully (`297 passed, 5 skipped, 8 deselected`),
  verified the package import under Python 3.9, and reran the repository-size
  check successfully.

## 2026-07-22 - Google Docs-ready manuscript DOCX

- User goal: provide the current Fire VASE climate-revision manuscript in DOCX
  form suitable for uploading/importing into Google Docs.
- Added `scripts/build_fire_vase_google_docs_docx.py`, which builds a
  Google-Docs-style manuscript DOCX from
  `manuscript_climate_revision_science_style.md`, the climate-revision figure
  PNGs, and the comprehensive figure legends.
- Generated
  `output/docx/fire_vase_climate_revision_google_docs_sanitized.docx`.
- Validation: ran the Google Docs title sanitizer and check, rendered the DOCX
  to 13 page PNGs plus an internal QA PDF with the document renderer, and
  visually checked the title page, back matter, dense Figure 3 page, caption
  continuation page, and final figure page.

## 2026-07-22 - Morphospace figure story refinement

- User goal: restore the visual story where VASE shapes are laid over the
  morphospace and the morphospace itself is colored by climate variables to
  show which climate dimensions align with which developmental forms.
- Updated `scripts/fire_vase_climate_revision.py` so Figure 2 overlays
  representative VASE glyphs within the population morphospace with
  non-overlapping callouts, making shape transitions across VASE axes visible.
- Updated Figure 3 so panels A-D show the same VASE morphospace colored by
  event-mean maximum temperature, VPD, 1000-hour fuel moisture, and wind speed,
  with simplified facet labeling and tighter colorbar spacing.
- Regenerated `figures/climate_revision_main/Figure_2_climate_revision.png`,
  `figures/climate_revision_main/Figure_3_climate_revision.png`,
  `output/pdf/fire_vase_climate_revision_science_style_manuscript.pdf`, and
  `output/docx/fire_vase_climate_revision_google_docs_sanitized.docx`.
- Validation: compiled `scripts/fire_vase_climate_revision.py`, rebuilt the
  full climate-revision figure/manuscript package, ran the Google Docs title
  sanitizer/check, rendered the DOCX to 13 page PNGs plus an internal QA PDF,
  and visually checked Figure 2 on page 9 and Figure 3/caption continuation on
  pages 10-11.

## 2026-07-22 - Science-style figure legends and numbering

- User goal: revise the figure and figure legends so figure numbers/titles are
  not part of the image artwork and the legends tell the full scientific story
  of each figure.
- Updated `scripts/fire_vase_climate_revision.py` so panel labels use
  lowercase `(a)`, `(b)`, etc., and rewrote all five generated main figure
  legends to begin with `Fig. N. Title.` followed by self-contained guidance on
  what is plotted, how to read it, and the science message.
- Updated both manuscript builders so the figure number/title is emitted as
  the first sentence of the figure legend rather than as a separate heading
  above the figure image.
- Regenerated `figures/climate_revision_main/figure_legends.md`,
  `output/pdf/fire_vase_climate_revision_science_style_manuscript.pdf`, and
  `output/docx/fire_vase_climate_revision_google_docs_sanitized.docx`.
- Validation: compiled the figure/PDF and DOCX builder scripts, rebuilt the
  figure/manuscript package, sanitized and rendered the DOCX, rendered the PDF
  with Poppler, visually checked the Figure 2 and Figure 3 pages in both DOCX
  and PDF outputs, and confirmed by `pdftotext` that the PDF legends begin with
  `Fig. 2.` and `Fig. 3.` rather than standalone figure headings.

## 2026-07-23 - Final Citation Check

- User goal: perform one last citation check, verify current references and
  uses, and add any missing citations only if needed.
- Audited
  `docs/manuscripts/fire_vase_developmental_morphology/manuscript_climate_revision_science_style.md`;
  all 16 references are cited, no cited number is missing, no reference is
  uncited, and the abstract has no citations.
- Verified the current references against external DOI, publisher, and
  bibliographic records, then checked claim fit by citation group.
- Added
  `docs/manuscripts/fire_vase_developmental_morphology/final_citation_check_2026-07-23.md`.
- No new main-text citations were added; the remaining pre-submission citation
  item is the final code/data archival DOI or accession, with optional
  supplementary-method citations for ridge regression, blocked validation, or
  software if those details are expanded.

## 2026-07-23 - Fire VASE Workflow Documentation and Website Update

- User goal: write up the Fire VASE manuscript/analysis work, document the
  code, and update the website to reflect the current real-data workflow.
- Added `docs/workflows/fire_vase_developmental_morphology.md` documenting the
  population-scale FIRED run, centroid and perimeter climate tables,
  developmental morphospace products, rebuild commands, figure narrative,
  validation checks, and current limitations.
- Updated MkDocs navigation, `docs/workflows/fire_analysis.md`,
  `docs/capabilities/fire-vase.md`, `docs/dev/fire_vase_lakehouse.md`, and
  `README.md` so users and developers can find the manuscript-scale Fire VASE
  pipeline.
- Expanded docstrings in the main Fire VASE manuscript, morphology atlas,
  perimeter climate, and Google Docs DOCX builder scripts to describe their
  role in the source-table-to-rendered-asset workflow.
- Validation: compiled the touched Python scripts, checked MkDocs nav targets,
  and checked local markdown links in the updated Fire VASE docs. Full
  `mkdocs build --strict` was not run because MkDocs is not installed in the
  current `.venv`.

## 2026-08-12 - Publication audit, grammar-first organization, and vignettes

- User goal: audit and clean up the repository for publication, make the core
  grammar visibly distinct from add-on projects that create custom verbs, and
  add reproducible website vignettes with runnable Jupyter notebooks.
- Audited the tracked tree, runtime/public API, MkDocs navigation, documentation
  duplication, notebook metadata/execution state, package dependencies, CI, and
  generated artifacts. Recorded findings and a compatibility-preserving phased
  extraction/archive plan in `docs/project/publication_plan.md`.
- Key measured finding: 203 tracked files and 104.71 MiB were under `output/`,
  `outputs/`, and `figures/`, compared with 0.66 MiB of runtime source. These
  Fire VASE research products were not deleted because they should first be
  archived with checksums and a DOI.
- Reorganized MkDocs around Core Grammar, Vignettes, Extend the Grammar,
  Integrations, Projects Built With It, and publication/reference sections.
  Corrected mkdocstrings discovery from the legacy `code/` mirror to runtime
  `src/`.
- Added core-versus-project ownership guidance, a custom-verb authoring guide,
  a project overview, a tested `examples/custom_verb_project/` scaffold, and
  clarified the same boundary in package docstrings, the README, public API,
  scope, and contributing docs.
- Replaced canonical examples of nonexistent prospective verbs such as
  `v.aggregate()` and `v.detrend()` with current exported APIs, and rewrote the
  old textbook verb page to distinguish current vocabulary from proposals.
- Added three deterministic offline notebooks under `docs/vignettes/` covering
  grammar basics, a project-owned custom verb, and Dask-backed lazy composition.
  Added a deterministic notebook builder, a temporary-copy execution runner,
  `vignettes` dependencies, Makefile support, and CI execution. Labeled the
  top-level `notebooks/` collection as exploratory.
- Removed seven orphaned generated/cache files from the repository root and
  `.cache`, and added ignore rules for viewer scratch HTML/PNG and MkDocs cache.
- Validation: focused tests passed (`7 passed`); the full offline suite passed
  with a noninteractive Matplotlib backend (`299 passed, 5 skipped, 8
  deselected`); all three supported notebooks executed offline; `mkdocs build
  --strict` succeeded and rendered each notebook as HTML plus a downloadable
  `.ipynb`; `uv.lock` was refreshed for the new extras.

## 2026-08-12 - Editorial website redesign

- User goal: replace the conventional documentation-style homepage with a
  more distinctive science-media presentation inspired by Impact Media Lab.
- Rebuilt `docs/index.md` as an editorial landing page with an oversized
  grammar-first statement, a visual pipe/verb composition, runnable-vignette
  stories, an explicit core/integration/project layer model, and direct calls
  to action.
- Added `docs/stylesheets/editorial.css` with a warm-paper and black visual
  system, acid-lime and coral accents, responsive story cards, CSS-native cube
  artwork, accessible focus states, reduced-motion behavior, and a quieter
  restyle for the surrounding Material documentation shell.
- Updated `mkdocs.yml` with persistent section tabs, the compact CubeDynamics
  mark, refreshed publication metadata, and the editorial stylesheet. Updated
  the browser theme color in the custom head partial.
- Used the reference site's editorial traits as design direction without
  copying its brand, text, or image assets; the landing page reuses existing
  CubeDynamics scientific figures.
- Validation: checked the homepage structure and image/link attributes,
  confirmed the generated homepage loads the new stylesheet and content, ran
  `git diff --check`, and completed a clean `mkdocs build --strict`.

## 2026-08-12 - Academic refinement of the website

- User goal: retain the improved website structure while making the design
  less playful and more appropriate for an academic research project.
- Reframed the homepage around transparent methods, reproducibility,
  computational scaling, research extensions, and the boundary between the
  stable framework and project-specific science.
- Replaced the high-saturation palette, oversized display typography,
  rotations, hard offset shadows, decorative orbits, and animated card
  treatments with a restrained navy, warm-paper, muted-teal, and rust system;
  serif research-publication headings; fine rules; and quieter interactions.
- Preserved the full-width landing-page structure, runnable vignettes,
  scientific figures, responsive behavior, and direct routes into the core
  grammar and custom-verb documentation.
- Validation: checked HTML structure and accessibility attributes, checked CSS
  delimiter balance, ran `git diff --check`, and completed a clean strict
  documentation build.

## 2026-08-12 - Logo-derived website details

- User goal: add a small amount of visual playfulness based on the
  CubeDynamics logo without losing the academic research direction.
- Added a compact logo signet to the hero, subtle layered data-cube marks at
  selected section edges, and a quiet raster/layer pattern behind the grammar
  vignette graphic. All additions use the logo's green, teal, and yellow-green
  cues within the site's muted palette.
- Kept the motifs decorative, noninteractive, hidden from assistive
  technologies, responsive at small widths, and secondary to the research
  content.
- Validation: checked HTML structure and decorative-image accessibility,
  checked CSS delimiter balance, ran `git diff --check`, and completed a clean
  strict documentation build.

## 2026-08-12 - Interactive hero data cube

- User goal: replace the static hero image with a memorable cube that visitors
  can manipulate and that responds to page scrolling.
- Replaced the hero's flat cube/verb diagram with a dependency-free CSS 3D
  spatiotemporal cube whose raster grids, translucent internal slices, and
  green/yellow layering derive from the CubeDynamics logo.
- Added pointer and touch dragging, scroll-linked rotation, arrow-key and Home
  controls, a reset button, focus styling, interaction instructions, and an
  assistive-technology status announcement. Scroll-linked movement is disabled
  when the visitor requests reduced motion; direct manipulation remains
  available.
- Added `docs/javascripts/interactive-cube.js` through the MkDocs JavaScript
  configuration and kept initialization compatible with ordinary loads and
  Material-style document navigation.
- Validation: checked JavaScript syntax, homepage structure and control
  attributes, CSS delimiter balance, generated asset references, ran
  `git diff --check`, and completed a clean strict documentation build.

## 2026-08-12 - Repo-native HTML cube hero and full equation mark

- User correction: the hero should use one of the repository's actual custom
  HTML cube viewers, not a new CSS object derived from the cube portion of the
  logo; the site header should also show the complete cube equation.
- Replaced the bespoke hero cube with an iframe embedding the existing,
  self-contained `docs/assets/figures/synchrony_occurrence_cube.html`. The
  artifact uses the canonical CubeDynamics HTML/CSS/JS viewer, real
  longitude/latitude/time axes, pointer rotation, and wheel zoom.
- Removed the temporary custom cube JavaScript and its MkDocs registration,
  and removed the now-unused CSS 3D implementation.
- Changed the MkDocs header mark from the square favicon to
  `cubedynamics_banner.png`, which shows the full cube-plus-grammar-to-result
  equation, while retaining the square cube image as the browser favicon.
- Validation: checked the embedded viewer source and interaction handlers,
  verified the iframe title and direct-viewer link, checked the rendered logo
  and script references, ran the focused viewer interaction/rotation tests
  (`4 passed`), ran `git diff --check`, and completed a clean strict
  documentation build.

## 2026-08-12 - Site analytics and search discoverability

- User goal: track documentation-site usage using the Google tooling already
  present in related repositories and improve technical SEO.
- Audited sibling CU-ESIIL sites and found that `analytics-library` and
  `data-library` use distinct GA4 measurement IDs but share one Search Console
  HTML verification file. Kept the analytics streams separate and reused only
  the organization verification file.
- Added optional GA4 loading controlled by the GitHub Actions repository
  variable `CUBEDYNAMICS_GA_MEASUREMENT_ID`. No analytics request is emitted
  when the variable is unset, and the tag disables Google Signals and ad
  personalization signals.
- Added Search Console verification, `robots.txt`, a discoverable generated
  sitemap, page-aware Open Graph and Twitter metadata, canonical URLs,
  homepage `SoftwareSourceCode` structured data, and a focused homepage search
  description. Documented setup, monitoring, privacy boundaries, and official
  Google references in `docs/project/site_analytics_seo.md`.
- Validation: ran `git diff --check`; completed clean strict MkDocs builds with
  and without a test measurement ID; confirmed the unconfigured build contains
  no Google tag, the configured build injects the supplied ID and privacy
  settings, metadata is page-aware, and the verification, robots, and sitemap
  files are present. Analytics remains inactive until a new CubeDynamics GA4
  stream is created and its measurement ID is set in GitHub.

## 2026-08-14 - Accessible code-block contrast

- User goal: make code chunks easier to read after the website redesign left
  gray code text on a nearly black background.
- Corrected the inherited-color conflict in `docs/stylesheets/editorial.css`.
  Light mode now uses an off-white code surface with dark navy text; dark mode
  uses a deep teal surface with explicit near-white text and accessible syntax
  colors. Generated Jupyter notebook inputs use the light, high-contrast code
  surface in either site theme so their embedded syntax palette remains clear.
- Validation: measured base foreground/background contrast at 13.12:1 in light
  mode and 16.13:1 in dark mode, ran `git diff --check`, and completed a clean
  strict MkDocs build including all three vignettes.
- Follow-up: the global light-mode code foreground also reached the homepage's
  intentionally dark “Readable workflows” panel, making the unhighlighted
  `pipe(cube)` expression dark on dark. Scoped an explicit near-white code
  foreground to that component so its plain text and syntax spans remain
  readable independently of the site-wide code palette.

## 2026-08-24 - Visual hackathon notebook lab

- User goal: prepare strong educational resources for a hackathon, with
  independent Jupyter notebooks demonstrating several ways to create or enter
  cubes, a broad range of verbs, working sample code, and a plot showing every
  workflow's result.
- Expanded the supported vignette collection from three to eight offline,
  deterministic notebooks. The learning path now covers cubes from NumPy
  arrays, tidy pandas tables, and multi-variable xarray Datasets; direct and
  piped verb calls; core statistical, generic, and shape-changing verbs;
  threshold states, event detection, and occurrence synchrony; project-owned
  custom verbs; and Dask-backed lazy computation.
- Made the collection hackathon-ready with numbered website navigation,
  45-minute, 90-minute, and open-build facilitation routes, local execution
  instructions, downloadable notebook sources, and a homepage/README entry
  point. Enabled notebook execution during documentation rendering so the
  published pages include their generated figures.
- Added notebook metadata and runner guardrails requiring each supported
  vignette to remain offline and emit a portable PNG or SVG plot. Added focused
  catalog tests covering the eight notebooks, metadata, plotting source, and
  documentation links. The interactive cube example uses inline viewer HTML so
  documentation builds do not leave randomly named helper files in the source
  tree.
- Validation: all eight notebooks executed successfully offline and passed the
  plot-output requirement; 13 focused catalog, pipe, statistics, and shape tests
  passed; `git diff --check` passed; and a clean strict MkDocs build executed and
  rendered all eight notebooks with figures and downloadable `.ipynb` files.
- Follow-up: added inline teaching comments throughout every notebook code cell.
  The annotations explain coordinate and broadcasting choices, cube contracts,
  direct versus piped calls, reducer and transform shapes, Dataset variable
  selection, state/event/synchrony semantics, custom verb factories, plotting
  comparisons, Dask chunks, and the explicit compute boundary. Each notebook
  now contains 7–12 comment lines focused on intent and expected outputs.
- Follow-up validation: all eight annotated notebooks again executed offline and
  emitted their required plots, and the clean strict documentation build
  rendered all annotated code and figures successfully.
- Header follow-up: corrected malformed output on the cube-from-arrays page.
  The interactive viewer had been inserted as a complete nested HTML document,
  allowing its `<head>`, `<body>`, and styles to interfere with the MkDocs page.
  The notebook now escapes that document into an isolated, titled, sandboxed
  iframe `srcdoc`, retaining manipulation without a helper file or DOM leakage.

## 2026-08-24 - Narrative vignette learning path

- User goal: present the educational material as a durable vignette section,
  organize it around users and analysis stories, and make the minimalist pipe
  the most visible expression of each method.
- Replaced event-specific framing with a publication-facing learning path that
  routes readers by the data they have and the question they want to answer.
  Added restrained vignette-specific styling and updated the homepage, README,
  site navigation, and lesson titles to use the same narrative language.
- Reworked all eight generated notebooks around a consistent sequence:
  context, concrete question, analysis story, compact pipe, figure, scientific
  interpretation, and a next variation. Data setup, analytical composition,
  and plotting now occupy separate cells so realistic preparation does not
  obscure the small CubeDynamics grammar.
- Changed the array and tidy-table lessons to use the pipe explicitly, retained
  inline comments around data contracts and non-obvious implementation choices,
  and preserved the isolated interactive HTML cube. Added tests requiring the
  narrative lesson structure, pipe use, complete catalog, offline metadata,
  plot source, and event-neutral wording.
- Validation: all eight notebooks executed successfully offline and emitted
  their required plots; 15 focused vignette, pipe, statistics, and shape tests
  passed; `git diff --check` passed; and a clean strict MkDocs build executed
  and rendered all eight lessons, figures, downloads, navigation labels, and
  the new vignette stylesheet.

## 2026-08-25 - CI plot-output backend fix

- User-reported failure: the GitHub Actions vignette runner executed the first
  notebook but found no portable static plot output.
- Root cause: the workflow globally sets `MPLBACKEND=Agg` for headless tests.
  Agg can draw figures but does not publish them into Jupyter output cells, so
  the vignette runner's PNG/SVG contract correctly failed.
- Updated `scripts/run_vignettes.py` to select Matplotlib's Jupyter inline
  backend explicitly for its temporary kernel environment, overriding Agg only
  for publication notebook execution. The documentation build step now uses
  the same inline backend so its rendered pages retain notebook figures.
- Added a catalog guardrail requiring the runner's backend override. Preserved
  the workflow's Agg default for ordinary unit and integration tests.
- Validation: reproduced the original failure locally with `MPLBACKEND=Agg`;
  reran that exact environment after the fix and all eight vignettes passed
  their plot-output checks; six catalog tests passed; `git diff --check`
  passed; and the strict documentation build succeeded with the corrected
  inline backend.

## 2026-08-25 - Real-data publication QA and cube-face validation

- User goal: replace generated vignette measurements with vetted real data,
  repair visibly incorrect cube sides, and publish an evidence-oriented QA
  pipeline modeled on the Fire VASE validation site.
- Rebuilt all eight narrative vignettes around one offline PRISM AN91d daily
  4 km observational extract for the Boulder region, 1–30 January 2024. Added
  a checked-in NetCDF, a provenance record with URL/byte/SHA-256 evidence for
  60 official daily archives, and a reproducible builder with an explicit
  `--download-missing` acquisition mode. No supported vignette generates
  measurement values or uses random data.
- Diagnosed the side-face defect in the canonical HTML viewer. Rectangular
  space-time textures used CSS `background-size: cover`, which cropped source
  pixels, and the right/bottom time axes did not account for their opposite CSS
  rotations. The viewer now fits complete textures, orients all six faces to
  the newest-front/oldest-back contract, and applies the same mapping to VASE
  masks. Focused tests verify unique faces and exact source-array orientation.
- Added `scripts/run_validation.py` with real-data, grammar, cube/HTML,
  vignette, and expected-failure modules. Each writes JSON and PNG evidence;
  the suite writes a manifest and collated PDF. Cube QA extracts the actual
  base64 PNGs from rendered HTML and requires exact RGBA equality for every
  pixel. Six contrast controls cover reversals, transposition, duplication,
  and texture cropping.
- Published validation overview, data, cube, contrast, and methods pages plus
  reviewed evidence assets. CI now runs the full suite with all notebooks and
  uploads its artifacts. The vignette index links the provenance and validation
  contract directly. Removed older generated Fire VASE and synchrony examples
  from the primary publication routes; the gate now checks those route pages so
  generated examples cannot silently reappear. Exact generated truth cases are
  retained only as software tests and explicit negative controls. Replaced the
  homepage hero with a separately rebuildable interactive cube generated from
  the same reviewed PRISM fixture, replaced generated homepage thumbnails with
  validation figures, and excluded historical generated recipes/assets from
  MkDocs output.
- Validation: the five-module suite passed, all eight notebooks executed and
  emitted plots, 16 focused tests passed, and `mkdocs build --strict` executed
  every notebook successfully. Browser QA confirmed the validation overview,
  decoded-face report, and repaired interactive PRISM cube render correctly.
  The broader offline pytest run reached 277 passed / 3 skipped with no failure
  before an unrelated long-running Matplotlib test was manually interrupted;
  a subsequent affected-area batch added 38 passed / 2 skipped before the same
  environment-specific stall.

## 2026-08-25 - Phase 1 scientific noun and source-flavor architecture

### User goal

- Expand CubeDynamics toward a broad environmental noun vocabulary while
  preserving `pipe(noun) | verb()` as the product center.
- Begin with a controlled Phase 1 that rationalizes gridMET, PRISM, and
  Sentinel-2, keeps backends below the public API, preserves rich provenance,
  stays streaming-first, and never silently substitutes generated data.

### Implementation

- Added `cubedynamics.data` noun functions for temperature, precipitation,
  VPD, wind, humidity, radiation, surface reflectance, and vegetation index.
  Added `sources`, `describe`, and `list_sources`; the catalog contains only
  integrations implemented now.
- Normalized provider variable names at the noun boundary while recording the
  original fields, provider/product/version, query, CRS, resolutions, backend,
  retrieval time, normalization, and raw/normalized/derived state. Existing
  provider-specific loaders and top-level compatibility helpers remain public.
- Found and removed a critical gridMET defect: both purported real backends
  generated random values and labeled them as real. The default now reads the
  authoritative annual NetCDF product. Explicit low-level synthetic opt-in is
  retained only for tests/demos and is categorically rejected by noun loaders.
- Added standardized Sentinel-2 provenance without materializing lazy arrays.
- Added offline noun, discovery, provenance, laziness, public API, gridMET, and
  source-QA tests. Updated the stale Fire VASE documentation assertion to check
  the reviewed real-data example instead of the excluded generated panel.
- Added a reproducible Phase 1 source-QA workflow and reviewed PRISM map/time
  series evidence with checksum, source, CRS, time, finite-value, physical
  range, temperature-order, and bounds checks. The manifest deliberately marks
  gridMET and Sentinel-2 real visual/numerical QA as pending.
- Reorganized the public site with a Scientific Data section, noun/source
  comparison pages, provenance and limitation guidance, a QA status page, and
  a phased data-vocabulary audit/plan. Corrected gridMET VPD units and removed
  an unrelated MODIS citation from the Sentinel-2 page.

### Validation

- 64 affected-area tests passed with 2 network-marked skips; the focused
  source-QA/publication follow-up passed after aligning the stale documentation
  test.
- `mkdocs build --strict` passed and rendered all eight observational-data
  vignettes plus the new noun and QA pages.
- A bounded live PRISM NcSS integration test passed when run with network
  access; the initial sandboxed attempt failed only at DNS resolution.
- The full offline suite reached 293 passed / 3 skipped / 8 deselected. One
  stale, unrelated documentation assertion failed and was corrected; the run
  then encountered the repository's pre-existing end-of-suite Matplotlib stall
  and was interrupted after approximately 100 seconds.
- The new/changed data library files contain no `.compute()`, `.to_netcdf()`,
  or `.to_zarr()` calls, and `git diff --check` passes.

### Known limitations and next phase

- Phase 1 architecture is implemented, but source QA is not called complete:
  gridMET still retrieves annual files before client-side AOI selection, and
  gridMET/Sentinel-2 need reviewed checksum-controlled real fixtures and QA
  figures. Finish those items before Phase 2.
- Recommended next source after closing Phase 1 QA is Daymet, followed by
  ERA5-Land, ERA5, and TerraClimate only as each meets the full source gate.

## 2026-08-25 - South Dakota environmental Decision Lab

### User goal

- Add a second-layer vignette collection for realistic South Dakota
  environmental decisions, centered on readable `pipe(noun) | verb()`
  analytical sentences rather than function-by-function tutorials.
- Use observed, vetted data; show source QA before decision views; provide
  reproducible notebooks and validation; never fabricate unavailable nouns or
  overstate overlap as causation, impact, or risk.

### Audit and design decisions

- Audited the public noun catalog, verb namespace, vignette builder/runner,
  MkDocs execution path, publication tests, and navigation. Climate/weather
  and Sentinel-2 nouns are public, but buildings, roads, fire history, mining
  claims, protected areas, surface water/hydrography, cropland/land cover,
  critical habitat, and population are not. General vector intersection,
  categorical change, proximity/density, cross-grid alignment, and transparent
  grouped summary contracts are also absent.
- Published four requested analyses as clearly labeled dependency designs
  rather than runnable calls to nonexistent APIs: Black Hills, Missouri &
  Watersheds, Habitat Squeeze, and Communities. Each records the decision,
  missing information, noun requirements, target grammar, QA publication gate,
  interpretation limits, and short forks. No computed result or fake map is
  shown.
- Added an API-current wildcard hackathon template requiring three public
  nouns, two noun families, visible QA, a decision figure, reproducibility, and
  explicit limitations. It demonstrates only current APIs and warns that
  Sentinel-2/climate grids require explicit scientific alignment.

### Executable observed-data vignette

- Added one fully executable Working Lands climate-screening notebook for a
  bounded central South Dakota window southwest of Pierre, 1–31 July 2024. It
  uses observed daily PRISM maximum temperature and precipitation acquired
  through `data.temperature` and `data.precipitation`; it does not claim to
  identify working lands, drought, vegetation sensitivity, forage loss,
  economic impact, causation, or risk.
- Added a reproducible public-loader fixture builder, a 31 × 15 × 19 checked
  NetCDF, and a provenance record with exact query, source service,
  documentation, source-revision caveat, physical summaries, and SHA-256
  `f9f3f0da6c621383b60d4895e661a185d3d58e7393b4f339ee91d36d83228a6a`.
  The offline fixture is explicitly a small publication/QA extract, not a
  hidden backend.
- Added the general `v.overlap` verb for coincident truth in exactly aligned
  boolean/state rasters. It accepts state Dataset outputs, refuses silent
  coordinate alignment, and is documented as neither vector intersection nor
  a risk/causal operation. The notebook composes `quantile_state`,
  `threshold_state`, `overlap`, and `mean` into a short analytical sentence.
- The notebook contains an early two-time-series/two-map source QA figure and
  a separate final co-occurrence-frequency map. Inline comments explain data
  contracts, thresholds, alignment, and interpretation. Raw xarray echoes were
  replaced with compact summaries after rendered browser QA showed that the
  result array disrupted the narrative.

### Publication and validation

- Added a dedicated South Dakota Decision Lab navigation section, landing-page
  status cards, restrained academic styling, a collection validation report,
  and a link from the foundational vignette learning path. The validation page
  is the source of truth for executable/design status, observed fixture
  evidence, acceptance checks, missing nouns, and missing reusable verbs.
- Extended the notebook runner to include both vignette collections by default
  and to enforce a metadata-defined minimum static-plot count; the decision
  notebook requires two plots. Added a Decision Lab QA script that writes JSON,
  source-QA PNG, and decision-view PNG evidence and compares the pipe result
  exactly with direct boolean logic. CI runs and uploads this evidence.
- Added tests for strict aligned-state behavior, fixture/provenance/physics,
  narrative structure, link/nav presence, actual API existence, absence of
  pretend API calls, wildcard requirements, two plot outputs, CI integration,
  and an opt-in live PRISM smoke test.
- Validation: 11 focused tests passed; the live two-day public-loader smoke test
  passed; the decision QA and Phase 1 source QA scripts passed; all nine
  publication notebooks executed offline and emitted their required plots;
  and `mkdocs build --strict` executed/rendered every notebook successfully.
  Browser QA confirmed both result figures, a complete H1/section structure,
  academic dependency-page presentation, no broken images or horizontal page
  overflow, and readable dark code on a light background. `git diff --check`
  passed.
- The broader offline suite reported 305 passed, 3 skipped, and 9 deselected
  with no test failure before the repository's pre-existing end-of-suite
  Matplotlib shutdown stall; it was manually interrupted after 134 seconds.

### Prioritized next integrations

- Highest-value nouns for completing the decision designs are buildings,
  roads, fire history, protected areas/land management, mining claims, surface
  water/hydrography, cropland/land cover, critical habitat, and population.
- Highest-value reusable verbs are geometry-aware intersection, transparent
  grouped summary, categorical change, explicit proximity/density, and
  scientifically declared cross-grid alignment. Each must satisfy source,
  CRS, boundary, units, temporal-support, missingness, and QA contracts before
  a dependency design is promoted to executable.

## 2026-08-26 - Lightweight semantic grammar and analysis coach

### User goal

- Make the existing `pipe(noun) | verb() | verb()` grammar semantically
  inspectable and helpful to scientists and future agents without adding a DSL,
  rewriting user order, or requiring new user-facing object classes.
- Add noun and verb metadata, state tracking, deterministic explanations and
  suggestions, metadata-only validation, order knowledge, useful scientific
  errors, diagrams, tests, and readable grammatical keywords.

### Design and implementation

- Audited the pipe, 62 callable names visible in `cubedynamics.verbs`, 38
  explicit `verbs.__all__` exports, documented state/event/project verbs,
  loaders, output metadata, dimensions, provenance, and information-changing
  operations. Recorded the baseline in `docs/project/grammar_inventory.md`.
- Added `cubedynamics.grammar`, a lightweight registry and inference layer with
  nine semantic states: observation, continuous field, categorical field,
  condition, event, feature, relationship, summary, and network. Verb contracts
  declare human descriptions, accepted/returned states, requirements,
  preservation/removal effects, ownership categories, and examples.
- Registered every callable in `verbs.__all__` plus documented state, event,
  synchrony, and biology verbs. Conceptual future verbs are present only in
  order-rule metadata with `implemented=False`; they are never offered as
  runnable suggestions.
- Extended `Pipe` with immutable `semantic_state` and `semantic_trace`, plus
  deterministic `explain()`, `suggest()`, and `validate()` methods. Pipe still
  calls each stage exactly once in written left-to-right order. Plain,
  unregistered Python callables remain valid and need no subclass or registry
  step.
- Added semantic preflight errors for incompatible kinds, missing temporal or
  spatial support, removed time variation, unordered time, and obvious CRS or
  dimension conflicts for aligned-state overlap. Underlying execution errors
  remain unchanged outside known semantic incompatibilities.
- Added the four requested order categories and the complete starter response
  set, including both directions for near/density, intersect/density,
  intersect/summarize, clip/summarize, filter/change, subtract/divide,
  normalize/threshold, and upstream/intersect. Rules are neutral,
  deterministic, and do not mutate pipelines.
- Added semantic metadata to scientific nouns, state/event/overlap outputs, and
  spatial block summary/comparison outputs so metadata survives unwrap and
  re-pipe workflows. Added backward-compatible `over=` to `mean`, `variance`,
  `anomaly`, and `zscore`; `dim=` remains supported and conflicts are explicit.

### Documentation and validation

- Added `docs/concepts/semantic_grammar.md` with state and architecture
  diagrams, explain/suggest/validate examples, order categories, and a
  near→density versus density→near interpretation table. Updated Pipe, grammar,
  public API, README, and MkDocs navigation pages.
- Added `tests/test_grammar_semantics.py` for exact order/no rewriting, state
  transitions, explanations, suggestions, reports, semantic errors, lost
  information, all order rules, public verb registry coverage, CRS conflicts,
  metadata propagation, and keyword compatibility. Expanded noun metadata
  assertions and retained focused regression coverage for VirtualCube,
  synchrony, spatial-block, plotting, and public APIs.
- Final focused affected-area run: 84 passed. An additional post-stall group
  covering plotting, shape/statistical verbs, vignettes, and VirtualCube paths
  passed 21 tests. `mkdocs build --strict`, Python compilation, and
  `git diff --check` passed.
- The required offline suite reached 349 passed, 3 skipped, and 9 deselected
  with no failures, then encountered the repository's pre-existing Matplotlib
  backend stall and was interrupted after about 97 seconds. The six semantic
  compatibility regressions found on the first broad run were corrected; their
  complete affected suites subsequently passed.

### Known limitations and next work

- Runtime inference is strongest for xarray, VirtualCube, EventResult, and
  metadata-bearing project outputs. Custom non-xarray objects fall back to an
  observation state unless their project adds semantic attrs or registry
  metadata.
- Some broad project/integration contracts are intentionally conservative and
  should be refined alongside their owning workflows. Unit compatibility is
  reported and preserved, but cross-object unit conversion/reconciliation
  awaits verbs that actually combine numeric quantities.
- High-value next work is to let external verb packages contribute registry
  entries through a documented registration hook, then implement vetted
  feature/network nouns and verbs such as near, density, intersect, summarize,
  and upstream against explicit CRS, boundary, unit, and provenance contracts.

## 2026-08-26 - Interrupted-work audit and Phase 1 source-QA completion

### User goal

- Re-read the interrupted publication, Decision Lab, and semantic-grammar
  briefs and complete work left unfinished when earlier tasks hit usage limits.
- Keep examples observational, reproducible, validated, and suitable for the
  publication website.

### Audit and decisions

- Re-audited the three pasted briefs and the resulting repository changes. The
  semantic grammar is implemented and tested. The Decision Lab intentionally
  contains one executable real-data vignette and four clearly labeled
  dependency designs because the required feature/network nouns and verbs do
  not yet exist; no speculative APIs or fake data were promoted as runnable.
- Identified the remaining Phase 1 publication gap: gridMET and Sentinel-2 had
  no reviewed numerical/visual baseline, and their dataset pages referenced
  text files masquerading as PNG previews. PRISM also retained an obsolete
  placeholder despite already having reviewed QA evidence.

### Implementation

- Added small real-data gridMET and Sentinel-2 fixtures with checksums, source
  requests, and provenance under `tests/fixtures/real_data/`, plus a reproducibility
  README and `scripts/build_phase1_qa_fixtures.py`.
- Expanded `scripts/run_source_qa.py` to validate PRISM, gridMET maximum
  temperature, and Sentinel-2 B04/B08 plus derived NDVI. Checks cover checksum,
  source, CRS, dates, finite data, coordinate order and resolution, bounds,
  broad physical/scale limits, and source-specific invariants. It writes JSON,
  figures, and a consolidated manifest.
- Replaced gridMET, Sentinel-2, and PRISM placeholder previews with reviewed
  real-data QA figures and documented exact evidence and limitations.
- Removed older FIRED, Landsat, and fire-workflow text files masquerading as
  PNGs. Their pages now state the missing QA evidence explicitly instead of
  displaying or soliciting an unvalidated screenshot; the asset policy now
  prohibits synthetic or text image placeholders.
- Found duplicate Sentinel-2 catalog records for identical acquisitions. The
  loader now keeps the newest `s2:generation_time` record using STAC metadata
  only, preserving lazy imagery, and records the selection in output attrs.
- Corrected the Sentinel-2 citation from a stale MODIS reference to the
  Copernicus/ESA Level-2A product.

### Validation

- A bounded live Sentinel-2 request to the Planetary Computer passed and
  confirmed unique, strictly ordered acquisition times after deduplication.
- Offline source QA passed for all three source adapters, and the gridMET and
  Sentinel-2 figures were visually inspected for readable, plausible output.
- The combined affected-area suite passed 84 tests. A final focused
  deduplication/live request passed 2 tests; its only warning is an upstream
  Planetary Computer Pydantic deprecation.
- `scripts/run_decision_qa.py` passed. `scripts/run_vignettes.py` executed all
  nine supported notebooks offline and confirmed their static plot outputs.
- `mkdocs build --strict`, Python compilation, and `git diff --check` passed.

### Limitations

- The baselines validate the named variables, places, and time windows, not
  every product permutation. gridMET maximum temperature is representative of
  the adapter; Sentinel-2 pixel-level cloud masking is not yet implemented.
- gridMET still downloads annual files before local AOI selection. Live tests
  remain separate from deterministic offline fixture checks.

## 2026-08-26 - CI repository-policy and documentation recovery

### User goal

- Fix the tracked repository-size failure for publication NetCDF fixtures and
  the offline-suite failure caused by a missing prescribed-burn VASE panel
  section.

### Implementation

- Moved all four checked-in observational NetCDF baselines and their provenance
  records to `tests/fixtures/real_data/`, the policy-approved fixture location.
  This includes PRISM teaching, South Dakota Decision Lab, gridMET, and
  Sentinel-2 extracts. The real formats and checksums are preserved; the size
  policy was not weakened and extensions were not disguised.
- Updated QA runners, fixture builders, validation scripts, tests, documentation,
  notebook metadata, and notebook loading cells to use the canonical fixture
  directory. Regenerated all nine supported notebooks from their builders.
- Restored the “Prescribed-burn VASE panel example” with an observed FIRED plus
  per-event gridMET loader pattern. Retired synthetic sample output remains
  excluded from public learning routes.
- Set Matplotlib's noninteractive `Agg` backend in repository pytest setup so
  plotting side-effect verbs cannot enter a local GUI event loop during tests.

### Validation

- `python scripts/check_repository_size.py --mode tracked` passed for 887
  tracked files. The nine prospective files in the new fixture directory also
  pass the same policy before staging.
- The exact offline command passed: 383 tests passed, 5 skipped, and 9
  deselected.
- Source QA and Decision Lab QA passed. All nine supported notebooks executed
  offline with required plots, and `mkdocs build --strict` passed after a full
  notebook cache refresh.

### Clean-clone follow-up

- GitHub Actions revealed that the repository-wide `*.nc` ignore rule still
  excluded the four relocated payloads while allowing their JSON provenance
  records to be committed. Replaced obsolete exceptions for the former data
  paths with the narrow `!tests/fixtures/real_data/*.nc` exception. All four
  NetCDF files are now visible to Git and remain allowed by the independent
  repository-size policy.
- `python scripts/run_validation.py --run-vignettes` passed all five
  publication validation modules. The exact offline suite again passed with
  383 tests, 5 skipped, and 9 deselected; tracked-size policy, prospective
  four-file fixture policy, and `git diff --check` also passed.

## 2026-08-26 - Interactive homepage repair and five-hub website structure

### User goal

- Repair the observed-PRISM cube on the homepage so visitors can rotate it.
- Replace the crowded top navigation with five useful destinations: Home,
  Get Started, Vignettes, Library, and Documentation.
- Gather all lessons, stories, projects, and examples under Vignettes; make
  nouns, verbs, and extension patterns discoverable under Library; and keep the
  exhaustive technical material under Documentation.
- Apply one restrained Impact Media Lab-style gallery system and reduce the
  amount of work that blocks initial page display.

### Implementation

- Fixed the canonical HTML cube viewer so its transformed presentation layer
  cannot intercept pointer events intended for the drag surface. Rebuilt the
  checksum-verified PRISM homepage asset at a more legible embedded size and
  added a focused interaction regression test.
- Consolidated thirteen top-level navigation groups into five. Existing deep
  pages remain available under purpose-driven nested sections rather than
  competing as primary tabs.
- Rebuilt the Get Started and Vignettes landings and added Library and
  Documentation hubs. They share an academic editorial hero, responsive
  gallery cards, restrained cube-derived line decoration, and reduced-motion
  behavior. The Library now includes explicit, truthful guidance for project
  nouns as well as custom verbs.
- Deferred the homepage iframe until the hero enters the viewport and the
  browser is idle, while retaining an explicit load button and no-script link.
  Enabled instant navigation and navigation pruning, and marked below-fold
  homepage figures for lazy asynchronous decoding.

### Validation

- In-browser QA reproduced the original hit-testing failure, then confirmed a
  real drag changes the homepage cube's rotation variables after the fix.
  Browser checks also confirmed exactly five tabs and rendered all four hub
  pages with their expected gallery cards.
- The exact offline suite passed: 387 tests passed, 5 skipped, and 9 deselected.
- `mkdocs build --strict` passed with all nine supported notebooks, and
  targeted navigation, publication, Decision Lab, and viewer checks passed.

## 2026-08-26 - Source lifecycle and reusable QA milestone

### User goal

- Apply the repository-informed data-serving plan without creating a parallel
  registry, grammar, or CI system.
- Complete the first architecture milestone: snapshot/rolling source modes,
  immutable serving revisions, provider-native identity, schema fingerprints,
  separate revision validity and live health, explicit certification outcomes,
  additive noun provenance, and four reusable QA profiles.
- Preserve the existing real-data baselines and stop before broad source
  expansion unless Daymet remained a clearly small follow-up.

### Implementation

- Extended the existing noun/source catalog with lifecycle, endpoint, access,
  identity-strategy, serving-revision, QA-profile, revision-status, and
  live-health metadata. No second registry or loader grammar was added.
- Added typed lifecycle and certification models plus deterministic responses
  for content extension, snapshot release, schema/semantic/history changes,
  and service-health changes. Scientific revision validity remains independent
  of current endpoint health.
- Added versioned xarray schema normalization/fingerprinting over scientific
  structure without reading lazy array values. Added provenance fields to noun
  outputs while retaining existing source/query/normalization metadata.
- Added substantive `climate_continuous_daily`,
  `continuous_raster_static`, `feature_line`, and `station_timeseries` QA
  profiles. The existing source-QA runner now composes them with its checksum,
  source-specific science, and visual checks and emits structured offline
  certification evidence.
- Updated the checked PRISM, gridMET, and Sentinel-2 evidence JSON and website
  documentation. Existing report keys, figures, fixtures, noun calls, and pipe
  behavior remain compatible.

### Validation

- Targeted lifecycle, fingerprint, profile, noun, and source-QA contracts:
  38 tests passed. The explicit offline streaming lane passed 4 tests.
- Exact offline suite after final changes: 409 passed, 5 skipped, and 9
  deselected.
- `python scripts/run_source_qa.py --output docs/assets/source_qa` passed for
  all three reviewed real-data sources.
- `python scripts/run_validation.py --run-vignettes` passed all five
  publication-validation modules when run with local Jupyter kernel ports.
- `mkdocs build --strict`, repository-size policy, Python compilation, and
  `git diff --check` passed.
- `uv build --out-dir /tmp/cubedynamics-dist` produced both the source
  distribution and wheel. Setuptools reported pre-existing license-metadata
  deprecation warnings but the build succeeded.

### Scope boundary and next task

- Daymet was not implemented or registered. The architecture and evidence form
  a coherent review unit, while a real Daymet adapter, upstream-identity
  strategy, fixture, online behavior, scientific QA, and documentation are a
  separate source-integration review.
- The next narrow task is a Daymet candidate using
  `climate_continuous_daily`; it should not enter discovery until its bounded
  real-data evidence and promotion decision pass review.

## 2026-08-26 - Deterministic gridMET yearly-loader regression fix

### User goal

- Repair CI failures in gridMET streaming tests after bounded OPeNDAP access
  was introduced.

### Implementation

- Consolidated bounded OPeNDAP and annual HTTPS access behind the existing
  `_open_gridmet_year` seam. The runtime still prefers provider-side bounded
  reads when a compatible engine is installed and falls back to HTTPS when it
  is not.
- Preserved compatibility with offline tests and internal adapters that
  replace the original three-argument yearly loader. Optional xarray engines
  installed on one CI image can no longer bypass that replacement and trigger
  environment-dependent behavior or live network access.

### Validation

- PRISM/gridMET streaming regression set: 12 tests passed.
- Exact offline suite: 418 tests passed, 5 skipped, and 9 deselected.
- `git diff --check` passed.

## 2026-08-27 - Documentation refactor from the supplied PDF

### User goal

- Execute the supplied documentation-refactor prompt: audit the site, simplify
  navigation, distinguish teaching from reference and analysis stories, and
  derive reference facts from existing Python/catalog sources without changing
  scientific behavior.

### Implementation

- Added a pre-refactor inventory and migration/ownership report under
  `docs/project/documentation_*`; simplified top-level navigation to Home,
  Learn, Library, Documents and Vignettes.
- Added deterministic reference generation for eight nouns, three sources,
  51 public verbs/helpers and indexes (65 pages), plus generated API object,
  pipe, data-lifecycle and visualization documentation.
- Added seven progressive Learn lessons and 31 reference examples using the
  checked PRISM fixture. Reserved APIs, optional workflows and missing source
  descriptions are disclosed instead of filled with invented examples.
- Preserved all nine notebook analysis code sequences; added a shared data,
  reproduction and cross-reference shell through their existing builders.
- Consolidated duplicate provider/verb/example directories, replaced empty
  how-to stubs, standardized maintained live recipes, and removed unsupported
  correlation-module/result claims. Historical routes and scientific reports
  remain available.
- Added common reference styling, active-tab contrast, notebook-link
  translation, generated-reference freshness tests and built-site link checks.
  Both documentation CI and Pages check freshness and links before publication.

### Validation and boundaries

- Offline suite: 467 passed, 5 skipped, 9 deselected.
- All nine supported notebooks executed with their required static plots;
  strict MkDocs build and built-site internal target/anchor checks passed.
- Generated reference freshness, tracked repository-size policy and
  `git diff --check` passed. No runtime `src/` or legacy `code/` changes.
- Browser review checked Library/verb reference presentation, a notebook figure
  and working noun link, deferred homepage loading and a 390-pixel viewport.
- No live provider recertification or viewer-backend repair was claimed.
  Sparse API docstrings, optional example coverage, advanced legacy recipe
  normalization and cube camera/axis presentation remain explicit follow-ups
  in the report. No commit, push or deployment was performed.

## 2026-08-27 - Browser QA suite checkpoint (paused at user request)

- Added optional pinned Playwright/pytest-playwright dependencies (Python
  3.10+), updated `uv.lock`, and marked browser tests as opt-in integration.
- Added `scripts/site_browser_checks.py`, `tests/browser/`, and offline helper
  regressions. Coverage includes every built HTML page (including standalone
  viewers), internal HTTP targets/anchors, decoded images/CSS backgrounds,
  deferred iframes, JavaScript/network errors, five hubs at desktop/mobile
  widths, and real mouse drag/wheel changes on the homepage cube.
- Added bounded external-link availability reporting in
  `scripts/check_external_links.py`. External link probes are advisory;
  browser failures gate publication. Both existing workflows now install
  Chromium, run the suite, and retain evidence under `artifacts/browser/`.
- Verified so far: four offline helper tests and 20 focused browser tests
  passed (negative controls, responsive hubs, cube drag/zoom).
- Full crawl against `/private/tmp/cubedynamics-docs-refactor-site` was
  interrupted for the user's connection pause. It had already reported
  failures; inspect per-page JSON/screenshots and traces in `artifacts/browser/`
  before resuming. Do not claim the full crawl passes yet.
- Resume: investigate crawl failures, finish/refine regressions and external
  probing, document coverage in `docs/dev/ci_testing.md`, rebuild current docs,
  then rerun the complete browser and offline suites. No commit/push/deployment.

## 2026-08-27 - Browser QA completed after connection pause

- Resumed the requested website link/image test-suite work. The first full
  Chromium crawl found seven pages displaying invalid PNG placeholders.
  Replaced those references with dimension/grammar explanations and working
  documentation links. Removed nine empty/text image stubs (seven displayed,
  two unused); no real-data figures were removed. Git retains the old stubs.
- Added `docs/overrides/partials/source.html` to retain the repository link
  without Material's optional GitHub metadata requests, which generated
  `releases/latest` 404s. Added a rendered regression for this behavior.
- Corrected the Lexcube repository URL and made Google Help language explicit.
  External probing now confirms HEAD 403/404/405/501 with a streamed GET without
  consuming the product body: Google Help returned HEAD 404 but GET 200.
  Negative tests still reject genuine GET 404s. External requests remain
  advisory in CI; internal links, images, resources and viewer errors gate
  both PR documentation checks and Pages publication.
- Hardened the local test server's Pages-prefix directory redirects and SVG
  link reading; added a redirect regression. Documented installation, coverage,
  evidence, exclusions, and local commands in `docs/dev/ci_testing.md`.
- Final strict build: `/private/tmp/cubedynamics-browser-qa-site`.
  All **310 Chromium tests passed** (288 built pages, 592 image occurrences,
  46 CSS background occurrences, deferred frames, mouse drag/zoom, desktop/
  mobile hubs, and detector controls). All **47 distinct outbound URLs**,
  including a Plotly link discovered at runtime, passed availability checks.
- Final offline suite: **478 passed, 5 skipped, 243 deselected**. Existing
  dependency warnings remain. Eleven offline browser-helper checks passed.
  Strict MkDocs build, static internal file/anchor checks, 65 generated-reference
  freshness checks, tracked repository-size policy, workflow YAML parsing,
  and `git diff --check` passed.
- Final machine-readable evidence is in `artifacts/browser/final/`; earlier
  failed-crawl evidence is retained separately. This verifies Chromium
  rendering/resources and interaction, not every browser, external anchors,
  or scientific figure semantics. Runtime scientific code was unchanged.
  No commit, push, or deployment was performed.

## 2026-08-27 - Reference usability follow-up completed

- User requested a small follow-up, preserving Home / Learn / Library /
  Documents / Vignettes and all runtime/scientific behavior. Work resumed
  after a pause; the earlier changes were already saved in `3393f0f`.
- Documents now presents a short user-reference directory: Verbs, Data,
  Pipe and grammar, Visualization, Full API, then a separate Developer
  documentation link. Internal contribution/CI, source lifecycle,
  architecture/contracts, publication and vocabulary plans, validation,
  deprecation inventories, and legacy material are regrouped under Developer
  documentation. All 60 former Documents routes remain in navigation.
- The generated primary verb browser has six scientific-purpose groups and
  an Other helpers fallback. The secondary A–Z inventory retains all 51
  public callables: 44 implemented, four compatibility names, one deprecated
  export, and two placeholders. Callable types derive from implementation
  inspection plus a small editorial exception map; grammar metadata supplies
  descriptions. Compatibility/deprecated inventories follow classification
  automatically, including newly deprecated names outside the exception map.
- `fit_model` and `correlation_cube` are reserved, not implemented operations.
  `aoi_signature`, `compare_aoi_signature`, `exceedance`, and `vase_demo` have
  explicit compatibility guidance. `month_filter` is labeled deprecated:
  its current export emits a warning recommending the same public symbol.
  Fixing that export/warning is a concrete runtime follow-up, not done here.
- Library remains catalog-driven: eight nouns and three sources. Navigation
  follows generated noun categories. Multi-source temperature/precipitation
  pages compare declared units, statistics, grids, time/coverage, revisions,
  and constraints; no data harmonization or live certification is implied.
  Noun-to-vignette links also derive from notebook reference links.
- Added `tests/test_reference_usability.py` and
  `tests/browser/test_reference_navigation.py`; maintained the full browser
  suite and CI gates. Added ownership/classification conventions to
  `docs/project/documentation_refactor.md`. Generated files were rebuilt
  through `scripts/build_reference_docs.py`, not hand-edited.
- Manual browser review and automated journeys checked desktop (1280 px)
  and phone (390 px): Home → Library → temperature; noun → PRISM source;
  Home → Documents → verbs; Transform → mean; mean → grammar vignette;
  vignette → temperature; Documents → Developer documentation. The full A–Z
  route, callable labels, notebook figure, and page overflow were checked.
  No page-level horizontal overflow was found on these paths. The preview
  initially retained an earlier page in browser cache; a fresh URL confirmed
  the final deprecated-name exclusion, and fresh Chromium journeys passed.
- Final validation:
  - Reference freshness: all **68 generated pages** current.
  - Strict MkDocs build: passed at
    `/private/tmp/cubedynamics-reference-usability-site`; all nine notebook
    pages rendered. Existing notebook render caches were reused; execution
    was separately repeated from scratch by the vignette runner.
  - Built-site internal files and anchors: passed, no unresolved targets.
  - Vignette runner: **9/9** supported real-data notebooks executed offline,
    with required static plot outputs. Local Jupyter transport warnings remain.
  - Focused documentation/reference/link tests: **76 passed**.
  - Full offline suite: **501 passed, 5 skipped, 245 deselected**.
  - Chromium suite: **316 passed**; **292 built pages**, **600 image
    occurrences**, **46 CSS backgrounds**, **zero failed pages**. Includes
    desktop/mobile journeys, deferred frames, cube drag/zoom, and detector
    negative controls. Reports and 18 journey screenshots are under
    `artifacts/browser/reference-usability/`.
  - Repository-size policy: passed for **1000 tracked files**.
  - Whitespace checks passed. Comparison with `9a6c768` confirms no changes
    to runtime `src/`, legacy `code/`, Home, Learn, or vignette sources.
- Existing sparse helper docstrings and live-provider availability were not
  repaired or recertified. No further site refactor, commit, push, or deployment
  was performed in this continuation.

## 2026-08-27 - Supplied manuscript citation-map draft added

- User requested adding the supplied manuscript PDF to the repository.
  Read the five pages and visually inspected the rendered original using
  the PDF workflow. Editorial citation markers were treated as draft content,
  not as instructions to perform a reference audit or change the software.
- Preserved the original 36,614-byte PDF at
  `paper/drafts/CubeDynamics_manuscript_citation_markers.pdf`. Added
  `paper/README.md` with title, draft status, receipt date, source checksum,
  and links to existing manuscript material; linked it from the root README.
  Existing `paper/paper.md` and `paper/paper.bib` remain unchanged.
- The index discloses unresolved citations and the original page-2 code
  block's literal newline escapes. No claims, citations, or PDF formatting
  were revised; no completed review or publication status is implied.
- Validation: byte comparison and SHA-256 match the supplied original;
  all manuscript-index links resolve; repository-size policy passes for
  tracked files and the new, untracked manuscript files. Strict MkDocs build,
  built-site internal file/anchor check, and `git diff --check` passed.
- No runtime changes, website navigation changes, commit, push, or deployment.

## 2026-08-27 - README and agent guide synchronized with the package

- User requested updating `README.md` and `AGENTS.md` to match current package
  content. Audited runtime exports, pipe/semantic behavior, source catalog and
  access paths, lifecycle/QA APIs, fixture/notebook ownership, packaging,
  Makefile, citation metadata, and CI workflows before editing.
- README now identifies the checkout's 0.1.0 alpha metadata without implying
  that a packaged release contains all main-branch work. Added the five site
  destinations, current extras and Python targets, an offline real-PRISM
  quickstart with a plot, a missingness-aware project verb with a plot, the
  eight-noun source table, and the nine-notebook publication collection.
  Kept live loading separate from the offline example and preserved the
  manuscript index link.
- Both guides distinguish core grammar from integrations/project vocabularies,
  pipe factories from direct helpers, reserved APIs from implementations, and
  compatibility from deprecation. Clarified metadata-only pipe validation,
  immediate stage calls versus lazy arrays, gridMET OPeNDAP/annual-HTTPS access,
  PRISM daily NcSS, the global adapter's no-download boundary, source-specific
  units, and revision validity versus endpoint health.
- AGENTS now maps catalog/lifecycle/schema/QA ownership, generated reference and
  notebook builders, classification and link hooks, developer documentation,
  fixture exceptions, browser QA, and explicit release boundaries. Preserved
  spatial/CRS, viewer time-axis/attachment, FireHull/FireEventDaily, renderer
  separation, backward-compatibility, and real-data safeguards.
- Added seven regressions in `tests/test_repository_guides.py` for version and
  extras, catalog coverage, notebook count, guide links/paths, checksum-verified
  offline example execution/plots, direct-versus-piped custom use and missingness,
  and static live-request signature/catalog validation (no live fetch).
- Validation: **7 guide tests passed**; **83 focused documentation tests passed**;
  full offline suite **508 passed, 5 skipped, 245 deselected**. All **68** generated
  references remain current. Strict MkDocs build and built-site internal
  file/anchor checks passed. Repository policy passed for **1003 tracked files**
  and the new regression file; `git diff --check` passed.
- No runtime, generated reference, notebook, website navigation, or manuscript
  content changed. Existing notebook render caches were reused by MkDocs;
  browser and live-provider suites were not rerun for this root-guide-only edit.
  No release, commit, push, or deployment was performed.

## 2026-08-27 — Source-lifecycle baseline and month_filter; Daymet blocked

- Request: preserve the baseline, repair month_filter, extend the existing
  lifecycle, and certify Daymet through a bounded NCSS request before expanding
  to any further source. Read AGENTS and the full pasted request. The named
  `CubeDynamics_Data_Source_Upgrade_Plan_repository_informed_v3(1).pdf` was not
  available; inspected the previously supplied `v3.pdf` and requested confirmation.
- Captured `artifacts/source_lifecycle/baseline.json` before runtime changes at
  SHA `b4321518cb5bbef393d9e82e7b702cb6d6c4578d`: package 0.1.0, 8 nouns,
  3 sources, 10 noun/source pairs, 51 public verb-namespace callables. Baseline
  offline suite: 508 passed, 5 skipped, 245 deselected; streaming: 32 passed;
  three source QA results passed; 68 generated references fresh; strict build
  passed. Commands, logs, source QA records and JUnit counts are retained.
- Moved the supported month_filter factory into `verbs/stats.py` and pointed
  `v.month_filter` directly at it. The old ops/top-level shortcuts still warn
  and forward. Preserved calendar selection, iterable capture, historical int
  coercion, empty-selection behavior and lazy arrays. Added 11 focused tests;
  updated generated reference classification, browser expectations, README,
  AGENTS and the deprecation inventory. No replacement public name was added.
- Added `scripts/source_lifecycle_evidence.py` and three tests. Baseline capture
  refuses to overwrite historical evidence. Release manifests compute catalog,
  callable/status, Python, notebook and reference inventories; link supplied
  JUnit/QA evidence; include serving history and working-tree fingerprints.
  Output: `artifacts/release_manifest.json`; overlapping suites are separate,
  not summed into an inflated total. The supported-notebook metadata key was
  corrected during baseline capture, before runtime edits.
- Daymet access check: the legacy 1840 NCSS request for tmax, bbox
  [-105.35,39.95,-105.20,40.10], 2020-07-01 through 2020-07-03 redirects to
  Earthdata/Hyrax and then login, returning HTTP 401 anonymously. The 2129
  THREDDS catalog redirects to Hyrax and returns HTTP 400. No EARTHDATA_TOKEN
  is configured. ORNL's March 2026 guidance in Earthdata Forum topic 7585
  points to indexed OPeNDAP access. This does not prove that an authenticated
  legacy NCSS request can work; no backend substitution was implemented.
- Evidence: `artifacts/source_qa/daymet/access_probe.json` records exact request,
  redirects, HTTP results, and separate retrieval BLOCKED / interpretation
  NOT_TESTED / certification BLOCKED. The diagnostic script is retained under
  `artifacts/source_lifecycle/probe_daymet.py`. The existing live runner also
  returned BLOCKED; its exit code 0 is not a scientific PASS. No scientific
  Daymet values, identity, fingerprint, or plots were invented.
- Final checks for completed work: offline 521 passed, 5 skipped, 245
  deselected; focused month_filter/evidence/Daymet-candidate 16 passed;
  streaming 32 passed; all three existing source QA results passed; reference
  freshness 68 pages; strict build and internal links passed; browser 316
  passed (292 pages, no recorded page errors). Browser launch initially failed
  inside the sandbox; the authorized rerun passed. Wheel/sdist build and twine
  both passed; clean wheel install with declared dependencies passed an isolated
  import and warning-free lazy month_filter smoke test. Existing setuptools
  license deprecation warnings remain. Size policy passed for 1007 tracked
  files and whitespace checks passed.
- The checkout advanced externally during work to `41e11aa975edfb53a343f98f55b01cdb89080241`,
  containing the implementation edits; this agent did not commit or push.
  Baseline SHA remains unchanged. No source data, catalog registration, serving
  history, source QA profiles, or scientific certification status was changed.
- Remaining: resolve authorized current Daymet backend and Earthdata access;
  confirm the SOP copy; then complete lifecycle fields, normalization, live
  numerical/visual certification and the generated dashboard. Do not promote
  Daymet or start 3DEP until that work is complete. Task is partial, not done.

## 2026-08-27 — Reproducible visual documentation, bounded first pass

- Request: make actual code/results/interpretation visible together, preserving
  the grammar, five tabs and existing notebook/browser architecture. Read AGENTS,
  the full supplied prompt, current generators, fixture/source QA, notebook
  execution, browser checks and recent work log. This task does not resume the
  separately blocked Daymet work above.
- Added shared executable editorial examples in `scripts/visual_examples.py`
  and offline production/freshness checks in `scripts/build_visual_docs.py`.
  The same code is displayed on static pages and copied into native cells by
  the existing notebook builder. Captions explain quantities, operations,
  baseline/units, interpretation and limitations. Export uses an asserted
  round-trip table rather than another redundant plot.
- Upgraded exactly these six teaching/reference surfaces: `learn/verbs.md`,
  `vignettes/grammar_basics.ipynb`, `library/nouns/temperature.md`,
  `datasets/which_dataset.md`, `reference/verbs/anomaly.md`, and
  `reference/verbs/threshold_state.md` (under docs). Existing generated apply
  and to_netcdf references gained links to the newly relevant vignette only.
  No runtime APIs, fixture bytes, catalog, source lifecycle or top-level tabs
  were changed.
- Seven unique scientific PNGs and one export table live under
  `docs/assets/generated/visual/`. All use the reviewed, checksum-verified real
  PRISM Boulder January 2024 fixture; the source-support figure additionally
  uses the reviewed gridMET Badlands July 2001 fixture. Different locations,
  periods and native C/K units are explicit: this is not a paired comparison,
  bias estimate or source-equivalence claim. No synthetic publication figures
  or manually pasted screenshots were introduced.
- The manifest records code, input/provenance/runtime hashes, captions,
  interpretations, output hashes and generation context. Existing source QA
  remains authoritative for these bounded fixtures, not live certification.
  Added per-cell output validation and optional retained executed notebooks to
  `run_vignettes.py`; no second notebook execution framework. CI/Pages check
  freshness and regenerate before building. Maintainer inventory/regeneration
  guidance is in `docs/dev/visual_documentation.md` and linked from AGENTS.
- Added 14 offline regressions for numerical equivalence, exact displayed code,
  provenance/freshness, offline generation and deliberate missing/corrupt/blank
  output/execution failures; added 12 browser cases for code-result ordering,
  decoded static/native notebook figures, captions and desktop/390px layout.
  Browser testing caught and fixed raw-HTML relative image URL depth under
  MkDocs directory URLs. Manual mobile review also caught wasted Jupyter gutter
  space; wider mobile figures now have a stricter >310px assertion. Static
  figures are lazy-loaded with intrinsic dimensions to reserve their space.

- Final validation: all 9 supported notebooks executed offline (14 static plot
  outputs total; grammar has 5 plots plus a verified table). Figure generation
  and freshness passed for all 8 results; repeated local generation produced
  identical hashes. All 68 reference pages are current. Full offline suite:
  535 passed, 5 skipped, 257 deselected (28.19s); focused visual/guide suite:
  21 passed. Strict MkDocs build passed (10.18s final cached build; the new
  notebook also executed successfully on its uncached build); internal file
  and anchor checks passed. Final Chromium suite: 329 passed (120.67s), 293
  crawled pages, zero page errors, 615 images and 46 backgrounds. PRISM,
  gridMET and Sentinel-2 existing source QA passed. Policy passed for 1007
  tracked and 14 new files; `git diff --check` passed.
- Evidence is under `artifacts/visual_docs/`: executed notebooks/run manifest,
  final built site, offline/browser JUnit, crawl report, desktop/mobile review
  screenshots and an independent regenerated output set. Local generation took
  2.38s after imports, with no provider requests. The 7 PNGs total 361,757 bytes;
  all figure/provenance assets total 423,847 bytes. Notebook HTML retains inline
  outputs (~1.03 MB); it does not fetch live environmental data. Sandbox socket
  restrictions required authorized Jupyter/browser reruns; these passed.
- Stop at this reviewed first pass. Next candidates: remaining Learn analytical
  lessons, states/events vignette, remaining implemented noun visualizations,
  mean/zscore references and a separately acquired/reviewed matched source
  comparison. Legacy figures elsewhere are not certified by this new manifest.
  No commit, push, release or deployment was performed.

## 2026-08-27 — Daymet OPeNDAP access experiment stopped at authentication

- Inspected the existing catalog, candidate serving history, noun dispatch,
  lifecycle outcomes, schema/QA profiles, certification writer and prior NCSS
  evidence. Confirmed the March 2026 ORNL Earthdata Forum guidance for indexed
  Daymet V4R1 OPeNDAP access; did not retry NCSS or change source registration.
- Added the unregistered diagnostic `scripts/probe_daymet_opendap.py`, reusing
  certification records and the existing evidence writer. It disables implicit
  environment/.netrc authentication, follows no redirects, caps response reads
  near 1 MiB, bounds requested cell count and validates returned dimensions
  before reading coordinates. It is not a public loader or geographic adapter.
- Exact attempted granule: `Daymet_Daily_V4R1.daymet_v4_daily_na_tmin_2024.nc`
  under Earthdata collection `C2532426483-ORNL_CLOUD`, suffix `.dap.nc4`;
  `dap4.ce=/y[5000:1:5002];/x[4000:1:4002];/tmin[0:1:0][5000:1:5002][4000:1:4002]`.
  Requested shape was one time slice by three rows by three columns.
- The sandbox attempt recorded a ConnectionError. Authorized network execution
  of `.venv/bin/python scripts/probe_daymet_opendap.py` reached the provider and
  returned HTTP 302 to `https://opendap.earthdata.nasa.gov/login/urs`. Stopped
  without following login or reading a body: zero response-body bytes, no sample.
  Command exit code 2 accurately signals BLOCKED, not scientific success.
- Evidence: `artifacts/source_qa/daymet/opendap_probe.json`; sandbox diagnosis:
  `opendap_sandbox_probe.json` in the same directory. Historical NCSS evidence
  and candidate serving record were preserved. No coordinates, units, observed
  provider identity, scientific values or plot were obtained. Grid translation,
  numerical/visual QA and certification remain NOT_TESTED/BLOCKED; Daymet is
  not ready for integration. No new serving revision or catalog entry was made.
- Follow-up safety tests and status-documentation edits were not completed
  before the user supplied three new source-experiment prompts (3DEP, roads,
  USGS streamflow). The attempted test patch did not apply. The diagnostic's
  non-authentication branches have not yet been regression-tested; do not claim
  them validated. Next Daymet step would require an explicitly authorized
  Earthdata authentication approach; no credentials were requested or accessed.

## 2026-08-27 — Three contained real-source projects: 3DEP, roads, USGS

- User clarified that all three supplied prompts should be completed as
  individually contained projects within the repo and its grammar, not as
  mutually exclusive stop instructions. Inspected catalog/noun dispatch,
  lifecycle/revisions, schema/provenance, static/vector/station QA profiles,
  spatial contract, dependencies, docs generators and test conventions first.
  Preserved the prior Daymet authentication blocker and its untracked probe;
  no credentials, synthetic fallback, production promotion or new tasks.
- Added `examples/source_projects/three_dep`, `roads`, and `usgs`, with separate
  commands and artifact roots. Project-owned nouns return native 2-D xarray
  elevation, a roads GeoDataFrame, and a time-by-station streamflow Dataset.
  Ordinary pipe/callable verbs work without a new registry or framework. Public
  `data.list_sources()` is unchanged: these are bounded candidate proofs, not
  broadly certified production sources. Shared helpers are limited to anonymous
  byte-capped HTTP and the existing certification writer.
- 3DEP: authoritative TNM `/api/v1/products`, dataset tag `National Elevation
  Dataset (NED) 1/3 arc-second Current`, selected ScienceBase
  `6a471a0d1ba49bcdf785e0fa`, `USGS_13_n40w106_20260630.tif`. WGS84 bounds
  `[-105.300,39.985,-105.291,39.994]` yielded a 99x99 EPSG:4269 window. GDAL
  requested two HTTP ranges totaling 770,048 bytes from a 413,480,184-byte tile;
  both returned 206. Separate range preflight: 16,384 bytes. Full-cell outward
  rounding, tile clipping and native north-up orientation are tested. Sample
  elevations 1886.041–2363.250 m; finite fraction 1.0. NAVD88 derives from the
  catalog CONUS description, not independent tile-specific vertical accuracy.
  Window/block caps and timeouts act before reads; total GDAL byte evidence is
  checked afterward, not represented as a hard runtime network firewall.
- Roads: shared WGS84 bounds `[-105.285,40.008,-105.270,40.020]`. Official
  Overture STAC resolved release `2026-08-19.0`, transportation/segment,
  GeoParquet 1.1.0, ODbL. Read 3 of 128 row groups in partition 00018, one of
  128 partitions, transferring 19,872,693 Parquet bytes (32 MB enforced cap).
  Collection contains 350,469,378 features; it was not materialized. Optional
  PyArrow 21.0.0 installed only in the dev virtualenv/project requirements.
  Current STAC schema version is null; preserved that and actual Arrow schema.
- OSM: anonymous `https://overpass-api.de/api/interpreter`, bounded ways query
  with exact highway class regex, 25s server timeout, 32 MiB server-memory
  setting, 5,001-feature truncation sentinel, 4 MB response cap. Both providers
  include native major/local motor-road classes plus service/living streets;
  OSM also retains its explicit `_link` classes. Excluded paths/trails/tracks,
  rail/ferries/construction/area features; no automatic class crosswalk.
  Preserved IDs, native tags/rules/connectors and full feature segmentation.
  Overture returned 528 features, OSM 611; explicit AOI clipping and UTM 13N
  measurement gave 43.115 km vs 43.065 km. Named fractions 56.1% vs 58.9% are
  segmentation-dependent, not quality rankings. Overture incorporates OSM:
  visual agreement is not independent ground truth. Independent maps and a
  same-scale comparison were inspected; overlapping tick labels/legends fixed.
- USGS: modern `https://api.waterdata.usgs.gov/ogcapi/v0/collections/continuous/items`,
  site `USGS-06730200` (Boulder Creek at N. 75th St.), parameter `00060`,
  `2026-08-26T00:00:00Z/2026-08-26T23:59:59Z`, limit 2000. Anonymous query
  returned 96 observations, 15-minute spacing, 32.8–36.9 ft^3/s, all Provisional,
  qualifier null; zero missing/negative/duplicate values or gaps above the
  provider's 72-minute threshold. Site and time-series metadata came from the
  same API; series ID `a36b95ef8f7140a3828b4e7c376bc4b5`, instantaneous statistic
  00011, native site/HUC/datum/threshold metadata retained. Per-row UUIDs may
  change on refresh; stable observation key is series ID + time. Preserve
  approval/qualifier/last-modified values as documented JSON-valued coordinates.
  No legacy API fallback, credentials, silent unit conversion or provisional
  filtering. Pagination fails closed rather than returning partial results.
- Small lifecycle extensions: pre-registration `CertificationRecord` accepts
  `serving_revision=None`; existing serving records/promotion gates remain
  strict. `OBSERVATION_UPDATE` distinguishes routine rolling value/status
  refreshes from declared product-wide historical revisions. It compares
  retained content without creating a new rolling serving interpretation.
  String metadata uses object dtype so status/qualifier string lengths do not
  create false schema-fingerprint drift. No generic time-series abstraction.
- All four provider records are PASS_WITH_CAVEATS with explicit reviewed-figure
  hashes. Figures, complete evidence and architecture reviews are under
  `docs/data/source_projects/` and `docs/assets/generated/source_projects/`
  (about 1.3 MB). Raw/local samples remain in ignored `artifacts/source_qa/`.
  `build_source_project_docs.py` reuses certification records; generation cannot
  automatically approve images and fresh-clone checks need no upstream data.
  Five tabs retained; added an experimental Library subsection and fixed the
  nav hook that initially dropped it, with a regression test. README/AGENTS
  explain experimental/public boundaries. No package catalog entries added.
- Validation so far: 55 new offline source/evidence controls passed; final full
  offline suite 593 passed, 5 skipped, 347 deselected (28.17s). Explicit online
  pytest: 3DEP + USGS 2 passed; Overture + OSM 2 passed (68.23s). Documentation/
  guide-focused suite 83 passed. Strict MkDocs build passed; all internal files
  and anchors resolve; 68 generated references and published source-project
  evidence checks pass. Regenerated the existing 8 visual results because their
  freshness manifest hashes runtime source. Existing PRISM/gridMET/Sentinel-2
  source QA passes. Tracked policy passed (1021 files) and all 34 new files
  passed policy; diff whitespace check passed. Final Chromium suite: 334 passed
  (253.31s), 298 pages, 630 images, 46 backgrounds, zero failed pages. Browser
  DOM review confirmed the experimental Library subsection, generated evidence
  rows, and decoded roads figures. Source-project and existing visual freshness
  checks passed again after final rendering. Browser JUnit is
  `artifacts/source_qa/project-browser-tests.xml`; crawl details are under
  `artifacts/browser/`. The local preview is on port 54939; no deployment.
- Added manual `.github/workflows/source-projects.yml`: independent project
  jobs, bounded real requests, evidence upload even on failure; no automatic
  figure approval or source promotion. Regular docs CI checks publication
  evidence offline. Actual local test commands/reports include:
  `pytest -m "not integration and not online" --maxfail=1 --disable-warnings -q`,
  project-specific `pytest ... -m online`, `mkdocs build --strict`,
  `scripts/check_site_links.py site`, `scripts/run_source_qa.py`, and browser
  pytest with JUnit under `artifacts/source_qa/`. No push, deployment or release.

### 2026-08-27 — Hardening the three source-noun projects

- User approved moving the new nouns toward production robustness. Added
  installed candidate adapters in `src/cubedynamics/data/usgs.py`,
  `three_dep.py`, and `roads.py`, with internal `_transport.py` and `_ranges.py`.
  The original independent proofs remain historical evidence; runtime code
  does not import them. Existing catalog nouns and serving histories are
  unchanged. Candidates are explicitly not production-certified.
- Shared anonymous transport enforces approved HTTPS origins, bounded retries,
  Retry-After/deadline handling, query-wide request/body-byte budgets, no
  redirects or ambient credentials, and explicit immutable raw snapshots.
  Offline replay validates identity/checksums and never downloads replacements.
  Range reads require a strong ETag and If-Match; whole-object and oversized
  reads fail before acquisition. Bounds are response bytes, not TCP/TLS traffic
  or a hard process memory/deadline guarantee.
- USGS retains native units, UTC station-series semantics, status/qualifier
  null-versus-absent flags, and provisional observations. Exact pagination and
  seven-day batching fail closed on partial or conflicting results. Live QA
  exposed cursor pagination rather than offset-only links; fixed and tested
  while preserving endpoint/query-scope checks. Rolling comparison ignores
  routine row-ID refreshes but detects value/status/qualifier changes.
- 3DEP reads a fully covering native window with Rasterio's capped Python
  opener (requires >=1.4); no silent tile clipping, mosaic, or uncapped fallback.
  Asheville had no Current-tagged result: explicitly selected ScienceBase ID
  `627f3798d34e3bef0c9a3198`, labeled as a pinned version, not current.
- Overture requires an explicit release, strict STAC/asset identities, native
  schemas and bounded row-group pruning. The first attempt hit the request
  budget because PyArrow requested many tiny columns. Coalesced row-group
  spans fixed this without removing limits; regression test verifies reads
  within a prefetched span do not make extra requests. OSM remains a small
  Overpass candidate with explicit node-in-bbox selection limitations, not a
  sustained production serving backend or a routing/completeness guarantee.
- Added `validate_source_promotion`: exact candidate/revision identity, seven
  explicit PASS gates, reviewer/scope, fresh timestamp, and verified evidence
  hashes. The old outcome-string gate remains deprecated for compatibility.
  No automatic approval, promotion, serving revision, or synthetic fallback.
- `scripts/check_source_candidates.py` runs independent real checks and exact
  offline replay. Live and replay reports are separate and use the existing
  CertificationRecord model. Successful retrieval is PASS_WITH_CAVEATS;
  scientific/visual certification remains NOT_TESTED, not inferred from plots.
  Live evidence under `artifacts/source_qa/candidates/`:
  - `usgs_cursor`: Boulder 96, Potomac 288, Lees Ferry 96 observations for
    August 26; raw-value/status/unit comparisons and NetCDF round trips passed.
    Real cursor test returned 96 observations over two 50-row pages; the
    eight-day request returned 768 observations across two time batches.
  - `three_dep_pinned`: Boulder 99x99 / 760,458 response bytes; Asheville
    55x55 / 802,007 bytes, both native EPSG:4269.
  - `overture_coalesced`: release `2026-08-19.0`, 528 road features,
    20,432,795 body bytes including metadata, 137 requests, 6.41 s.
  - `osm`: 611 features, 486,251 body bytes. All four exact offline replays
    passed. These are bounded samples, not throughput or soak guarantees.
- Added 368,261 bytes of real USGS response/request fixtures and provenance
  under `tests/fixtures/real_data/usgs_streamflow/`. The generated
  `streamflow_snapshots.ipynb` tells a three-step story with three inline plots,
  native observations, one-line anomaly pipes, visible provisional warnings,
  and explicit offline replay. Browser inspection verified readable rendered
  code/plots; warnings no longer expose machine-specific traceback paths.
- Added source production-readiness documentation, linked it from all three
  projects, and updated API/README/AGENTS/vignette navigation. Five site tabs
  retained. Validation documentation distinguishes the published PRISM baseline
  from new candidate evidence. The full publication run exposed an old
  eight-lessons/all-PRISM assumption; replaced it with explicit supported input
  pairs, hash verification, required lessons, and unknown/corrupt/missing-input
  regression controls. Notebook stdout/stderr now survives in the run log.
- CI adds installed-wheel replay, generated-notebook freshness checks,
  independent weekly/manual candidate checks and evidence uploads, and an
  Ubuntu/macOS optional-decoder matrix. These are configured, not represented
  as already observed hosted runs. Pytest discovery now targets the original
  source/test trees in their original order, excluding temporary wheel/build
  artifacts that caused a local import-mismatch collection failure.
- Final validation: offline pytest **682 passed, 5 skipped, 349 deselected**
  (33.92 s); JUnit `artifacts/source_qa/candidates/offline-all.xml`. Full browser
  suite **336 passed** (215.99 s), including both added pages; JUnit
  `artifacts/source_qa/candidates/browser.xml`. Strict MkDocs build and built
  internal file/anchor checks passed. Installed non-editable wheel imported
  candidate modules and replayed all three real USGS stations. Eight visual
  results, 68 references, historical source evidence and new notebook freshness
  checks passed. Full publication QA passed five modules and executed **all
  ten notebooks offline**, with three plots from the new streamflow lesson.
  One concurrent run hit a local Jupyter startup timeout; standalone retry
  passed without changing the scientific checks. Tracked policy passed for
  1021 files; all 67 untracked candidate/previous-project files passed policy.
- Remaining release requirements: representative approved/missing-status USGS
  data, broader independent scientific/visual review, supported-limit and soak
  measurements, an OSM serving decision, and reviewed serving-history/rollback
  exercise. Do not label these candidates production-ready before those gates.
  Local website preview remains on port 54939. No commit, push, deployment or
  package release was performed; pre-existing working-tree changes preserved.

## 2026-08-28 — Main noun-library documentation and real-data lessons

- User requested that elevation, roads, and streamflow be presented alongside
  the existing nouns, with equivalent reference and vignette treatment rather
  than an experimental-project entry. Resumed the same task after interruption.
- Added three generated noun references and four source references (3DEP,
  Overture, OSM, USGS), with installed signatures, arguments, returned-data
  contracts, source differences, live examples, figures, provenance and limits.
  The main library now documents eleven nouns; the runtime catalog still has
  its original eight. This editorial integration does not assign serving
  revisions or claim broader source certification. No loader or grammar
  behavior changed in this task.
- Preserved the five top-level tabs and existing styles. Added all three noun
  lessons as peers in the Vignettes gallery; moved source engineering reports
  to Documents / Developer documentation while retaining their URLs. Updated
  Learn, Documents, public API notes, README and AGENTS to match. All seven
  source flavors share one source-index table.
- Added elevation_landscape and roads_local_network notebooks; integrated the
  existing streamflow_snapshots notebook into the same main-library journey.
  Each source lesson has three code/plot steps, narrative interpretation and
  checksum-verified real inputs. Static terrain uses spatial mean and an
  ordinary centering callable, not a temporal anomaly or invented time axis.
  Roads use explicit project-owned clipping and projected-length verbs; native
  classifications remain separate and are not routing or completeness claims.
- Froze 2,167,592 bytes of small lesson inputs and provenance from the prior
  validated raw-response snapshots via exact offline replay: a 99x99 native
  Boulder 3DEP window, 528 Overture features from release 2026-08-19.0, and 611
  OSM features. No new live retrieval, synthetic values, resampling, geometry
  simplification, or road-class crosswalk was introduced. Input attribution,
  native metadata and checksums are retained under tests/fixtures/real_data.
- scripts/source_lesson_content.py owns the two lessons' analytical code;
  scripts/build_source_vignettes.py produces notebooks and seven real-data
  reference figures with an input/output hash manifest. CI checks freshness.
  Expanded publication validation to verify these explicit fixture/provenance
  pairs, including every file of multi-file inputs and unsafe-path rejection.
- Added notebook-download links and corrected the MkDocs notebook-link hook
  to resolve them to the copied .ipynb files rather than the rendered page.
  Added six desktop/mobile noun → source → lesson → download → noun browser
  journeys, plus nine reference/fixture/figure/lesson regression tests.
- Publication QA passed all five modules and executed all twelve supported
  notebooks offline, with three static plots from each source lesson. Evidence:
  artifacts/validation/suite_manifest.json and notebook-execution.log. Strict
  MkDocs build, all built internal files/anchors, 75 generated references,
  notebook/figure freshness and tracked repository-size checks passed.
- Final offline pytest: **693 passed, 5 skipped, 364 deselected** (32.87 s),
  recorded in artifacts/source_qa/noun-library-offline.xml. Repository policy
  also passed for all 93 untracked files, including prior source-project work.
- Final full Chromium suite: **351 passed** (243.60 s), recorded in
  artifacts/browser/noun-library-final.xml. It checks built links, image loads
  and desktop/mobile journeys, including actual notebook JSON downloads and
  three decoded plots per source lesson. The initial run caught a URL-joining
  error in the new download test, not in the website; fixed with urljoin and
  reran the complete suite successfully. Manual browser inspection also
  confirmed the main-library navigation and matching 390/1280-pixel layouts.
- Local preview remains on port 54939. No commit, push, deployment or package
  release was performed; all pre-existing source-project changes preserved.

## 2026-08-28 — Include the nested elevation fixture in clean checkouts

- User reported CI failures in source-figure freshness and the elevation
  lesson. Both came from the same omission: `.gitignore` allowed only direct
  `tests/fixtures/real_data/*.nc`, so the nested `source_lessons/elevation.nc`
  existed locally but was never included in Git. Earlier local/untracked-only
  checks did not catch the ignored input.
- Added an exact ignore exception for this reviewed 215,108-byte fixture,
  leaving bulk and unreviewed nested NetCDF files ignored. Its SHA-256 remains
  `708b1e76b8baeb58f416d44009c517bb6a4b078faae4bb39e0495c72baf16ea8`,
  matching the original provenance and figure manifest. No acquisition,
  substituted measurements, or expected-data checksum changes.
- The source-figure checker now reports missing paths before scanning current
  inputs, and names changed/unrecorded inputs. Added five regression cases for
  ignored evidence, preservation of bulk-data exclusions, missing fixtures,
  changed hashes and unexpected inputs. Updated AGENTS fixture guidance.
- Regenerated the noun artifacts through their owner; only the changed
  generator's input hash changed. All seven figure byte hashes, notebooks and
  scientific input hashes remain unchanged.
- Verified in a temporary Git-filtered checkout projection containing tracked
  and commit-eligible files, not ignored caches or artifacts. The temporary
  repository was given a local QA commit because the existing visual builder
  records HEAD. Confirmed imports resolve to that copy's src directory; reused
  the installed Python 3.11 dependency environment, not a new Linux runner.
- From that copy, the reported CI generation/check sequence passed: eight
  visual results, 75 references, historical source evidence, streamflow lesson,
  and all source notebooks/seven figures. Offline pytest: **698 passed,
  5 skipped, 56 deselected** (34.90 s). The clean-copy repository-size policy
  passed all 1,115 tracked files, including the elevation input. Publication
  validation passed five modules and executed all twelve notebooks offline.
  Evidence: artifacts/source_qa/noun-fixture-clean-checkout.xml and
  artifacts/source_qa/noun-fixture-clean-validation/. Focused local tests:
  14 passed. `git diff --check` passed.
- No source-repository commit, push or deployment. The newly unignored
  elevation.nc must be included with these changes when committing.

## 2026-08-28 — 0.1.0 release hardening, without publication

- User requested a release-only audit and full artifact gate, with no new
  scientific features, source promotion, branch protection/permission changes,
  tags, publication, DOI fabrication, module extraction or research deletion.
  Inspected AGENTS, metadata, API/runtime imports, all workflows, catalog,
  installed candidates, notebook/figure owners and release-manifest tooling
  before editing. Base commit: 57a32dd81829ee29092bdf2b45c92aac6e889660.
- pyproject/runtime/both citation versions were already 0.1.0, with alpha
  appropriate. Citation descriptions were outdated and the docs copy lacked
  URL/license. Active release version 1.1.0 was not found; matches were external
  dependency versions and GeoParquet metadata, not package releases. Historical
  publication/changelog navigation language was marked historical, not erased.
- The first real isolated build/Twine check passed, but archive inspection
  found nine internal test files in the wheel and 121 test files in the sdist.
  Added narrow package-discovery exclusions and MANIFEST.in pruning; required
  serving_history.json, viewer template, runtime code and climate_cube_math
  remain. No fixtures, research outputs, manuscripts or evidence are packaged.
- Added check_release_artifact.py: archive inventory/version/runtime parity,
  exact installed wheel SHA and file-byte checks, rejection of checkout/editable
  imports, package-only deterministic unit control, and actual README PRISM
  code against its external reviewed fixture with numerical/figure validation.
- Added explicit run_vignettes.py release mode with an external isolated kernel
  interpreter and before/after installed-wheel guards. Default development
  execution is preserved. The source notebooks remain unchanged;
  real-data fixtures remain repository inputs rather than package data.
- Added a non-publishing run_release_gate.py using existing source lifecycle
  inventory/manifests, with command logs, exact wheel/sdist identity, actual
  Python/platform versus configured CI targets, source QA scope and candidate
  caveats. Failed/incomplete gates and changed release inputs cannot be marked
  ready. The manifest excludes its own digest to avoid a self-reference loop.
- Added explicit 0.1 support classes, dependency audit, release-note draft and
  release checklist. Both citation files now match with no DOI. Runtime
  dependencies and scientific APIs are unchanged. Candidate USGS/3DEP/Overture/
  OSM remain outside the eight-noun catalog; Daymet remains BLOCKED.
- CI package checks now cover clean-wheel imports/README/replay across the
  existing Python 3.9–3.12 targets, with all wheel notebooks on 3.11. Publish
  builds gain artifact checks but no trigger, environment, permissions or
  branch-policy changes. No workflow was dispatched. New tests cover archive
  payload rejection, missing assets, version/citation consistency, editable
  rejection, kernel identity and refusal to record incomplete gates.
- Manually inspected seven current noun figures: three terrain, three roads
  and raw USGS discharge. References expose the first figure and link to the
  complete three-plot lessons; the native datum, lack of OSM/Overture scientific
  equivalence, and USGS provisional status remain explicit.
- Full non-publishing gate passed on macOS arm64 / Python 3.11.11: isolated
  build, Twine, archive inspection, fresh outside-checkout wheel-only install,
  pip check, installed grammar/compatibility checks, the actual README PRISM
  analysis and figure, candidate wheel replay, and all 12 supported notebooks
  against the exact wheel. Package code resolved to the external environment's
  site-packages; real fixtures remained external inputs. Evidence and resolved
  dependencies: artifacts/release-0.1.0/; curated record:
  manifests/releases/v0.1.0-candidate.json.
- Offline suite: 715 passed, 5 skipped; streaming contracts: 32 passed;
  Chromium built-site suite: 354 passed. Ordinary notebook execution,
  publication validation (five modules plus 12 notebooks), source/decision QA,
  all generated visual/reference/noun/streamflow/source-project checks, strict
  MkDocs build, internal file/anchor links, tracked repository policy and diff
  checks passed. Repository policy also checked all eight new files. Source
  fixture baselines retain PASS_WITH_CAVEATS, not live endpoint certification.
- After clarifying that crc32c has no direct runtime import, rebuilt the site
  strictly, rechecked all internal links and reran the affected dependency-audit
  page in Chromium (1 passed). The 21 base dependencies remain unchanged;
  review unused crc32c and cleaner optional boundaries in a separate 0.2 pass.
- Final wheel: cubedynamics-0.1.0-py3-none-any.whl (292,722 bytes), SHA256
  462b8bb41d749fd16f5e47f5e9e9f168c61ed2c44139042c4dfd99f5ce8ab029.
  Sdist: cubedynamics-0.1.0.tar.gz (253,083 bytes), SHA256
  e61f510d57592dee8a903e49a7c6c0fb3665437ffeaff62224012f6d2458eae9.
- Ready for v0.1.0rc1 review; artifacts themselves remain version 0.1.0 and no
  rc tag exists. This is a base commit plus an uncommitted, hash-recorded overlay.
  Python 3.9/3.10/3.12 CI runs are configured, not locally observed. Existing
  dependency deprecation warnings and limited provider/fixture coverage remain
  caveats. No scientific runtime edits, dependency moves, source promotion,
  commit, push, tag, publication, DOI, branch protection or permission changes.

## 2026-08-28 — Repair clean-wheel CI archive-hash validation

- User supplied Python 3.9 and 3.10 package-job failures after successful wheel
  installation and `pip check`, both using pip 23.0.1. Starting checkout was
  clean at 1628705. Reproduced the identical failure with a fresh external
  Python 3.11.11 environment and pip 23.0.1: local-wheel `direct_url.json`
  contained `archive_info: {}`. The old checker misreported absent hash
  evidence as a SHA256 mismatch. Upgrading pip in the build environment does
  not update the separate installer seeded by `python -m venv`.
- Both package/publish validation workflows and run_release_gate.py now
  upgrade the external environment's pip before installing the wheel. The
  local gate records this as mandatory `upgrade-installer` evidence. No
  workflow trigger, permission, scientific dependency or runtime change.
- check_release_artifact.py accepts modern `hashes` and legacy `hash` archive
  metadata, rejects conflicts/malformed/missing SHA256, and gives an explicit
  upgrade/reinstall diagnostic for missing evidence. Exact archive SHA256,
  installed file bytes, external import paths and editable rejection remain
  enforced. RELEASING.md documents the cause and repair procedure.
- Added 30 regression cases for metadata formats, missing/malformed/conflicting
  hashes, wrong wheels, modified installed code and installer upgrade ordering
  in both workflows and the local gate. The legacy-format regression failed
  against the original checker before the fix.
- Controlled reproduction: upgraded the same external environment to pip
  26.2.1 and reinstalled the unchanged wheel offline (`--force-reinstall
  --no-deps`). Its metadata then contained the matching SHA256. Full installed
  artifact check passed, including all 132 runtime files, package-only grammar,
  the actual real-data README PRISM analysis/figure, and existing candidate
  imports/three real USGS snapshot checks. `pip check` passed. Wheel SHA256
  remains 462b8bb41d749fd16f5e47f5e9e9f168c61ed2c44139042c4dfd99f5ce8ab029.
- Validation: offline suite 745 passed, 5 skipped, 367 deselected; strict MkDocs,
  built-site links/anchors, repository policy (1,123 tracked files) and diff
  checks passed. Evidence: artifacts/release-pip-compat/installed.json and
  offline.xml. No full release-gate/browser rerun or new release-readiness
  claim; the historical release manifest is unchanged. Linux Python 3.9/3.10
  CI jobs still need to rerun after these changes are committed/pushed; no
  commit, push, tag, deployment or publication performed here.
