"""Visualization verbs wrapping simple interactive widgets."""

from __future__ import annotations

from typing import Any, Optional, Tuple

import xarray as xr

from ..deprecations import warn_deprecated
from ..verbs.plot import plot as _plot_verb


def plot(
    time_dim: str | None = "time",
    cmap: str = "viridis",
    clim: Optional[Tuple[float, float]] = None,
    aspect: str = "equal",
):
    """Deprecated. Use :func:`cubedynamics.verbs.plot` instead.

    This wrapper exists for backward compatibility and forwards arguments to
    the canonical plotting verb while preserving historical validation.
    """

    def _inner(cube: Any):
        warn_deprecated(
            "cubedynamics.ops.viz.plot",
            "cubedynamics.verbs.plot",
            since="0.2.0",
            removal="0.3.0",
        )

        # Preserve backwards-compatible validation for callers still using this module.
        if not isinstance(cube, xr.DataArray):
            raise TypeError(
                "v.plot expects an xarray.DataArray. "
                f"Got type {type(cube)!r}."
            )

        # Map legacy args to the newer verb implementation.
        vmin_vmax = clim if clim is not None else (None, None)
        plot_kwargs = {"aspect": aspect}
        if vmin_vmax[0] is not None:
            plot_kwargs["vmin"] = vmin_vmax[0]
        if vmin_vmax[1] is not None:
            plot_kwargs["vmax"] = vmin_vmax[1]

        return _plot_verb(
            cube,
            time_dim=time_dim,
            cmap=cmap,
            kind="auto",
            **plot_kwargs,
        )

    return _inner


__all__ = ["plot"]
