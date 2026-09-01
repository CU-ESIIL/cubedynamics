# 0.1.0rc1 release notes

**First public alpha / early scientific software release candidate.** PyPI
published `0.1.0rc1` on August 31, 2026. The package version is actually
`0.1.0rc1`; it is not a relabeled `0.1.0` wheel. Publication did not assign a
DOI or promote candidate data sources.

## Installation and acceptance testing

Install the public prerelease with an explicit pin:

```bash
python -m pip install cubedynamics==0.1.0rc1
```

See [installation](../getting_started/install.md) for fresh environments,
checksums, and the distinction from a future final release. The
[quickstart](../quickstart.md) needs no source checkout.

Please report problems in [GitHub Issues](https://github.com/CU-ESIIL/cubedynamics/issues)
with the installed version, Python/platform, `pip check`, package import
path, minimal code and full traceback. Do not include credentials. A failed
public install is a release blocker, not permission to substitute a clone.

## Outside-user acceptance findings

Post-publication testing installed `0.1.0rc1` from PyPI in an external Jupyter
environment and exercised live PRISM data. The public artifact installed and
the main workflow ran, but the test exposed semantic inconsistencies in
condition reductions, variance units, overlap representation, plotting of
semantic results, and fire-workflow routing. The repository's
[RC1 validation triage](rc1_validation_triage.md) separates those defects from
intentional exact-alignment guardrails, optional Lexcube availability, invalid
random chains, and genuine fire/climate date mismatches. The corrections are
for a subsequent, separately versioned candidate; they do not alter the bytes
already published as `0.1.0rc1`.

A second naive-user pass found three first-use blockers in the published rc1:
an eager optional Sentinel-2/Rasterio import could make the entire package
unimportable on Debian/aarch64 when Rasterio's GDAL dependency could not find
`libexpat.so.1`; Boolean provenance metadata was not accepted by h5netcdf; and
the first PRISM path inherited a monthly default despite daily-only real
streaming. The checkout defers the optional compiled stack, applies a
deterministic NetCDF serialization policy, and makes maintained PRISM examples
explicitly daily. Clean Debian-slim installed-wheel checks, first-use API
acceptance, and a separate bounded online PRISM execution are required for the
next candidate. See the [triage](rc1_validation_triage.md) and
[documentation generation audit](public_docs_generation_audit.md). These fixes
also postdate the immutable public rc1 artifact.

## Ready for documented use

- A composable pipe grammar over labeled spatiotemporal objects, with ordinary
  callable/custom-verb support and explicit result boundaries.
- Maintained vocabulary for transformation, reduction, states/events and
  comparisons, with factory/direct-call distinctions in reference pages.
- Eight documented catalog nouns backed by gridMET, PRISM and Sentinel-2;
  explicit source/statistic selection and preserved provenance.
- Twelve supported offline notebooks with reviewed external observations,
  figures and interpretation. Fixtures belong to the checkout, not the wheel.
- Source schema, QA, revision and certification architecture that separates
  endpoint availability from scientific suitability.
- Wheel/sdist inspection, isolated installed-wheel first-use and README tests,
  clean Debian-slim import checks on x86_64 and aarch64, and a release notebook
  mode that verifies exact wheel identity in each kernel.

The [0.1 API contract](api_support_0_1.md) names the stable subset. This is not a
promise that every exported callable or metadata report is permanently frozen.

## Usable candidates, not promoted sources

3DEP elevation, Overture/OSM roads, and USGS streamflow are installed candidate
adapters with explicit source-specific imports, bounded acquisition and real
offline lessons. They have no production serving revision and remain outside
catalog discovery. Successful import or notebook execution is not promotion.

## Project-specific vocabulary

Fire VASE, synchrony, biology and tubes remain in the distribution for current
0.x compatibility. Their methods and assumptions are separate from the core
grammar. Fire plotting still uses Plotly; the general cube viewer is the
custom HTML/CSS/JavaScript renderer. No research outputs were deleted or major
modules extracted during this release pass.

## Known limitations

- Remote services can be unavailable. Offline QA does not establish new live
  source PASS results or guarantee throughput for large requests.
- Shared nouns do not harmonize temperature units/statistics, grids, masks,
  vertical datums, source revisions or native road classes. Overture includes
  OSM; comparisons are not independent ground truth. USGS observations may be
  provisional and revised later.
- Daymet remains **BLOCKED**, outside implemented discovery, with its existing
  authentication/access review incomplete. See [Daymet status](../datasets/daymet.md).
- Some paths need optional decoders/backends; the base install remains broad.
  See the [dependency audit](dependency_audit_0_1.md).
- Coaching/report schemas and early APIs can evolve before 1.0.
  `v.correlation_cube` and `v.fit_model` remain reserved, not implemented.
- `climate_cube_math` remains a warning-emitting compatibility namespace.
- No release DOI exists yet. Add only a genuinely assigned archival DOI after
  a separately authorized release, keeping both citation records synchronized.

## Release evidence

The curated candidate record lives in `manifests/releases/` in the repository;
large logs and executed notebooks remain under ignored `artifacts/release-0.1.0rc1/`.
Records distinguish the base commit from uncommitted release-hardening changes,
actual Python versions exercised from configured CI targets, and fixture checks
from live certification. Rebuild after release-relevant changes; old hashes do
not validate a new artifact.
