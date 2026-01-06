# Changelog

## Unreleased

- Rebranded the project as CubeDynamics with a pipe-first API.
- Added docs for `pipe`, `anomaly`, `month_filter`, `variance`, `correlation_cube`, and `to_netcdf` verbs.
- Documented the `Pipe` helper and new operations reference structure.
- `fire_plot` now requests daily gridMET/PRISM data by default and propagates provenance metadata on returned cubes.
- Added an `allow_synthetic` safety switch to gridMET/PRISM loaders with clearer empty-time/all-NaN error messages.

## Earlier work

See the Git history for previous releases and prototype implementations while we stabilize the streaming adapters.
