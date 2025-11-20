# Examples Gallery

A quick tour of cube visualizations built with the grammar and streaming renderer.

## Basic cube viewer

```python
pipe(cube) | v.plot(title="Cube preview")
```

## Grammar tutorial snapshot

```python
p = (CubePlot(cube)
     .aes(fill="ndvi")
     .stat_time_anomaly(time_dim="time")
     .geom_cube()
     .scale_fill_continuous(center=0, palette="diverging")
     .coord_cube(elev=30, azim=45)
     .theme_cube_studio())
```

## Faceted scenarios

```python
(CubePlot(cube)
 .facet_grid(row="scenario", col="model")
 .geom_cube()
 .scale_fill_continuous(center=0, palette="diverging")
 .theme_cube_studio())
```

## Streaming huge NDVI stacks

Use a `VirtualCube` or dask-backed cube with `thin_time_factor=6` to preview decades quickly while the progress bar streams updates in notebooks.
