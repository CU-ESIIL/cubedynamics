---
description: "Download the current CubeDynamics overview manuscript and supplementary information."
---

# CubeDynamics overview manuscript

## CubeDynamics: An Inspectable Grammar for Environmental Data Analysis

The current package-wide manuscript explains the motivation, design, evidence,
and limits of CubeDynamics as an inspectable grammar for environmental data
analysis. It describes source-qualified nouns, named transformations, authored
order, semantic state and trace, ordinary scientific Python objects, validation,
extension boundaries, and the distinction between computational repeatability
and scientific inspectability.

| Document | Contents | Download |
| --- | --- | --- |
| Overview manuscript | 19 pages: motivation, related systems, grammar design, worked example, semantic validation, discussion, conclusions, availability, and references | <a href="../cubedynamics-overview-manuscript.pdf" download>Download the overview manuscript (PDF, 247 KB)</a> |
| Supplementary information | 33 pages: version boundaries, architecture, contracts, source inventory, QA evidence, vignette records, validation, extension status, reproduction commands, and claim-to-evidence tables | <a href="../cubedynamics-overview-manuscript-supplement.pdf" download>Download the supplement (PDF, 314 KB)</a> |

Both documents are dated **25 September 2026**. They are preserved here exactly
as supplied; no pages, figures, metadata, or manuscript content were changed
for website publication.

## Scope and version boundary

The manuscript discusses the public `0.1.0rc3` candidate and explicitly
separated repository evidence available on 25 September 2026. The public
artifact, the later repository state, and any future final release are distinct
software states. The manuscript does not make the mutable development checkout
part of the published release retroactively.

The PDFs are dated scholarly products, not live API specifications. The
installed runtime, tests, generated callable references, public API contract,
and exact Git identity remain the sources of truth for current software behavior.
Use [`cubedynamics.version_info()`](../getting_started/runtime_identity.md) to
identify the code actually imported by an analysis.

## Reading paths

- [Scientific inspectability](../concepts/scientific_inspectability.md) presents
  the central argument as website documentation.
- [Learn](../learn/index.md) turns the grammar into a guided sequence.
- [Public API and stability](../project/public_api.md) records current callable
  and maturity boundaries.
- [Methods and citation](../methods_and_citation.md) gives concise reporting and
  citation guidance.
- [Vignettes](../vignettes/index.md) provide supported executable examples on
  reviewed observational data.

## File identity

The retained SHA-256 checksums are:

```text
9980f5aaa83f3e38a72ea0d350a9675b3a22a54fc15f027ca02885c6d048adbf  overview manuscript
ea8c3ea03ddf69c799b638f38e8f9f1b2211ab55b24db3e86decaca93831d09f  supplementary information
```
