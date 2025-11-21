# Streaming-First Rendering & Huge Data

The cube viewer is designed for massive NEON, Sentinel-2, PRISM, and gridMET cubes. It iterates over time slices and never materializes the full cube in memory.

## Why streaming?

- Continental NDVI archives exceed laptop memory
- Long PRISM or gridMET histories are easier to browse slice by slice
- Progress feedback keeps notebooks responsive during big pulls

## How it works

- Uses `VirtualCube` and dask-backed DataArrays lazily
- Iterates over time frames: `for t in range(0, nt, thin_time_factor)`
- Extracts only 2D slices per iteration (`frame.values` for the selected time)
- Combines min/max ranges after all slices for consistent color scales
- Shows a progress indicator (`progress_style="bar"` or `"pulse"`)

Vase volumes reuse the same pattern: `build_vase_mask` walks time slices using coordinates only, so face overlays from
`geom_vase_outline` keep the streaming pipeline intact. See [Vase Volumes & Arbitrary 3-D Subsets](vase-volumes.md) for details.

## Faceting with streaming

Facets subset the cube one panel at a time while sharing scales:

```python
(CubePlot(ndvi)
 .facet_grid(row="scenario", col="model")
 .geom_cube()
 .scale_fill_continuous(center=0)
)
```

Each facet panel pulls only its own slices, so you can fan out scenarios without memory blowups.

## Performance best practices

- Keep inputs chunked; avoid `ndvi.compute()` unless absolutely necessary
- Lower `thin_time_factor` to preview long series quickly
- Use `out_html` to write intermediate panels and reuse them in reports
- Prefer `.facet_wrap` when the facet variable has many categories so you can control `ncol`

## Streaming progress in Jupyter

When `show_progress=True`, the renderer streams slices and displays a live progress bar. It is safe to interrupt and restart without corrupting the cube.
