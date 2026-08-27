# Recipes

Applied workflows complement the [executable notebooks](../vignettes/index.md).
Live-data recipes require provider access; method guides and dependency designs
are not claims of a newly computed result.

| Workflow | What it covers |
| --- | --- |
| [gridMET temperature variability](gridmet_variance_cube.md) | Daily variance and within-period z-scores; live query |
| [PRISM precipitation anomalies](prism_variance_cube.md) | Within-period departures; live query |
| [Sentinel-2 NDVI departures](s2_ndvi_zcube.md) | Red/NIR bands → NDVI → z-score; live query |
| [Cube math primitives](cube_math_primitives.md) | Temporal differences, smoothing and spatial aggregation |
| [FIRED event VASE and climate](fire_event_vase_hull.md) | Event geometry, climate attribution and rendering |
| [Spatial synchrony blocks](spatial_synchrony_units.md) | Group and compare AOI signatures; long-record workflow |
| [Sentinel-2 center correlation](s2_corr_center.md) | Advanced satellite method |
| [Sentinel-2 tail dependence](s2_tail_dep_manual.md) | Advanced satellite tuning |

For methods, see [synchrony](../synchrony/index.md),
[the four primitives](../synchrony/primitives.md),
[biological coupling](../synchrony/biology_coupling.md), and
[suitability tubes](../viz/suitability_tubes.md).
For the object model and fire-panel workflow, see
[Fire VASE / FireHull](../capabilities/fire-vase.md).

[Write a vignette](recipe_template.md) · [Reproducibility contract](../vignettes/structure.md) ·
[Find data](../library/index.md) · [Find a verb](../reference/verbs/index.md)
