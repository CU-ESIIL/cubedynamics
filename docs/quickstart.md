---
description: "Install CubeDynamics, load vetted observational data, and write a first pipe-and-verb analysis."
hide:
  - navigation
  - toc
---

<div class="cd-hub">

<header class="cd-hub-hero" data-parallax>
  <div class="cd-hub-hero-copy">
    <p class="cd-hub-kicker">Get started · one noun, one pipe, two verbs</p>
    <h1>From data to question.</h1>
  </div>
  <p class="cd-hub-deck">Start with observed temperature, keep the analytical sentence short, and leave with a result you can inspect and plot.</p>
</header>

<section class="cd-hub-band">
  <div>
    <p class="cd-hub-kicker">01 · Install</p>
    <h2>A small core, familiar data structures.</h2>
  </div>
  <div>
    <p class="cd-hub-intro">CubeDynamics composes operations on xarray objects. The package supplies the grammar; data adapters supply the observations.</p>
  </div>
</section>

<section class="cd-quick-code">
  <h2>Install the package</h2>
  <pre><code>pip install cubedynamics</code></pre>
</section>

<section class="cd-hub-band cd-hub-band--tint">
  <div>
    <p class="cd-hub-kicker">02 · Load a noun</p>
    <h2>Ask for the scientific thing first.</h2>
  </div>
  <p class="cd-hub-intro">This request uses observed PRISM daily maximum temperature near Boulder. It requires network access and retains provider, product, units, query, and retrieval metadata on the returned cube.</p>
</section>

<section class="cd-quick-code">
  <h2>Load observed temperature</h2>
  <pre><code>from cubedynamics import data, pipe, verbs as v

temperature = data.temperature(
    source="prism",
    statistic="maximum",
    bbox=[-105.55, 39.85, -105.05, 40.15],
    start="2024-01-01",
    end="2024-01-30",
)</code></pre>
</section>

<section class="cd-hub-band">
  <div>
    <p class="cd-hub-kicker">03 · Write the method</p>
    <h2>Read the analysis as a sentence.</h2>
  </div>
  <p class="cd-hub-intro">Calculate the daily anomaly at each cell, then average across space. Parentheses make the sequence clear and defer unwrapping until the final result.</p>
</section>

<section class="cd-quick-code">
  <h2>Compose two verbs</h2>
  <pre><code>spatial_anomaly = (
    pipe(temperature)
    | v.anomaly(dim="time")
    | v.mean(dim=("y", "x"), keep_dim=False)
).unwrap()

spatial_anomaly.plot()</code></pre>
</section>

<aside class="cd-hub-note">That is the whole model: a noun supplies a cube; the pipe makes a sequence explicit; verbs express what happens next.</aside>

<section class="cd-hub-band">
  <div>
    <p class="cd-hub-kicker">Choose the next path</p>
    <h2>Learn by doing or browse the vocabulary.</h2>
  </div>
  <p class="cd-hub-intro">The learning gallery tells complete analysis stories. The library is the faster route when you already know whether you need a noun, verb, source adapter, or project extension.</p>
</section>

<div class="cd-gallery">
  <a class="cd-gallery-card cd-gallery-card--wide" href="../vignettes/">
    <small>Guided learning</small>
    <h3>Run a complete vignette</h3>
    <p>Follow context, question, pipe, figure, and interpretation in one executable notebook.</p>
    <strong>Open the vignette gallery →</strong>
  </a>
  <a class="cd-gallery-card" href="../library/">
    <small>Vocabulary</small>
    <h3>Browse nouns and verbs</h3>
    <p>Find data access, transformations, renderers, and extension patterns.</p>
    <strong>Open the library →</strong>
  </a>
  <a class="cd-gallery-card" href="../getting_started/install/">
    <small>Environment</small>
    <h3>Installation options</h3>
    <p>Set up editable, notebook, and development environments.</p>
    <strong>Review installation →</strong>
  </a>
  <a class="cd-gallery-card cd-gallery-card--wide" href="../documentation/">
    <small>Technical depth</small>
    <h3>Inspect every contract</h3>
    <p>Move into API reference, streaming, validation, visualization, and development architecture.</p>
    <strong>Open documentation →</strong>
  </a>
</div>

</div>
