---
description: "Browse the CubeDynamics nouns, verbs, data sources, and patterns for building project-specific vocabulary."
hide:
  - navigation
  - toc
---

<div class="cd-hub">

<header class="cd-hub-hero" data-parallax>
  <div class="cd-hub-hero-copy">
    <p class="cd-hub-kicker">Library · the working vocabulary</p>
    <h1>Nouns in. Verbs through.</h1>
  </div>
  <p class="cd-hub-deck">Find the scientific data that enters a pipeline, the operations that transform it, and the patterns that let a research project speak in its own precise vocabulary.</p>
</header>

<section class="cd-hub-band">
  <div>
    <p class="cd-hub-kicker">The grammar</p>
    <h2>Small pieces, explicit meaning.</h2>
  </div>
  <p class="cd-hub-intro">A noun returns a well-described scientific cube. A verb returns a callable operation. The pipe makes their sequence visible without hiding the xarray object underneath.</p>
</section>

<section class="cd-quick-code">
  <h2>The complete analytical sentence</h2>
  <pre><code>result = (
    pipe(data.temperature(source="prism", ...))
    | v.anomaly(dim="time")
    | v.mean(dim=("y", "x"), keep_dim=False)
).unwrap()</code></pre>
</section>

<div class="cd-gallery">
  <a class="cd-gallery-card cd-gallery-card--wide" href="../data/">
    <small>Nouns</small>
    <h3>Start with a scientific thing</h3>
    <p>Temperature, precipitation, humidity, radiation, vegetation index, surface reflectance, and the vetted sources that currently implement them.</p>
    <strong>Browse scientific nouns →</strong>
  </a>
  <a class="cd-gallery-card" href="../api/verbs/">
    <small>Verbs</small>
    <h3>Transform a cube</h3>
    <p>Reducers, transforms, state and event operations, shapes, models, plotting, and project vocabulary.</p>
    <strong>Browse the verb catalog →</strong>
  </a>
  <a class="cd-gallery-card" href="../datasets/">
    <small>Sources</small>
    <h3>Choose a provider</h3>
    <p>Compare coverage, resolution, access method, limitations, and integration maturity.</p>
    <strong>Compare data sources →</strong>
  </a>
  <a class="cd-gallery-card cd-gallery-card--wide" href="../concepts/core_and_projects/">
    <small>Architecture</small>
    <h3>Know what belongs in core</h3>
    <p>Separate reusable grammar from the assumptions and vocabulary owned by a research project.</p>
    <strong>Review the boundary →</strong>
  </a>
</div>

<section class="cd-hub-band cd-hub-band--tint">
  <div>
    <p class="cd-hub-kicker">Extend it</p>
    <h2>Make the vocabulary match the science.</h2>
  </div>
  <p class="cd-hub-intro">Most add-ons should be small project packages: named noun wrappers for vetted inputs, verb factories for scientific operations, tests for both, and notebooks that tell the analysis story.</p>
</section>

<div class="cd-gallery">
  <a class="cd-gallery-card" href="../extending/custom_nouns/">
    <small>Project input</small>
    <h3>Make a custom noun</h3>
    <p>Normalize one trusted loader into the cube and provenance contract your project expects.</p>
    <strong>Build a noun wrapper →</strong>
  </a>
  <a class="cd-gallery-card cd-gallery-card--wide" href="../extending/custom_verbs/">
    <small>Project method</small>
    <h3>Write a custom verb project</h3>
    <p>Turn a documented scientific rule into a pipe-compatible callable that preserves coordinates and laziness.</p>
    <strong>Build a verb →</strong>
  </a>
  <a class="cd-gallery-card" href="../vignettes/custom_verb_project/">
    <small>Executable lesson</small>
    <h3>Follow the full example</h3>
    <p>See project vocabulary introduced, tested, run, plotted, and interpreted in a notebook.</p>
    <strong>Run the vignette →</strong>
  </a>
</div>

<aside class="cd-hub-note">The library documents what is implemented now. Planned nouns and aspirational APIs stay out until their loaders, tests, QA, and documentation exist.</aside>

</div>
