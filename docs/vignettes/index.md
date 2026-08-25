---
description: "Learn CubeDynamics through narrative, executable lessons that begin with a research question and end with an interpretable figure."
---

<div class="cd-vignettes">

<header class="cd-vignettes-hero">
  <p class="cd-vignettes-kicker">Learn by following an analysis</p>
  <h1>Vignettes</h1>
  <p class="cd-vignettes-deck">Each lesson begins with a familiar data situation, asks one concrete question, expresses the analysis as a small pipe, and ends by reading a figure.</p>
</header>

<p><strong>One evidence base:</strong> every lesson uses the same checksum-controlled
PRISM observational extract. Review its source, bounds, units, and acceptance
checks in the <a href="../validation/data/">validation report</a>.</p>

<section class="cd-pipe-principle" aria-labelledby="pipe-principle-title">
  <div>
    <p class="cd-vignettes-kicker">The central idea</p>
    <h2 id="pipe-principle-title">Keep the analytical sentence short.</h2>
    <p>Preparing data can take several lines. The scientific operation should still be easy to see, explain, change, and review.</p>
  </div>
  <pre><code>result = (
    pipe(cube)
    | v.anomaly(dim="time")
    | v.mean(dim=("y", "x"), keep_dim=False)
).unwrap()</code></pre>
</section>

</div>

## Start with the data you have

Choose the first lesson that resembles your starting point. These stories all
arrive at the same `(time, y, x)` cube contract.

<div class="cd-vignette-grid cd-vignette-grid--three">
  <a class="cd-vignette-card" href="cube_from_arrays/">
    <span class="cd-vignette-number">01</span>
    <p class="cd-vignette-kind">You have an array</p>
    <h3>From values to a scientific cube</h3>
    <p>Add coordinates, units, and provenance; compare a map with a pixel history; then rotate the cube.</p>
    <strong>Begin with NumPy →</strong>
  </a>
  <a class="cd-vignette-card" href="cube_from_tidy_table/">
    <span class="cd-vignette-number">02</span>
    <p class="cd-vignette-kind">You have observations</p>
    <h3>From a tidy table to a comparable signal</h3>
    <p>Reshape rows into a cube and use one clean verb to standardize every location through time.</p>
    <strong>Begin with pandas →</strong>
  </a>
  <a class="cd-vignette-card" href="cube_from_dataset/">
    <span class="cd-vignette-number">03</span>
    <p class="cd-vignette-kind">You have several variables</p>
    <h3>Ask two questions of one Dataset</h3>
    <p>Select aligned variables, preserve their meanings, and compose a separate pipe for each question.</p>
    <strong>Begin with xarray →</strong>
  </a>
</div>

## Follow the grammar into an analysis

Once a cube is ready, continue with the story closest to the work you want to
do. The code remains small even as the scientific vocabulary becomes richer.

<div class="cd-vignette-grid cd-vignette-grid--two">
  <a class="cd-vignette-card cd-vignette-card--wide" href="grammar_basics/">
    <span class="cd-vignette-number">04</span>
    <p class="cd-vignette-kind">You want a readable method</p>
    <h3>Write the analysis as a sentence</h3>
    <p>See direct and piped calls agree, combine built-in and ordinary functions, and identify the minimal grammar.</p>
    <strong>Learn the core pipe →</strong>
  </a>
  <a class="cd-vignette-card cd-vignette-card--wide" href="verbs_gallery/">
    <span class="cd-vignette-number">05</span>
    <p class="cd-vignette-kind">You want to explore possibilities</p>
    <h3>Ask several questions of one cube</h3>
    <p>Compare means, variance, anomalies, standardized values, project functions, and model-ready shapes.</p>
    <strong>Explore the verb gallery →</strong>
  </a>
  <a class="cd-vignette-card cd-vignette-card--wide" href="states_and_events/">
    <span class="cd-vignette-number">06</span>
    <p class="cd-vignette-kind">You care about episodes</p>
    <h3>Follow cold from value to event</h3>
    <p>Turn measurements into states, states into events, and events into a spatial relationship.</p>
    <strong>Follow the event story →</strong>
  </a>
  <a class="cd-vignette-card cd-vignette-card--wide" href="custom_verb_project/">
    <span class="cd-vignette-number">07</span>
    <p class="cd-vignette-kind">Your project has a method</p>
    <h3>Give the project its own verb</h3>
    <p>Encode a scientific rule as a small callable factory and keep project assumptions visible.</p>
    <strong>Build a custom verb →</strong>
  </a>
  <a class="cd-vignette-card cd-vignette-card--wide" href="lazy_composition/">
    <span class="cd-vignette-number">08</span>
    <p class="cd-vignette-kind">Your cube is larger</p>
    <h3>Scale the same analysis lazily</h3>
    <p>Keep the grammar unchanged while Dask delays computation until the final result is needed.</p>
    <strong>Follow the lazy workflow →</strong>
  </a>
</div>

## The rhythm of every lesson

<ol class="cd-lesson-rhythm">
  <li><strong>Context</strong><span>Meet the data and the research situation.</span></li>
  <li><strong>Question</strong><span>Decide what the analysis must reveal.</span></li>
  <li><strong>Pipe</strong><span>Read the method as one compact expression.</span></li>
  <li><strong>Figure</strong><span>See the transformation rather than only inspecting an array.</span></li>
  <li><strong>Interpretation</strong><span>Connect the visual result back to the question.</span></li>
</ol>

## Run the vignettes

From a repository checkout:

```bash
python -m pip install -e ".[vignettes]"
python scripts/run_vignettes.py
```

To edit them interactively:

```bash
python -m pip install jupyterlab
jupyter lab docs/vignettes/
```

The source notebooks are small and offline. The runner executes clean copies,
verifies the real-data metadata and static plot output, and leaves the checked-in
notebooks unmodified. The documentation build executes the same sources and
places their figures beside the code on the website.

## Reproducibility contract

- Every lesson declares a Python 3 kernel and uses only public APIs.
- Every lesson uses the checked-in PRISM observational fixture; the complete
  URL and SHA-256 source record is checked in beside it.
- Publication lessons contain no random or generated measurement values.
- No lesson requires a token, network service, private path, or hidden state.
- Assertions sit beside important contracts so a broken example fails loudly.
- Each lesson ends with an explanatory static figure; the first also includes
  the repository-native interactive cube viewer.
- The [validation suite](../validation/index.md) executes the notebooks and
  checks data, grammar, decoded cube pixels, and expected-failure controls.
