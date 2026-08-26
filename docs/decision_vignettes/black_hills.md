---
description: "Dependency design for a Black Hills multi-noun planning review."
---

# Black Hills · Growth, Fire, and Extraction

<div class="cd-dependency-banner"><strong>Dependency design · not executable yet</strong><span>Required public feature nouns and vector/raster intersection are not implemented. This page does not display invented results.</span></div>

## The decision

Where in the South Dakota Black Hills are human development, historical
wildfire, and extractive activity close enough that a planner may want to
review several legitimate land-use considerations together?

The candidate AOI is the South Dakota portion of the Black Hills. Exact bounds
must be fixed only after the authoritative feature sources pass coverage and
edge checks; the page will not choose a visually dramatic subset first.

## The missing information

A claims map, a fire-perimeter map, or a development map cannot show whether
the same places contain several considerations. Spatial overlap would indicate
a need for closer review—not that an activity caused harm and not that any
actor is inherently bad.

## The nouns

| Noun | Public status | Publication requirement |
|---|---|---|
| Buildings | Missing | Vetted footprints or counts, dates, completeness limits |
| Fire history | Missing | Authoritative perimeters, event dates, geometry QA |
| Mining claims | Missing | Claim status/date semantics and duplicate handling |
| Protected areas | Missing | Designation categories and boundary provenance |
| VPD | Implemented (`gridmet`) | Optional weather context; not a wildfire-risk layer |

## The analytical sentence

The following is a **target grammar**, not runnable Python:

```text
BUILDINGS → INTERSECT FIRE HISTORY → INTERSECT MINING CLAIMS → SUMMARIZE BY REVIEW UNIT
```

It becomes publishable only after public nouns and general spatial verbs pass
the repository's CRS, boundary, and alignment contracts. The page deliberately
does not write `data.buildings(...)` or `v.intersect(...)` as if those APIs
already existed.

## What happened?

Nothing has been computed. The blocked operations are a geometry-aware
intersection that preserves source identity and a transparent grouped summary.
Neither operation should be hidden in a Black Hills-specific verb.

## QA publication gate

Before a result can appear, the executable page must show:

- building footprint or count coverage and known omission patterns;
- fire perimeters by event/year, including invalid-geometry counts;
- mining-claim status categories and temporal completeness;
- protected-area categories and boundary provenance;
- CRS, AOI-edge, duplicate-feature, and empty-overlap checks.

## Decision view

Unavailable until the nouns pass QA. The intended sequence is four small
source maps followed by an overlap map labeled “places for additional review,”
never “risk.”

## What this does and does not tell us

If implemented, the analysis could identify co-located mapped considerations.
It would not establish wildfire probability, ecological effect, legal status,
or causal relationships among development, fire, and extraction.

## Fork this question

- Replace mining claims with roads once both nouns are vetted.
- Summarize overlap by a documented administrative unit.
- Add VPD only as separately labeled weather context.

