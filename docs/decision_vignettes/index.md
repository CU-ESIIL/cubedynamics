---
description: "South Dakota environmental decision examples built from explicit nouns, reusable verbs, visible QA, and careful interpretation."
---

<div class="cd-vignettes cd-decision-lab">

<header class="cd-vignettes-hero cd-decision-hero">
  <p class="cd-vignettes-kicker">Environmental Decision Vignettes</p>
  <h1>South Dakota Decision Lab</h1>
  <p class="cd-vignettes-deck">Environmental decisions rarely depend on one dataset. These examples show how CubeDynamics combines environmental nouns through short, readable analytical pipes—and how to stop when the evidence is not ready.</p>
</header>

<section class="cd-pipe-principle" aria-labelledby="decision-principle-title">
  <div>
    <p class="cd-vignettes-kicker">The repeated method</p>
    <h2 id="decision-principle-title">Check the nouns. Read the sentence. Interpret only what it measured.</h2>
    <p>Every publishable result keeps source QA beside the final decision view. A planned noun is never presented as a working loader.</p>
  </div>
  <div class="cd-decision-flow" aria-label="Question to interpretation workflow">
    <span>QUESTION</span><b>↓</b><span>NOUNS</span><b>↓</b><span>PIPE</span><b>↓</b><span>QA</span><b>↓</b><span>DECISION VIEW</span><b>↓</b><span>INTERPRETATION</span>
  </div>
</section>

</div>

## Choose a decision question

“Executable” means the page uses current public loaders and verbs, checked
observations, visible QA, and an offline notebook. “Dependency design” means
the decision is scientifically worthwhile but one or more public nouns or
general spatial operations do not yet exist. Those pages are honest design
specifications—not mock analyses.

<div class="cd-vignette-grid cd-vignette-grid--two">
  <a class="cd-vignette-card cd-vignette-card--wide cd-decision-card--planned" href="black_hills/">
    <span class="cd-vignette-number">A</span>
    <p class="cd-vignette-kind">Dependency design</p>
    <h3>Black Hills · Growth, fire & extraction</h3>
    <p>Where are development, wildfire history, and extractive activity close enough to warrant joint review?</p>
    <span class="cd-noun-list">Buildings · fire history · mining claims · protected areas</span>
    <strong>Inspect the dependency design →</strong>
  </a>
  <a class="cd-vignette-card cd-vignette-card--wide cd-decision-card--planned" href="missouri_water/">
    <span class="cd-vignette-number">B</span>
    <p class="cd-vignette-kind">Dependency design</p>
    <h3>Missouri & watersheds · Water in a changing landscape</h3>
    <p>Where has mapped surface water changed, and which human or agricultural systems are nearby?</p>
    <span class="cd-noun-list">Surface water · hydrography · cropland · roads</span>
    <strong>Inspect the dependency design →</strong>
  </a>
  <a class="cd-vignette-card cd-vignette-card--wide cd-decision-card--ready" href="working_lands/">
    <span class="cd-vignette-number">C</span>
    <p class="cd-vignette-kind">Executable now · observed data</p>
    <h3>Working Lands · Read hot-and-dry weather as two nouns</h3>
    <p>Where did unusually warm July days and trace-or-no-rain days coincide in a bounded central South Dakota window?</p>
    <span class="cd-noun-list">Temperature · precipitation</span>
    <strong>Run the decision notebook →</strong>
  </a>
  <a class="cd-vignette-card cd-vignette-card--wide cd-decision-card--planned" href="habitat_squeeze/">
    <span class="cd-vignette-number">D</span>
    <p class="cd-vignette-kind">Dependency design</p>
    <h3>Habitat Squeeze · Conservation under multiple pressures</h3>
    <p>Where do mapped human activities overlap places already identified as conservation priorities?</p>
    <span class="cd-noun-list">Critical habitat · protected areas · roads · claims</span>
    <strong>Inspect the dependency design →</strong>
  </a>
  <a class="cd-vignette-card cd-vignette-card--wide cd-decision-card--planned" href="communities/">
    <span class="cd-vignette-number">E</span>
    <p class="cd-vignette-kind">Dependency design</p>
    <h3>Communities · Who and what is exposed?</h3>
    <p>Which built areas occur in landscapes with a history of wildfire or another clearly measured condition?</p>
    <span class="cd-noun-list">Buildings · population · fire history · climate</span>
    <strong>Inspect the dependency design →</strong>
  </a>
  <a class="cd-vignette-card cd-vignette-card--wide cd-decision-card--template" href="wildcard/">
    <span class="cd-vignette-number">✦</span>
    <p class="cd-vignette-kind">Hackathon template</p>
    <h3>What should South Dakota know?</h3>
    <p>Start with a real decision, choose at least three vetted nouns, and show what the usual map leaves out.</p>
    <span class="cd-noun-list">Your question · public nouns · reusable verbs · visible QA</span>
    <strong>Fork the template →</strong>
  </a>
</div>

## What is ready today?

The [collection validation report](validation.md) is the source of truth. It
lists the exact implemented vocabulary, the working notebook's observed-data
provenance and acceptance checks, and every noun or reusable verb blocking the
four dependency designs. That ledger is intentional: these vignettes are also
a stress test of the CubeDynamics grammar.

## Run the executable decision vignette

```bash
python -m pip install -e ".[vignettes]"
python scripts/run_vignettes.py docs/decision_vignettes/working_lands.ipynb
```

The notebook is network-free because it uses a small, checksum-controlled
PRISM extract acquired by the public noun loaders. To refresh the observation
fixture from the provider, run `python scripts/build_sd_working_lands_fixture.py`
with network access, then rerun the validation suite.
