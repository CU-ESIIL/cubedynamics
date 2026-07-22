# CubeDynamics

**Install:** `pip install cubedynamics`  →  `import cubedynamics`

**Migration note:** this project was renamed from `climate_cube_math` to `cubedynamics`.
Legacy imports will keep working for now but emit a `DeprecationWarning`; please
update your code to use the new package name.

<p align="center">
  <img src="https://raw.githubusercontent.com/CU-ESIIL/cubedynamics/main/docs/assets/img/cubedynamics_logo.png" alt="CubeDynamics" width="520">
</p>

![Tests](https://github.com/CU-ESIIL/cubedynamics/actions/workflows/tests.yml/badge.svg) ![Docs](https://github.com/CU-ESIIL/cubedynamics/actions/workflows/pages.yml/badge.svg)

CubeDynamics: a grammar of streaming environmental computation.

CubeDynamics is a Python framework for computing on environmental data streams through **spatiotemporal cubes**, rather than treating storage, retrieval, and visualization as the main product.

It is designed for scientists and data practitioners who want to reason explicitly about **space, time, scale, and events**—and to do so reproducibly and efficiently, even for large datasets.

Scientists and AI agents use the same streaming interface, so workflows can be explored interactively, scripted, or orchestrated programmatically without switching mental models.





---

## Why this project exists

Most environmental datasets already form data cubes:
- climate grids evolving through time
- vegetation indices measured repeatedly over landscapes
- disturbance events unfolding in space and time

Yet most workflows break these dimensions apart:
- spatial analysis in GIS
- temporal analysis in tables
- statistics elsewhere
- visualization last

CubeDynamics keeps **space and time together**, making spatiotemporal structure a first-class part of the analysis.

Most neighboring tools answer:

> How do I store, query, or retrieve a cube?

CubeDynamics answers:

> How do I compute on a stream of environmental data?

---

## What CubeDynamics enables

- **Spatiotemporal cube operations** (means, variance, anomalies, synchrony)
- **Grammar-based pipelines** using `pipe | verb | verb`
- **Streaming-first analysis** via VirtualCubes for large datasets
- **Event- and hull-based workflows** (fires, droughts, phenology)
- **Integrated visualization** of space–time structure

Fire events now follow a clearer object model built around:

- `FireEventDaily` for canonical FIRED-like daily event geometry
- `FireHull` for the derived fire-time hull / VASE geometry

The intent is to keep FIRED ingestion, hull geometry, environmental attribution,
cube conversion, and visualization separable so fire workflows remain part of
the same composable cube grammar as the rest of CubeDynamics.

---

## Minimal example

```python
from cubedynamics import pipe, verbs as v
import cubedynamics as cd

cube = cd.ndvi(
    lat=40.0,
    lon=-105.25,
    start="2022-01-01",
    end="2023-01-01",
)

pipe(cube) | v.anomaly() | v.variance() | v.plot()
```

This pipeline:
- loads a spatiotemporal cube
- computes anomalies through time
- measures variability at each spatial location
- visualizes the result

---

## Documentation

📘 Full documentation website 👉 https://cu-esiil.github.io/cubedynamics/

Key entry points:
- Concepts – cube abstraction, pipes & verbs, streaming
- Getting Started – first success in minutes
- Capabilities & Verbs – complete textbook-style reference
- Datasets – supported data sources, fields, citations
- Recipes – end-to-end scientific workflows

---

## Installation

### Stable release from PyPI

```bash
pip install cubedynamics
```

### Install from a tagged release

For reproducible reviews, install directly from a Git tag:

```bash
pip install "git+https://github.com/CU-ESIIL/cubedynamics.git@v0.1.0"
```

Replace `v0.1.0` with the release tag you want to test.

### Developer install

```bash
git clone https://github.com/CU-ESIIL/cubedynamics.git
cd cubedynamics
make install
make test
```

The repo includes a `.python-version` default and a `Makefile` that creates a
local `.venv/` for development. The virtual environment is intentionally ignored
by git.

See the documentation for optional extras, large-data workflows, and examples.

Useful extras:
- `pip install -e ".[test]"` for tests and packaging checks
- `pip install -e ".[docs]"` for MkDocs builds
- `pip install -e ".[viz]"` for Lexcube-backed visualization helpers

## Data and generated outputs

CubeDynamics keeps code, schemas, config templates, docs, and small fixtures in
Git. Large scientific products belong outside the repository: local scratch
roots, shared object storage, or a lakehouse path configured by the user.

Fire VASE work treats the VASE as a scientific data object first. Source fire
observations, canonical fire time, geometry, climate attribution, detected
events, derived traits, VASE slices, rendered assets, manifests, and cohort
summaries are separate versioned products. Rendered panels and PDFs are views of
those data products, not the source of truth.

Use `config/storage.example.yml` as the committed template and copy it to the
ignored `config/storage.yml` for local paths or credentials. Pipeline output
roots should be explicit and default to ignored locations such as
`./scratch/fire_vase_run/`. The repository size guardrail is configured in
`config/repository_policy.yml` and can be checked with:

```bash
python scripts/check_repository_size.py --mode tracked
```

Generated Parquet, GeoParquet, Zarr, NetCDF, GLB, TIFF, bulk rendered assets,
and runtime manifests should not be committed.

---

## Project status & scope

- Active development
- APIs are stabilizing; deprecations follow a warn-first policy
- Focused on spatiotemporal environmental analysis
- Built on top of xarray and related ecosystem tools

See the documentation for the public API and stability guarantees.

---

## Cite CubeDynamics

Please cite the project using the guidance in [CITATION.cff](CITATION.cff).
A Zenodo DOI will be added to the citation metadata after the first tagged
release is archived.

(See the documentation for dataset-specific citations.)

---

## Contributing

Contributions are welcome.
- See CONTRIBUTING.md for development guidelines
- Open issues for bugs, questions, or feature discussions

## Release (for JOSS)

- Create a Git tag (e.g., `v0.1.0`) and push it to GitHub.
- Draft a GitHub Release from the tag; Zenodo will archive the release and mint
  a DOI once connected.
- Update `CITATION.cff`, `.zenodo.json`, and `paper/paper.md` with the minted
  DOI after the archive appears.
- Ensure tests pass and documentation builds for the tagged version.
- Submit to JOSS with the tag, Zenodo DOI, and `paper/` directory included.

---

## License

MIT License (see [LICENSE](LICENSE)).
