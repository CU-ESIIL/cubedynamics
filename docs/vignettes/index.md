---
description: "Learn CubeDynamics through narrative, executable lessons and real-data research stories that end in interpretable figures."
hide:
  - navigation
  - toc
---

<div class="cd-hub">

<header class="cd-hub-hero" data-parallax>
  <div class="cd-hub-hero-copy">
    <p class="cd-hub-kicker">Vignettes · stories, lessons, and examples</p>
    <h1>Follow the analysis.</h1>
  </div>
  <p class="cd-hub-deck">Begin with a research situation, ask one concrete question, express the method as a small pipe, and end by reading a figure.</p>
</header>

<section class="cd-hub-band">
  <div>
    <p class="cd-hub-kicker">The learning path</p>
    <h2>Start with the data you have.</h2>
  </div>
  <p class="cd-hub-intro">The eight core notebooks use the same checksum-controlled PRISM observational extract. They move from arrays, tables, and Datasets into verbs, events, custom vocabulary, and lazy computation.</p>
</section>

<section class="cd-quick-code">
  <h2>Keep the analytical sentence short</h2>
  <pre><code>result = (
    pipe(cube)
    | v.anomaly(dim="time")
    | v.mean(dim=("y", "x"), keep_dim=False)
).unwrap()</code></pre>
</section>

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

<section class="cd-hub-band">
  <div>
    <p class="cd-hub-kicker">The lesson rhythm</p>
    <h2>Five moves in every story.</h2>
  </div>
  <ol class="cd-lesson-rhythm">
    <li><strong>Context</strong><span>Meet the data and research situation.</span></li>
    <li><strong>Question</strong><span>Decide what the analysis must reveal.</span></li>
    <li><strong>Pipe</strong><span>Read the method as one compact expression.</span></li>
    <li><strong>Figure</strong><span>See the transformation.</span></li>
    <li><strong>Interpretation</strong><span>Return the result to the question.</span></li>
  </ol>
</section>

<section class="cd-hub-band cd-hub-band--tint">
  <div>
    <p class="cd-hub-kicker">Applied collections</p>
    <h2>Move from syntax to decisions.</h2>
  </div>
  <p class="cd-hub-intro">These galleries organize longer research narratives, decision questions, domain add-ons, and reusable recipes. They distinguish executable workflows from transparent dependency designs.</p>
</section>

<div class="cd-gallery">
  <a class="cd-gallery-card cd-gallery-card--wide" href="../decision_vignettes/">
    <small>Decision lab</small>
    <h3>South Dakota environmental questions</h3>
    <p>Working lands, water, fire, habitat, and exposure stories grounded in real-data readiness and explicit missing dependencies.</p>
    <strong>Enter the Decision Lab →</strong>
  </a>
  <a class="cd-gallery-card" href="../workflows/">
    <small>Research workflows</small>
    <h3>Climate, vegetation, and remote sensing</h3>
    <p>See how the same grammar carries across environmental domains.</p>
    <strong>Browse workflows →</strong>
  </a>
  <a class="cd-gallery-card" href="../synchrony/">
    <small>Project vocabulary</small>
    <h3>Synchrony and biological coupling</h3>
    <p>Follow states, events, spatial primitives, theory, and validation boundaries.</p>
    <strong>Open synchrony stories →</strong>
  </a>
  <a class="cd-gallery-card cd-gallery-card--wide" href="../capabilities/fire-vase/">
    <small>Project vocabulary</small>
    <h3>Fire VASE and FireHull</h3>
    <p>Treat fire events as spatiotemporal objects and connect event geometry with environmental context.</p>
    <strong>Open the capability guide →</strong>
  </a>
  <a class="cd-gallery-card" href="../recipes/">
    <small>Focused examples</small>
    <h3>Recipe gallery</h3>
    <p>Adapt compact, task-oriented examples once the core grammar is familiar.</p>
    <strong>Browse recipes →</strong>
  </a>
  <a class="cd-gallery-card cd-gallery-card--wide" href="../examples_gallery/">
    <small>More educational material</small>
    <h3>Examples and task-based how-tos</h3>
    <p>Continue into climate–vegetation correlation, source-specific workflows, state cubes, synchrony, and viewer patterns.</p>
    <strong>Open the complete example collection →</strong>
  </a>
</div>

<section class="cd-hub-band">
  <div>
    <p class="cd-hub-kicker">Reproducibility contract</p>
    <h2>Run, inspect, and verify.</h2>
  </div>
  <div class="cd-hub-intro">
    <p>Every core lesson declares a Python 3 kernel, uses public APIs and observed data, contains assertions beside important contracts, and ends with an explanatory static figure. The first also includes the repository-native interactive cube viewer.</p>
    <p>The runner executes clean copies, verifies metadata and plot output, and leaves checked-in notebooks unchanged. The documentation build executes the same sources so figures appear beside code on the website.</p>
  </div>
</section>

<section class="cd-quick-code">
  <h2>Run all core vignettes</h2>
  <pre><code>python -m pip install -e ".[vignettes]"
python scripts/run_vignettes.py</code></pre>
</section>

<aside class="cd-hub-note">Review source bounds, units, checksums, cube decoding, and expected-failure controls in the <a href="../validation/">validation report</a>.</aside>

</div>
