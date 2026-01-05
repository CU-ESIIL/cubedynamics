# Deprecation & Legacy Inventory

This inventory highlights modules and documents by stability class.

Legend:
- **A** Active + Public
- **B** Active + Internal
- **C** Legacy (retained for compatibility/old language)
- **D** Dead (safe to remove)

## Code modules

| Path | Class | Evidence | Proposed action |
| --- | --- | --- | --- |
| `src/cubedynamics/__init__.py` | A | Exports public symbols via `__all__` and used throughout docs/examples. | Keep; update exports when public surface changes. |
| `src/cubedynamics/piping.py` | A | `pipe` and `Pipe` referenced in docs (`concepts/grammar`, quickstart) and tests. | Keep as core entry point. |
| `src/cubedynamics/verbs/` | A | Imported as `verbs` namespace in README, docs, and examples; verbs power plotting and analysis. | Keep; add deprecations per verb if renamed. |
| `src/cubedynamics/data/{gridmet,prism}.py` | A | Loaders exposed in `cubedynamics.__all__` and docs/recipes. | Keep; treat as public loaders. |
| `src/cubedynamics/sentinel.py` | A | New Sentinel-2 loaders exposed in `__all__`; used by docs and pipelines. | Keep; deprecate older aliases. |
| `src/cubedynamics/data/sentinel2.py` | C | Older loader names (`load_s2_*`) still imported but now emit deprecations. | Keep as warning alias until removal window. |
| `src/cubedynamics/demo.py`, `src/cubedynamics/demo_vase.py` | C | Used only in exploratory examples; not referenced in nav or tests. | Move to explicit legacy/demo area or document as non-stable. |
| `src/cubedynamics/vase_viz.py` | C | Viewer convenience; not exported publicly, superseded by `verbs.plot` and `viz`. | Mark as legacy; consider redirecting users to `v.plot`. |
| `src/cubedynamics/ops/*`, `streaming/*`, `ops_fire/*`, `ops_io/*`, `viewers/*`, `utils/*`, `config.py` | B | Imported internally by verbs and pipelines; not documented as public. | Keep internal; document as unstable surface. |
| `src/cubedynamics/tests/` | B | Internal test helpers; not part of package exports. | Keep for regression coverage. |

No D-class code confidently identified; uncertain items kept as legacy aliases.

## Documentation

| Path | Class | Evidence | Proposed action |
| --- | --- | --- | --- |
| `docs/quickstart.md`, `docs/concepts/*`, `docs/verbs/*` | A | Linked in MkDocs nav; use current vocabulary. | Keep as canonical docs. |
| `docs/vase_volumes.md` | A | Canonical vase guide referenced by legacy stub. | Keep; ensure language matches glossary. |
| `docs/vase-volumes.md` | C | Legacy path kept for backward compatibility; now stub pointing to canonical page. | Keep stub; leave full content in `docs/legacy/`. |
| `docs/legacy/vase-volumes.md` | C | Archived original vase volume write-up. | Keep in legacy folder; omit from nav. |
| `docs/viewer_debug_notes.md`, `docs/streaming_renderer.md` | C | Developer notes not in nav; older terminology. | Move to `docs/legacy/` or annotate as internal references. |
| `docs/examples/*`, `docs/recipes/*` | B | Supplemental material referenced sporadically. | Keep; audit for vocabulary alignment. |

No D-class docs identified yet; treat ambiguous pages as legacy instead of deleting.

## Tests and examples

| Path | Class | Evidence | Proposed action |
| --- | --- | --- | --- |
| `tests/` (root) | B | Internal regression tests; not shipped to users. | Keep and expand to cover public API. |
| `notebooks/`, `examples/` | C | Exploratory content; not tied into nav or CI. | Keep as legacy examples; consider refreshing or moving to `docs/legacy/` later. |

This inventory should be revisited after adding deprecation warnings and redirect stubs to confirm whether any C-class items can be safely removed.
