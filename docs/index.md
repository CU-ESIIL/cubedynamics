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
    <h1>A composable grammar for spatiotemporal science.</h1>
    <p class="cd-hero-deck">CubeDynamics provides a transparent, streaming-aware way to express environmental analyses as small, testable operations.</p>
    <div class="cd-hero-actions">
      <a class="cd-action cd-action--acid" href="grammar/">Read the core methods <span aria-hidden="true">→</span></a>
      <a class="cd-action cd-action--ghost" href="vignettes/">Run a vignette <span aria-hidden="true">↗</span></a>
    </div>
  </div>
  <div class="cd-hero-art">
    <div class="cd-html-cube-hero">
      <div class="cd-html-cube-frame">
        <iframe src="assets/figures/synchrony_occurrence_cube.html" title="Interactive occurrence synchrony cube with longitude, latitude, and time axes" loading="eager" sandbox="allow-scripts allow-same-origin" allowfullscreen></iframe>
      </div>
      <div class="cd-html-cube-meta">
        <p><strong>Live CubeDynamics viewer</strong><span>Occurrence synchrony · longitude × latitude × time</span></p>
        <a href="assets/figures/synchrony_occurrence_cube.html">Open full viewer <span aria-hidden="true">↗</span></a>
      </div>
      <p class="cd-html-cube-instructions">Drag the cube to rotate it. Scroll over the viewer to zoom.</p>
    </div>
  </div>
</section>

<section class="cd-manifesto">
  <div class="cd-data-cube cd-data-cube--manifesto" aria-hidden="true"><span></span><span></span><span></span></div>
  <p class="cd-section-label">Research design</p>
  <h2>A stable grammar for transparent, extensible analysis.</h2>
  <div class="cd-manifesto-grid">
    <p class="cd-manifesto-lead">CubeDynamics separates a small computational framework from the domain-specific methods developed by research projects.</p>
    <p>Researchers can compose operations while keeping space, time, metadata, and analytical intent visible. Project assumptions remain explicit in custom verbs instead of becoming hidden framework behavior.</p>
  </div>
</section>

<section class="cd-grammar-strip" aria-label="CubeDynamics grammar example">
  <div class="cd-data-cube cd-data-cube--grammar" aria-hidden="true"><span></span><span></span><span></span></div>
  <div class="cd-grammar-heading">
    <p class="cd-section-label">Computational model</p>
    <h2>Readable workflows. Explicit operations.</h2>
  </div>
  <div class="cd-code-stage">
    <pre><code><span class="cd-code-muted">from</span> cubedynamics <span class="cd-code-muted">import</span> pipe, verbs <span class="cd-code-muted">as</span> v

result = (
    pipe(cube)
    <span class="cd-code-acid">| v.anomaly</span>(dim=<span class="cd-code-coral">"time"</span>)
    <span class="cd-code-acid">| v.mean</span>(dim=(<span class="cd-code-coral">"y"</span>, <span class="cd-code-coral">"x"</span>))
).unwrap()</code></pre>
    <p>The same expression works with in-memory arrays and Dask-backed data while preserving a reviewable record of the analysis.</p>
  </div>
</section>

<section class="cd-stories">
  <div class="cd-data-cube cd-data-cube--stories" aria-hidden="true"><span></span><span></span><span></span></div>
  <div class="cd-stories-head">
    <div>
      <p class="cd-section-label">Reproducible examples</p>
      <h2>From method to implementation.</h2>
    </div>
    <p>Each vignette is an executable research example with deterministic inputs and a clear relationship to the public API.</p>
  </div>

  <div class="cd-story-grid">
    <a class="cd-story cd-story--feature" href="vignettes/grammar_basics/">
      <div class="cd-story-visual cd-story-visual--grammar">
        <span class="cd-visual-word">PIPE</span>
        <span class="cd-visual-symbol">|</span>
        <span class="cd-visual-word">VERB</span>
      </div>
      <div class="cd-story-copy">
        <p class="cd-story-tag">01 · Runnable notebook</p>
        <h3>Core grammar and data model</h3>
        <p>Construct a deterministic cube, compose public verbs, and inspect the resulting dimensions and metadata.</p>
        <span class="cd-story-link">Open the methods vignette →</span>
      </div>
    </a>

    <a class="cd-story" href="vignettes/lazy_composition/">
      <div class="cd-story-image">
        <img src="assets/figures/synchrony_coupling_lag_curve.png" alt="A scientific plot of synchrony across time lags">
      </div>
      <div class="cd-story-copy">
        <p class="cd-story-tag">02 · Computational scaling</p>
        <h3>Lazy composition</h3>
        <p>Verify that Dask-backed data remain lazy across an ordinary CubeDynamics pipeline.</p>
        <span class="cd-story-link">Examine the computation →</span>
      </div>
    </a>

    <a class="cd-story" href="extending/custom_verbs/">
      <div class="cd-story-image cd-story-image--coral">
        <img src="assets/figures/synchrony_event_diagnostics.png" alt="A scientific diagnostic panel showing event synchrony">
      </div>
      <div class="cd-story-copy">
        <p class="cd-story-tag">03 · Research extensions</p>
        <h3>Project-specific verbs</h3>
        <p>Encode a project’s methods and assumptions as a small, documented, and tested vocabulary.</p>
        <span class="cd-story-link">Author a custom verb →</span>
      </div>
    </a>
  </div>
</section>

<section class="cd-layers">
  <div class="cd-layers-intro">
    <p class="cd-section-label">Software architecture</p>
    <h2>A clear boundary between framework and research.</h2>
  </div>
  <ol class="cd-layer-list">
    <li><span>01</span><div><strong>Core grammar</strong><p><code>pipe</code>, <code>Pipe</code>, verb factories, and cube contracts.</p></div></li>
    <li><span>02</span><div><strong>Shared vocabulary</strong><p>Common operations such as anomaly, mean, variance, and z-score.</p></div></li>
    <li><span>03</span><div><strong>Integrations</strong><p>Data adapters, streaming execution, files, and renderers.</p></div></li>
    <li><span>04</span><div><strong>Project extensions</strong><p>Synchrony, biology, Fire VASE, and the verbs your project owns.</p></div></li>
  </ol>
</section>

<section class="cd-final-cta">
  <div class="cd-data-cube cd-data-cube--final" aria-hidden="true"><span></span><span></span><span></span></div>
  <p class="cd-section-label">Documentation and reproducibility</p>
  <h2>Inspect the method. Run the analysis.</h2>
  <div class="cd-final-actions">
    <a class="cd-action cd-action--dark" href="quickstart/">Start with the quickstart <span aria-hidden="true">→</span></a>
    <a class="cd-text-link" href="concepts/core_and_projects/">Review core and project boundaries →</a>
  </div>
</section>

</div>
