from __future__ import annotations

from typing import Any, Optional, Tuple

import xarray as xr

from ..viewers.simple_plot import simple_cube_widget


def plot(
    time_dim: str | None = "time",
    cmap: str = "viridis",
    clim: Optional[Tuple[float, float]] = None,
    aspect: str = "equal",
):
    """
    Pipe verb: interactive slice plot of a 3D cube using a simple
    ipywidgets + matplotlib viewer.

    Example
    -------
    from cubedynamics import pipe, verbs as v

    pipe(cube) | v.plot(time_dim="time", cmap="RdBu_r", clim=(-3, 3))
    """

    def _inner(cube: Any):
        if not isinstance(cube, xr.DataArray):
            raise TypeError(
                "v.plot expects an xarray.DataArray. "
                f"Got type {type(cube)!r}."
            )
        return simple_cube_widget(
            cube,
            time_dim=time_dim,
            cmap=cmap,
            clim=clim,
            aspect=aspect,
        )

    return _inner


__all__ = ["plot"]
