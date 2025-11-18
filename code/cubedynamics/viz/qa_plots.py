"""Quality-assurance plotting helpers."""

from __future__ import annotations

import matplotlib.pyplot as plt
import xarray as xr


def plot_median_over_space(
    cube: xr.DataArray,
    ax: plt.Axes | None = None,
    dims: list[str] | None = None,
    ylabel: str = "",
    title: str = "",
    ylim: tuple[float, float] | None = None,
) -> plt.Axes:
    """Plot the median over space of a 3D cube as a time series."""

    dims = dims or [dim for dim in cube.dims if dim not in (cube.dims[0],)]
    if not dims:
        raise ValueError("Cube must have spatial dimensions to aggregate over")
    ts = cube.median(dim=dims, skipna=True)
    if ax is None:
        _, ax = plt.subplots(figsize=(8, 3))
    ts.to_series().plot(ax=ax)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.grid(True, alpha=0.3)
    if ylim is not None:
        ax.set_ylim(*ylim)
    if "long_name" in cube.attrs:
        ax.set_xlabel(cube.dims[0])
    return ax
