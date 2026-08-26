---
description: "Dependency design for conservation-priority overlap in South Dakota."
---

# Habitat Squeeze · Conservation Under Multiple Pressures

<div class="cd-dependency-banner"><strong>Dependency design · not executable yet</strong><span>Conservation, management, infrastructure, extraction, and agricultural feature nouns are not implemented as vetted public loaders.</span></div>

## The decision

Where do mapped roads, development, extraction, or agriculture overlap places
already identified by an authoritative source as conservation priorities?

The eventual South Dakota AOI should be selected from a named conservation
question and source jurisdiction, not from whichever overlay looks busiest.

## The missing information

A conservation layer identifies a priority under a particular policy or
scientific framework. A pressure layer identifies a mapped human activity.
Neither alone shows where the two deserve joint review, and their overlap is
not proof of harm.

## The nouns

| Noun | Public status | Publication requirement |
|---|---|---|
| Critical habitat | Missing | Species/designation identity, effective dates, legal caveat |
| Protected areas | Missing | Designation type, manager, and boundary provenance |
| Land management | Missing | Agency/ownership categories and update date |
| Roads and buildings | Missing | Scale, date, completeness, and geometry QA |
| Claims or cropland | Missing | Status/year semantics and category accuracy |

## The analytical sentence

Target grammar only:

```text
CONSERVATION PRIORITY → OVERLAP MAPPED HUMAN PRESSURES → SUMMARIZE WITHOUT RANKING ACTORS
```

A general density or proximity operation may be justified, but it must declare
distance units, CRS, edge effects, and whether it counts features or occupied
area. No source-specific “habitat squeeze” verb should conceal those choices.

## What happened?

No overlap was computed because the nouns are not public. This page documents
the scientific contract the integrations must meet.

## QA publication gate

The future vignette must show conservation categories, pressure layers
separately, date compatibility, geometry validity, CRS, category counts,
coverage gaps, and sensitivity to any distance parameter.

## Decision view

Unavailable. The intended progression is `CONSERVATION VALUE + HUMAN
PRESSURES → PLACES OF OVERLAP`, with the contributing layers visible beside
the result.

## What this does and does not tell us

The analysis could identify places that merit review under the selected source
definitions. It would not rank good and bad actors, establish impact, or replace
species- and site-specific assessment.

## Fork this question

- Compare road proximity with mapped claims as separate views.
- Change the conservation designation while retaining its source meaning.
- Test whether conclusions persist across defensible proximity distances.

