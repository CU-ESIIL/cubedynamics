# Projects built with the grammar

These projects demonstrate how a shared cube grammar can support specialized
scientific vocabularies. They are examples of extending CubeDynamics, not
alternative definitions of its core.

## Included case studies

- **Synchrony** builds state, event, occurrence, severity, timing, duration,
  and coupling verbs on the common pipe contract.
- **Fire VASE** combines fire-event geometry, environmental attribution, and
  rendering through fire-specific verbs and adapters.
- **Biological coupling** rasterizes observations and aligns biological and
  environmental state cubes.
- **Suitability tubes** explores contiguous space-time regions through a
  specialized geometry vocabulary.

Some of these modules remain importable from `cubedynamics.verbs` for `0.x`
compatibility. Their scientific assumptions and project outputs should remain
documented with their owning project. Future extraction into extension packages
must use the deprecation policy described in the [public API](../project/public_api.md).

## Build your own

- [Core versus project verbs](../concepts/core_and_projects.md)
- [Write a custom verb project](../extending/custom_verbs.md)
- [Custom-verb vignette](../vignettes/custom_verb_project.ipynb)
- [Example project scaffold](https://github.com/CU-ESIIL/cubedynamics/tree/main/examples/custom_verb_project)
