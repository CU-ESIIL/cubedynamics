# Source engineering and validation

For everyday use, start with the main noun references:
[elevation](../../library/nouns/elevation.md), [roads](../../library/nouns/roads.md),
and [streamflow](../../library/nouns/streamflow.md). Each has an executable
real-data vignette. This developer directory preserves acquisition history.

What changes when the input is terrain, a mapped road network, or observations
from a streamgage? These three contained projects test that question using real
provider data. They reuse CubeDynamics' grammar and source QA, while keeping
the source-specific meaning visible.

- [3DEP: read a landscape without downloading a tile](three_dep.md)
- [Roads: one noun, two observation systems](roads.md)
- [USGS: observations that can change after retrieval](usgs.md)
- [Generated certification evidence](evidence.md)
- [Hardened runtime candidates and production gates](production.md)

The original proofs below are retained as historical access evidence. The
new installed candidates add bounded retries, raw snapshot replay, pinned
range reads and stricter release gates. They are still not production catalog
registrations; [read the current scope and remaining gates](production.md).

These are **experimental project-owned nouns**, not additions to
`cubedynamics.data.list_sources()` or production serving revisions. Their
Python modules live under `examples/source_projects/`; install this checkout
editable and run from the repository root. Each has its own command, tests,
report, real-data figures and stop boundary. No website tab or generic source
framework was added.

## What the proofs establish

Small real requests, explicit limits, inspectable provenance, preserved native
semantics, structural/numerical checks, and reviewed diagnostic figures. They
do **not** establish spatial completeness, independent ground truth, broad
provider reliability, or suitability for a particular scientific decision.

Raw upstream samples remain in ignored artifacts. Small reviewed figures and
machine-readable evidence are published here. Rerunning a rolling query may
produce different content; retain the raw response and checksum when exact
replay matters. Publication evidence is checked offline; live provider checks
are separately marked `online` and `integration`.

[Custom nouns](../../extending/custom_nouns.md) · [Custom verbs](../../extending/custom_verbs.md) ·
[Source lifecycle](../../dev/source_lifecycle.md)
