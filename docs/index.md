---
description: "Compose transparent, reproducible, streaming-aware analyses of spatiotemporal environmental data with the CubeDynamics pipe-and-verb grammar."
hide:
  - navigation
  - toc
---

<div class="cd-home">

<section class="cd-editorial-hero">
  <div class="cd-hero-copy">
    <p class="cd-kicker"><span></span> Open-source methods for spatiotemporal research</p>
    <h1>CubeDynamics</h1>
    <p class="cd-hero-deck">Nouns → Verbs → Answers. Compose environmental observations and small, explicit operations into an inspectable analysis.</p>
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

<section class="cd-grammar-strip" aria-label="CubeDynamics grammar example">
  <div class="cd-grammar-heading"><h2>One question, one short pipe</h2></div>
  <div class="cd-code-stage">
    <pre><code>from cubedynamics import data, pipe, verbs as v

cube = data.temperature(
    source="prism", bbox=[-105.55, 39.85, -105.05, 40.15],
    start="2024-01-01", end="2024-01-30",
)
answer = (pipe(cube) | v.mean(dim="time", keep_dim=False)).unwrap()</code></pre>
    <p>Observed daily maximum temperature → mean over the requested dates.
    Live access requires a network; <a href="learn/">Learn</a> uses a frozen real-data extract.</p>
  </div>
</section>

<section class="cd-stories">
  <h2>Where would you like to go?</h2>
  <div class="cd-gallery">
    <a class="cd-gallery-card" href="learn/"><h3>Learn</h3><p>A progressive introduction to nouns, verbs, pipes and interpretation.</p></a>
    <a class="cd-gallery-card" href="library/"><h3>Library</h3><p>Find environmental nouns, available sources, coverage and quality.</p></a>
    <a class="cd-gallery-card" href="documentation/"><h3>Documents</h3><p>Look up software behavior, arguments and return values.</p></a>
    <a class="cd-gallery-card" href="vignettes/"><h3>Vignettes</h3><p>Run real-data analyses with code, figures and provenance.</p></a>
  </div>
</section>

</div>
