# Public documentation generation and age audit

This audit records which documentation generation should teach first use and
which material exists only for compatibility or project history. It is a
release-maintenance control, not a claim that every prose page is an API
contract. Runtime implementations, tests, generated references, and explicit
support notes remain authoritative.

Last reviewed: **2026-09-01** for the RC1 outside-user follow-up.

## Classification rules

| Class | Meaning | Publication treatment |
| --- | --- | --- |
| **CURRENT** | Matches the supported noun/pipe/verb API and is tested or generated from runtime facts. | May teach first use and appear in primary navigation. |
| **LEGACY / COMPATIBILITY** | Retained because users or old links may depend on it, but not the recommended on-ramp. | Preserve the URL, label it, and link to current material. |
| **DEPRECATED** | Describes an API that warns and forwards to a supported replacement. | Document only in compatibility inventories; do not teach first. |
| **REMOVE FROM PUBLICATION** | Duplicate, misleading, synthetic-as-science, broken, or unsupported material with no useful URL obligation. | Exclude from the built site; delete only through an explicit archival decision. |

## Page generations

| Material | Class | Owner / evidence | Action |
| --- | --- | --- | --- |
| `docs/quickstart.md` | **CURRENT** | Installed-wheel external quickstart gate; checksum-pinned real PRISM extract | Primary reproducible on-ramp. |
| `docs/getting_started.md` and `docs/getting_started/install.md` | **CURRENT** | First-use wheel gate, release artifact checks, bounded live PRISM script | Keep short and aligned with the current release candidate. |
| `docs/learn/` | **CURRENT** | Documentation tests and semantic grammar tests | Teach nouns, verbs, order, inspection, and provenance. |
| `docs/library/` and `docs/reference/verbs/` | **CURRENT, GENERATED** | `scripts/build_reference_docs.py`; catalog, signatures, docstrings, grammar metadata | Never hand-edit generated pages. Regenerate and review diffs. |
| Supported notebooks under `docs/vignettes/` and `docs/decision_vignettes/` | **CURRENT, GENERATED/EXECUTED** | Notebook builders, wheel vignette execution, real fixture provenance | Keep all supported lessons executable with visible figures. |
| `docs/getting_started/first_prism_cube.md` | **LEGACY / COMPATIBILITY URL** | Historical inbound links | Retain as a labeled bridge to the maintained lesson. |
| `docs/dev/legacy_reference.md` | **LEGACY / COMPATIBILITY** | Historical consolidated prose | Keep under developer documentation; never use as first-use guidance. |
| Provider-specific `load_*` examples | **LEGACY / ADVANCED** when a noun exists | Public compatibility contract and provider tests | Keep only where provider controls are the topic; noun examples lead elsewhere. |
| Positional PRISM calls and old top-level transformation shortcuts | **DEPRECATED** | Runtime warnings and deprecation inventory | Keep in compatibility tests/inventory, not primary lessons. |
| Synthetic Fire VASE recipe and historical generated demonstration assets listed in `exclude_docs` | **REMOVE FROM PUBLICATION** | `mkdocs.yml` exclusion and real-data publication policy | Retain only as explicit test/history material until separately archived. |
| Unmarked exploratory files under `notebooks/` | **REMOVE FROM SUPPORTED PUBLICATION SET** | Supported-notebook metadata policy | Do not link as maintained vignettes without promotion and execution evidence. |

## First-use acceptance path

The maintained path is deliberately singular:

```text
install wheel
  → import cubedynamics
  → discover noun and source
  → retrieve reviewed observations
  → pipe through semantic verbs
  → explain / validate / inspect semantic trace
  → plot
  → unwrap
  → export
```

Offline CI runs this public sequence with an installed wheel and a bounded
observed-data-shaped control. A separate external quickstart gate retrieves the
checksum-pinned real PRISM extract. The online workflow independently executes
the bounded daily PRISM noun request; provider availability is not conflated
with offline API correctness or source certification.

## Maintenance rule

When a current example changes, update its executable checker in the same
change. Preserve useful old URLs, but convert stale first-use prose to a labeled
bridge instead of leaving multiple contradictory generations live.
