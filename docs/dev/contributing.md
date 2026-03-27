# Contributing

Thank you for helping build CubeDynamics! This project keeps CubeDynamics lightweight, streaming-first, and well documented.

## Repository layout

```text
src/
  cubedynamics/
    __init__.py           # re-exports verbs and pipe helpers
    piping.py             # Pipe class + helpers
    ops/
      __init__.py
      transforms.py       # anomaly, month_filter, NDVI helpers
      stats.py            # variance, correlation_cube, rolling metrics
      io.py               # to_netcdf and future exporters
docs/                  # MkDocs + Material site
```

Tests live under `tests/` and rely on `pytest`. Documentation is built with MkDocs (Material theme); run `mkdocs serve` while editing docs.

## Local setup

1. Fork or branch from `main` and create feature branches for your work.
2. Install dependencies in editable mode (e.g., `python -m pip install -e ".[dev]"`).
3. Run `pytest` plus any relevant notebooks/scripts before opening a pull request.

## Adding a new verb

1. Create the implementation in `cubedynamics/ops/`.
2. Follow the factory pattern:

   ```python
   def verb_name(...):
       def _inner(cube):
           ...
       return _inner
   ```

3. Re-export the verb in `cubedynamics/verbs/__init__.py` (and optionally `cubedynamics/__init__.py`) so users can `from cubedynamics import verbs as v` and call `v.verb_name` directly.
4. Document the new function under `docs/reference/verbs_*.md` and add examples using the pipe syntax.
5. Write tests that cover direct invocation and pipe usage.

## Streaming philosophy

- **Streaming-first** – functions should operate on iterables, chunked dask arrays, or lazy `xarray` objects whenever possible.
- **Side-effect aware** – avoid downloading entire archives; expose hooks for caching and resuming streams.
- **Composable** – keep verbs pure (no global state) so they chain cleanly in the pipe system.

## Docs + website

- Keep the navigation structure in `mkdocs.yml` aligned with the docs files.
- Use the new section layout (Concepts, Getting Started, Examples, Verbs Reference, Related Work, Development) when adding content.
- Remember that Lexcube widgets do not render on the static site; include screenshots or Binder links where appropriate.

## Opening a pull request

- Describe the change, test coverage, and any data access requirements.
- Update the [Roadmap](roadmap.md) or [Changelog](changelog.md) when user-facing features ship.
- Issues and discussions are welcome for roadmap ideas, new data sources, or Lexcube visualizations.
