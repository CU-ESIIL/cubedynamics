from __future__ import annotations

from typing import Any, Optional, Tuple, Dict

import matplotlib.pyplot as plt
import numpy as np
import xarray as xr
import geopandas as gpd
import pandas as pd
import plotly.graph_objects as go

from ..fire_time_hull import (
    build_fire_event_daily,
    compute_time_hull_geometry,
    compute_derivative_hull,
    load_climate_cube_for_event,
    build_inside_outside_climate_samples,
    plot_climate_filled_hull,
    plot_inside_outside_hist,
    plot_derivative_hull,
    FireEventDaily,
    FireHull,
    TimeHull,
    Vase,
    ClimateCube,
    HullClimateSummary,
    sample_inside_outside,
    time_hull_to_vase,
    log,
)
from ..piping import Verb
from ..streaming import VirtualCube
from ..vase import VaseDefinition
from .vase import vase as _vase_base


def _unwrap_fire_cube(obj):
    if obj is None:
        raise ValueError("fire verb requires an input cube/DataArray; got None.")
    if isinstance(obj, VirtualCube):
        base_da = obj.materialize()
        if not isinstance(base_da, xr.DataArray):
            raise TypeError("VirtualCube underlying data is not a DataArray.")
        return base_da, obj
    if isinstance(obj, xr.DataArray):
        return obj, obj
    raise TypeError(f"Unsupported type for fire verb: {type(obj)!r}")


def _plot_time_hull_vase(
    vase_obj: Vase,
    da: xr.DataArray,
    summary: HullClimateSummary | None,
    **plot_kwargs,
):
    """Render a TimeHull-derived vase using matplotlib for compatibility."""

    verts = np.asarray(vase_obj.verts_km)
    tris = np.asarray(vase_obj.tris)
    meta = getattr(vase_obj, "metadata", {}) or {}
    t_days_vert = np.asarray(meta.get("t_days_vert", []), dtype=float)
    metrics = meta.get("metrics", {}) or {}

    intensities = None
    if isinstance(summary, HullClimateSummary):
        day_vals = np.asarray(summary.per_day_mean.sort_index().values, dtype=float)
        M = int(metrics.get("days", day_vals.size if day_vals.size else 0) or 0)
        if M <= 0 and t_days_vert.size:
            M = int(np.nanmax(t_days_vert)) if np.isfinite(t_days_vert).any() else day_vals.size
        if M > 0 and day_vals.size:
            if len(day_vals) < M:
                day_vals = np.pad(day_vals, (0, M - len(day_vals)), mode="edge")
            elif len(day_vals) > M:
                day_vals = day_vals[:M]
            if t_days_vert.size:
                layer_indices = np.clip((t_days_vert - 1).astype(int), 0, M - 1)
                intensities = day_vals[layer_indices]

    from matplotlib import cm
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection

    fig = plt.figure(figsize=plot_kwargs.get("figsize", (6, 4)))
    ax = fig.add_subplot(111, projection="3d")
    faces = [verts[idx] for idx in tris]

    if intensities is not None and intensities.size:
        norm = plt.Normalize(vmin=float(np.nanmin(intensities)), vmax=float(np.nanmax(intensities)))
        face_colors = []
        for tri in tris:
            vals = intensities[tri]
            face_colors.append(cm.viridis(norm(np.nanmean(vals))))
    else:
        face_colors = "steelblue"

    poly = Poly3DCollection(faces, facecolors=face_colors, linewidths=0.4, alpha=0.7)
    poly.set_edgecolor(plot_kwargs.get("edgecolor", "#2c3e50"))
    ax.add_collection3d(poly)
    ax.set_xlabel("x (km)")
    ax.set_ylabel("y (km)")
    ax.set_zlabel("days")

    if isinstance(summary, HullClimateSummary) and intensities is not None and intensities.size:
        mappable = cm.ScalarMappable(
            cmap="viridis",
            norm=plt.Normalize(vmin=float(np.nanmin(intensities)), vmax=float(np.nanmax(intensities))),
        )
        mappable.set_array([])
        fig.colorbar(mappable, ax=ax, label=da.name or "value")

    ax.view_init(elev=plot_kwargs.get("elev", 26), azim=plot_kwargs.get("azim", -58))
    ax.set_title(plot_kwargs.get("title", "Fire time-hull vase"))
    plt.tight_layout()
    plt.show()
    return fig


def extract(
    da: xr.DataArray | VirtualCube | None = None,
    *,
    fired_event: FireEventDaily,
    date_col: str = "date",
    n_ring_samples: int = 100,
    n_theta: int = 96,
    verbose: bool = False,
):
    """Attach canonical fire hull and climate summaries to a cube."""

    def _op(value: xr.DataArray | VirtualCube):
        base_da, original_obj = _unwrap_fire_cube(value)
        hull: FireHull = compute_time_hull_geometry(
            fired_event,
            n_ring_samples=n_ring_samples,
            n_theta=n_theta,
            verbose=verbose,
        )
        summary: HullClimateSummary = build_inside_outside_climate_samples(
            fired_event,
            ClimateCube(da=base_da),
            date_col=date_col,
            verbose=verbose,
        )
        base_da.attrs["fire_time_hull"] = hull
        base_da.attrs["fire_climate_summary"] = summary
        base_da.attrs["vase"] = time_hull_to_vase(hull)
        return original_obj

    if da is None:
        return Verb(_op)
    return _op(da)


def climate_hist(
    da: xr.DataArray | VirtualCube | None = None,
    *,
    bins: int = 40,
    var_label: str | None = None,
):
    """Plot climate distributions inside vs outside the event footprint."""

    if da is None:
        return Verb(lambda value: climate_hist(value, bins=bins, var_label=var_label))

    base_da, original_obj = _unwrap_fire_cube(da)
    summary = base_da.attrs.get("fire_climate_summary")
    if not isinstance(summary, HullClimateSummary):
        raise ValueError(
            "climate_hist() requires attrs['fire_climate_summary'] to be a "
            "HullClimateSummary, typically added by v.extract()."
        )
    plot_inside_outside_hist(summary, bins=bins, var_label=var_label or base_da.name or "value")
    return original_obj


def vase(
    da: xr.DataArray | VirtualCube | None = None,
    *,
    vase=None,
    outline: bool = True,
    verbose: bool = False,
    **plot_kwargs,
):
    """Plot either a generic VaseDefinition or a fire TimeHull-derived vase."""

    def _inner(value: xr.DataArray | VirtualCube):
        base_da, original_obj = _unwrap_fire_cube(value)
        vase_obj = vase if vase is not None else base_da.attrs.get("vase", None)
        if vase_obj is None:
            raise ValueError("v.vase() requires a vase definition via `vase=` or attrs['vase'].")
        if verbose and vase is None:
            print("Using vase from attrs['vase']")
        if isinstance(vase_obj, VaseDefinition):
            return _vase_base(vase=vase_obj, outline=outline, **plot_kwargs)(base_da)
        if isinstance(vase_obj, Vase):
            summary = base_da.attrs.get("fire_climate_summary")
            if summary is None:
                raise ValueError(
                    "Time-hull vase plotting requires attrs['fire_climate_summary']; run v.extract first."
                )
            return _plot_time_hull_vase(vase_obj, base_da, summary, **plot_kwargs)
        return _vase_base(vase=vase_obj, outline=outline, **plot_kwargs)(base_da)

    if da is None:
        return Verb(_inner)
    return _inner(da)


def fire_plot(
    da: xr.DataArray | None = None,
    *,
    fired_event: FireEventDaily | None = None,
    fired_daily: gpd.GeoDataFrame | None = None,
    event_id: Any | None = None,
    climate_variable: str = "vpd",
    freq: str | None = None,
    time_buffer_days: int = 1,
    n_ring_samples: int = 200,
    n_theta: int = 296,
    color_limits: Optional[Tuple[float, float]] = None,
    z_exaggeration: float = 2.2,
    scalar_debug_mode: Optional[str] = None,
    debug_scalars: bool = False,
    show_hist: bool = False,
    verbose: bool = False,
    save_prefix: Optional[str] = None,
    fast: bool = False,
    allow_synthetic: bool = False,
    prefer_streaming: bool = True,
) -> Dict[str, Any]:
    """Fire time-hull + climate visualization workflow.

    Supports cube-first (preferred) and legacy fire-first invocation styles.
    Returns a fire analysis bundle and a Plotly hull figure (`fig_hull`) as the
    current interactive backend for fire-specific visualization.
    """

    cube_first = da is not None
    if cube_first:
        if fired_event is None and fired_daily is None:
            raise ValueError("cube-first fire_plot requires fired_event or fired_daily+event_id")
    else:
        if fired_daily is None or event_id is None:
            raise ValueError("legacy fire_plot requires fired_daily and event_id")

    event = build_fire_event_daily(
        fired_daily=fired_daily, event_id=event_id, fired_event=fired_event
    )
    log(
        verbose,
        f"Built FireEventDaily id={event.event_id} window {event.t0.date()}–{event.t1.date()} centroid=({event.centroid_lat:.3f}, {event.centroid_lon:.3f})",
    )

    hull = compute_time_hull_geometry(
        event,
        n_ring_samples=n_ring_samples,
        n_theta=n_theta,
    )
    log(verbose, "TimeHull metrics:", hull.metrics)

    if cube_first:
        cube_da = da
        time_min = event.t0 - pd.Timedelta(days=time_buffer_days)
        time_max = event.t1 + pd.Timedelta(days=time_buffer_days)
        cube_da = cube_da.sel(time=slice(time_min, time_max))
        cube = ClimateCube(da=cube_da)
    else:
        cube = load_climate_cube_for_event(
            event,
            time_buffer_days=time_buffer_days,
            variable=climate_variable,
            freq=freq,
            prefer_streaming=prefer_streaming,
            allow_synthetic=allow_synthetic,
            verbose=verbose,
        )
    log(verbose, f"Cube shape {cube.da.shape} dims={cube.da.dims}")
    if verbose and hasattr(cube, "da"):
        src = cube.da.attrs.get("source")
        log(verbose, f"GRIDMET source: {src}")

    def _nan_guard(val):
        check = val.isnull().all()
        if hasattr(check, "compute"):
            check = check.compute()
        return bool(check)

    time_len = int(cube.da.sizes.get("time", 0)) if "time" in cube.da.sizes else 0
    all_nan = _nan_guard(cube.da) if cube.da.size else True
    if time_len == 0 or all_nan:
        freq_use = freq or cube.da.attrs.get("freq") or "D"
        message = (
            "empty time axis" if time_len == 0 else "all-NaN climate data"
        )
        message = (
            f"{message}; freq='{freq_use}' may miss timestamps for short windows. "
            "Pass freq='D' or expand the date range."
        )
        if not allow_synthetic:
            raise RuntimeError(message)

        time_min = event.t0 - pd.Timedelta(days=time_buffer_days)
        time_max = event.t1 + pd.Timedelta(days=time_buffer_days)
        times = pd.date_range(time_min, time_max, freq=freq_use)
        if times.size == 0:
            times = pd.date_range(time_min, time_max, freq="D")
            freq_use = "D"

        synth_da = xr.DataArray(
            np.zeros((len(times), 1, 1), dtype=float),
            coords={"time": times, "y": [event.centroid_lat], "x": [event.centroid_lon]},
            dims=("time", "y", "x"),
            name=climate_variable,
            attrs={
                **cube.da.attrs,
                "source": cube.da.attrs.get("source", "synthetic"),
                "is_synthetic": True,
                "freq": freq_use,
                "requested_start": str(time_min),
                "requested_end": str(time_max),
                "backend_error": message,
                "epsg": cube.da.attrs.get("epsg", 4326),
            },
        )
        cube = ClimateCube(da=synth_da)

    summary = sample_inside_outside(event, cube.da, fast=fast, verbose=verbose)
    log(
        verbose,
        f"Collected {summary.values_inside.size} inside / {summary.values_outside.size} outside samples",
    )
    if hasattr(hull, "attach_environment"):
        hull = hull.attach_environment(cube.da, variables=[climate_variable])

    if color_limits is None:
        vals = summary.per_day_mean.values
        if vals.size == 0:
            color_limits = (0.0, 1.0)
        else:
            color_limits = (
                float(np.nanpercentile(vals, 2)),
                float(np.nanpercentile(vals, 98)),
            )
        if not np.isfinite(color_limits[0]) or not np.isfinite(color_limits[1]) or color_limits[1] <= color_limits[0]:
            finite = vals[np.isfinite(vals)]
            if finite.size:
                vmin = float(np.nanmin(finite))
                vmax = float(np.nanmax(finite))
                if vmax <= vmin:
                    vmax = vmin + 1e-9
                color_limits = (vmin, vmax)

    if debug_scalars:
        vals = np.asarray(summary.per_day_mean.values, dtype=float)
        finite = vals[np.isfinite(vals)]
        pct = [1, 5, 25, 50, 75, 95, 99]
        pct_vals = np.nanpercentile(finite, pct).tolist() if finite.size else [float("nan")] * len(pct)
        log(
            True,
            "fire_plot scalar summary:",
            {
                "per_day_mean_len": int(vals.size),
                "nan_count": int(np.isnan(vals).sum()),
                "min": float(np.nanmin(finite)) if finite.size else float("nan"),
                "max": float(np.nanmax(finite)) if finite.size else float("nan"),
                "percentiles": dict(zip([str(p) for p in pct], pct_vals)),
            },
        )

    if climate_variable == "tmmx":
        var_label = "Max temperature (°C)"
        title_prefix = "GRIDMET tmmx"
    elif climate_variable == "tmmn":
        var_label = "Min temperature (°C)"
        title_prefix = "GRIDMET tmmn"
    elif climate_variable == "vpd":
        var_label = "Vapor pressure deficit (kPa)"
        title_prefix = "GRIDMET vpd"
    else:
        var_label = climate_variable
        title_prefix = climate_variable

    if hasattr(hull, "plot"):
        fig_hull = hull.plot(
            color=climate_variable,
            summary=summary,
            title_prefix=title_prefix,
            var_label=var_label,
            save_prefix=save_prefix,
            color_limits=color_limits,
            z_exaggeration=z_exaggeration,
            scalar_debug_mode=scalar_debug_mode,
            debug=debug_scalars,
        )
    else:
        fig_hull = plot_climate_filled_hull(
            hull,
            summary,
            title_prefix=title_prefix,
            var_label=var_label,
            save_prefix=save_prefix,
            color_limits=color_limits,
            z_exaggeration=z_exaggeration,
            scalar_debug_mode=scalar_debug_mode,
            debug=debug_scalars,
        )

    if show_hist:
        plot_inside_outside_hist(summary, var_label=var_label)

    return {
        "event": event,
        "hull": hull,
        "cube": cube,
        "summary": summary,
        "fig_hull": fig_hull,
        "color_limits": color_limits,
    }


def fire_panel(
    da: xr.DataArray | None = None,
    *,
    fired_event: FireEventDaily | None = None,
    fired_daily: gpd.GeoDataFrame | None = None,
    event_id: Any | None = None,
    climate_variable: str = "vpd",
    freq: str | None = None,
    time_buffer_days: int = 1,
    n_ring_samples: int = 200,
    n_theta: int = 296,
    bins: int = 40,
    show_hist: bool = True,
    verbose: bool = False,
    **kwargs,
) -> tuple[Dict[str, Any], go.Figure, Any | None]:
    """Return the fire analysis bundle plus figure objects for custom layouts."""

    results = fire_plot(
        da,
        fired_event=fired_event,
        fired_daily=fired_daily,
        event_id=event_id,
        climate_variable=climate_variable,
        freq=freq,
        time_buffer_days=time_buffer_days,
        n_ring_samples=n_ring_samples,
        n_theta=n_theta,
        show_hist=False,
        verbose=verbose,
        **kwargs,
    )

    fig_hist = None
    if show_hist:
        plot_inside_outside_hist(results["summary"], bins=bins, var_label=climate_variable)
        fig_hist = plt.gcf()

    return results, results["fig_hull"], fig_hist


def fire_derivative(
    da: xr.DataArray | None = None,
    *,
    fired_daily: gpd.GeoDataFrame,
    event_id: Any,
    order: int = 1,
    n_ring_samples: int = 200,
    n_theta: int = 296,
    save_prefix: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Fire derivative hull visualization verb.

    Builds a time-hull from FIRED daily perimeters and then constructs
    a derivative hull where radius encodes:

      • order=1 → perimeter spread *speed* (km/day)
      • order=2 → perimeter spread *acceleration* (km/day²)

    Parameters
    ----------
    da
        Currently unused. Included so this function can be used in a
        CubeDynamics pipeline, e.g.:

            pipe(ndvi) | v.fire_derivative(fired_daily=..., event_id=...)

    fired_daily
        FIRED daily GeoDataFrame with 'id', 'date', and 'geometry' columns.

    event_id
        Event ID in fired_daily.

    order
        1 for speed hull, 2 for acceleration hull.

    n_ring_samples, n_theta
        Geometry resolution parameters forwarded to compute_time_hull_geometry.

    save_prefix
        Optional filename stem to save a PNG/PDF of the derivative hull
        using Plotly static image export (requires `kaleido`).

    Returns
    -------
    dict
        {
            "event": FireEventDaily,
            "base_hull": TimeHull,
            "derivative_hull": TimeHull,
            "fig": go.Figure,
        }
    """
    if order not in (1, 2):
        raise ValueError("order must be 1 (speed) or 2 (acceleration).")

    # 1) Event geometry
    event = build_fire_event(fired_daily, event_id)
    print(
        f"Built FireEventDaily for id={event_id}, "
        f"t0={event.t0.date()}, t1={event.t1.date()}, "
        f"centroid=({event.centroid_lat:.3f}, {event.centroid_lon:.3f})"
    )

    # 2) Base time-hull geometry in km,km,days
    base_hull = compute_time_hull_geometry(
        event,
        n_ring_samples=n_ring_samples,
        n_theta=n_theta,
    )
    print("Base TimeHull metrics:", base_hull.metrics)

    # 3) Derivative hull (speed or acceleration)
    deriv_hull = compute_derivative_hull(base_hull, order=order)
    print("Derivative TimeHull metrics:", deriv_hull.metrics)

    # 4) Plot the derivative hull
    fig = plot_derivative_hull(
        base_hull,
        deriv_hull,
        order=order,
        title_prefix="Fire time-hull derivative",
    )
    fig.show()

    if save_prefix is not None:
        try:
            fig.write_image(f"{save_prefix}.png", scale=2)
            fig.write_image(f"{save_prefix}.pdf")
            print(f"Saved derivative hull figure to {save_prefix}.png/.pdf")
        except Exception as e:
            print(
                "Could not write PNG/PDF for derivative hull. "
                "Make sure `kaleido` is installed.\n"
                f"Error: {e}"
            )

    return {
        "event": event,
        "base_hull": base_hull,
        "derivative_hull": deriv_hull,
        "fig": fig,
    }
