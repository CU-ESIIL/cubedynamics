---
description: "Dependency design for observed surface-water change and nearby systems in South Dakota."
---

# Missouri & Watersheds · Water in a Changing Landscape

<div class="cd-dependency-banner"><strong>Dependency design · not executable yet</strong><span>Surface water, hydrography, cropland, roads, and general change/overlay support are not public CubeDynamics nouns and verbs.</span></div>

## The decision

Where has mapped surface water changed along a bounded Missouri River,
reservoir, or tributary AOI, and which human or agricultural systems are near
those changes?

A specific South Dakota water body will be selected only after source QA shows
a genuine, interpretable temporal signal. The AOI will not be cherry-picked
from a result to imply causation.

## The missing information

An early water map and a recent water map are hard to compare mentally. A
change layer is more useful when the contributing dates remain visible and
nearby systems can be inspected without treating proximity as a cause.

## The nouns

| Noun | Public status | Publication requirement |
|---|---|---|
| Surface water | Missing | Stable water classification, dates, cloud/ice and sensor QA |
| Hydrography | Missing | Flowline/waterbody identity and topology provenance |
| Cropland | Missing | Year-specific classes and accuracy limitations |
| Roads or buildings | Missing | Completeness, date, geometry, and scale limits |
| Elevation | Missing | Datum, resolution, and resampling rules |

## The analytical sentence

This is a design target, not executable code:

```text
EARLY WATER → COMPARE WITH RECENT WATER → KEEP CHANGE → OVERLAP NEARBY SYSTEMS
```

The general change verb must define categorical transitions rather than
subtracting class codes. The overlay must preserve distance or intersection
semantics explicitly.

## What happened?

No water-change result has been produced. Publishing a polished map before
validating clouds, ice, classification stability, hydrologic identity, and
temporal comparability would put documentation ahead of the package.

## QA publication gate

The future page must visibly show `EARLY WATER → RECENT WATER → CHANGE` before
any decision overlay, plus observation counts, missingness, classification
categories, spatial alignment, and a numerical change-area check.

## Decision view

Unavailable. The eventual final map may show where measured water-class
transitions occur near cropland or infrastructure. It must not infer why water
changed.

## What this does and does not tell us

Spatial and temporal co-occurrence could guide field review or data requests.
It would not establish hydrologic causation, water availability, damage, or
regulatory consequence.

## Fork this question

- Compare two defensible seasons rather than arbitrary annual snapshots.
- Replace cropland with roads after both sources pass QA.
- Ask how results change with the proximity distance made explicit.

