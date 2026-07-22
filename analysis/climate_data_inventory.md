# Climate Data Inventory

Generated: 2026-07-22T20:51:21.743861+00:00

## Population-wide daily centroid climate

Source: gridMET cached NetCDF files listed in `scratch/fire_vase_run_full/gridmet_cache_manifest.json`; variables are tmmx, tmmn, vpd, vs.
Spatial resolution: gridMET native 4-km grid.
Temporal resolution: daily. The processing manifest labels the component `gridmet-hourly-v0`, but the available table is daily and every slice has one daily value per variable.
Exposure basis: event centroid / nearest grid-cell extraction for each daily VASE slice.
Absolute or anomaly: absolute values in the source table; this revision also derives a region-month fire-season anomaly diagnostic from the observed fire population. It is not a true local climatological normal.
Date range: 2000-11-02 to 2021-05-01.
Fires with complete climate values: 237,235 of 278,569. Slice rows with climate values: 550,961 of 626,102.
Missingness pattern: 41,334 fires have missing cached climate values, reported as outside gridMET coverage or missing grid value in `processing_failures_climate.parquet`.

| Variable | Units | Summary types in revision | Safe for blocked prediction? | Aligns with developmental time? | Used in new manuscript? |
|---|---:|---|---|---|---|
| Maximum temperature | degrees C | daily slice, event mean, early/middle/late means, hot-day fraction, region-month anomaly | mostly yes for raw values; anomaly is an exploratory population-normalization unless recomputed inside folds | yes | yes |
| Minimum temperature | degrees C | daily slice, event mean, region-month anomaly | mostly yes for raw values; anomaly caveat as above | yes | yes |
| Vapor pressure deficit | kPa | daily slice, event mean, event maximum, early/middle/late means, high-VPD-day fraction, region-month anomaly | mostly yes for raw values; anomaly caveat as above | yes | yes |
| Wind speed | m s-1 | daily slice, event mean, early/middle/late means, windy-day fraction, region-month anomaly | mostly yes for raw values; anomaly caveat as above | yes | yes |
| Wind present | unitless fraction | always 1.0 in the climate-complete event table | no, because it has no variation | yes in principle | no |

## Perimeter, active-burned-area, and perimeter-extension pilot

Source: `scratch/fire_vase_run_full/tables/vase_climate_exposures.parquet`, produced by `scratch/fire_vase_run_full/perimeter_climate_build_report.json`.
Fire count: 25. Rows: 255. Climate-available rows: 175.
Exposure bases present: active_burned_area, cumulative_burned_area, perimeter_extension.
Extension distances: 5000.0, 10000.0, 25000.0 m.
Variables: maximum temperature, minimum temperature, VPD, and wind speed summarized by zone as mean/min/max/std, plus sampled cell count and exposure area.
Status: useful as a methods pilot and limitation figure only. It is not population-wide enough for the main inferential climate result.

| exposure_zone | rows | fires | climate_available |
| --- | --- | --- | --- |
| active_burned_area | 51 | 25 | 0.686 |
| cumulative_burned_area | 51 | 25 | 0.686 |
| perimeter_extension | 153 | 25 | 0.686 |

## Variables searched but not available as population-wide analysis products

Wind direction, gusts, precipitation, relative humidity, soil moisture, fuel moisture, drought indices, vegetation, topography, suppression, ignition cause, and true local seasonal normals were not found in the current population-wide Fire VASE tables. They should not be claimed as analyzed.

## Current manuscript use

The new manuscript uses population-wide daily centroid gridMET temperature, VPD, and wind speed; derived extreme-day fractions; early/middle/late exposure summaries; and a clearly labeled region-month anomaly diagnostic. Perimeter and active-burned-area climate are described as a pilot and limitation, not as main evidence.
