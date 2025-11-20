"""Plotting verb with streaming-friendly cube defaults."""

from __future__ import annotations

from typing import Any

import xarray as xr
from IPython.display import IFrame

from cubedynamics.plotting.cube_viewer import cube_from_dataarray
from cubedynamics.utils import _infer_time_y_x_dims
from cubedynamics.viewers.simple_plot import simple_cube_widget


PlotResult = xr.plot.FacetGrid | IFrame | Any


def _select_dataarray(obj: Any, var_name: str | None) -> xr.DataArray:
    if isinstance(obj, xr.Dataset):
        if var_name is None:
            if len(obj.data_vars) == 1:
                var_name = list(obj.data_vars)[0]
            else:
                raise ValueError(
                    "Dataset must supply a variable name via 'var' or 'name' when multiple data variables exist."
                )
        if var_name not in obj.data_vars:
            raise ValueError(
                f"Variable {var_name!r} not found in Dataset; available variables: {list(obj.data_vars)}"
            )
        return obj[var_name]
    if isinstance(obj, xr.DataArray):
        return obj
    raise TypeError(
        "plot verb expects an xarray.DataArray or Dataset; "
        f"received {type(obj)!r}."
    )


def plot(
    obj: Any | None = None,
    *,
    time_dim: str | None = None,
    y_dim: str | None = None,
    x_dim: str | None = None,
    kind: str = "auto",
    out_html: str | None = None,
    cmap: str = "viridis",
    size_px: int = 260,
    thin_time_factor: int = 4,
    **kwargs,
) -> Any:
    """Pipe-friendly plotting helper.

    When invoked without ``obj``, returns a callable suitable for ``pipe(...) | v.plot(...)``.
    When ``obj`` is provided directly, executes immediately.
    """

    def _op(target: Any) -> PlotResult:
        local_kwargs = dict(kwargs)
        var_name = local_kwargs.pop("var", None) or local_kwargs.pop("name", None)
        da = _select_dataarray(target, var_name)

        # Infer dimensions when needed
        inferred_tyx = _infer_time_y_x_dims(da) if None in (time_dim, y_dim, x_dim) else None
        t_dim = time_dim or (inferred_tyx[0] if inferred_tyx else None)
        y_axis = y_dim or (inferred_tyx[1] if inferred_tyx else None)
        x_axis = x_dim or (inferred_tyx[2] if inferred_tyx else None)

        if kind not in {"auto", "cube", "2d"}:
            raise ValueError("kind must be one of {'auto', 'cube', '2d'}")

        if kind == "cube":
            if da.ndim != 3:
                raise ValueError(
                    "Cube viewer requires a 3D DataArray with time, y, x dimensions."
                )
            if None in (t_dim, y_axis, x_axis):
                raise ValueError("Could not infer time/y/x dimensions for cube viewer.")
            return cube_from_dataarray(
                da,
                out_html=out_html or "cube_da.html",
                cmap=cmap,
                size_px=size_px,
                thin_time_factor=thin_time_factor,
            )

        if kind == "auto" and da.ndim == 3:
            inferred = _infer_time_y_x_dims(da)
            t_dim = t_dim or inferred[0]
            # Map optional vmin/vmax kwargs to clim for the widget
            vmin = local_kwargs.pop("vmin", None)
            vmax = local_kwargs.pop("vmax", None)
            clim = (vmin, vmax) if vmin is not None or vmax is not None else None
            return simple_cube_widget(
                da,
                time_dim=t_dim,
                cmap=cmap,
                clim=clim,
                aspect=local_kwargs.pop("aspect", "equal"),
            )

        # 2D fallback
        if da.ndim == 2:
            da2 = da
        elif da.ndim >= 3:
            inferred = _infer_time_y_x_dims(da)
            t_dim = t_dim or inferred[0]
            if t_dim is None:
                raise ValueError("Cannot select 2D slice without a time dimension.")
            da2 = da.isel({t_dim: -1})
        else:
            raise ValueError(f"Cannot plot DataArray with dims={da.dims}")

        return (
            da2.plot.imshow(cmap=cmap, **local_kwargs)
            if hasattr(da2.plot, "imshow")
            else da2.plot(**local_kwargs)
        )

    if obj is None:
        return _op
    return _op(obj)


__all__ = ["plot"]
