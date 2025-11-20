"""Interactive plotting verb for time-indexed cubes."""

from __future__ import annotations

from typing import Iterable, Sequence

import ipywidgets as widgets
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import xarray as xr

from ..streaming import VirtualCube


def _select_data_var(ds: xr.Dataset, var_name: str | None) -> xr.DataArray:
    if var_name is not None:
        if var_name not in ds.data_vars:
            raise ValueError(
                f"Requested variable {var_name!r} not found in dataset variables {list(ds.data_vars)}"
            )
        return ds[var_name]

    first_var = sorted(ds.data_vars)[0]
    return ds[first_var]


def _normalize_dataarray(
    obj: xr.DataArray | xr.Dataset,
    *,
    time_dim: str,
    y_dim: str,
    x_dim: str,
    var_name: str | None,
) -> xr.DataArray:
    if isinstance(obj, xr.Dataset):
        da = _select_data_var(obj, var_name)
    elif isinstance(obj, xr.DataArray):
        da = obj
    else:
        raise TypeError(
            "plot verb expects an xarray.DataArray or xarray.Dataset after materialization; "
            f"received {type(obj)!r}"
        )

    missing = {time_dim, y_dim, x_dim} - set(da.dims)
    if missing:
        raise ValueError(
            f"DataArray is missing required dimensions {missing}; found dims {da.dims}"
        )

    extra_dims: Sequence[str] = [
        dim for dim in da.dims if dim not in {time_dim, y_dim, x_dim}
    ]
    if extra_dims:
        da = da.isel({dim: 0 for dim in extra_dims}).squeeze(drop=True)

    return da.transpose(time_dim, y_dim, x_dim)


def _infer_time_index_from_tile(
    vc: VirtualCube, first_da: xr.DataArray, time_dim: str
) -> pd.Index:
    time_values = pd.Index(first_da[time_dim].values)
    start = vc.coords_metadata.get("start")
    end = vc.coords_metadata.get("end")

    freq: str | pd.Timedelta | None = None
    if len(time_values) >= 2:
        dt_index = pd.DatetimeIndex(time_values)
        freq = pd.infer_freq(dt_index)
        if freq is None:
            delta = dt_index[1] - dt_index[0]
            if not pd.isna(delta):
                freq = delta

    if freq is None or start is None or end is None:
        return time_values

    ranges: list[pd.Timestamp] = []
    tiler_outputs = list(vc.time_tiler(vc.loader_kwargs))
    if not tiler_outputs:
        tiler_outputs = [{}]

    for spec in tiler_outputs:
        chunk_start = spec.get("start", start)
        chunk_end = spec.get("end", end)
        rng = pd.date_range(chunk_start, chunk_end, freq=freq)
        ranges.extend(rng.to_list())

    full_index = pd.DatetimeIndex(ranges).unique().sort_values()
    if len(full_index) == 0:
        return time_values
    return full_index


def _iter_time_labels(time_index: pd.Index) -> Iterable[str]:
    for value in time_index:
        yield str(value)


def plot(
    time_dim: str = "time",
    y_dim: str = "y",
    x_dim: str = "x",
    var_name: str | None = None,
    cmap: str | None = None,
    vmin: float | None = None,
    vmax: float | None = None,
    figsize: tuple[float, float] | None = (6, 4),
    title: str | None = None,
    aspect: str = "equal",
):
    """Pipe verb: interactive time slider + 2D map viewer for cubes."""

    def _op(obj: xr.DataArray | xr.Dataset | VirtualCube):
        nonlocal vmin, vmax

        is_virtual = isinstance(obj, VirtualCube)
        if is_virtual:
            vc = obj
            tile_iter = vc.iter_time_tiles()
            first_tile = next(tile_iter, None)
            if first_tile is None:
                raise ValueError("VirtualCube produced no tiles to visualize")

            first_da = _normalize_dataarray(
                first_tile, time_dim=time_dim, y_dim=y_dim, x_dim=x_dim, var_name=var_name
            )
            time_index = _infer_time_index_from_tile(vc, first_da, time_dim)
            da = first_da
        else:
            da = _normalize_dataarray(
                obj, time_dim=time_dim, y_dim=y_dim, x_dim=x_dim, var_name=var_name
            )
            time_index = pd.Index(da[time_dim].values)

        if da.ndim != 3:
            raise ValueError(
                "plot verb expects a 3D DataArray after normalization (time, y, x); "
                f"received dims {da.dims}"
            )

        n_time = da.sizes[time_dim]
        if n_time == 0:
            raise ValueError("Cannot plot an empty cube with no time steps")

        time_labels = list(_iter_time_labels(time_index))
        slider = widgets.IntSlider(
            value=0,
            min=0,
            max=len(time_index) - 1,
            step=1,
            description=time_dim,
            continuous_update=False,
            readout=True,
        )
        label = widgets.Label()
        out = widgets.Output()

        if vmin is None or vmax is None:
            first_slice = da.isel({time_dim: 0})
            arr = np.asarray(first_slice.values)
            if vmin is None:
                vmin = float(np.nanmin(arr))
            if vmax is None:
                vmax = float(np.nanmax(arr))

        def _slice_virtual(idx: int) -> xr.DataArray:
            target_time = time_index[idx]
            loader_kwargs = {**vc.loader_kwargs, "start": target_time, "end": target_time}
            tile = vc.loader(**loader_kwargs)
            tile_da = _normalize_dataarray(
                tile, time_dim=time_dim, y_dim=y_dim, x_dim=x_dim, var_name=var_name
            )
            if tile_da.sizes.get(time_dim, 0) > 1:
                coord_vals = np.asarray(tile_da[time_dim].values)
                matches = np.where(coord_vals == np.array(target_time))[0]
                if matches.size:
                    tile_da = tile_da.isel({time_dim: int(matches[0])})
            return tile_da.squeeze(drop=True)

        def _get_slice(idx: int) -> xr.DataArray:
            if is_virtual:
                return _slice_virtual(idx)
            return da.isel({time_dim: idx}).squeeze(drop=True)

        def _update(change: dict | None = None) -> None:
            idx = slider.value if change is None else change.get("new", slider.value)
            with out:
                out.clear_output(wait=True)
                slice_da = _get_slice(int(idx))
                fig, ax = plt.subplots(figsize=figsize)
                slice_da.plot.imshow(
                    ax=ax,
                    cmap=cmap,
                    vmin=vmin,
                    vmax=vmax,
                    add_colorbar=True,
                )
                time_val = time_index[int(idx)]
                plot_title = title or (
                    f"{slice_da.name} @ {time_val}" if slice_da.name is not None else str(time_val)
                )
                ax.set_title(plot_title)
                ax.set_aspect(aspect)
                fig.tight_layout()
                label.value = f"{time_dim}: {time_labels[int(idx)]}"
                plt.show()

        _update()
        slider.observe(_update, names="value")

        controls = widgets.HBox([slider, label])
        return widgets.VBox([controls, out])

    return _op


__all__ = ["plot"]
