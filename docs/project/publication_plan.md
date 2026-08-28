# Publication-readiness audit and plan

This audit records the repository state on 12 August 2026 and turns it into a
publication plan. It distinguishes changes that are safe before a `0.x`
release from moves that need an explicit archival decision.

This page is a historical audit, not the current release checklist. For the
0.1.0 alpha candidate see [release notes](release_0_1_0.md),
[API support](api_support_0_1.md), and [dependency decisions](dependency_audit_0_1.md).
Current navigation is Home / Learn / Library / Documents / Vignettes.

## Executive finding

CubeDynamics has a coherent core, but the repository does not yet present that
core in proportion to its importance. The stable idea is the computation
grammar:

```text
cube-like value -> pipe -> verb -> verb -> result
```

Dataset access, rendering, synchrony, and Fire VASE work are valuable uses of
that grammar. They should read as integrations and project extensions, not as
four competing definitions of the package.

## Evidence from the audit

| Area | Finding | Publication risk |
| --- | --- | --- |
| Repository shape | 807 tracked files; 203 are under `output/`, `outputs/`, or `figures/` | The checkout looks like a Fire VASE research archive before it looks like a reusable grammar |
| Tracked size | 119.35 MiB total; 104.71 MiB is in those three generated-output directories | Cloning, reviewing, and archiving the software is unnecessarily heavy |
| Runtime | 117 Python files under `src/cubedynamics`; the pipe implementation is small and well tested | Domain modules visually outweigh the core abstraction |
| Documentation | 220 files with overlapping top-level, `concepts/`, `recipes/`, `howto/`, and legacy pages | Readers have several plausible starts and cannot tell which pages are canonical |
| API docs | MkDocs discovered Python from `code/`, the legacy mirror, rather than `src/` | Published reference could disagree with the installed package |
| Examples | Several prominent grammar examples used `v.aggregate()` and `v.detrend()`, which are not exported verbs | The first explanation of the grammar was not runnable |
| Notebooks | 16 tracked notebooks had no executed code cells; several lacked kernel metadata and some used network-only sources | There was no small, supported, offline reproducibility set |
| Dependencies | Dataset, geospatial, visualization, and notebook dependencies are all installed with the base package | The install surface does not yet express core versus integrations |
| Research products | Fire VASE scripts, schemas, manuscripts, results, and rendered outputs are interleaved with package material | A project built with CubeDynamics can be mistaken for CubeDynamics itself |

The audit used tracked files and current source only. It did not judge the
scientific validity of manuscript outputs or online data services.

## Target organization

The publication story has four layers:

1. **Core grammar** — `pipe`, `Pipe`, the verb-factory protocol, cube contracts,
   composition, and laziness expectations.
2. **Maintained vocabulary and adapters** — generally useful built-in verbs,
   data-source adapters, and renderers that demonstrate the protocol.
3. **Project extensions** — domain packages or project modules that create
   custom verbs, such as synchrony, biology, and Fire VASE workflows.
4. **Research products** — manuscripts, derived tables, figures, reports, and
   large rendered assets. These are citable project artifacts, not runtime
   package contents.

This distinction is conceptual in `0.1`: imports remain compatible. It becomes
physical in later releases only after deprecation and archival work.

## Work completed in this publication pass

- Reorganized the website navigation around **Core Grammar**, **Vignettes**,
  **Extend the Grammar**, **Integrations**, and **Projects Built With It**.
- Added a core-versus-project boundary and a custom-verb authoring guide.
- Added a small custom-verb project scaffold under
  `examples/custom_verb_project/`.
- Added deterministic, offline notebooks that are both website pages and
  downloadable Jupyter notebooks.
- Added a notebook execution command and CI check.
- Pointed API discovery at `src/`, the runtime source of truth.
- Replaced nonexistent verbs in canonical grammar examples with exported verbs.
- Labeled the older `notebooks/` collection as exploratory rather than
  publication-verified.

## Phased publication plan

### Phase 1 — safe before the next release

- Keep the compatibility-preserving information architecture introduced here.
- Require every supported vignette to execute offline in CI.
- Require new project-specific verbs to identify their owning project and
  maturity in docs.
- Keep generated scientific products out of new commits unless they are small,
  intentional website assets.
- Add a release checklist item that checks the wheel, docs, vignettes, citation
  metadata, and repository-size policy.

### Phase 2 — archive and extract deliberately

- Publish the current Fire VASE result bundle in a DOI-bearing research
  archive, record checksums and the release/tag that produced it, then remove
  duplicated generated HTML/PDF/PNG/CSV products from the software repository.
- Move Fire VASE manuscript history and analysis scripts to a project
  repository or a clearly bounded `projects/fire-vase/` tree.
- Decide whether synchrony, biology, tubes, and Fire VASE are maintained
  built-ins or separately versioned extension packages. Use deprecations before
  changing imports.
- Remove the `code/` mirror after confirming no remaining docs or guardrail test
  requires it.

### Phase 3 — reduce the install surface

- Measure import and install impact, then define a minimal core dependency set.
- Move data sources, geospatial operations, notebook tooling, and renderers into
  named optional extras without breaking common installs.
- Consider an extension entry-point mechanism only after two independent
  project packages need discovery. Plain Python verb factories are sufficient
  today.

## Publication gates

A release candidate should satisfy all of the following:

- `pytest -m "not integration and not online" -q`
- `python scripts/run_vignettes.py`
- `mkdocs build --strict`
- wheel build and clean-environment import
- no canonical example references an unexported verb
- no supported vignette requires credentials or an unrecorded download
- generated project products have an explicit archival and provenance policy

## Decisions still requiring maintainers

The generated Fire VASE artifacts may be evidentiary products for a manuscript.
Deleting them from Git without first archiving and checksum-recording them would
trade clarity for lost provenance. The recommended decision is to archive the
bundle first, then remove it in a dedicated, reviewable change.

Similarly, physically extracting domain modules is a packaging and governance
decision, not a documentation cleanup. The current pass makes the boundary
clear while preserving every documented import.
