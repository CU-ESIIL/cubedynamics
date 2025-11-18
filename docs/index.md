# Climate Cube Math

Welcome!  This microsite and repository exist to demonstrate a single idea:
turn daily fire perimeters into an intuitive 3D "climate cube" that captures how
an event evolves through time.  Everything you need lives in two places:

1. The `cubedynamics` Python package that ships with this repo.
2. The vignette notebook that walks through the package step by step.

```bash
python -m pip install -e .
```

Once installed you can open the vignette locally or explore it directly on this
website.  The same notebook powers the tutorial tab in the navigation bar via
the `mkdocs-jupyter` plugin.

## Why keep it small?

The previous training template included dozens of how-to pages, placeholder
images, and references to shared infrastructure.  That content was helpful for a
classroom but made it hard to see the project itself.  By stripping the repo
back to a package + website we get:

- **Clarity** – all of the files in version control tell the project story.
- **Reproducibility** – the vignette is the canonical way to run the code.
- **Focus** – editing happens either in `cubedynamics/` or inside `docs/`.

## What you will find

- **Notebook vignette** – generate a synthetic event, inspect the GeoDataFrame,
  and render a ruled time hull in a few cells.
- **API reference** – short docstrings pulled straight from the Python modules
  so you always know which arguments control smoothing, rotation, or styling.

If you would like to extend the project simply add new modules inside the
package and mention them from the docs.  Everything else has been removed on
purpose to keep things lightweight.
