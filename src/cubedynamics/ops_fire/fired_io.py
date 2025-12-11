from __future__ import annotations


from dataclasses import dataclass
from typing import Optional

import warnings
from pathlib import Path
import zipfile
import tempfile

import pandas as pd
import geopandas as gpd
import requests

from .time_hull import FireEventDaily, build_fire_event


@dataclass
class TemporalSupport:
    """
    Simple representation of a dataset's trustworthy temporal coverage.

    Parameters
    ----------
    start : pd.Timestamp
        Lower bound (inclusive) for when the dataset is considered reliable.
    end : pd.Timestamp, optional
        Upper bound (inclusive). If None, treat as open-ended into the future.
    """

    start: pd.Timestamp
    end: Optional[pd.Timestamp] = None


def load_fired_conus_ak(
    dataset_page: str = "https://scholar.colorado.edu/concern/datasets/d504rm74m",
    download_id: str = "h702q749s",           # file id (CONUS+AK events/daily ZIP)
    which: str = "events",                    # "events" or "daily"
    prefer: str = "gpkg",                     # "gpkg" or "shp"
    timeout: int = 180,
) -> gpd.GeoDataFrame:
    """
    Stream FIRED CONUS+AK polygons (Nov 2001–Mar 2021) from CU Scholar.

    This function downloads a ZIP archive containing both 'events' and
    'daily' layers, extracts the requested layer, and returns a GeoDataFrame
    in EPSG:4326.

    Parameters
    ----------
    dataset_page : str
        Landing page for the FIRED dataset.
    download_id : str
        ID of the ZIP file to download from CU Scholar.
    which : {"events", "daily"}
        Which layer to extract from the archive.
    prefer : {"gpkg", "shp"}
        Preferred file format inside the ZIP.
    timeout : int
        HTTP timeout in seconds.

    Returns
    -------
    GeoDataFrame
        FIRED layer in EPSG:4326.
    """
    assert which in ("events", "daily")
    assert prefer in ("gpkg", "shp")

    inner = {
        ("events", "gpkg"): "fired_conus-ak_events_nov2001-march2021.gpkg",
        ("events", "shp"):  "fired_conus-ak_events_nov2001-march2021.shp",
        ("daily", "gpkg"):  "fired_conus-ak_daily_nov2001-march2021.gpkg",
        ("daily", "shp"):   "fired_conus-ak_daily_nov2001-march2021.shp",
    }
    want_primary = inner[(which, prefer)]
    want_alt = inner[(which, "shp" if prefer == "gpkg" else "gpkg")]

    sess = requests.Session()
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/125.0 Safari/537.36"
        ),
        "Accept": "*/*",
        "Referer": dataset_page,
        "Connection": "keep-alive",
    }

    # Touch landing page first (helps avoid 403)
    r0 = sess.get(dataset_page, headers=headers, timeout=timeout)
    r0.raise_for_status()

    # Download ZIP
    zip_url = f"https://scholar.colorado.edu/downloads/{download_id}"
    resp = sess.get(zip_url, headers=headers, stream=True, timeout=timeout, allow_redirects=True)
    resp.raise_for_status()

    ct = resp.headers.get("Content-Type", "")
    cd_hdr = resp.headers.get("Content-Disposition", "")
    if ("zip" not in ct.lower()) and (".zip" not in cd_hdr.lower()):
        warnings.warn("Response does not clearly indicate a ZIP; proceeding anyway.")

    with tempfile.TemporaryDirectory() as td:
        zpath = Path(td) / "fired.zip"
        with open(zpath, "wb") as f:
            for chunk in resp.iter_content(chunk_size=1 << 20):
                if chunk:
                    f.write(chunk)

        with zipfile.ZipFile(zpath, "r") as z:
            names = z.namelist()

            chosen = None
            for candidate in (want_primary, want_alt):
                if candidate in names:
                    chosen = candidate
                    break

            if chosen is None:
                for n in names:
                    if which in n and (n.endswith(".gpkg") or n.endswith(".shp")):
                        chosen = n
                        break

            if chosen is None:
                raise RuntimeError(
                    "Could not find a FIRED layer inside the ZIP "
                    f"(looked for '{want_primary}' / '{want_alt}')."
                )

            z.extract(chosen, path=td)
            gdf = gpd.read_file(Path(td) / chosen)

            if gdf.crs:
                gdf = gdf.to_crs("EPSG:4326")
            else:
                gdf.set_crs("EPSG:4326", inplace=True)
            return gdf


def pick_event_with_joint_support(
    fired_daily: gpd.GeoDataFrame,
    *,
    climate_support: TemporalSupport,
    time_buffer_days: int = 14,
    min_days: int = 3,
    id_col: str = "id",
    date_col: str = "date",
    verbose: bool = False,
):
    """
    Pick a FIRED event whose buffered time window sits inside climate support.

    Parameters
    ----------
    fired_daily : GeoDataFrame
        FIRED daily polygons.
    climate_support : TemporalSupport
        Dataset temporal coverage window.
    time_buffer_days : int
        Days to buffer before t0 and after t1 of the event.
    min_days : int
        Minimum required duration in days for the event.
    id_col : str
        Event ID column name.
    date_col : str
        Date column name.
    verbose : bool, default False
        If True, print selection diagnostics.

    Returns
    -------
    event_id
        Identifier of the chosen event.

    Raises
    ------
    ValueError
        If no event satisfies the constraints.
    """
    df = fired_daily[[id_col, date_col]].copy()
    df[date_col] = pd.to_datetime(df[date_col], errors="coerce").dt.normalize()

    grp = df.groupby(id_col)[date_col].agg(["min", "max"]).rename(
        columns={"min": "t0", "max": "t1"}
    )
    grp["duration_days"] = (grp["t1"] - grp["t0"]).dt.days + 1

    buffer = pd.Timedelta(days=time_buffer_days)

    earliest_allowed_t0 = climate_support.start + buffer
    mask = grp["t0"] >= earliest_allowed_t0

    if climate_support.end is not None:
        latest_allowed_t1 = climate_support.end - buffer
        mask &= grp["t1"] <= latest_allowed_t1

    mask &= grp["duration_days"] >= min_days

    candidates = grp[mask].sort_values("t0")
    if candidates.empty:
        raise ValueError(
            "No FIRED events found whose buffered window fits inside climate support.\n"
            f"Climate support: [{climate_support.start.date()} .. "
            f"{(climate_support.end.date() if climate_support.end is not None else 'open')}], "
            f"buffer={time_buffer_days} days, min_days={min_days}."
        )

    chosen_id = candidates.index[0]

    if verbose:
        chosen_row = candidates.loc[chosen_id]
        dur = int(chosen_row["duration_days"])
        t0 = chosen_row["t0"]
        t1 = chosen_row["t1"]
        buffer = pd.Timedelta(days=time_buffer_days)
        print(
            f"Selected event id={chosen_id!r} with t0={t0.date()}, t1={t1.date()} "
            f"(duration ≈ {dur} days), buffered window "
            f"[{(t0 - buffer).date()} .. {(t1 + buffer).date()}] is inside climate support."
        )
    return chosen_id


def load_fired_event_by_joint_support(
    climate_support: TemporalSupport,
    *,
    time_buffer_days: int = 14,
    min_days: int = 40,
    which: str = "daily",
    prefer: str = "gpkg",
    verbose: bool = False,
    **kwargs,
) -> FireEventDaily:
    """
    Convenience helper: load FIRED, pick an event with joint temporal support,
    and build a FireEventDaily.

    Parameters
    ----------
    climate_support : TemporalSupport
        Dataset temporal coverage window.
    time_buffer_days : int
        Days to buffer FIRED event windows when checking support.
    min_days : int
        Minimum required duration in days.
    which : {"events", "daily"}
        Which FIRED layer to download.
    prefer : {"gpkg", "shp"}
        Preferred format inside the ZIP.
    verbose : bool, default False
        If True, print selection diagnostics.
    **kwargs :
        Additional arguments passed through to load_fired_conus_ak.

    Returns
    -------
    FireEventDaily
    """
    fired_daily = load_fired_conus_ak(which=which, prefer=prefer, **kwargs)
    event_id = pick_event_with_joint_support(
        fired_daily,
        climate_support=climate_support,
        time_buffer_days=time_buffer_days,
        min_days=min_days,
        verbose=verbose,
    )
    return build_fire_event(fired_daily, event_id)
