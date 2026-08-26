"""Credentialed, bounded Daymet candidate access for live certification.

Daymet remains outside noun discovery until a reviewed real fixture is
certified. ORNL DAAC currently requires a NASA Earthdata bearer token.
"""

from __future__ import annotations

from io import BytesIO
import os
from typing import Mapping, Sequence

import requests
import xarray as xr


DAYMET_V4_NCSS = (
    "https://thredds.daac.ornl.gov/thredds/ncss/ornldaac/1840/"
    "daymet_v4_daily_na_{variable}_{year}.nc"
)


def build_daymet_ncss_request(
    *, variable: str, year: int, bbox: Sequence[float], start: str, end: str
) -> tuple[str, dict[str, str]]:
    """Build the documented ORNL NCSS request without issuing it."""

    west, south, east, north = (float(item) for item in bbox)
    if not (west < east and south < north):
        raise ValueError("Daymet bbox must be [west, south, east, north].")
    if variable not in {"tmax", "tmin", "prcp", "srad", "vp", "swe", "dayl"}:
        raise ValueError(f"Unsupported Daymet variable {variable!r}.")
    return DAYMET_V4_NCSS.format(variable=variable, year=year), {
        "var": variable,
        "north": str(north),
        "west": str(west),
        "east": str(east),
        "south": str(south),
        "disableProjSubset": "on",
        "horizStride": "1",
        "time_start": f"{start}T12:00:00Z",
        "time_end": f"{end}T12:00:00Z",
        "timeStride": "1",
        "accept": "netcdf",
    }


def load_daymet_candidate(
    *,
    variable: str,
    bbox: Sequence[float],
    start: str,
    end: str,
    earthdata_token: str | None = None,
    timeout: int = 120,
) -> xr.Dataset:
    """Retrieve one bounded single-year Daymet sample for certification."""

    start_year, end_year = int(start[:4]), int(end[:4])
    if start_year != end_year:
        raise ValueError("The candidate loader currently requires a single-year request.")
    token = earthdata_token or os.environ.get("EARTHDATA_TOKEN")
    if not token:
        raise PermissionError("Daymet certification requires EARTHDATA_TOKEN.")
    url, params = build_daymet_ncss_request(
        variable=variable, year=start_year, bbox=bbox, start=start, end=end
    )
    response = requests.get(
        url,
        params=params,
        headers={"Authorization": f"Bearer {token}", "User-Agent": "cubedynamics-daymet/1"},
        timeout=timeout,
    )
    response.raise_for_status()
    dataset = xr.open_dataset(BytesIO(response.content), engine="scipy").load()
    rename = {name: target for name, target in (("x", "x"), ("y", "y")) if name in dataset.dims}
    if rename:
        dataset = dataset.rename(rename)
    dataset.attrs.update(
        {
            "source": "Daymet",
            "source_provider": "NASA ORNL DAAC",
            "source_product": "Daymet Daily V4",
            "source_url": response.url,
            "is_synthetic": False,
            "bounded_access": True,
        }
    )
    return dataset


__all__ = ["build_daymet_ncss_request", "load_daymet_candidate"]
