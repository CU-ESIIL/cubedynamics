---
description: "Participant and complete worked notebooks for the CubeDynamics EDS seminar."
---

# EDS seminar

Work through CubeDynamics 0.1.0rc3 across four environmental stories: Working
Lands, a Boulder cold snap, multivariate weather and remote sensing. Both
notebooks use the same code and make live PRISM, gridMET and Sentinel-2
requests, so an internet connection and provider availability are required.

<div class="cd-gallery">
  <a class="cd-gallery-card cd-gallery-card--wide" href="participant/">
    <small>Follow along</small>
    <h3>Participant notebook</h3>
    <p>The clean, runnable supershowcase notebook for working through every story during the seminar.</p>
    <strong>Open the participant notebook →</strong>
  </a>
  <a class="cd-gallery-card cd-gallery-card--wide" href="answers/">
    <small>Scroll or review</small>
    <h3>Complete worked notebook</h3>
    <p>The same supershowcase with saved outputs, figures, tables and execution diagnostics.</p>
    <strong>Open the worked notebook →</strong>
  </a>
  <a class="cd-gallery-card" href="eds_seminar_supershowcase.pdf">
    <small>No Python required</small>
    <h3>PDF walkthrough</h3>
    <p>A 43-page export of the completed run with the code, explanations, figures and tables.</p>
    <strong>Open the seminar PDF →</strong>
  </a>
</div>

## Download

| Version | Use it for | Notebook file |
| --- | --- | --- |
| Participant | Follow along and run each story yourself | <a href="participant/participant.ipynb" download>Download participant notebook</a> |
| Complete | Review every result and saved figure without rerunning | <a href="answers/answers.ipynb" download>Download complete worked notebook</a> |
| PDF | Follow the completed run without Python | <a href="eds_seminar_supershowcase.pdf" download>Download the 43-page PDF</a> |

The install cell is pinned to the public `v0.1.0rc3` Git commit rather than
PyPI, where rc3 is not currently available. Start in a fresh Python 3 kernel.
The initial install and the observational data requests require network access;
the saved outputs in the complete version are a seminar snapshot, not a live
source-health or scientific-certification claim.
