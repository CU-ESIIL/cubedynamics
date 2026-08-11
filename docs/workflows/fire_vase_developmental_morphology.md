# Fire VASE Developmental Morphology

Fire VASE is the population-scale fire-history workflow used for the current
developmental morphology manuscript. It treats each FIRED event as a real
observed life history, converts daily growth into a comparable VASE profile,
and then attaches climate as an explanatory layer rather than as part of the
shape definition.

The workflow has two linked products:

- a durable analysis database under ignored local roots such as
  `scratch/fire_vase_run_full/`
- rendered views of that database, including atlases, manuscript figures, PDF
  drafts, and Google Docs-ready DOCX files

Rendered figures are not the source of truth. They are reproducible views of
the VASE tables, feature tables, climate-attribution tables, manifests, and
figure-generation scripts.

## Current Scope

The manuscript-scale run uses real FIRED-derived daily fire histories from
2000-2021. The current population contains 278,569 events and 626,102 daily
VASE slices. Complete daily centroid gridMET climate is available for 237,235
fires.

The centroid climate table includes:

- maximum and minimum temperature
- vapor pressure deficit
- wind speed and a simple wind-presence flag
- precipitation
- maximum and minimum relative humidity
- specific humidity
- 100-hour and 1000-hour dead fuel moisture
- energy release component and burning index
- reference and potential evapotranspiration
- solar radiation

The perimeter exposure workflow is a companion product. It summarizes climate
over active daily burned polygons, cumulative burned area, and configurable
exterior perimeter-extension buffers. It is deliberately stored separately from
the centroid baseline so figures can compare exposure definitions without
silently changing earlier analyses.

## Analysis Stages

| Stage | Main script | Main products |
| --- | --- | --- |
| Cache climate years | `scripts/cache_gridmet_years.py` | cached gridMET NetCDF files and `gridmet_cache_manifest.json` |
| Build centroid VASE tables | `scripts/fire_vase_build_climate_tables.py` | `fire_catalog.parquet`, `fire_traits.parquet`, `vase_slices.parquet` |
| Build perimeter exposure table | `scripts/fire_vase_build_perimeter_climate_tables.py` | `vase_climate_exposures.parquet` plus a build report |
| Build developmental morphospace | `scripts/fire_vase_developmental_morphology_analysis.py` | feature tables, medoids, shape categories, atlas PDF |
| Audit claims and null framing | `scripts/fire_vase_manuscript_claim_audit.py` | claim audit, reviewer notes, revised manuscript drafts |
| Generate climate-revision figures and manuscript | `scripts/fire_vase_climate_revision.py` | five main figures, supplementary figures, Science-style PDF, manuscript Markdown |
| Generate Google Docs-ready manuscript | `scripts/build_fire_vase_google_docs_docx.py` | `output/docx/fire_vase_climate_revision_google_docs.docx` |

## Rebuild Commands

Run the comprehensive gridMET cache first when the optional climate variables
are needed:

```bash
python scripts/cache_gridmet_years.py --preset comprehensive --keep-going
```

Build or refresh the centroid VASE climate table:

```bash
python scripts/fire_vase_build_climate_tables.py \
  --config config/fire_vase_pipeline.yml \
  --table-root scratch/fire_vase_run_full/tables \
  --report scratch/fire_vase_run_full/climate_build_comprehensive_report.json
```

Build the perimeter and perimeter-extension exposure companion table:

```bash
python scripts/fire_vase_build_perimeter_climate_tables.py \
  --include-optional-variables \
  --table-root scratch/fire_vase_run_full/tables \
  --report scratch/fire_vase_run_full/perimeter_climate_build_comprehensive_report.json
```

Build the population morphology atlas:

```bash
python scripts/fire_vase_developmental_morphology_analysis.py \
  --table-root scratch/fire_vase_run_full/tables \
  --data-output-dir scratch/fire_vase_developmental_morphology \
  --output output/pdf/fire_vase_developmental_morphology_atlas.pdf
```

Build the climate-revision figures and Science-style manuscript PDF:

```bash
python scripts/fire_vase_climate_revision.py
```

Build the Google Docs-ready manuscript:

```bash
python scripts/build_fire_vase_google_docs_docx.py
```

## What the Current Figures Show

The current manuscript figures are organized as a story:

- Figure 1 shows that similar final burned areas can arise through different
  life histories.
- Figure 2 places representative VASE shapes over the morphospace so readers
  can see how developmental forms change across VASE coordinates.
- Figure 3 colors the morphospace by climate variables and compares climate
  groups, emphasizing that climate shifts the prevalence of developmental
  forms.
- Figure 4 tests whether climate effects depend on current developmental
  state using leakage-safe next-day-growth baselines.
- Figure 5 shows matched examples where similar climate can lead to different
  forms and similar forms can arise under different climate pathways.

The figure legends live in `figures/climate_revision_main/figure_legends.md`.
They are written in Science style: the figure number and title are part of the
legend, not the image artwork, and each legend explains how to read the figure
and what scientific message it supports.

## Validation and Audits

The manuscript workflow includes explicit checks that keep the story bounded:

- reviewer-style critique rounds in
  `docs/manuscripts/fire_vase_developmental_morphology/`
- a Science author-guideline compliance note
- a citation audit and final citation check
- render checks for PDF and DOCX outputs
- repository-size checks to keep bulk products out of git

The current final citation check is
`docs/manuscripts/fire_vase_developmental_morphology/final_citation_check_2026-07-23.md`.

## Current Limits

The main manuscript analysis still treats centroid daily gridMET exposure as
the complete-population baseline. The perimeter and perimeter-extension climate
table is available as a richer companion product, but its coverage and role
must be reported separately when used in figures or claims.

The workflow does not yet include topography, vegetation, suppression activity,
ignition cause, wind direction, wind gusts, or local-normal climate anomalies
as complete-population covariates. Those are the next data-integration steps.

The current prediction values are linear baseline results from blocked
validation. They are useful for bounding deterministic climate explanation, but
they are not optimized predictive models and should not be interpreted as
causal estimates.
