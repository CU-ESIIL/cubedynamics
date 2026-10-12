# Design origins and related systems

Main §2 and SI S2–S4 preserve context that exceeds the short JOSS paper.
CubeDynamics developed across climate, vegetation, fire, terrain, roads,
streamflow, synchrony, teaching, and decision projects. The author's account
connects named analytical stages in Ben Fry's information-design work with
the narrative continuity of R tabular workflows and the grammar of graphics.
Moving to xarray and Dask motivated retaining readable progression alongside
environmental source identity and changing object interpretation.

This is design history, not comparative usability evidence. Literate
programming, transformations among data states, and computational notebooks
provide related precedents for explaining executable work. The manuscript
does not report improved comprehension, productivity, adoption, or decisions.

## Complementary layers

| Tradition or system | Existing role | CubeDynamics relationship |
| --- | --- | --- |
| NumPy, xarray, Dask | Arrays, labels, deferred/parallel computation | Reused numerical foundation |
| Rasterio/rioxarray, GeoPandas/Shapely, STAC | Raster/vector handling, geometry, asset descriptions | Data and geospatial infrastructure |
| Relational and Earth-observation cubes | Multidimensional aggregation and sampled fields | Precedents for cube organization |
| Map, cubic map, array and coverage algebra | Local, neighborhood, zonal, global and multidimensional operations | Precedents for verbs; algorithms not claimed as new |
| Analysis-ready and semantic cubes | Preprocessing, comparability, query semantics | Complementary preparation and interoperability |
| xclim, clisops, intake-esm, ESMValTool | Indicators, operations, catalogs, evaluation recipes | Specialist methods and data systems used alongside the grammar |
| Kepler, Pegasus, CWL, WINGS, openEO | Execution, portable workflows, constraints, process graphs | Broader orchestration scope than the local pipe |
| ModelBuilder and GeoJModelBuilder | Graphical geoprocessing composition | Related visible-sequence design |
| SWEET, observation ontologies, SSN/SOSA, variable descriptions | Formal concepts and relations | Richer semantic standards; CubeDynamics is not a formal ontology |
| Provenance models and RO-Crate | Input/derivation records and archival packaging | Broader records needed beyond a local trace |

The grammar uses ordinary Python syntax and a pragmatic contract vocabulary.
It does not implement a complete language or environmental ontology. State
is a compact interpretation rather than proof of metadata correctness.
For the full scholarly attributions, consult main Table 1 and SI S3 and their
reference lists; the new JOSS bibliography is a shorter, separate collection.

## Contribution routes

Researchers can report scientific boundaries in a vignette or project verb.
Software engineers can improve reusable contracts, tests, provenance, QA,
packaging, and documentation. Source maintainers contribute trusted loading,
dimensions, units, CRS, provider/product identity, reviewed fixtures, QA, and
serving history. Domain-method developers can retain assumptions in ordinary
Python functions with direct/piped tests and interpretation guidance.
Reviewers follow the expression into source and evidence records.

Project-specific work need not acquire a new container or plugin registration.
Promotion into shared vocabulary requires stronger public contracts, tests,
source review, generated references, and an executable example. See
[core and project vocabulary](../concepts/core_and_projects.md),
[custom nouns](../extending/custom_nouns.md),
[custom verbs](../extending/custom_verbs.md), and
[contributing](../dev/contributing.md).

## Future synthesis

Main §6 imagines larger multivariate specifications while retaining distinct
analytical paths and evidence. Current linear pipes and a bounded two-input
example do not establish arbitrary branch-and-join synthesis, automatic
harmonization, national scalability, uncertainty propagation, autonomous
source selection, or scientific judgment. Agent tool use is a design
hypothesis with no reported agent or tool-selection evaluation.

Source: [main, pp. 3–5 and 11–12](../assets/manuscripts/2026-10-12/main-39.pdf#page=3)
and [SI, pp. 3–7](../assets/manuscripts/2026-10-12/supplement-11.pdf#page=3).
