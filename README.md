# CubeDynamics

**Install:** `pip install cubedynamics`  →  `import cubedynamics`

**Migration note:** this project was renamed from `climate_cube_math` to `cubedynamics`.
Legacy imports will keep working for now but emit a `DeprecationWarning`; please
update your code to use the new package name.

<p align="center">
  <img src="https://raw.githubusercontent.com/CU-ESIIL/cubedynamics/main/docs/assets/img/cubedynamics_logo.png" alt="CubeDynamics" width="520">
</p>

![Tests](https://github.com/CU-ESIIL/cubedynamics/actions/workflows/tests.yml/badge.svg) ![Docs](https://github.com/CU-ESIIL/cubedynamics/actions/workflows/pages.yml/badge.svg)

CubeDynamics is a composable grammar for spatiotemporal cubes.

Its stable center is deliberately small: wrap a cube with `pipe`, then apply
plain Python verbs with `|`. Data adapters, renderers, and scientific workflows
connect to that grammar; they are not competing cores.

It is designed for scientists and data practitioners who want to reason explicitly about **space, time, scale, and events**—and to do so reproducibly and efficiently, even for large datasets.

The same expression works in a notebook, a script, a streaming job, or an
agent-driven workflow.

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

## The package has layers

| Layer | Role | Examples |
| --- | --- | --- |
| **Core grammar** | Compose cube operations | `pipe`, `Pipe`, verb factories, cube contracts |
| **Built-in vocabulary** | Common operations | `v.mean`, `v.anomaly`, `v.variance`, `v.zscore` |
| **Integrations** | Connect external systems | dataset loaders, streaming adapters, renderers |
| **Project extensions** | Add domain-specific verbs | synchrony, biology, Fire VASE, your own package |

Existing `0.x` imports remain compatible while the documentation makes these
ownership boundaries explicit.

---

## Minimal scientific example

```python
from cubedynamics import data, pipe, verbs as v

cube = data.temperature(
    source="prism",
    statistic="maximum",
    bbox=[-105.75, 39.50, -104.75, 40.50],
    start="2024-01-01",
    end="2024-01-30",
)

result = (
    pipe(cube)
    | v.anomaly(over="time")
    | v.variance(over="time", keep_dim=False)
)

print(result.explain())
validated = result.validate()
summary = result.unwrap()
```

Loading names the scientific noun and source flavor. The pipe stays focused on
the analysis. Source-variable names, provider, query, CRS, normalization, and
retrieval details remain attached as provenance.

The repository's [narrative vignettes](https://cu-esiil.github.io/cubedynamics/vignettes/)
run offline from a checksum-controlled observational PRISM extract. CubeDynamics
never silently substitutes generated measurements when a scientific source is
unavailable.

Project-specific verbs use the same protocol:

```python
def clip_values(low, high):
    def _op(cube):
        return cube.clip(min=low, max=high)
    return _op

clipped = (pipe(cube) | clip_values(0, 1)).unwrap()
```

---

## Documentation

📘 Full documentation website 👉 https://cu-esiil.github.io/cubedynamics/

Key entry points:

- [Core grammar versus project verbs](https://cu-esiil.github.io/cubedynamics/concepts/core_and_projects/)
- [Semantic grammar and analysis coaching](https://cu-esiil.github.io/cubedynamics/concepts/semantic_grammar/)
- [Narrative, executable vignettes](https://cu-esiil.github.io/cubedynamics/vignettes/)
- [Write a custom verb project](https://cu-esiil.github.io/cubedynamics/extending/custom_verbs/)
- [Public API and stability](https://cu-esiil.github.io/cubedynamics/project/public_api/)
- [Publication audit and plan](https://cu-esiil.github.io/cubedynamics/project/publication_plan/)
- [Manuscript working drafts](paper/README.md) - supplied drafts and editorial
  citation notes, separate from validated software reference.

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
- `pip install -e ".[vignettes]"` for notebook kernels and vignette execution
- `pip install -e ".[viz]"` for Lexcube-backed visualization helpers

Run the publication notebooks without changing their saved outputs:

```bash
python scripts/run_vignettes.py
```

The vignette collection contains eight independent, offline notebooks. Each
lesson begins with a research situation and a concrete question, makes the
analytical pipe easy to see, and ends by interpreting a figure. Together they
cover cubes from arrays, tidy tables, and multi-variable Datasets; statistical
transforms; states, events, synchrony; custom project verbs; and Dask-backed
lazy execution. The runner verifies that every notebook emits its plot.

## Data and generated outputs

CubeDynamics keeps code, schemas, config templates, docs, and small fixtures in
Git. Large scientific products belong outside the repository: local scratch
roots, shared object storage, or a lakehouse path configured by the user.

The included Fire VASE project treats the VASE as a scientific data object first. Source fire
observations, canonical fire time, geometry, climate attribution, detected
events, derived traits, VASE slices, rendered assets, manifests, and cohort
summaries are separate versioned products. Rendered panels and PDFs are views of
those data products, not the source of truth.

The manuscript-scale Fire VASE workflow now has a dedicated documentation page:
`docs/workflows/fire_vase_developmental_morphology.md`. It describes the
real-data FIRED population run, centroid and perimeter climate-attribution
tables, developmental morphospace products, manuscript figures, PDF/DOCX
outputs, validation checks, and current limitations.

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

The current repository still contains a historical tracked Fire VASE result
bundle. The [publication plan](docs/project/publication_plan.md) recommends
archiving that bundle with a DOI and checksums before removing it from Git.

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
