# Climate Cube Math

`cubedynamics` provides streaming access to climate data cubes plus reusable
statistics, vegetation-index helpers, and QA visualizations for understanding
Sentinel-2, GRIDMET, PRISM, and related datasets.  This repository also
includes a MkDocs site and reproducible vignette that document the package.

## Installation

You can install the latest library directly from the repository:

```bash
pip install git+https://github.com/CU-ESIIL/climate_cube_math.git
```

During development use an editable install from the repo root:

```bash
python -m pip install -e .
```

## Quick start

```python
import cubedynamics as cd

s2 = cd.load_s2_cube(
    lat=43.89,
    lon=-102.18,
    start="2023-06-01",
    end="2023-09-30",
    edge_size=512,
)

ndvi = cd.compute_ndvi_from_s2(s2)
ndvi_z = cd.zscore_over_time(ndvi)
```

The same package still ships the ruled time hull helpers used in the training
materials:

* `cubedynamics.demo.make_demo_event()` builds a small GeoDataFrame that mimics
  how a fire perimeter evolves through time.
* `cubedynamics.hulls.plot_ruled_time_hull()` converts that data into a 3D ruled
  surface so the temporal pattern can be inspected visually.

## Documentation and vignette

The public website is generated from the `docs/` folder using MkDocs Material
and includes:

1. A concise landing page that explains the project goals.
2. A rendered copy of `docs/vignette.ipynb` so visitors can step through the
   example without leaving the site.
3. An API reference driven by `mkdocstrings` that documents the core
   `cubedynamics` modules.

To preview the site locally run:

```bash
mkdocs serve
```

## Repository layout

```
code/cubedynamics/   # installable Python package
  data/              # Sentinel-2, GRIDMET, PRISM loaders
  indices/           # vegetation index helpers
  stats/             # anomaly, rolling, correlation utilities
  viz/               # QA and lexcube visualization helpers
  utils/             # chunking, reference pixel helpers
  demo.py            # demo GeoDataFrame generator
  hulls.py           # ruled time hull plotting helper
  __init__.py

docs/
  index.md           # landing page
  api.md             # mkdocstrings API reference
  vignette.ipynb     # notebook rendered on the site
  stylesheets/
    extra.css        # small cosmetic tweaks for MkDocs Material

.github/workflows/pages.yml  # deploys the docs site to GitHub Pages
mkdocs.yml                   # MkDocs configuration
pyproject.toml               # package metadata
```

With this layout you only need to touch two places when extending the project:
add or update Python modules inside `code/cubedynamics/` and describe those
changes through Markdown or notebooks in `docs/`.

## Installation

For the streaming-first package preview install directly from GitHub:

```bash
pip install "git+https://github.com/CU-ESIIL/climate_cube_math.git@main"
```

Once published to PyPI the goal is to allow a simple install:

```bash
pip install cubedynamics
```

`cubedynamics` follows a streaming-first philosophy that prefers chunked IO over
full downloads.  The accompanying pytest suite encodes this expectation by
running streaming markers by default and skipping download-marked tests unless
explicitly requested.
