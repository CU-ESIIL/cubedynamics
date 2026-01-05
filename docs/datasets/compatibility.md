# Compatibility matrix

Use this matrix to align verbs and datasets. If a cell is blank, that combination may require custom preprocessing or has not been tested yet.

| Dataset | Ready-made loader | Visualization verbs | Event verbs |
|---------|-------------------|---------------------|-------------|
| gridMET | `load_gridmet_cube`, `stream_gridmet_to_cube` | `plot`, `plot_mean`, `maps` | `extract`, `climate_hist` |
| PRISM | `load_prism_cube` | `plot`, `maps` | `extract`, `climate_hist` |
| Sentinel-2 NDVI | `load_s2_ndvi_cube`, `load_sentinel2_ndvi_cube` | `plot`, `landsat_ndvi_plot` | `tubes`, `vase` |
| Landsat 8 (MPC) | `landsat8_mpc`, `landsat_vis_ndvi` | `plot`, `landsat_ndvi_plot` | `tubes`, `vase` |
| FIRED (events/perimeters) | `fired_event`, `load_fired_daily_perimeter` | `fire_plot`, `fire_panel` | `extract`, `vase`, `tubes` |

---
Back to [Datasets Overview](index.md)  
Next recommended page: [Citations](citations.md)
