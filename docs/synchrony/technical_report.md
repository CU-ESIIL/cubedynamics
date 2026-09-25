---
description: "Download the current technical report and supplementary information for the cold- and warm-temperature synchrony study."
---

# Synchrony technical report

## The Spatial Organization of Cold and Warm Temperature Synchrony

The ASymClim Working Group's current technical report presents the scientific
motivation, definitions, validation, Colorado analysis, finite-range pilot,
continuous-decay analysis, interpretation, and limitations behind the local
climate-tail synchrony work documented on this site.

| Document | Contents | Download |
| --- | --- | --- |
| Technical report | 22 pages: framing, methods, validation, results, discussion, conclusions, data/code availability, and references | <a href="../spatial-organization-cold-warm-temperature-synchrony.pdf" download>Download the technical report (PDF, 2.3 MB)</a> |
| Supplementary information | 38 pages: detailed definitions, calculation semantics, spatial diagnostics, sensitivity analyses, computational reproducibility, observational comparison, limitations, figures, and reference tables | <a href="../spatial-organization-cold-warm-temperature-synchrony-supplement.pdf" download>Download the supplement (PDF, 3.8 MB)</a> |

Both documents are dated **25 September 2026**. They are preserved here exactly
as supplied; no pages, figures, metadata, or scientific content were changed
for website publication.

## Scope of the scientific snapshot

The report analyzes daily PRISM temperature from 1 November 2023 through
30 January 2024. It defines cold synchrony from jointly selected lower-tail
TMIN values, warm synchrony from jointly selected upper-tail TMAX values, and
`Delta S = S_cold - S_warm`. The main statewide calculation uses a 100 km
observation window over Colorado, with bounded analyses extending to 500 km to
study empirical range and continuous spatial decay.

The evidence concerns spatial organization during one winter window. It does
not establish historical trends, persistent climate regimes, universal
characteristic distances, or dispersal kernels. The GHCN-Daily comparison is
observational agreement rather than an independent holdout because PRISM
incorporates station information and exact station membership is unavailable.

## Relationship to the software documentation

The PDFs are dated scientific products. The installed implementation, public
API, tests, and generated callable references remain authoritative for current
software behavior. Start with the
[local climate-tail synchrony recipe](../recipes/spatial_synchrony_signature.md)
for the current verb grammar, or read the
[continuous-decay guide](empirical_synchrony_decay.md) for a focused explanation
of d25, d50, d75, effective synchrony length, and multiscale slopes.

## File identity

The retained SHA-256 checksums are:

```text
c65743903d182627fd792055c554eba24277aba6e8f5db3072d3d816e35c32a9  technical report
52d31187b75e15bbe67477bb5532438876a4f1c51be170820cc0183c2f421cc4  supplementary information
```
