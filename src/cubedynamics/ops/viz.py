"""Visualization verbs wrapping simple interactive widgets."""

from __future__ import annotations

from typing import Any, Optional, Tuple

import xarray as xr

from ..verbs.plot import plot as _plot_verb


def plot(
    time_dim: str | None = "time",
    cmap: str = "viridis",
    clim: Optional[Tuple[float, float]] = None,
    aspect: str = "equal",
):
    """Legacy wrapper for the interactive plotting verb.

    Delegates to :func:`cubedynamics.verbs.plot` to keep behavior consistent
    for callers importing from ``cubedynamics.ops.viz``.
    """

    def _inner(cube: Any):
        # Preserve backwards-compatible validation for callers still using this module.
        if not isinstance(cube, xr.DataArray):
            raise TypeError(
                "v.plot expects an xarray.DataArray. "
                f"Got type {type(cube)!r}."
            )

        # Map legacy args to the newer verb implementation.
        vmin_vmax = clim if clim is not None else (None, None)
        return _plot_verb(
            time_dim=time_dim if time_dim is not None else "time",
            y_dim=cube.dims[1] if len(cube.dims) >= 2 else "y",
            x_dim=cube.dims[2] if len(cube.dims) >= 3 else "x",
            cmap=cmap,
            vmin=vmin_vmax[0],
            vmax=vmin_vmax[1],
            aspect=aspect,
        )(cube)

    return _inner


__all__ = ["plot"]
