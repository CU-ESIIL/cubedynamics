# Changelog

## 0.1.0 candidate — not yet released

- First public alpha target; [release notes and limitations](project/release_0_1_0.md).
- Preserved the core grammar, eight catalog nouns and candidate-source boundary.
- Excluded repository/internal tests from wheel and sdist; retained viewer
  templates, serving history and the deprecated compatibility namespace.
- Added exact-wheel installation, canonical README and notebook validation.
- Synchronized citation metadata and documented the [0.1 API support contract](project/api_support_0_1.md).

## Unreleased

- Rebranded the project as CubeDynamics with a pipe-first API.
- Added docs for `pipe`, `anomaly`, `month_filter`, `variance`, and `to_netcdf`; `correlation_cube` remains reserved, not implemented.
- Documented the `Pipe` helper and new operations reference structure.
- `fire_plot` now requests daily gridMET/PRISM data by default and propagates provenance metadata on returned cubes.
- Added an `allow_synthetic` safety switch to gridMET/PRISM loaders with clearer empty-time/all-NaN error messages.
- `load_prism_cube` now returns a DataArray when a single variable is requested, matching docs examples.
- Fixed cube viewer rotation so drag/zoom updates the cube as well as axis labels.
- Standardized PRISM precipitation units to millimeters and aligned cube viewer rotation variables with the wrapper element.

## Earlier work

See the Git history for previous releases and prototype implementations while we stabilize the streaming adapters.
