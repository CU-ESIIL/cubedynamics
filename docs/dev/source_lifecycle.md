# Source lifecycle, revisions, and certification

CubeDynamics has one catalog: the noun/source records used by
`data.sources()`, `data.describe()`, and the noun loaders. Source lifecycle
metadata extends those records; it is not a second registry and it does not
change the `pipe(cube) | verb()` grammar.

## The identity model

Four identities answer different questions:

| Identity | Question | Example |
| --- | --- | --- |
| Scientific noun | What phenomenon does the analysis need? | `temperature` |
| Source flavor | Which implemented provider/product path supplies it? | `prism` |
| Upstream identity | Which provider-native assets or records answered this request? | catalog URL, dataset URL, item IDs, processing baseline |
| Serving revision | Which CubeDynamics interpretation and adapter contract produced it? | `temperature.prism@2026-08-26.1` |

A serving revision has the exact form `noun.source_flavor@YYYY-MM-DD.N`. It is
immutable: a schema, semantic, or adapter interpretation change creates a new
candidate revision rather than rewriting the meaning of an old one.

`source_mode` describes how the upstream source advances:

- `snapshot`: a named release does not extend in place;
- `rolling`: content may extend while the serving interpretation remains the
  same. Retrieval/query time and provider identity still record what was seen.

Provider version strings are not invented. Each catalog record declares an
`upstream_identity_strategy`; each returned noun cube records the provider,
product, endpoint, strategy, any identity fields the adapter actually
observed, and retrieval time. When the provider adapter exposes no exact
native identity, provenance says so explicitly.

## Validity is not availability

`revision_status` answers whether a serving revision is scientifically usable:

- `VALIDATED`
- `SUPERSEDED`
- `ROLLED_BACK`

`live_health` answers whether the current remote service is working:

- `HEALTHY`
- `DEGRADED`
- `UNAVAILABLE`
- `STALE`

These axes are intentionally independent. For example, a checksum-controlled
offline PRISM revision can remain `VALIDATED` during a THREDDS outage, while
its live health becomes `UNAVAILABLE`. Static catalog metadata starts `STALE`;
the separately scheduled online lane is responsible for fresh health evidence.

## Schema fingerprints

`data.schema_fingerprint(cube)` produces a versioned SHA-256 over normalized,
scientifically meaningful xarray structure:

- variable and coordinate names;
- dimension names and each variable's dimension order;
- dtypes, units, calendar, fill/nodata, and categorical flags;
- CRS and grid-mapping metadata.

Dimension lengths, Dask chunk shapes, retrieval timestamps, array values, and
mapping order are excluded. Equivalent bounded requests therefore share a
fingerprint, while a units, dtype, dimension-order, CRS, or grid-mapping change
does not. Fingerprinting stays metadata-only and does not compute a lazy cube.

## Certification outcomes and gates

Every certification uses explicit outcomes: `NOT_TESTED`, `PASS`,
`PASS_WITH_CAVEATS`, `FAIL`, or `BLOCKED`. Passing certification cannot contain
a failed or blocked gate. The existing offline source-QA runner records these
gate groups:

1. endpoint verification (explicitly `NOT_TESTED` in offline mode);
2. bounded sample retrieval and fixture integrity;
3. reusable profile and observed schema;
4. source-specific numerical science;
5. visual evidence and provider-native identity.

Offline certification and live-source checks are different modes. Offline
checks use reviewed, checksum-controlled observational extracts and are stable
in CI. Live checks detect endpoint and upstream drift, but service outages do
not retroactively invalidate the reviewed offline baseline.

Pre-registration source proofs may use `serving_revision=None` in a
`CertificationRecord`. That means **no serving revision has been assigned**,
not a new version or a promotion. Registered serving records still require a
valid immutable identifier and the existing promotion gates. See the three
[contained source projects](../data/source_projects/index.md).

## Reusable QA profiles

The first profile library is available through `data.list_qa_profiles()` and
`data.evaluate_qa_profile()`:

| Profile | Useful checks |
| --- | --- |
| `climate_continuous_daily` | numeric continuous variables, units, CRS, x/y coordinates, unique increasing daily time |
| `continuous_raster_static` | numeric raster, units, CRS, finite unique one-dimensional x/y coordinates; temporal layers are allowed |
| `feature_line` | positive feature count, line-only geometries, identifiers, CRS, valid geometries |
| `station_timeseries` | station IDs and locations, numeric variables, units, unique stations, increasing time |

Profiles are structural contracts, not substitutes for source science. A
source integration adds its own physical ranges, cross-variable relationships,
checksum, provenance, and plot review on top of a reusable profile.

## Change classification

Upstream observations are classified before maintenance work:

| Change | Default response |
| --- | --- |
| `CONTENT_EXTENSION` | Keep a rolling revision if interpretation is unchanged; snapshots require a candidate revision |
| `OBSERVATION_UPDATE` | Routine provisional/value/status refresh: retain and compare retrievals; keep a rolling interpretation unchanged. A snapshot change still requires a candidate. |
| `NEW_SNAPSHOT_RELEASE` | Create and certify a candidate revision |
| `SCHEMA_CHANGE` | Create a candidate and review the adapter |
| `SEMANTIC_CHANGE` | Create a candidate with scientific and adapter review |
| `HISTORICAL_REVISION` | Create a candidate and compare old/new history |
| `SERVICE_HEALTH_CHANGE` | Update live health only |

`data.decide_source_change()` makes those defaults deterministic and testable.
Promotion still requires reviewed evidence; this helper does not promote a
source automatically.

## Serving history, promotion, and rollback

`cubedynamics.data/serving_history.json` is the small source-controlled ledger.
Each immutable entry records candidate/current/retired stage, scientific
status, creation and promotion dates, adapter version, schema fingerprint,
normalization contract, QA evidence, and caveats. `data.serving_history()` and
`data.current_revision_record()` read it; `data.validate_promotion()` requires
a validated candidate, passing certification, schema fingerprint, and QA link.
`data.rollback_target()` refuses rollback unless a previously validated retired
revision actually exists. These functions validate proposed transitions; they
do not silently rewrite history.

## Schema drift beyond xarray

`data.normalize_vector_schema()` and `data.normalize_api_schema()` provide
dependency-light contracts for future vector and station/API sources.
`data.compare_normalized_schemas()` reports added, removed, and changed paths
alongside expected and observed fingerprints, so a drift review is evidence
rather than a single mismatched hash.

## Live certification evidence

`scripts/run_live_source_certification.py` reuses the same QA profile on a tiny
remote sample and writes JSON under `artifacts/source_qa/live/`. The existing
weekly online workflow runs it and uploads the records. Endpoint availability
updates `live_health`; it never changes historical revision validity. Missing
credentials or an inaccessible provider produce `BLOCKED`/`UNAVAILABLE`, not a
synthetic sample or a false pass.

## Current milestone boundary

Daymet now has an immutable candidate record and bounded credentialed NCSS
request builder, but remains outside noun discovery. ORNL DAAC currently
requires NASA Earthdata authentication and the unauthenticated service returns
401, so promotion is blocked until a credentialed subset can be reviewed and
checked in under the approved fixture policy. This state is deliberately
visible in serving history and live-certification evidence.
