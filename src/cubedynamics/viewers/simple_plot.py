from __future__ import annotations

from typing import Optional, Tuple

import ipywidgets as widgets
import matplotlib.pyplot as plt
import numpy as np
import xarray as xr


def _infer_dims(
    cube: xr.DataArray,
    time_dim: Optional[str],
) -> Tuple[str, str, str]:
    """
    Infer time, y, x dim names for a 3D cube.

    Rules:
    - Require a 3D DataArray.
    - If time_dim is given, use that.
    - Else if 'time' is present, use 'time'.
    - Else use the first dimension as the "time-like" dimension.
    - For spatial dims, use the last two remaining dims.
    """
    if not isinstance(cube, xr.DataArray):
        raise TypeError("simple_cube_widget expects an xarray.DataArray")

    dims = list(cube.dims)
    if len(dims) != 3:
        raise ValueError(
            f"simple_cube_widget expects a 3D DataArray, got dims={dims}"
        )

    if time_dim is None:
        if "time" in dims:
            time_dim = "time"
        else:
            time_dim = dims[0]

    if time_dim not in dims:
        raise ValueError(
            f"time_dim={time_dim!r} not found in dims={dims}"
        )

    spatial_dims = [d for d in dims if d != time_dim]
    if len(spatial_dims) != 2:
        raise ValueError(
            f"Expected exactly 2 spatial dims besides {time_dim!r}, "
            f"found {spatial_dims}"
        )

    y_dim, x_dim = spatial_dims[-2], spatial_dims[-1]
    return time_dim, y_dim, x_dim


def simple_cube_widget(
    cube: xr.DataArray,
    time_dim: str | None = "time",
    cmap: str = "viridis",
    clim: Optional[Tuple[float, float]] = None,
    aspect: str = "equal",
) -> widgets.VBox:
    """
    Minimal interactive viewer for a 3D cube (time, y, x).

    - Uses ipywidgets + matplotlib.
    - Adds a time slider over the time dimension.
    - Plots 2D slices without loading the whole cube into memory.
    - Intended as the default native viewer for CubeDynamics.

    Parameters
    ----------
    cube : xr.DataArray
        3D DataArray, typically (time, y, x) or similar.
    time_dim : str | None
        Name of the time-like dimension. If None, it will be inferred
        (prefer 'time', otherwise the first dimension).
    cmap : str
        Matplotlib colormap name.
    clim : (float, float) | None
        Fixed color limits (vmin, vmax). If None, compute from the first slice.
    aspect : str
        Aspect for imshow, e.g. "equal" or "auto".

    Returns
    -------
    widgets.VBox
        A widget container suitable for display in Jupyter.
    """
    time_dim, y_dim, x_dim = _infer_dims(cube, time_dim)
    n_time = cube.sizes[time_dim]

    # Build index coordinate labels if available
    time_coord = cube.coords.get(time_dim, None)
    if (time_coord is not None) and (time_coord.ndim == 1):
        # Use coordinate values for labels if possible
        time_labels = [str(v) for v in time_coord.values]
    else:
        time_labels = [str(i) for i in range(n_time)]

    # Slider over time indices
    time_slider = widgets.IntSlider(
        value=0,
        min=0,
        max=n_time - 1,
        step=1,
        description=time_dim,
        continuous_update=False,
        readout=True,
    )

    # Drop-down for label display (optional but nice)
    label_dropdown = widgets.Dropdown(
        options=[
            (f"{i}: {lab}", i) for i, lab in enumerate(time_labels)
        ],
        value=0,
        description="Index",
        disabled=False,
    )

    def _sync_slider(change):
        # Keep slider and dropdown in sync
        if change["name"] == "value":
            time_slider.value = change["new"]

    label_dropdown.observe(_sync_slider, names="value")

    output = widgets.Output()

    # Compute color limits from first slice if not provided.
    if clim is None:
        first_slice = cube.isel({time_dim: 0})
        arr = first_slice.values
        vmin = float(np.nanmin(arr))
        vmax = float(np.nanmax(arr))
    else:
        vmin, vmax = clim

    def _plot_slice(t_idx: int):
        # Select one time slice without loading the full cube.
        slice_da = cube.isel({time_dim: int(t_idx)})

        with output:
            output.clear_output(wait=True)
            fig, ax = plt.subplots(figsize=(5, 4))

            # Use xarray's plotting to respect coords if present
            im = slice_da.plot.imshow(
                ax=ax,
                cmap=cmap,
                vmin=vmin,
                vmax=vmax,
                add_colorbar=True,
            )

            ax.set_title(f"{time_dim} index = {t_idx}")
            ax.set_aspect(aspect)
            fig.tight_layout()
            plt.show()

    # Wire both slider and dropdown to the same plotting function
    widgets.interactive_output(
        lambda value: _plot_slice(value),
        {"value": time_slider},
    )
    widgets.interactive_output(
        lambda value: _plot_slice(value),
        {"value": label_dropdown},
    )

    controls = widgets.HBox([time_slider, label_dropdown])
    return widgets.VBox([controls, output])
