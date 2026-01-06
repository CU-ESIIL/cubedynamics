from __future__ import annotations

from typing import Any, Optional, Tuple, Dict

import numpy as np
import xarray as xr
import geopandas as gpd
import pandas as pd

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
    TimeHull,
    ClimateCube,
    HullClimateSummary,
    sample_inside_outside,
    log,
)


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
    show_hist: bool = False,
    verbose: bool = False,
    save_prefix: Optional[str] = None,
    fast: bool = False,
    allow_synthetic: bool = False,
    prefer_streaming: bool = True,
) -> Dict[str, Any]:
    """Fire time-hull + climate visualization verb.

    Supports cube-first (preferred) and legacy fire-first invocation styles.
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

    summary = sample_inside_outside(event, cube.da, fast=fast, verbose=verbose)
    log(
        verbose,
        f"Collected {summary.values_inside.size} inside / {summary.values_outside.size} outside samples",
    )

    if color_limits is None:
        vals = summary.per_day_mean.values
        if vals.size == 0:
            color_limits = (0.0, 1.0)
        else:
            color_limits = (
                float(np.nanpercentile(vals, 5)),
                float(np.nanpercentile(vals, 95)),
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

    fig_hull = plot_climate_filled_hull(
        hull,
        summary,
        title_prefix=title_prefix,
        var_label=var_label,
        save_prefix=save_prefix,
        color_limits=color_limits,
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

