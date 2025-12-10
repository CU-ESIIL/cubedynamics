from __future__ import annotations

from typing import Optional

from .fired_io import (
    load_fired_conus_ak,
    pick_event_with_joint_support,
    load_fired_event_by_joint_support,
    TemporalSupport,
)
from .time_hull import FireEventDaily, build_fire_event


def fired_event(
    *,
    event_id: Optional[int] = None,
    climate_support: Optional[TemporalSupport] = None,
    which: str = "daily",
    prefer: str = "gpkg",
    min_days: int = 40,
    time_buffer_days: int = 14,
    **kwargs,
) -> FireEventDaily:
    """
    Public entry point for loading a FIRED fire event.

    Two use cases:
      (1) fired_event(event_id=21281)
      (2) fired_event(climate_support=TemporalSupport(...))

    Parameters
    ----------
    event_id : int, optional
        If provided, return this event.
    climate_support : TemporalSupport, optional
        If provided (and event_id is None), auto-select a fire whose
        buffered window fits inside climate coverage.
    which : {"daily", "events"}
        Which FIRED layer to load.
    prefer : {"gpkg", "shp"}
        Preferred format inside the ZIP.
    min_days : int
        Minimum duration for auto-selection.
    time_buffer_days : int
        Buffer on both ends of FIRED time window when testing support.
    **kwargs :
        Passed through to load_fired_conus_ak.

    Returns
    -------
    FireEventDaily
    """

    if event_id is not None:
        gdf = load_fired_conus_ak(which=which, prefer=prefer, **kwargs)
        return build_fire_event(gdf, event_id)

    if climate_support is not None:
        return load_fired_event_by_joint_support(
            climate_support,
            time_buffer_days=time_buffer_days,
            min_days=min_days,
            which=which,
            prefer=prefer,
            **kwargs,
        )

    raise ValueError("Must provide either event_id or climate_support")
