# AGENTS.md — CubeDynamics Repository Operating Guide

This file is for autonomous/human coding agents working in this repo. It explains **how the project is organized**, **what is considered stable vs internal**, and **how to safely modify/debug/test changes**.

## 1) Project identity and architectural intent

- Package name: `cubedynamics` (formerly `climate_cube_math`).
- Core idea: a **grammar of operations** for spatiotemporal cubes using `pipe(cube) | verb() | verb()`.
- Design goals:
  - **Streaming-first** and laziness-preserving behavior.
  - **Composable verbs** (small transformations with minimal side effects).
  - Consistent cube semantics with explicit space/time dimensions.

Primary references:
- `README.md`
- `src/cubedynamics/piping.py`
- `docs/project/public_api.md`
- `PROMPT_LOG.md` for recent user goals, decisions, artifacts, and validation

## 2) Source-of-truth directories (important)

### Runtime package code (primary)
- `src/cubedynamics/**` is the actual package installed via `pyproject.toml` (`package-dir = "src"`).

### Legacy/doc mirror code (secondary)
- `code/cubedynamics/**` is a legacy/doc-oriented mirror used by documentation tooling and some guardrail tests.
- **Do not assume `code/` is authoritative** for runtime behavior.
- If a change touches patterns checked in `code/` tests (e.g., eager compute bans), verify relevant tests continue to pass.

### Tests
- Main regression suite: `tests/**`.
- Additional package-internal tests: `src/cubedynamics/tests/**`.

### Docs
- MkDocs site content under `docs/**` and nav in `mkdocs.yml`.

## 3) Public API vs internal modules

Use this boundary when making changes:

### Public/canonical API (prefer to extend here)
- `cubedynamics` top-level namespace (`src/cubedynamics/__init__.py`)
- Pipe system:
  - `cubedynamics.piping.pipe`
  - `cubedynamics.piping.Pipe`
- Verb namespace: `cubedynamics.verbs` (`from cubedynamics import verbs as v`)
- Public loaders exposed from `cubedynamics` and `cubedynamics.data.*`

### Internal/unstable (safe to refactor carefully)
- `cubedynamics.ops*`, `cubedynamics.streaming*`, `cubedynamics.ops_fire*`,
  `cubedynamics.ops_io*`, `cubedynamics.plotting*`, `cubedynamics.viewers*`,
  `cubedynamics.utils*`, `cubedynamics.config`.

### Legacy compatibility
- Renamed/legacy aliases are intentionally retained with deprecation strategy.
- Preserve backwards compatibility unless the task explicitly removes deprecated paths.

## 4) Core programming model you must preserve

## Pipe and verbs
- `pipe(value)` wraps values in `Pipe`.
- `Pipe.__or__` applies callable stages in sequence.
- Verbs are commonly factories returning inner callables (`verb(args...) -> _op(cube)`).
- Some verbs are **pass-through side-effect verbs** (e.g., plotting/viewers): preserve chainability and viewer attachment behavior.

## Cube shape and metadata conventions
- Standard dims/constants in `src/cubedynamics/config.py`:
  - time: `time`
  - spatial: `y`, `x`
  - optional: `band`
- Spatial verbs should follow `docs/design/spatial_dataset_contract.md`:
  - reliable spatial-dim inference
  - CRS inference precedence
  - boundary-inclusive geometry semantics
  - strict failure on ambiguous dimensions/CRS

## Streaming/lazy expectations
- Avoid eager `.compute()` in library paths unless truly required.
- Avoid eager disk IO side effects in core transformations.
- Keep VirtualCube workflows lazy until explicit materialization (`VirtualCube.materialize()`).
- For long climate records, prefer bounded streaming/batching patterns over
  building one huge Dask graph. Library code should stay lazy; examples may
  checkpoint final/intermediate analysis outputs when the user explicitly runs
  a long workflow.

## 5) Data/loaders overview (what talks to network)

Data sources/loaders are in:
- `src/cubedynamics/data/gridmet.py`
- `src/cubedynamics/data/prism.py`
- `src/cubedynamics/data/sentinel2.py`
- Streaming wrappers in `src/cubedynamics/streaming/` and `src/cubedynamics/prism_streaming.py`

Many integration/online tests require external services/network; keep unit paths offline-friendly.

### PRISM streaming specifics
- Runtime PRISM work lives in `src/cubedynamics/data/prism.py`.
- Real PRISM streaming currently uses the NCSCO THREDDS NetCDF Subset Service
  for daily AOI-cropped requests. Use `freq="D"` for real PRISM streaming.
- Do not silently fall back to synthetic data for science workflows.
  Synthetic PRISM data must require `allow_synthetic=True` and be clearly
  marked with provenance.
- PRISM is a CONUS/US product, not a global climate backend. For global loops,
  add or use a different global source rather than implying PRISM covers the
  globe.
- Some historical PRISM daily files have THREDDS encoding/grid quirks. Keep
  focused tests around catalog aliases, lazy NcSS requests, OPeNDAP fallback
  behavior, and coordinate/grid normalization.

## 6) Testing strategy and required commands

Pytest markers are defined in `pytest.ini`:
- `integration` → external services / heavier paths
- `online` → explicit network/cubo dependence
- `streaming` → laziness/streaming behavior

Recommended validation flow after code changes:
1. Fast local/offline suite:
   - `pytest -m "not integration" -q`
2. Targeted tests for touched area:
   - e.g., `pytest tests/test_plot_verb.py -q`
3. Optional/full if needed:
   - `pytest -q`
4. If docs or API docs changed:
   - `mkdocs build --strict`

## 7) Safe edit playbook for common tasks

## Add/modify a verb
1. Implement in appropriate module (`verbs/` and/or underlying `ops/` internals).
2. Preserve factory style and pipe compatibility.
3. Re-export in `src/cubedynamics/verbs/__init__.py`.
4. If publicly intended, ensure top-level exposure/docs alignment as needed.
5. Add/adjust tests for direct call + pipe use.

## Modify plotting/viewer behavior
1. Check invariants docs first:
   - `docs/dev/viewer_backend.md`
   - `docs/dev/cube_viewer_invariants.md`
2. Keep cube-attached elements under cube transform node.
3. Do not break time-axis orientation assumptions (front/newest convention).
4. Run viewer-related tests (`tests/test_cube_viewer*.py`, plotting tests).

## Modify spatial/fire workflows
1. Follow Spatial & CRS contract exactly.
2. Ensure reprojection rules and boundary semantics remain correct.
3. Run fire/hull + spatial tests.

## 8) Debugging checklist

When debugging a failure, quickly classify it:

- **API/export issue**
  - Check `src/cubedynamics/__init__.py` and `src/cubedynamics/verbs/__init__.py` exports.
- **Pipe semantics issue**
  - Reproduce with tiny synthetic cube and direct `pipe(...) | ...` chain.
  - Inspect pass-through flags/attachments in `piping.py`.
- **Viewer regression**
  - Use `tools/debug_viewer_pipeline.py`.
  - Confirm axis rig invariants and coordinate orientation.
- **Spatial/CRS mismatch**
  - Verify inferred dims/EPSG precedence and date normalization rules.
- **Unexpected eager compute/IO**
  - Search touched files for `.compute(`, `.to_netcdf(`, `.to_zarr(` and rerun relevant tests.

## 9) Documentation and consistency rules

- Keep docs aligned with actual API names and stability policy.
- If a user-facing behavior changes, update the most relevant docs page(s) and changelog/development docs when appropriate.
- Maintain terminology consistency: “CubeDynamics”, “pipe”, “verbs”, “spatiotemporal cube”, “streaming-first”.
- Keep `PROMPT_LOG.md` current for substantial work. Add a dated entry with:
  user goal/prompts, important design decisions, files changed or artifacts
  created, validation run, and known caveats/follow-ups. Keep it factual and
  concise; do not include secrets, credentials, private tokens, or unrelated
  chat transcript.

## 10) Practical command reference

Environment setup:
- `pip install -e .`
- `pip install -r requirements.txt` (if full deps are needed)

Useful targeted runs:
- `pytest tests/test_public_api_smoke.py -q`
- `pytest tests/test_piping_verbs.py tests/test_plot_verb.py -q`
- `pytest -m "not integration" -q`

Docs checks:
- `mkdocs serve`
- `mkdocs build --strict`

## 11) Known pitfalls

- Confusing `src/` (runtime truth) with `code/` (legacy/doc mirror).
- Breaking pipe pass-through behavior for plotting verbs.
- Violating CRS/dimension contract by silently guessing ambiguous spatial metadata.
- Accidentally introducing eager compute/IO in core code paths.
- Updating docs nav/content inconsistently.
- Treating server-side AOI streaming as cloud-optimized chunked access. THREDDS
  NcSS avoids full archive downloads, but long records can still be slow
  because they require many daily requests.
- Leaving generated artifacts or caches undocumented. Analysis outputs belong
  under `artifacts/`; source changes should not depend on those files unless a
  test or example explicitly reads them.

## 12) When in doubt

- Prefer minimal, composable changes.
- Preserve backward compatibility unless explicitly instructed otherwise.
- Add a focused regression test for every bug fix.
- Use synthetic small cubes for deterministic unit tests.

## 13) Visualization architecture and fire plot recovery plan

The repository currently contains more than one visualization backend. Treat this as a transition state, not as permission to let them drift further apart. The custom HTML/CSS/JS cube viewer exposed through v.plot() is the canonical interactive viewer for general cube rendering. The fire-specific v.fire_plot() workflow currently still exposes a Plotly-based hull figure as its primary interactive display. Future work should move toward shared space-time semantics and clearer renderer boundaries, not ad hoc backend switching.

When touching visualization code, separate four concerns: (1) event or cube data construction, (2) geometry generation, (3) scene or adapter packaging, and (4) rendering backend. Changes that blur those layers tend to create regressions and make migration harder.

Implementation rules for agents:
- Do not silently replace one viewer system with another without also updating docs, tests, and architectural notes.
- If you touch axis placement, time-depth direction, cube-attached labels, or camera semantics, read `docs/dev/cube_viewer_invariants.md` first and keep those invariants aligned.
- Fire-plot work must preserve separation between event geometry generation, climate/event data fusion, and rendering backend.
- Prefer `FireEventDaily` and `FireHull` as the canonical fire/VASE object model; keep legacy names such as `TimeHull` only as compatibility aliases unless the task explicitly removes them.
- Prefer cube-compatible outputs when possible. If a hull-to-cube or environment-attribution step is incomplete, expose a narrow documented API with a clear limitation instead of hiding the gap inside plotting code.
- Do not claim fire_plot is fully migrated unless rendering actually runs through the custom cube-viewer path.
- Do not update screenshots/docs only while leaving contradictory code behavior.
- Do not change coordinate conventions without updating `docs/dev/cube_viewer_invariants.md` and relevant tests together.
- When in doubt, prefer an adapter layer over duplicating geometry logic in two renderers.
