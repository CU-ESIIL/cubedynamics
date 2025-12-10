"""
Example: Fire time-hull × GRIDMET climate

This example assumes:
  - Network access to CU Scholar and GRIDMET.
  - FIRED and GRIDMET servers are reachable.

It is not run in automated tests.
"""

import pandas as pd

import cubedynamics as cd
from cubedynamics import pipe, verbs as v
from cubedynamics.ops_fire.fired_io import TemporalSupport


def main():
    clim_support = TemporalSupport(
        start=pd.Timestamp("1980-01-01"),
        end=None,
    )

    fired_evt = cd.fired_event(event_id=21281)

    clim = cd.gridmet(
        lat=fired_evt.centroid_lat,
        lon=fired_evt.centroid_lon,
        start=str(fired_evt.t0 - pd.Timedelta(days=14)).split(" ")[0],
        end=str(fired_evt.t1 + pd.Timedelta(days=14)).split(" ")[0],
        variable="tmmx",
    )

    cube = pipe(clim) | v.extract(fired_event=fired_evt)

    pipe(clim) | v.extract(fired_event=fired_evt) | v.vase()
    pipe(clim) | v.extract(fired_event=fired_evt) | v.climate_hist()


if __name__ == "__main__":
    main()
