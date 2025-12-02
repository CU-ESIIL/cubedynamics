# Cube viewers

## Standalone HTML cube viewer

Generate a fully offline, self-contained cube viewer using:

```python
from cubedynamics.viewers import write_cube_viewer

write_cube_viewer(ndvi, "ndvi_cube.html")
```

The output HTML bundles all JavaScript and textures so it can be opened directly in
a browser or embedded into a notebook with `IFrame("ndvi_cube.html", width=900, height=900)`.

### Notebook usage

The viewer is fully interactive inside Jupyter (classic or Lab) because it renders a self-contained
`IPython.display.HTML` block. Dragging and scroll/trackpad events are wired to the transparent drag
surface layered over the cube, so you can rotate and zoom the cube inline without needing any extra
widgets or extensions. If you prefer a static export, write the HTML to disk and open it separately
as shown above.

### Multi-band cubes

If your DataArray includes a `band` dimension (e.g., `(time, band, y, x)`), the cube viewer
will automatically select a single band for display. When there is only one band, it is used
directly; when there are multiple bands, the viewer defaults to the first band and emits a
warning. To control which band is visualized, select it before plotting:

```python
red = cube.sel(band="red")
pipe(red) | v.plot(time_dim="time")
```

### Mouse/trackpad controls

- **Rotate:** click-and-drag anywhere in the cube frame (faces or the transparent padding). The drag surface captures the pointer so rotation keeps flowing even if the cursor leaves the canvas mid-drag.
- **Zoom:** use a trackpad pinch gesture or mouse scroll to zoom the cube in/out.
- **Reset view:** rerun the cell or reload the saved HTML; the cube opens with the initial azimuth/elevation set in `coord_cube`.
