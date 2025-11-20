# Captions, Legends, and Scientific Storytelling

Cube figures include publication-ready captions and legends that mirror the grammar of graphics.

## Caption structure

Captions live in a `<div class="cube-caption">` block with:

- **Figure label**: `Figure {id}.`
- **Title**: bold short description
- **Text**: markdown-friendly body with math support

```python
p = CubePlot(cube, title="Fire event NDVI")
p.caption = {
    "id": 3,
    "title": "NDVI anomaly",
    "text": "Markdown, inline math $\\nabla$, and hyperlinks are supported.",
}
html = p.to_html()
```

## Legends and scales

Legends are driven by `ScaleFillContinuous` and `ScaleAlphaContinuous`:

```python
p = (CubePlot(cube)
     .scale_fill_continuous(center=0, palette="diverging", name="NDVI z-score"))
```

Shared scales propagate across facets and keep colorbars aligned.

## Styling via themes

`CubeTheme` exposes CSS variables for background, axis, and legend colors:

- `--cube-bg-color`
- `--cube-title-color`
- `--cube-axis-color`
- `--cube-legend-color`
- `--cube-caption-font-size`

Use `theme_cube_studio()` for balanced defaults or override individual fields when instantiating `CubePlot`.
