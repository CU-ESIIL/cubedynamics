# CubePlot Grammar of Graphics

Climate cubes use a ggplot-inspired grammar so you can build 3D visualizations layer by layer. The grammar mirrors **data → aes → stat → geom → scale → coord → theme → facet → annotation**.

## Core pieces

- **Data**: any xarray `DataArray` or `VirtualCube`
- **Aesthetics (`aes`)**: map cube variables to visuals (`fill`, `alpha`, `slice`)
- **Stats (`stat_*`)**: `stat_time_mean`, `stat_time_anomaly`, `stat_space_mean`, `stat_identity`
- **Geoms (`geom_*`)**: `geom_cube`, `geom_slice`, `geom_outline`, with a `geom_path3d` stub ready for trajectories
- **Scales**: `ScaleFillContinuous`, `ScaleAlphaContinuous` with diverging/centered options
- **Coordinates**: `coord_cube` / `CoordCube` for camera elevation, azimuth, zoom, and aspect
- **Themes**: `CubeTheme`, `theme_cube_studio` (CSS variables for background, legend, axes)
- **Facets**: `facet_wrap`, `facet_grid` for multi-panel cube walls
- **Annotations**: `annot_plane`, `annot_text` for domain and figure storytelling

## Minimal example

```python
from cubedynamics import pipe, verbs as v

(pipe(cube)
 | v.plot(title="NDVI cube")
)
```

## Layered example

```python
from cubedynamics.plotting.cube_plot import CubePlot

p = (CubePlot(cube, title="NDVI anomaly")
     .aes(fill="ndvi")
     .stat_time_anomaly(time_dim="time")
     .geom_cube()
     .scale_fill_continuous(center=0, palette="diverging")
     .coord_cube(elev=35, azim=45)
     .theme_cube_studio()
)

p.save("figure1.html")
```

## Faceting

```python
(CubePlot(cube)
 .aes(fill="ndvi")
 .facet_wrap(by="scenario", ncol=2)
 .geom_slice(axis="time", value="2012-06-10")
 .scale_fill_continuous(palette="sequential")
)
```

## Annotations and captions

Use `annot_plane` for domain markers and `caption` metadata for publication-ready figures:

```python
p = (CubePlot(cube, title="Scenario comparison")
     .annot_plane(axis="time", value="2012-06-10", text="Fire event")
     .annot_text(coord=(10, 20, 30), text="Tower")
)

p.caption = {"id": 2, "title": "NDVI anomaly", "text": "**Markdown** + $\nabla$ ready."}
p.save("scenario.html")
```

## CubePlot philosophy

- Everything accepts cubes lazily—no forced `.compute()`
- Scales and themes drive legends automatically
- `pipe(ndvi) | v.plot()` stays the default, while `CubePlot(...)` offers full control
