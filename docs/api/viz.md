# Visualization
> **See also:**  \
> - [API Reference](reference.md)  \
> - [Inventory (User)](../function_inventory.md)  \
> - [Inventory (Full / Dev)](inventory_full.md)

Interactive cube rendering uses :class:`cubedynamics.plotting.cube_plot.CubePlot`
and viewer helpers. Plotting verbs call these under the hood.

## CubePlot

### ``CubePlot(data, aes=None, fill_scale=None, coord=None, ...)``
Grammar-of-graphics inspired core for cube figures. Accepts a cube-like
DataArray, optional aesthetics (:class:`CubeAes`), facets, theme, annotations,
and vase overlays. Key methods:

* ``to_html()`` – return the full standalone viewer HTML.
* ``save(path, format="html")`` – write the HTML to disk; PNG export is stubbed
  with a clear error.
* ``_repr_html_()`` – Jupyter-friendly iframe renderer that writes a temporary
  HTML file and returns an IFrame via :func:`show_cube_viewer`.

### Themes and scales

* :class:`CubeTheme` – colors, fonts, padding. :func:`theme_cube_studio()`
  returns the default configuration.
* :class:`ScaleFillContinuous` / :class:`ScaleAlphaContinuous` – legend and fill
  scaling; ``infer_limits`` defensively handles remote I/O failures via
  ``drop_bad_assets``.

### Layers and geoms

* :class:`CubeLayer` plus helpers ``geom_cube``, ``geom_slice``, ``geom_outline``,
  and ``geom_path3d`` define how data map to viewer glyphs.
* :class:`CubeFacet` supports small multiples by ``row``/``col``/``wrap`` fields.

## Viewer helpers

### ``cubedynamics.plotting.viewer.show_cube_viewer(html, width=850, height=850, prefix=None)``
Write a standalone HTML file and return an :class:`IPython.display.IFrame`
pointing at it. Used by :meth:`CubePlot._repr_html_` and notebook workflows.

### ``cubedynamics.plotting.viewer._write_cube_html(html, prefix="cube_viewer")``
Low-level helper that materializes the HTML to disk; primarily used internally.

## Performance and streaming notes

* ``CubePlot`` will materialize stats lazily; when working with VirtualCube
  inputs, ensure upstream verbs have produced a concrete DataArray before
  plotting.
* ``ScaleFillContinuous.infer_limits`` drops failed assets before computing
  limits, improving robustness for remote Sentinel/stackstac sources.
