# Notebook status

This directory contains exploratory and historical notebooks. Several use
online datasets, optional visualization backends, or APIs that were current
when the notebook was created. They are useful development records, but they
are not the publication reproducibility suite.

The supported vignettes live under [`docs/vignettes/`](../docs/vignettes/).
Those notebooks:

- render directly on the documentation website;
- use deterministic, offline inputs;
- have complete kernel metadata;
- are executed by `python scripts/run_vignettes.py` and CI; and
- are kept free of saved outputs so reviews see code rather than stale results.

When an exploratory notebook becomes a supported vignette, reduce it to one
scientific story, replace ambient paths and credentials with explicit inputs,
add assertions for its important result, and add it to the vignette runner.
