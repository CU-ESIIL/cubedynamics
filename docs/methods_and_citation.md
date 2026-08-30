# Methods & Citation

CubeDynamics is an inspectable environmental grammar around ordinary scientific
Python objects. Source-qualified nouns retain product identity; semantic verbs
and explicit parameters describe transformations; authored order supplies the
analytical syntax; and state and trace record how the scientific object changes.
Numerical work remains with xarray, Dask, NumPy, and established geospatial
libraries.

## Methods summary

- State the scientific noun and source flavor, including provider/product,
  native variable, units, statistic, spatial and temporal bounds, and revision.
- Preserve authored operation order in `pipe(noun) | verb() | verb()`; order can
  change the scientific question even when both sequences are reproducible.
- Record verb parameters and inspect `semantic_state`, `semantic_trace`,
  `explain()`, and `validate()` before crossing the local `unwrap()` boundary.
- Distinguish deferred computation from bounded source access. VirtualCube and
  Dask-backed operations can remain lazy, but laziness alone says nothing about
  remote transport behavior.
- Pair the statement with environment, input, revision, provenance, and output
  records that remain outside the pipe.

Pair the pipeline with its data provenance and the checks in
[Validation](validation/index.md), so a reader can inspect both the method and
the bounded evidence supporting its results. Fixture checks, live health,
adapter interpretation, and scientific fitness are distinct claims.

See [Scientific inspectability](concepts/scientific_inspectability.md) for the
research framing and the [current manuscript draft](documentation/main-17.pdf)
for the dated argument on which this summary is based. The draft is editorial
material, not the source of truth for current API or release status.

## Citing this project

When publishing results derived from CubeDynamics:

- Reference the package by name: **CubeDynamics**
- Include the project repository URL: <https://github.com/CU-ESIIL/cubedynamics>
- Record the exact package version or commit and the source-data revision
- Report the source-qualified nouns, authored pipeline, and verb parameters
- Preserve provenance and validation evidence with the analytical outputs
- State what happened outside the pipe, including preparation after retrieval
  and transformations after `unwrap()`

For formal citation guidance, see [CITATION.cff](CITATION.cff) or the
[repository README](https://github.com/CU-ESIIL/cubedynamics#readme). The
citation metadata currently contains no release DOI; do not invent one.
