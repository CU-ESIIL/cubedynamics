"""Verb for plotting mean and variance cubes side-by-side."""

from __future__ import annotations

import xarray as xr
from IPython.display import display

from cubedynamics.plotting.multicube_plot import MultiCubePlot
from cubedynamics.piping import Verb, _attach_viewer
from cubedynamics.streaming import VirtualCube

__all__ = ["plot_mean"]


def _materialize_if_virtual(value):
    if isinstance(value, VirtualCube):
        return value.materialize()
    return value


def plot_mean(
    da: xr.DataArray | None = None,
    *,
    dim: str = "time",
    width: int = 1000,
    height: int = 500,
    ddof: int = 1,
    **options,
):
    """Plot mean and variance cubes with synchronized controls.

    The viewer is rendered as a side effect in notebooks while the original cube
    is returned so pipe chains can continue.
    """

    def _op(value: xr.DataArray):
        da_value = _materialize_if_virtual(value)
        if not isinstance(da_value, xr.DataArray):
            raise TypeError(
                "v.plot_mean expects an xarray.DataArray or compatible VirtualCube. "
                f"Got type {type(da_value)!r}."
            )

        mean_da = da_value.mean(dim=dim, keep_attrs=True)
        var_da = da_value.var(dim=dim, ddof=ddof, keep_attrs=True)

        mean_da = mean_da.assign_attrs(**getattr(da_value, "attrs", {}))
        var_da = var_da.assign_attrs(**getattr(da_value, "attrs", {}))

        plot = MultiCubePlot(
            cubes=[mean_da, var_da],
            labels=["Mean", "Variance"],
            title=f"{da_value.name or 'cube'}: mean / variance over {dim}",
            width=width,
            height=height,
            **options,
        )
        display(plot)
        _attach_viewer(value, plot)

        return value

    if da is None:
        return Verb(_op)
    return _op(da)

