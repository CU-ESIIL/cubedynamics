# Visualization verbs

Visualization verbs display cubes inline or generate QA plots without leaving the pipe chain.

<a id="vshow_cube_lexcube"></a>

### `v.show_cube_lexcube(**kwargs)`

Integrate [Lexcube](https://github.com/carbonplan/lexcube) for interactive `(time, y, x)` exploration. The verb displays the widget as a side effect and returns the original cube so pipelines keep flowing.

```python
from cubedynamics import pipe, verbs as v

pipe(cube) \
    | v.month_filter([6, 7, 8]) \
    | v.show_cube_lexcube(title="PRISM JJA precipitation", cmap="RdBu_r")
```

- **Parameters**: pass any Lexcube keyword arguments (`title`, `cmap`, `vmin`, `vmax`). Datasets with a single data variable are automatically converted to a DataArray.
- **Notes**: Widgets render only in live notebook environments and require a 3D `(time, y, x)` cube. Reducers such as `v.mean`/`v.variance` should use `keep_dim=True` to preserve this layout.

For QA plots outside Lexcube, call the functional helper `cubedynamics.plot_median_over_space(cube, ...)`.

---

## Update (2025): New `v.plot` cube viewer

### `verbs.plot(obj, kind="auto", **kwargs)`

Generic plotting verb.

- `kind="auto"` (default):
  - If `obj` is 3D `(time,y,x)`, may dispatch to the cube viewer or a slice-based plot, depending on configuration.
  - For 2D arrays, uses the existing 2D plotting (Matplotlib) behavior.

- `kind="cube"`:
  - Uses the HTML cube viewer with streaming, non-blocking progress text and Lexcube-style axis labels.
  - Parameters forwarded:
    - `out_html`, `cmap`, `size_px`, `thin_time_factor`.
  - Notebook outputs must be trusted so the embedded JavaScript can run; when scripting is blocked the
    viewer displays an inline warning (“Interactive controls need JavaScript”) instead of silently
    staying static.

- `kind="slice"`:
  - Old behavior: 2D map with time slider (ipywidgets + Matplotlib), if still kept for backward compatibility.

### `verbs.map(obj, time_index=None, **kwargs)`

Map-style visualization of `(y,x)` or `(time,y,x)` DataArrays using a MapGL-style engine (pydeck).

Parameters:

- `obj`: piped object or xarray DataArray/Dataset.
- `time_index`: optional index along the time dimension for 3D inputs (defaults to the last timestep).
- `**kwargs`: forwarded to `vis_map.show_map_pydeck`, including:
  - `cmap`, `vmin`, `vmax`: color scaling.
  - `height`, `width`: canvas size.

Returns a pydeck `Deck` object displayed inline in Jupyter.

### `v.quick_map()` (planned)

Future work will expose small multiples and static PNG exporters for dashboards. Track development in the [Roadmap](../dev/roadmap.md).
