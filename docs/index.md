---
hide:
  - navigation
  - toc
---

<div class="cd-home">

<section class="cd-editorial-hero">
  <div class="cd-hero-copy">
    <p class="cd-kicker"><span></span> Open-source · grammar-first · streaming-aware</p>
    <h1>Make cubes<br><em>speak.</em></h1>
    <p class="cd-hero-deck">CubeDynamics turns spatiotemporal data into readable scientific stories—one composable verb at a time.</p>
    <div class="cd-hero-actions">
      <a class="cd-action cd-action--acid" href="vignettes/">Run a vignette <span aria-hidden="true">↗</span></a>
      <a class="cd-action cd-action--ghost" href="grammar/">Meet the grammar <span aria-hidden="true">→</span></a>
    </div>
  </div>
  <div class="cd-hero-art" aria-label="Cube plus verb becomes a transformed cube">
    <div class="cd-orbit cd-orbit--one"></div>
    <div class="cd-orbit cd-orbit--two"></div>
    <div class="cd-cube-stack">
      <div class="cd-cube-token cd-cube-token--input">
        <span class="cd-token-label">cube</span>
        <span class="cd-token-meta">time · y · x</span>
      </div>
      <div class="cd-verb-token">
        <span>+</span>
        <strong>verb()</strong>
      </div>
      <div class="cd-cube-token cd-cube-token--output">
        <span class="cd-token-label">result</span>
        <span class="cd-token-meta">lazy · named · ready</span>
      </div>
    </div>
    <p class="cd-art-caption">A small grammar.<br>A huge field of view.</p>
  </div>
</section>

<section class="cd-manifesto">
  <p class="cd-section-label">The big idea</p>
  <h2>The grammar is the core.<br><span>Projects bring the verbs.</span></h2>
  <div class="cd-manifesto-grid">
    <p class="cd-manifesto-lead">Environmental science already has arrays, catalogs, renderers, and cloud archives. CubeDynamics gives them a shared language for computation.</p>
    <p>Wrap a cube. Apply a verb. Keep space, time, metadata, and intent visible. Build project-specific vocabularies without turning every scientific assumption into framework code.</p>
  </div>
</section>

<section class="cd-grammar-strip" aria-label="CubeDynamics grammar example">
  <div class="cd-grammar-heading">
    <p class="cd-section-label">One line, many scales</p>
    <h2>Readable enough<br>to reason about.</h2>
  </div>
  <div class="cd-code-stage">
    <div class="cd-code-dots" aria-hidden="true"><span></span><span></span><span></span></div>
    <pre><code><span class="cd-code-muted">from</span> cubedynamics <span class="cd-code-muted">import</span> pipe, verbs <span class="cd-code-muted">as</span> v

result = (
    pipe(cube)
    <span class="cd-code-acid">| v.anomaly</span>(dim=<span class="cd-code-coral">"time"</span>)
    <span class="cd-code-acid">| v.mean</span>(dim=(<span class="cd-code-coral">"y"</span>, <span class="cd-code-coral">"x"</span>))
).unwrap()</code></pre>
    <p>NumPy-sized today. Dask-backed tomorrow. The expression stays legible.</p>
  </div>
</section>

<section class="cd-stories">
  <div class="cd-stories-head">
    <div>
      <p class="cd-section-label">Start with a story</p>
      <h2>See the grammar<br>doing science.</h2>
    </div>
    <p>Runnable notebooks, project vocabularies, and research workflows—each built on the same small compositional idea.</p>
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
        <h3>The core grammar</h3>
        <p>Build a deterministic cube, compose public verbs, and unwrap the result—offline, in minutes.</p>
        <span class="cd-story-link">Open the vignette ↗</span>
      </div>
    </a>

    <a class="cd-story" href="vignettes/lazy_composition/">
      <div class="cd-story-image">
        <img src="assets/figures/synchrony_coupling_lag_curve.png" alt="A scientific plot of synchrony across time lags">
      </div>
      <div class="cd-story-copy">
        <p class="cd-story-tag">02 · Streaming mindset</p>
        <h3>Lazy by design</h3>
        <p>Watch Dask-backed data stay lazy across an ordinary CubeDynamics pipeline.</p>
        <span class="cd-story-link">Follow the computation ↗</span>
      </div>
    </a>

    <a class="cd-story" href="extending/custom_verbs/">
      <div class="cd-story-image cd-story-image--coral">
        <img src="assets/figures/synchrony_event_diagnostics.png" alt="A scientific diagnostic panel showing event synchrony">
      </div>
      <div class="cd-story-copy">
        <p class="cd-story-tag">03 · Extend the language</p>
        <h3>Your science, your verbs</h3>
        <p>Turn a project’s methods and assumptions into a small, tested vocabulary.</p>
        <span class="cd-story-link">Build a project verb ↗</span>
      </div>
    </a>
  </div>
</section>

<section class="cd-layers">
  <div class="cd-layers-intro">
    <p class="cd-section-label">Know what you are using</p>
    <h2>One ecosystem.<br>Four clear layers.</h2>
  </div>
  <ol class="cd-layer-list">
    <li><span>01</span><div><strong>Core grammar</strong><p><code>pipe</code>, <code>Pipe</code>, verb factories, and cube contracts.</p></div></li>
    <li><span>02</span><div><strong>Shared vocabulary</strong><p>Common operations such as anomaly, mean, variance, and z-score.</p></div></li>
    <li><span>03</span><div><strong>Integrations</strong><p>Data adapters, streaming execution, files, and renderers.</p></div></li>
    <li><span>04</span><div><strong>Project extensions</strong><p>Synchrony, biology, Fire VASE, and the verbs your project owns.</p></div></li>
  </ol>
</section>

<section class="cd-final-cta">
  <p class="cd-section-label">Ready to move?</p>
  <h2>Bring a cube.<br><em>Leave with a workflow.</em></h2>
  <div class="cd-final-actions">
    <a class="cd-action cd-action--dark" href="quickstart/">Get started <span aria-hidden="true">↗</span></a>
    <a class="cd-text-link" href="concepts/core_and_projects/">Understand core vs. projects →</a>
  </div>
</section>

</div>
