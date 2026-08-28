---
description: "Real-data analyses with explicit questions, compact pipelines, figures and reproduction instructions."
---

# Vignettes

Run a complete analysis: Context → Question → Pipe → Figure → Interpretation.
For a short introduction to the grammar, start with [Learn](../learn/index.md).

## Executable real-data notebooks

These eight notebooks use the same reviewed PRISM extract. Each tells a
scientific story and includes working code, figures, Data used, Reproduce and
See also sections. [Read the shared structure](structure.md).

<div class="cd-gallery">
  <a class="cd-gallery-card" href="cube_from_arrays/">
    <small>01 · You have an array</small>
    <h3>Build a scientific cube</h3>
    <p>Add coordinates, units, and provenance; compare a map with a pixel history; then rotate the cube.</p>
    <strong>Begin with NumPy →</strong>
  </a>
  <a class="cd-gallery-card cd-gallery-card--wide" href="cube_from_tidy_table/">
    <small>02 · You have observations</small>
    <h3>Make locations comparable</h3>
    <p>Reshape rows into a cube and use one clean verb to standardize every location through time.</p>
    <strong>Begin with pandas →</strong>
  </a>
  <a class="cd-gallery-card cd-gallery-card--wide" href="cube_from_dataset/">
    <small>03 · You have several variables</small>
    <h3>Ask two questions of one Dataset</h3>
    <p>Select aligned variables, preserve their meanings, and compose a separate pipe for each question.</p>
    <strong>Begin with xarray →</strong>
  </a>
  <a class="cd-gallery-card" href="grammar_basics/">
    <small>04 · You want a readable method</small>
    <h3>Write analysis as a sentence</h3>
    <p>Compare direct and piped calls, combine built-in and ordinary functions, and see the minimal grammar.</p>
    <strong>Learn the core pipe →</strong>
  </a>
  <a class="cd-gallery-card" href="verbs_gallery/">
    <small>05 · You want possibilities</small>
    <h3>Explore the verb gallery</h3>
    <p>Compare means, variance, anomalies, standardized values, project functions, and model-ready shapes.</p>
    <strong>Browse working verbs →</strong>
  </a>
  <a class="cd-gallery-card cd-gallery-card--wide" href="states_and_events/">
    <small>06 · You care about episodes</small>
    <h3>Follow cold from value to event</h3>
    <p>Turn measurements into states, states into events, and events into a spatial relationship.</p>
    <strong>Follow the event story →</strong>
  </a>
  <a class="cd-gallery-card cd-gallery-card--wide" href="custom_verb_project/">
    <small>07 · Your project has a method</small>
    <h3>Give the project its own verb</h3>
    <p>Encode a scientific rule as a small callable factory and keep project assumptions visible.</p>
    <strong>Build a custom verb →</strong>
  </a>
  <a class="cd-gallery-card" href="lazy_composition/">
    <small>08 · Your cube is larger</small>
    <h3>Scale the same analysis lazily</h3>
    <p>Keep the grammar unchanged while Dask delays computation until the final result is needed.</p>
    <strong>Follow the lazy workflow →</strong>
  </a>
</div>


## Keep the analytical sentence short

```python
result = (
    pipe(cube)
    | v.anomaly(dim="time")
    | v.mean(dim=("y", "x"), keep_dim=False)
).unwrap()
```

Put source acquisition and preparation before the pipe. Explain the baseline
and interpretation after it. See [anomaly](../reference/verbs/anomaly.md) and
[mean](../reference/verbs/mean.md) for their canonical argument reference.

## Explore a noun

Three different objects, the same grammar. Each lesson uses frozen real source
data, explains the baseline and limitations, and produces three inline figures.

<div class="cd-gallery">
  <a class="cd-gallery-card" href="elevation_landscape/">
    <small>Terrain · USGS 3DEP</small>
    <h3>Read a landscape at its native scale</h3>
    <p>Inspect a real hillside, center on a local baseline, and reduce the map to a west–east profile.</p>
    <strong>Explore elevation →</strong>
  </a>
  <a class="cd-gallery-card" href="roads_local_network/">
    <small>Networks · Overture and OSM</small>
    <h3>Compare mapped roads carefully</h3>
    <p>Keep native segments and classes, clip an explicit area, and measure length with two small project verbs.</p>
    <strong>Explore roads →</strong>
  </a>
  <a class="cd-gallery-card" href="streamflow_snapshots/">
    <small>Water · USGS stations</small>
    <h3>Keep the observations and their evidence</h3>
    <p>Inspect real discharge, subtract a one-day mean, and reuse the pipe at three identified stations.</p>
    <strong>Explore streamflow →</strong>
  </a>
</div>

References: [elevation](../library/nouns/elevation.md) ·
[roads](../library/nouns/roads.md) · [streamflow](../library/nouns/streamflow.md).

## Other analyses and educational material

| Collection | What to expect |
| --- | --- |
| [Working Lands](../decision_vignettes/working_lands.ipynb) | Executed notebook: observed hot-and-dry weather in South Dakota |
| [South Dakota Decision Lab](../decision_vignettes/index.md) | One executable analysis; other questions are labeled dependency designs |
| [Research workflows](../workflows/index.md) | Domain workflow directories and analysis reports |
| [Fire VASE](../capabilities/fire-vase.md) | Observed FIRED/gridMET examples and explicit renderer limitations |
| [Synchrony](../synchrony/index.md) | Methods and project vocabulary; not a second core grammar |
| [Recipes](../recipes/index.md) | Task-oriented live-data code; provider access may be required |
| [Examples and how-tos](../examples_gallery.md) | Additional source and workflow guidance |

## Reproduce

From the repository root:

```bash
python -m pip install -e ".[vignettes]"
python scripts/run_vignettes.py
```

The runner executes clean copies of all twelve supported notebooks, verifies
static plots, and leaves source notebooks unchanged. MkDocs renders the same
code and figures on the site. [Validation](../validation/index.md) records
the real-data checks; live-data recipes are not covered by the offline claim.
