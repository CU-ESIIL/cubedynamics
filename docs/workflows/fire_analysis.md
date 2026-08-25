# Fire Analysis

Fire workflows in CubeDynamics treat events as spatiotemporal computational objects, not just polygons or screenshots.

That means the workflow is about:

- event construction
- hull or VASE geometry
- environmental attribution
- comparison and explanation

## Population Fire VASE analysis

The current Fire VASE manuscript workflow scales that idea from a single event
to a population of real FIRED events. Each fire is represented as a
developmental VASE, climate is attached afterward, and the resulting tables are
used to build morphospace figures, atlases, Science-style manuscript drafts,
and Google Docs-ready documents.

Start with [Fire VASE developmental morphology](fire_vase_developmental_morphology.md)
for the manuscript-scale pipeline, including the data products, regeneration
commands, figure narrative, validation checks, and known limitations.

Recommended starting points:

- [Fire VASE developmental morphology](fire_vase_developmental_morphology.md)
- [Fire event vase + climate merge](../recipes/fire_event_vase_hull.md)
- [Real FIRED event + climate recipe](../recipes/fire_event_vase_hull.md)
- [Fire VASE / FireHull](../capabilities/fire-vase.md)
