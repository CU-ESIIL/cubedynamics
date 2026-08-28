---
description: "How CubeDynamics runs reproducible publication QA locally and in continuous integration."
---

# Validation methods

The suite has five modules—data, grammar, cube, vignettes, and contrasts—and a
single runner: `scripts/run_validation.py`.

Each module writes:

- `result.json`, containing named boolean acceptance checks;
- `diagnostic.png`, a human-inspectable view of the evidence; and
- a PASS or FAIL state consumed by the suite manifest.

The runner also writes `suite_manifest.json` and `validation_report.pdf`.
Failures raise immediately and produce a nonzero command exit. CI runs the
suite with `--run-vignettes`, so a notebook execution failure, missing plot,
data mismatch, grammar mismatch, or rendering mismatch blocks publication.

## Vignette contract

All supported core and source notebooks must:

- declare an explicitly supported real input and its provenance JSON in notebook metadata;
- pass SHA-256 checks for the NetCDF input or every retained USGS response/request record;
- run offline without credentials or private paths;
- contain no random data generation;
- use the public `pipe` and verb API; and
- emit at least one static plot.

The first lesson additionally embeds the repository-native interactive viewer.
Website figures and locally executed notebooks therefore come from the same
source cells and same real observations.

The eight core lessons retain the PRISM input. Streamflow uses three real USGS
response snapshots; elevation and roads use serialized native 3DEP and
Overture/OSM extracts with hashes. Unknown input/provenance combinations are
rejected, not accepted because a notebook claims to use real data. The runner
also executes the supported Decision Lab notebook, for twelve offline notebooks
in total; [Decision Lab QA](../decision_vignettes/validation.md) checks its inputs.
Notebook output is retained in `artifacts/validation/notebook-execution.log`.

The gate also scans the primary vignette, synchrony, Fire VASE, workflow, and
recipe entry pages so they do not promote generated cubes, generated fires, or
the old demo-only routes. Historical generated recipe sources and assets remain
available to software maintainers but are explicitly excluded from the MkDocs
publication build.

## What remains generated

Deterministic arrays remain appropriate inside unit tests and negative controls
because their exact truth is known. They are excluded from the publication
vignettes and are not presented as scientific evidence. This boundary keeps
software regression tests rigorous without confusing learners about the source
of the educational data.
