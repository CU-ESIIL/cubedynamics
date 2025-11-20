"""Interactive plotting verb for time-indexed cubes."""

from __future__ import annotations

from typing import Optional, Tuple

import ipywidgets as widgets
import matplotlib.pyplot as plt
import numpy as np
import xarray as xr

# Import the VirtualCube type from wherever it lives in this repo.
try:  # pragma: no cover - import guard
    from cubedynamics.streaming import VirtualCube
except Exception:  # pragma: no cover - fallback if import path changes
    VirtualCube = tuple()  # type: ignore


def _to_dataarray(
    cube: xr.DataArray | xr.Dataset | VirtualCube,
    time_dim: str,
    y_dim: str,
    x_dim: str,
    var_name: Optional[str] = None,
) -> xr.DataArray:
    """Normalize cube-like input to a 3D (time, y, x) :class:`xarray.DataArray`.

    - If cube is a Dataset, select ``var_name`` or the first data var.
    - If cube is a VirtualCube, materialize a full DataArray lazily.
    """

    if isinstance(cube, VirtualCube):
        if hasattr(cube, "to_xarray"):
            cube = cube.to_xarray()  # type: ignore[attr-defined]
        elif hasattr(cube, "materialize"):
            cube = cube.materialize()  # type: ignore[attr-defined]
        else:
            raise TypeError("VirtualCube object does not expose a materialization method")

    if isinstance(cube, xr.Dataset):
        if var_name is not None:
            da = cube[var_name]
        else:
            name = list(cube.data_vars)[0]
            da = cube[name]
    elif isinstance(cube, xr.DataArray):
        da = cube
    else:
        raise TypeError(f"Unsupported cube type for plot(): {type(cube)}")

    for dim in (time_dim, y_dim, x_dim):
        if dim not in da.dims:
            raise ValueError(f"Expected dimension {dim!r} in DataArray, got dims={da.dims}")

    return da.transpose(time_dim, y_dim, x_dim, ...)


def plot(
    *,
    time_dim: str = "time",
    y_dim: str = "y",
    x_dim: str = "x",
    var_name: Optional[str] = None,
    cmap: Optional[str] = None,
    vmin: Optional[float] = None,
    vmax: Optional[float] = None,
    figsize: Tuple[float, float] = (6.0, 4.0),
    title: Optional[str] = None,
    aspect: Optional[str | float] = "equal",
):
    """Pipe verb: interactive time slider + 2D map viewer for cubes.

    Returns an :class:`ipywidgets.VBox` with a time slider, label, and plot area.
    """

    def _op(cube: xr.DataArray | xr.Dataset | VirtualCube):
        da = _to_dataarray(
            cube,
            time_dim=time_dim,
            y_dim=y_dim,
            x_dim=x_dim,
            var_name=var_name,
        )

        n_time = da.sizes[time_dim]
        if n_time == 0:
            raise ValueError("Cannot plot cube with zero length along time dimension.")

        slider = widgets.IntSlider(
            value=0,
            min=0,
            max=n_time - 1,
            step=1,
            description=time_dim,
            continuous_update=False,
        )

        first_time_val = da[time_dim].values[0]
        label = widgets.Label(value=f"{time_dim}: {np.asarray(first_time_val)}")

        out = widgets.Output()

        def _update(change=None):
            idx = slider.value
            time_val = da[time_dim].values[idx]

            with out:
                out.clear_output(wait=True)
                try:
                    da_t = da.isel({time_dim: idx})

                    fig, ax = plt.subplots(figsize=figsize)

                    if np.isnan(da_t.values).all():
                        ax.text(
                            0.5,
                            0.5,
                            "No valid data for this time index",
                            ha="center",
                            va="center",
                            transform=ax.transAxes,
                        )
                        ax.set_axis_off()
                    else:
                        da_t.plot.imshow(
                            ax=ax,
                            cmap=cmap,
                            vmin=vmin,
                            vmax=vmax,
                            add_colorbar=True,
                        )
                        ax.set_xlabel(x_dim)
                        ax.set_ylabel(y_dim)

                    if aspect is not None:
                        ax.set_aspect(aspect)

                    if title is not None:
                        ax.set_title(title)
                    else:
                        ax.set_title(f"{getattr(da, 'name', 'cube')} @ {np.asarray(time_val)}")

                    label.value = f"{time_dim}: {np.asarray(time_val)}"

                    plt.tight_layout()
                    plt.show()

                except Exception as e:  # pragma: no cover - visual debugging
                    print("Plot update failed:", repr(e))
                    raise

        _update()

        slider.observe(_update, names="value")

        controls = widgets.HBox([slider, label])
        widget = widgets.VBox([controls, out])
        return widget

    return _op


__all__ = ["plot"]
