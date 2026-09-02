# Changelog

## 0.1.0rc3 — prepared, not yet released

- Carries the release-workflow ordering fix that validates an exact tagged
  checkout before same-run artifacts are downloaded into it.
- Preserves the strict clean-source guard and the scientific behavior tested in
  the earlier release candidates.

## 0.1.0rc2 — tagged 2026-09-02; superseded before publication

- Generalized release identity, artifact names, candidate manifests, and the
  verification-only tag workflow so later prerelease and stable versions do
  not require version-specific YAML edits.
- Bound explicit GitHub and PyPI publication to a version- and commit-specific
  bundle whose wheel, sdist, checksums, and passing gate manifest are verified
  immediately before the public write.
- Preserved the scientific behavior and the historical RC1 evidence; this is a
  release-process hardening candidate, not a new scientific feature release.

## 0.1.0rc1 — released 2026-08-31

- Corrected contradictory installation claims identified by an independent
  outside-user test. Public wheel/PyPI commands are explicitly post-publication.
- Prepared real RC-versioned wheel/sdist artifacts, GitHub Release asset upload,
  checksums, and a no-checkout quickstart using existing public reviewed data.
- Preserved source candidate boundaries and all mandatory release checks.
- Kept VirtualCube's legacy annual tile aliases working with pandas 3 without
  changing calendar boundaries, eager/lazy behavior, or source selection.

- First public alpha; [release notes and limitations](project/release_0_1_0.md).
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
