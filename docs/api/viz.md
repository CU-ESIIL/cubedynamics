# Visualization API

The [plot verb](../reference/verbs/plot.md) uses the custom HTML cube viewer.
Fire plotting still uses a Plotly hull backend; Lexcube is a separate optional
widget integration. This reference does not switch or unify those renderers.

## CubePlot

::: cubedynamics.plotting.cube_plot.CubePlot
    options:
      members: [to_html, save]
      show_docstring_examples: false

## Themes and aesthetics

::: cubedynamics.plotting.cube_plot.CubeTheme

::: cubedynamics.plotting.cube_plot.theme_cube_studio

::: cubedynamics.plotting.cube_plot.CubeAes

::: cubedynamics.plotting.cube_plot.CoordCube

## HTML display helper

::: cubedynamics.plotting.viewer.show_cube_viewer

## Optional Lexcube helper

::: cubedynamics.viz.lexcube_viz.show_cube_lexcube

The [show_cube_lexcube verb](../reference/verbs/show_cube_lexcube.md) wraps this
helper as a pass-through pipe stage. Lexcube installation and a compatible
Jupyter frontend are required.

## See also

[Cube viewer guide](../viz/cube_viewer.md) ·
[Viewer invariants](../dev/cube_viewer_invariants.md) ·
[Fire rendering architecture](../dev/fire_plot_architecture.md) ·
[Observed-data notebooks](../vignettes/index.md)
