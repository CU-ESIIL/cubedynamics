# From source proofs to production nouns

For usage, arguments, source options and lessons, use the main noun library:
[elevation](../../library/nouns/elevation.md), [roads](../../library/nouns/roads.md),
and [streamflow](../../library/nouns/streamflow.md). This page records engineering
evidence and operational promotion requirements.

The three projects now have **installed, bounded candidate adapters**. They
are not production-certified catalog entries. The eight existing catalog
nouns and their serving histories are unchanged.

Production means reliable behavior within a declared scope, not arbitrary
global queries. A good plot, successful download or passing unit suite cannot
establish scientific suitability on its own.

## Candidate contracts

| Candidate import | Supported scope | Explicit stop boundaries |
| --- | --- | --- |
| `cubedynamics.data.usgs.streamflow` | One USGS station; continuous discharge; native units/status; `time × station` | 31 days, 10,000 observations, 7-day batches, 40 attempts, 16 MB response bodies |
| `cubedynamics.data.three_dep.elevation` | One fully covering CONUS 1/3 arc-second tile; native `y × x` | 0.02° query sides, 256 native pixels per side, 80 attempts, 8 MB bodies; no mosaic or silent clipping |
| `cubedynamics.data.roads.roads(source="overture")` | Explicit release; native road features/classes | 0.02° query sides, 5,000 features, 3 partitions, 4 row groups per partition, 400 attempts, 40 MB bodies including metadata |
| `cubedynamics.data.roads.roads(source="osm")` | Small Overpass way query; native classes/IDs | 0.02° query sides, 5,000 features, 6 attempts, 4 MB bodies; not a production application backend |

Loaders consume data explicitly. They do not acquire laziness merely by being
used with `pipe`. Static terrain gets no invented time axis; roads remain
GeoDataFrames. Use operations appropriate for the returned object. In
particular, a station series is not input to the raster cube viewer.

All candidates are in the installed runtime; none imports the `examples/`
tree. Install `cubedynamics[roads]` for Overture's optional PyArrow reader.
The capped 3DEP opener requires Rasterio 1.4 or newer and refuses an uncapped
fallback on older versions.

## A short pipe with an inspectable source

```python
from cubedynamics import pipe, verbs as v
from cubedynamics.data.usgs import streamflow

# Explicit live acquisition: choose a NEW directory for every refresh.
observations = streamflow(
    site="USGS-06730200",
    start="2026-08-26T00:00:00Z",
    end="2026-08-26T23:59:59Z",
    snapshot_dir="artifacts/my-analysis/usgs-2026-08-26",
)
departures = (pipe(observations) | v.anomaly(dim="time")).unwrap()
departures.streamflow.isel(station=0).plot()
```

Pass the same arguments with `offline=True` to verify and replay the original
bodies. A live refresh must use a new directory: existing snapshots are never
silently replaced. The [offline notebook](../../vignettes/streamflow_snapshots.ipynb)
uses three checked-in real snapshots and emits a plot for every analysis step.

USGS `approval_status`, `qualifier` and `last_modified` retain native strings.
Companion `_present` and `_is_null` coordinates distinguish absent, null and
empty fields. Only explicit missing discharge becomes NaN; nonnumeric or
nonfinite numeric text fails. UTC is explicit, duplicate observations fail,
and multiple time series require `series_id`. Provisional values are retained
with a warning, not discarded or relabeled approved.

`compare_observations(before, after)` compares values and scientific status
over identical station/series/window/units. Routine record-ID or modification
timestamp changes are not scientific changes. Raw snapshots retain both.

## Network and reproducibility safeguards

- Anonymous HTTPS with approved origins, no redirects, implicit credentials,
  synthetic substitution or automatic source switching.
- Up to three attempts for transient failures, bounded by the total request
  budget. Respect `Retry-After`; refuse waits beyond the query deadline.
- Query deadlines: USGS/3DEP 180 s, Overture 300 s, OSM 90 s. Checks occur
  between reads; socket timeouts cap individual blocked reads. These are not
  process-killing hard deadlines.
- Count response-body bytes across attempts and objects. Announced oversize
  is rejected before reading; an unannounced overrun is detected within one
  8 KiB chunk. TCP/TLS overhead is not included in these measurements.
- Strong ETag plus `If-Match` prevents assembling ranges from changed objects.
  Multipart ETags are object identities, not SHA256 content checksums.
- Exact raw bodies and request records are stored only when explicitly asked.
  Replay verifies content hashes and never falls back to network. Query-local
  memoization avoids duplicate reads; no hidden persistent cache is created.
- Overture coalesces selected compressed row-group spans before decoding; no
  unpruned whole-file scan. Declared row-group size is limited, but peak Python/
  Arrow process memory is not claimed to be a hard-capped amount.

Pinned cloud snapshots may require the same decoder versions for byte-range
replay. A new decoder can request different ranges and will fail if they were
not retained. USGS JSON replay is independent of raster/Parquet decoding.

## Measured checks, and what they do not establish

During the August 27, 2026 local validation:

- USGS: Boulder Creek (96 observations), Potomac (288), and Colorado River at
  Lees Ferry (96), all for August 26. Values/status were checked against raw
  provider responses; NetCDF round trips and piped reductions passed. All
  these retained samples were provisional. A real 50-row cursor-pagination
  query returned 96 observations across two pages; an eight-day request
  returned 768 observations across two time batches.
- 3DEP: the Boulder 99×99 window used 760,458 body bytes; an explicitly pinned
  Asheville 55×55 window used 802,007. Both retain native EPSG:4269 coordinates.
  Asheville had **no Current-tagged catalog result**; tile
  `627f3798d34e3bef0c9a3198` was selected explicitly, not presented as current.
- Overture: pinned release `2026-08-19.0` returned 528 native Boulder road
  features using 20,432,795 body bytes including metadata. Coalescing reads
  replaced hundreds of tiny column requests; the measured run took 6.41 s.
- OSM: 611 native features, 486,251 response bytes, in one small Boulder AOI.

These timings are individual observations, not service guarantees or a soak
test. Terrain vertical accuracy, road completeness/topology, and hydrologic
suitability remain unapproved. Overture and OSM are not independent ground
truth. The approved-status and broad missing-data populations still need
representative real-data review; unit fault controls alone do not cover them.

OSM's bbox query selects ways with a node in the bbox; a long crossing way can
be absent even though it geometrically intersects. Public Overpass is not a
sustained application serving plan. Larger workloads require an explicit
regional-extract/dedicated-service design, not silent backend substitution.
See [Overpass operating guidance](https://dev.overpass-api.de/overpass-doc/en/preface/commons.html).

## Run the checks independently

```bash
python -m pytest tests/test_source_transport.py tests/test_source_candidates_usgs.py \
  tests/test_source_candidates_spatial.py tests/test_source_promotion.py -q
python scripts/check_source_candidates.py --project usgs --output artifacts/new-usgs-run
python scripts/check_source_candidates.py --project usgs --output artifacts/new-usgs-run --offline
python scripts/run_vignettes.py docs/vignettes/streamflow_snapshots.ipynb
```

Other `--project` choices are `three_dep`, `overture`, and `osm`. Each writes
its own `candidate-report.json` and figures, including failure evidence. The
existing weekly/manual online workflow runs these independently; ordinary
offline CI does not rely on provider availability. No job auto-promotes a
source or automatically approves generated scientific figures.

## Required production promotion

`data.validate_source_promotion(candidate, certification, artifact_root=...)`
is a read-only, fail-closed gate. It requires:

1. A VALIDATED CANDIDATE and certification for that exact serving revision.
2. Matching noun/source, adapter version, interpretation contract and schema.
3. Explicit PASS for contract, offline tests, scientific review, bounded
   access, installed-package checks, visual review and documentation.
4. A named reviewer, supported scope, fresh timezone-aware certification,
   and verified SHA256 artifacts including the candidate's QA evidence.

The old outcome-string `validate_promotion` remains a deprecated structural
check for compatibility; it is not production approval. Live endpoint health
is independent of the scientific validity of retained data.

**Remaining release work:** broader real-data scientific review, approved and
missing-status USGS cases, performance/soak measurements at supported limits,
an OSM serving decision, and an actual reviewed serving-history/rollback
exercise. Until those gates pass, these adapters stay candidates.
