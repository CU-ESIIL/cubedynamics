# Design Philosophy: Streaming + Grammar + Scientific Defaults

CubeDynamics blends three pillars:

1. **Streaming-first**: VirtualCube and lazy dask arrays avoid memory blowups while keeping notebooks responsive.
2. **Grammar-of-graphics**: Inspired by ggplot, with layers, stats, geoms, scales, coords, themes, facets, and annotations tailored to cubes.
3. **Scientific-quality defaults**: Studio theme, caption+legend alignment, and axis labels that read like figure-ready panels.

## Comparison to ggplot

| Grammar element | CubeDynamics analogue |
| --- | --- |
| data | xarray DataArray / VirtualCube |
| aes | `CubeAes(fill, alpha, slice)` |
| stat | `stat_time_mean`, `stat_time_anomaly`, `stat_space_mean` |
| geom | `geom_cube`, `geom_slice`, `geom_outline` |
| scale | `ScaleFillContinuous`, `ScaleAlphaContinuous` |
| coord | `coord_cube` |
| theme | `CubeTheme`, `theme_cube_studio` |
| facet | `facet_wrap`, `facet_grid` |

## Streaming storytelling

Captions + legends + annotations combine to tell the data story while the renderer streams frames. Start simple with `pipe(cube) | v.plot()` and graduate to `CubePlot(...).facet_wrap(...)` when you need multi-panel reports.
