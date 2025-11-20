# Faceting: Multi-Panel Cube Figures

Faceting splits a cube into multiple panels to compare scenarios, models, or categories. `CubePlot` supports both `facet_wrap` and `facet_grid`.

## facet_wrap

Wrap categories into a grid:

```python
(CubePlot(cube)
 .facet_wrap(by="scenario", ncol=2)
 .geom_cube())
```

## facet_grid

Lay out rows and columns explicitly:

```python
(CubePlot(cube)
 .facet_grid(row="scenario", col="model")
 .geom_cube())
```

Shared fill/alpha scales keep legends aligned while each facet streams its own slices.
