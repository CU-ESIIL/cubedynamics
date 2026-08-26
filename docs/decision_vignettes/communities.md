---
description: "Dependency design for linking environmental conditions with exposed communities."
---

# Communities · Who and What Is Exposed?

<div class="cd-dependency-banner"><strong>Dependency design · not executable yet</strong><span>Exposure requires vetted population or building nouns and a coherent hazard/history noun; those public interfaces are not available.</span></div>

## The decision

Which South Dakota communities or built areas occur in landscapes with a
documented environmental hazard history or clearly measured changing
condition?

A Rapid City/Black Hills fire-history story is a plausible candidate, but it
will not be selected until structure coverage and event-perimeter sources are
validated together.

## The missing information

An environmental layer becomes more decision-relevant when the people or
assets potentially exposed are represented. Historical intersection can
describe past spatial context; it cannot by itself estimate future risk.

## The nouns

| Noun | Public status | Publication requirement |
|---|---|---|
| Population | Missing | Census vintage, unit, allocation method, uncertainty |
| Buildings | Missing | Footprint/count completeness, date, use limitations |
| Fire history | Missing | Event dates, perimeter quality, duplicate handling |
| Temperature or VPD | Implemented | Weather context only; not a hazard model |
| Roads | Missing | Network completeness and scale |

## The analytical sentence

Target grammar only:

```text
BUILT AREAS → OVERLAP DOCUMENTED FIRE HISTORY → SUMMARIZE HISTORICAL EXPOSURE CONTEXT
```

The final noun and terminology must match. Buildings support statements about
mapped structures; population supports statements about resident counts only
under the source's allocation assumptions.

## What happened?

Nothing has been calculated. Using public temperature or VPD alone would not
preserve the question because neither identifies communities or establishes a
wildfire hazard layer.

## QA publication gate

Required visible checks include structure/population coverage, event dates and
perimeters, CRS and boundary alignment, temporal compatibility, duplicate
counts, missing areas, and a direct comparison of each noun before overlap.

## Decision view

Unavailable. When implemented, the result should say “structures occurring in
landscapes with documented wildfire history” unless a validated forward hazard
model supports stronger language.

## What this does and does not tell us

The analysis could guide where to seek more detailed preparedness or asset
data. Historical overlap is not a probability forecast, vulnerability
assessment, or estimate of future loss.

## Fork this question

- Replace fire history with a defensibly measured heat condition.
- Compare buildings with population without treating them as interchangeable.
- Change the time period and state exactly what temporal claim changes.

