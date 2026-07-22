# Fire VASE Lakehouse Architecture

The fire VASE lakehouse separates science products from rendered views. A VASE
is a versioned data object made from fire-time geometry and environmental
attribution; a panel, mesh, SVG, PDF, or PNG is an asset derived from that data.

## Product Classes

- Immutable source observations: raw fire records and upstream provenance.
- Canonical fire time and geometry: normalized daily or hourly fire-time rows
  with validated geometry keys.
- Derived traits and events: reusable tables for cohort selection, event
  alignment, and summary products.
- VASE slices: ring-level geometry and climate attribution for each fire-time
  slice.
- Rendered assets: GLB, PNG, SVG, HTML, or PDF views registered back to the
  VASE cache key.
- Population summaries: cohort, medoid, and event-aligned quantile products.

## Core Tables

Schemas live in `schemas/*.schema.json` for:

- `fire_observations_raw`
- `fire_time`
- `fire_geometry`
- `fire_traits`
- `fire_events`
- `vase_slices`
- `vase_assets`
- `processing_manifest`
- `processing_runs`
- `fire_catalog`
- `processing_failures`
- `cohort_summaries`

## Versioning

Component versions are independent: source, geometry, climate, events, traits,
VASE, and render. Cache keys are content-addressed from the fire identity,
component versions, and upstream keys. A climate version update invalidates
climate, events, traits, VASE, and render outputs while preserving source and
geometry products. Event-only updates invalidate events, traits, VASE, and
render outputs.

## Partitioning

Tables are partitioned by `year`, `region`, `spatial_bucket`, and
`processing_version`. They are not partitioned by `fire_id`, which keeps cohort
queries and compaction practical.

## Repository Boundary

Git stores code, schemas, config templates, documentation, small fixtures, and
small curated release manifests. Bulk outputs stay in ignored roots such as
`scratch/`, `artifacts/`, `lakehouse/`, `manifests/runs/`, or external object
storage. Use `scripts/check_repository_size.py` before committing generated
work.

## Pilot

Run a real-data pilot from the configured catalog:

```bash
python scripts/fire_vase_lakehouse_pilot.py \
  --config config/fire_vase_pipeline.yml \
  --output-root ./scratch/fire_vase_run \
  --sample-size 1000
```

The pilot never pads with synthetic fires. If the source catalog contains fewer
than the requested count, it writes all available rows and records the shortfall
in `pilot_report.json`.
