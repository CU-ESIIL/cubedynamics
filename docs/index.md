---
description: "Make environmental analysis readable, reproducible, and scientifically inspectable with source-qualified nouns, semantic verbs, and authored order."
hide:
  - navigation
  - toc
---

<div class="cd-home">

<section class="cd-editorial-hero">
  <div class="cd-hero-copy">
    <p class="cd-kicker"><span></span> Open-source methods for spatiotemporal research</p>
    <h1>CubeDynamics</h1>
    <p class="cd-hero-deck">Source-qualified nouns → semantic verbs → inspectable answers. Make environmental analysis readable without hiding source identity, authored order, or evidence.</p>
    <p>Preparing 0.1.0rc1 · not yet published. <a href="getting_started/install/">Installation status and release instructions</a>.</p>
    <div class="cd-hero-actions">
      <a class="cd-action cd-action--acid" href="learn/">Learn <span aria-hidden="true">→</span></a>
      <a class="cd-action cd-action--ghost" href="vignettes/">Run a vignette <span aria-hidden="true">↗</span></a>
    </div>
  </div>
  <div class="cd-hero-art">
    <div class="cd-html-cube-hero">
      <div class="cd-cube-picker">
        <label for="hero-cube-example">Explore an example</label>
        <select id="hero-cube-example" aria-controls="hero-cube-frame" aria-describedby="hero-cube-description" disabled>
          <!-- HERO_EXAMPLE_OPTIONS -->
        </select>
      </div>
      <div class="cd-html-cube-frame cd-deferred-embed" data-deferred-embed>
        <iframe id="hero-cube-frame" src="about:blank" data-src="assets/figures/prism_boulder_tmax_cube.html" title="Interactive cube of observed PRISM daily maximum temperature" loading="lazy" sandbox="allow-scripts allow-same-origin" allowfullscreen></iframe>
        <div class="cd-embed-loader">
          <strong>Observed PRISM temperature cube</strong>
          <span>Interactive viewer loads after the page is ready.</span>
          <button type="button">Load interactive cube</button>
        </div>
      </div>
      <div class="cd-html-cube-meta">
        <p aria-live="polite"><strong id="hero-cube-kind">Interactive raster cube</strong><span id="hero-cube-description">Observed PRISM daily maximum temperature</span></p>
        <div class="cd-cube-links">
          <a id="hero-cube-open" href="assets/figures/prism_boulder_tmax_cube.html">Open full viewer <span aria-hidden="true">↗</span></a>
          <a id="hero-cube-lesson" href="vignettes/cube_from_arrays/">Lesson / source notes <span aria-hidden="true">↗</span></a>
        </div>
      </div>
      <p class="cd-html-cube-instructions">Drag the cube to rotate it. Scroll over the viewer to zoom.</p>
      <noscript><p>Choose a standalone example:</p><ul><!-- HERO_EXAMPLE_LINKS --></ul></noscript>
    </div>
  </div>
</section>

<section class="cd-manifesto">
  <p class="cd-section-label">Scientific inspectability</p>
  <h2>Rerunnable is not the same as inspectable.</h2>
  <div class="cd-manifesto-grid">
    <p class="cd-manifesto-lead">A script can run twice and still hide the scientific question it asked. Thresholding before a mean and averaging before a threshold use the same operations, but they produce different scientific objects.</p>
    <div>
      <p>CubeDynamics treats a pipeline as an executable scientific statement. The expression stays short; semantic state and an ordered trace preserve what changed; source records and bounded QA expose the evidence beneath the abstraction.</p>
      <p>Numerical work remains with xarray, Dask, and established geospatial libraries. The grammar does not choose a scientifically appropriate source or certify a decision. <a class="cd-text-link" href="concepts/scientific_inspectability/">Read the scientific framing →</a></p>
    </div>
  </div>
</section>

<section class="cd-grammar-strip" aria-label="CubeDynamics grammar example">
  <div class="cd-grammar-heading"><h2>One question, one short pipe</h2></div>
  <div class="cd-code-stage">
    <pre><code>from cubedynamics import data, pipe, verbs as v

cube = data.temperature(
    source="prism", statistic="maximum",
    bbox=[-105.55, 39.85, -105.05, 40.15],
    start="2024-01-01", end="2024-01-30",
)
answer = (pipe(cube) | v.mean(dim="time", keep_dim=False)).unwrap()</code></pre>
    <p>Observed daily maximum temperature → mean over the requested dates.
    Authored order is preserved, not rearranged. Live access requires a network;
    <a href="learn/">Learn</a> uses a frozen real-data extract.</p>
  </div>
</section>

<section class="cd-layers" aria-label="From statement to evidence">
  <div class="cd-layers-intro">
    <p class="cd-section-label">One readable expression, three inspectable layers</p>
    <h2>Keep the statement short. Keep the evidence close.</h2>
  </div>
  <ol class="cd-layer-list">
    <li><span>01</span><div><strong>Statement</strong><p>A source-qualified noun enters a pipe. Configured verbs and their parameters say what happens, in the order the researcher authored.</p></div></li>
    <li><span>02</span><div><strong>State and trace</strong><p>The current object—observation, condition, event, relationship, or summary—and every completed stage remain available for inspection.</p></div></li>
    <li><span>03</span><div><strong>Source and evidence</strong><p>Native variables, units, queries, revisions, provenance, fixtures, and bounded QA stay reachable. A common noun never implies that its sources are interchangeable.</p></div></li>
  </ol>
</section>

<section class="cd-stories">
  <h2>Where would you like to go?</h2>
  <div class="cd-gallery">
    <a class="cd-gallery-card" href="learn/"><h3>Learn</h3><p>Build an analytical statement from source-qualified nouns, verbs, authored order, state, and trace.</p></a>
    <a class="cd-gallery-card" href="library/"><h3>Library</h3><p>Find environmental nouns while keeping provider, product, units, coverage, and limitations visible.</p></a>
    <a class="cd-gallery-card" href="documentation/"><h3>Documents</h3><p>Look up scientific contracts, software behavior, arguments, return values, and evidence boundaries.</p></a>
    <a class="cd-gallery-card" href="vignettes/"><h3>Vignettes</h3><p>Follow real-data questions from context through code, figures, interpretation, and provenance.</p></a>
  </div>
</section>

</div>
