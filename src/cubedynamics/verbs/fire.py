from __future__ import annotations

from typing import Any, Optional, Tuple, Dict

import numpy as np
import xarray as xr
import geopandas as gpd

from ..fire_time_hull import (
    build_fire_event,
    compute_time_hull_geometry,
    load_climate_cube_for_event,
    build_inside_outside_climate_samples,
    plot_climate_filled_hull,
    plot_inside_outside_hist,
    FireEventDaily,
    TimeHull,
    ClimateCube,
    HullClimateSummary,
)


def fire_plot(
    da: xr.DataArray | None = None,
    *,
    fired_daily: gpd.GeoDataFrame,
    event_id: Any,
    climate_variable: str = "tmmx",
    time_buffer_days: int = 14,
    n_ring_samples: int = 200,
    n_theta: int = 296,
    color_limits: Optional[Tuple[float, float]] = None,
    show_hist: bool = True,
    save_prefix: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Fire time-hull + climate visualization verb.

    This is a thin wrapper around the fire/time-hull prototype so that
    the output plot looks the same as the notebook demo:

      • 3-D Plotly Mesh3d hull colored by mean climate inside
      • Optional Matplotlib histogram of inside vs outside pixels

    Parameters
    ----------
    da
        Currently unused. Included so this function can be used as a
        CubeDynamics verb in a pipeline, e.g.:

            pipe(ndvi) | v.fire_plot(fired_daily=..., event_id=...)

    fired_daily
        FIRED *daily* GeoDataFrame with columns like ``id``, ``date``,
        and ``geometry``.

    event_id
        Event ID in ``fired_daily`` to visualize.

    climate_variable
        GRIDMET variable name (e.g. "tmmx", "vpd").

    time_buffer_days
        Number of days padding before/after the fire when fetching
        climate data.

    n_ring_samples, n_theta
        Geometry resolution for the time-hull.

    color_limits
        Optional (vmin, vmax) for the colorbar. If None, derived from
        the climate cube (5th–95th percentiles), matching the prototype.

    show_hist
        If True, also draw the Matplotlib histogram.

    save_prefix
        Optional filename stem to save PNG/PDF via Plotly (requires
        ``kaleido``).

    Returns
    -------
    dict
        {
            "event": FireEventDaily,
            "hull": TimeHull,
            "cube": ClimateCube,
            "summary": HullClimateSummary,
            "fig_hull": go.Figure,
            "color_limits": (vmin, vmax),
        }
    """
    # 1) Build event
    event = build_fire_event(fired_daily, event_id)
    print(
        f"Built FireEventDaily for id={event_id}, "
        f"t0={event.t0.date()}, t1={event.t1.date()}, "
        f"centroid=({event.centroid_lat:.3f}, {event.centroid_lon:.3f})"
    )

    # 2) Time-hull geometry
    hull = compute_time_hull_geometry(
        event,
        n_ring_samples=n_ring_samples,
        n_theta=n_theta,
    )
    print("TimeHull metrics:", hull.metrics)

    # 3) Climate cube
    cube = load_climate_cube_for_event(
        event,
        time_buffer_days=time_buffer_days,
        variable=climate_variable,
    )
    print(f"Climate cube shape: {cube.da.shape} | dims: {cube.da.dims}")
    print("GRIDMET source:", cube.da.attrs.get("gridmet_source", "unknown"))

    # 4) Inside vs outside samples
    summary = build_inside_outside_climate_samples(event, cube)
    print(
        f"Collected {summary.values_inside.size} inside pixels and "
        f"{summary.values_outside.size} outside pixels."
    )

    # 5) Color limits
    if color_limits is None:
        vmin = float(np.nanpercentile(cube.da.values, 5))
        vmax = float(np.nanpercentile(cube.da.values, 95))
        color_limits = (vmin, vmax)
        print(f"[INFO] Using auto color_limits={color_limits} for this run.")

    # 6) Variable label
    if climate_variable == "tmmx":
        var_label = "Temperature max"
    elif climate_variable == "vpd":
        var_label = "Vapor pressure deficit (kPa)"
    else:
        var_label = climate_variable

    # 7) 3-D Plotly hull (matches prototype look)
    fig_hull = plot_climate_filled_hull(
        hull,
        summary,
        title_prefix=f"GRIDMET {climate_variable}",
        var_label=var_label,
        save_prefix=save_prefix,
        color_limits=color_limits,
    )
    fig_hull.show()

    # 8) Optional histogram panel
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

