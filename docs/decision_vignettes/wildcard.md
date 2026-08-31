---
description: "A scientifically honest, API-current template for a South Dakota environmental decision project."
---

# What Should South Dakota Know?

<div class="cd-dependency-banner cd-template-banner"><strong>Hackathon template</strong><span>Begin with a real decision. Use only public, vetted nouns in runnable code; document unavailable nouns as dependencies.</span></div>

## The challenge

Find a real environmental decision and identify information that is usually
missing from the map used to make it. Your project should combine at least
three CubeDynamics nouns from at least two noun families, use reusable verbs,
show a source-level QA figure, and end with one decision-oriented figure.

## Start with the decision

Write one question that a planner, land manager, conservation practitioner,
water manager, rancher, emergency manager, or environmental scientist could
act on. Then write what a conventional single-layer map fails to show.

Do not begin by browsing for the most dramatic-looking data.

## Check the vocabulary before coding

```python
from cubedynamics import data

data.list_sources()          # every noun/source flavor implemented today
data.describe("temperature", "prism")
```

If a noun is absent from `data.list_sources()`, it is not a public loader. Add
it to your dependency list instead of writing a pretend call. At publication
time, the implemented families include gridded climate/weather nouns and
Sentinel-2 surface observations. Combining families may require an explicit,
scientifically justified alignment step.

## An API-current starter

This compact two-noun climate sentence uses actual current interfaces. It is a
starter, not a complete three-noun submission:

```python
from cubedynamics import data, pipe, verbs as v

temperature = data.temperature(
    source="prism", statistic="maximum", bbox=aoi,
    start="2024-07-01", end="2024-07-31",
)
precipitation = data.precipitation(
    source="prism", bbox=aoi,
    start="2024-07-01", end="2024-07-31",
)

warm = pipe(temperature) | v.quantile_state(
    quantile=0.75, direction="above"
)
dry = pipe(precipitation) | v.threshold_state(
    threshold=0.1, direction="below"
)

result = (
    pipe(warm.unwrap())
    | v.overlap(dry.unwrap())
    | v.mean(dim="time", keep_dim=False)
).unwrap()["state"]
```

`v.overlap` is for already aligned state rasters and refuses silent coordinate
alignment. It returns a condition Dataset; after `mean`, selecting `state`
gives the proportion summary used here. It is not a vector-intersection
function. A possible third public
noun is `data.vegetation_index(..., source="sentinel2")`, but you must resolve
its different grid, observation dates, clouds, and scale explicitly before
combining it. Do not paste it into `v.overlap` and hope the coordinates match.

## Your analytical sentence

Keep the logic short enough to read without surrounding prose:

<div class="cd-decision-flow cd-decision-flow--horizontal"><span>NOUN A</span><b>→</b><span>GENERAL VERB</span><b>→</b><span>NOUN B</span><b>→</b><span>SUMMARY</span></div>

Explain verbs scientifically: what state, threshold, alignment, change, or
summary did each one define? Avoid narrating ordinary Python mechanics.

## QA · Check the nouns before trusting the sentence

Show at least one source-level QA figure before the result. Good evidence
includes a point time series plus a spatial slice for climate, early/recent
panels for change, category maps and counts for polygons, or footprint/network
coverage and density sanity checks. Add numerical checks for dimensions,
units, missingness, physical ranges, dates, CRS, and exact alignment.

## Standard submission pattern

<div class="cd-decision-flow"><span>QUESTION</span><b>↓</b><span>NOUNS + SOURCE FLAVORS</span><b>↓</b><span>PIPE</span><b>↓</b><span>VISIBLE QA</span><b>↓</b><span>DECISION MAP</span><b>↓</b><span>INTERPRETATION + LIMITATIONS</span></div>

A strong submission answers: **What could a real decision maker know or do
differently after seeing this?** It also says what the result cannot establish.

## Completion checklist

1. Decision question and why someone might care
2. Missing information
3. At least three public nouns and their source flavors
4. At least two noun families
5. Short pipe using reusable verbs
6. Visible source QA and numerical sanity checks
7. One decision-oriented figure
8. Careful interpretation and explicit limitations
9. Reproducible environment, bounded AOI/time, and tests

## Fork this question

- Change the AOI while preserving the decision logic.
- Swap one source flavor and compare source assumptions.
- Replace one noun only if the new noun changes the question coherently.
