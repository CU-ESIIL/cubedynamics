# Development

CubeDynamics keeps the codebase small and modular so contributors can add new verbs, streaming sources, or docs without friction.

## Repository layout

```
src/
  cubedynamics/
    __init__.py           # re-exports verbs and pipe helpers
    piping.py             # Pipe class + helpers
    ops/
      __init__.py
      transforms.py       # anomaly, month_filter, etc.
      stats.py            # variance, correlation_cube stub
      io.py               # to_netcdf and future exporters
```

Tests live under `tests/` and rely on `pytest`. Documentation is built with MkDocs (Material theme).

## Adding a new verb

1. Create the implementation in an appropriate module inside `cubedynamics/ops/`.
2. Follow the factory pattern: `def verb_name(...):
       def _inner(cube):
           ...
       return _inner`.
3. Re-export the verb in `cubedynamics/verbs/__init__.py` (and `cubedynamics/__init__.py` if backward compatibility is needed) so users can `from cubedynamics import verbs as v` and call `v.verb_name` directly.
4. Document the new function under `docs/ops_*.md` and add examples using the pipe syntax.
5. Write tests that cover direct invocation and pipe usage.
6. All spatial verbs **must** follow the [Spatial & CRS Dataset Contract](design/spatial_dataset_contract.md) for dimension detection, CRS inference, and geometry alignment; reuse the shared helpers and fixtures described there.

## Streaming philosophy

- **Streaming-first** – functions should operate on iterables, chunked dask arrays, or lazy `xarray` objects whenever possible.
- **Side-effect aware** – avoid downloading entire archives; expose hooks for caching and resuming streams.
- **Composable** – keep verbs pure (no global state) so they chain cleanly in the pipe system.

## Documentation workflow

- Run `mkdocs serve` locally to preview docs at http://127.0.0.1:8000.
- Keep the navigation structure in `mkdocs.yml` aligned with the docs files.
- Update the changelog for user-facing additions.
