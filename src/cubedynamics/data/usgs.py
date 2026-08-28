"""Bounded USGS discharge candidate; not yet a certified catalog source.

Uses the modern OGC continuous collection. Values stay in provider units with
native approval/qualifier metadata. No gridding, filling, unit conversion,
provisional filtering, or legacy endpoint fallback is implicit.
"""
from __future__ import annotations

import json
import re
from urllib.parse import parse_qs, urljoin, urlsplit
import warnings

import numpy as np
import pandas as pd
import xarray as xr

from ._transport import ReadLimits, SourceClient, SourceBudgetError, SourceSchemaError

BASE = "https://api.waterdata.usgs.gov/ogcapi/v0/collections"
CONTRACT = "usgs-continuous-discharge-v1"
MAX_DAYS = 31
MAX_ROWS = 10_000
PAGE_SIZE = 2000


def _scope(site, start, end, series_id):
    if not isinstance(site, str) or not re.fullmatch(r"USGS-\d{8,15}", site):
        raise ValueError("Exactly one agency-prefixed USGS site is required")
    first, last = pd.Timestamp(start), pd.Timestamp(end)
    if pd.isna(first) or pd.isna(last) or first.tzinfo is None or last.tzinfo is None:
        raise ValueError("Explicit timezone-aware start/end required")
    first, last = first.tz_convert("UTC"), last.tz_convert("UTC")
    if not pd.Timedelta(0) < last - first <= pd.Timedelta(days=MAX_DAYS):
        raise ValueError("Streamflow requires a positive interval no longer than 31 days")
    if series_id is not None and (not isinstance(series_id, str) or not re.fullmatch(r"[a-fA-F0-9-]{32,36}", series_id)):
        raise ValueError("Invalid time-series ID")
    return first, last


def _pages(client, params):
    """Follow bounded cursor/offset pagination for the identical scoped query."""
    endpoint = BASE + "/continuous/items"
    url, query = endpoint, params
    seen, features, matched = set(), [], None
    for _ in range(10):
        body = client.json(url, params=query)
        page = body.get("features")
        if not isinstance(page, list) or len(page) > PAGE_SIZE:
            raise SourceSchemaError("Invalid or oversized observation page")
        if body.get("numberReturned", len(page)) != len(page):
            raise SourceSchemaError("Observation page count mismatch")
        count = body.get("numberMatched")
        if isinstance(count, int):
            if count < 0 or (matched is not None and matched != count):
                raise SourceSchemaError("Observation count changed while paging; retry a fresh snapshot")
            matched = count
            if count > MAX_ROWS:
                raise SourceBudgetError("Observation count exceeds 10000; shorten the interval")
        features.extend(page)
        if len(features) > MAX_ROWS:
            raise SourceBudgetError("Observation row budget exceeded")
        following = [link.get("href") for link in body.get("links", []) if link.get("rel") == "next"]
        if not following:
            if matched is not None and len(features) != matched:
                raise SourceSchemaError("Incomplete observation response")
            return features
        if len(following) != 1 or not isinstance(following[0], str) or not page:
            raise SourceSchemaError("Ambiguous or empty pagination")
        next_url = urljoin(endpoint, following[0])
        parts = urlsplit(next_url)
        if (f"{parts.scheme}://{parts.netloc}{parts.path}" != endpoint
                or parts.fragment or next_url in seen):
            raise SourceSchemaError("Unsafe or repeating pagination link")
        next_params = parse_qs(parts.query, keep_blank_values=True)
        expected = {k: [str(v)] for k, v in params.items()}
        # Changing station, variable, time, limit or adding CQL is never allowed.
        cursor = next_params.get("cursor")
        offset = next_params.get("offset")
        paging_ok = ((offset == [str(len(features))] and cursor is None)
                     or (offset is None and cursor is not None and len(cursor) == 1
                         and 0 < len(cursor[0]) <= 2048
                         and all(32 < ord(c) < 127 for c in cursor[0])))
        if ({k: v for k, v in next_params.items() if k not in ("offset", "cursor")} != expected
                or not paging_ok):
            raise SourceSchemaError("Pagination changed the query scope or offset")
        seen.add(next_url)
        url, query = next_url, None
    raise SourceBudgetError("Pagination page budget exceeded")


def _normalize(features, location, metadata, *, site, first, last, trace):
    if not features:
        raise SourceSchemaError("No discharge observations for the requested station/window")
    try:
        rows = [f["properties"] for f in features]
        identifiers = {row["time_series_id"] for row in rows}
        if len(identifiers) != 1:
            raise SourceSchemaError("Multiple time series; supply series_id explicitly")
        series_id = next(iter(identifiers))
        meta = metadata["properties"]
        if (location["id"] != site or metadata["id"] != series_id
                or meta["monitoring_location_id"] != site or meta["parameter_code"] != "00060"):
            raise SourceSchemaError("Site/series metadata identity mismatch")
        if any(row["monitoring_location_id"] != site or row["parameter_code"] != "00060" for row in rows):
            raise SourceSchemaError("Observations differ from requested site/parameter")
        units = meta["unit_of_measure"]
        if not isinstance(units, str) or not units or {r["unit_of_measure"] for r in rows} != {units}:
            raise SourceSchemaError("Missing or inconsistent discharge units")
        if not meta.get("statistic_id") or {r["statistic_id"] for r in rows} != {meta["statistic_id"]}:
            raise SourceSchemaError("Missing or inconsistent statistic context")
        if any(pd.Timestamp(row["time"]).tzinfo is None for row in rows):
            raise SourceSchemaError("Provider time must include timezone")
        times = pd.to_datetime([r["time"] for r in rows], utc=True, errors="raise")
        if times.isna().any() or times.duplicated().any() or (times < first).any() or (times > last).any():
            raise SourceSchemaError("Missing, duplicate or out-of-window observation time")
        values = np.asarray([np.nan if r["value"] is None else float(r["value"]) for r in rows])
        if any(r["value"] is not None and not np.isfinite(v) for r, v in zip(rows, values)):
            raise SourceSchemaError("Non-finite numeric text is not an explicit missing value")
        if location["geometry"]["type"] != "Point":
            raise SourceSchemaError("Monitoring location must be a point")
        lon, lat = location["geometry"]["coordinates"][:2]
        if not (-180 <= lon <= 180 and -90 <= lat <= 90):
            raise SourceSchemaError("Invalid monitoring coordinates")
        order = np.argsort(times.asi8)
        coords = {"time": times[order].tz_localize(None).to_numpy(dtype="datetime64[ns]"),
                  "station": np.asarray([site], dtype=object),
                  "longitude": ("station", [lon]), "latitude": ("station", [lat]),
                  "time_series_id": ("station", np.asarray([series_id], dtype=object)),
                  "record_id": ("time", np.asarray([str(f["id"]) for f in features], dtype=object)[order])}
        for key in ("approval_status", "qualifier", "last_modified"):
            if any(r.get(key) is not None and not isinstance(r[key], str) for r in rows):
                raise SourceSchemaError(f"Provider changed {key} from string/null")
            # Separate flags retain missing vs null vs empty without forcing
            # users to decode JSON strings to select provisional observations.
            coords[key] = ("time", np.asarray([r.get(key) or "" for r in rows], dtype=object)[order])
            coords[key + "_present"] = ("time", np.asarray([key in r for r in rows], dtype="int8")[order])
            coords[key + "_is_null"] = ("time", np.asarray([key in r and r[key] is None for r in rows], dtype="int8")[order])
        cube = xr.Dataset({"streamflow": (("time", "station"), values[order, None],
                          {"units": units, "long_name": "Discharge", "parameter_code": "00060",
                           "statistic_id": meta["statistic_id"]})}, coords=coords,
            attrs={"source": "USGS", "scientific_noun": "streamflow", "source_flavor": "usgs",
                   "source_mode": "rolling", "crs": "EPSG:4326", "is_synthetic": 0,
                   "requested_start": first.isoformat(), "requested_end": last.isoformat(),
                   "time_zone": "UTC", "semantic_units": units, "source_url": BASE + "/continuous/items",
                   "interpretation_contract": CONTRACT, "release_status": "candidate_not_certified",
                   "stable_observation_key": "time_series_id + time",
                   "site_metadata": json.dumps(location, sort_keys=True),
                   "series_metadata": json.dumps(metadata, sort_keys=True),
                   "provenance": json.dumps(trace, sort_keys=True),
                   "reproducibility": "Replay the retained raw snapshot; live observations may be revised."})
        cube.time.attrs["timezone"] = "UTC"
        if "Provisional" in cube.approval_status.values:
            warnings.warn("USGS provisional discharge retained; values may be revised.", UserWarning, stacklevel=2)
        return cube
    except (KeyError, TypeError, ValueError) as exc:
        if isinstance(exc, SourceSchemaError):
            raise
        raise SourceSchemaError(f"Invalid USGS observation/metadata schema: {exc}") from exc


def streamflow(*, site, start, end, source="usgs", series_id=None,
               snapshot_dir=None, offline=False):
    """Load bounded native USGS discharge as a ``time × station`` Dataset.

    Candidate API, not a production catalog registration. One station, at most
    31 days / 10000 observations, 7-day request batches, 40 requests including
    retries, 16 MB body budget, 180 s between-read deadline. Network reads are
    eager here; subsequent compatible pipe verbs keep their ordinary semantics.

    ``series_id`` selects an exact provider series when a station has multiple.
    Missing observations are not filled. All statuses are retained. An empty or
    partial response raises an explicit error. ``snapshot_dir`` saves exact raw
    responses; use a NEW directory for each refresh and ``offline=True`` for
    hash-verified replay, without network or silent cache fallback.
    """
    if source != "usgs":
        raise ValueError("streamflow currently supports source='usgs' only")
    first, last = _scope(site, start, end, series_id)
    with SourceClient(origins={"https://api.waterdata.usgs.gov"}, limits=ReadLimits(),
                      snapshot_dir=snapshot_dir, offline=offline) as client:
        features, previous_boundary = [], None
        cursor = first
        while cursor < last:
            stop = min(last, cursor + pd.Timedelta(days=7))
            params = {"f": "json", "monitoring_location_id": site, "parameter_code": "00060",
                      "time": f"{cursor.isoformat()}/{stop.isoformat()}", "limit": PAGE_SIZE}
            if series_id is not None:
                params["time_series_id"] = series_id
            batch = _pages(client, params)
            batch_keys = set()
            # Adjacent inclusive windows share one timestamp. Deduplicate only
            # byte-equivalent boundary features; conflicting refreshes fail.
            for feature in batch:
                row = feature.get("properties", {})
                stamp = pd.Timestamp(row.get("time"))
                if pd.isna(stamp) or stamp.tzinfo is None or stamp < cursor or stamp > stop:
                    raise SourceSchemaError("Observation outside requested batch")
                if series_id is not None and row.get("time_series_id") != series_id:
                    raise SourceSchemaError("Provider ignored requested series_id")
                key = (row.get("time_series_id"), stamp)
                if key in batch_keys:
                    raise SourceSchemaError("Duplicate observation within a batch")
                batch_keys.add(key)
                if previous_boundary is not None and stamp == cursor and key in previous_boundary:
                    if feature != previous_boundary[key]:
                        raise SourceSchemaError("Observation revised across batch boundary; retry fresh snapshot")
                    continue
                features.append(feature)
            if len(features) > MAX_ROWS:
                raise SourceBudgetError("Combined row budget exceeded")
            previous_boundary = {(f["properties"]["time_series_id"], pd.Timestamp(f["properties"]["time"])): f
                                 for f in batch if pd.Timestamp(f["properties"]["time"]) == stop}
            cursor = stop
        if not features:
            raise SourceSchemaError("No discharge observations for the requested station/window")
        series = {f["properties"].get("time_series_id") for f in features}
        if len(series) != 1:
            raise SourceSchemaError("Multiple time series; supply series_id explicitly")
        chosen = next(iter(series))
        if not isinstance(chosen, str) or not re.fullmatch(r"[a-fA-F0-9-]{32,36}", chosen):
            raise SourceSchemaError("Invalid provider time-series ID")
        location = client.json(BASE + f"/monitoring-locations/items/{site}", params={"f": "json"})
        metadata = client.json(BASE + f"/time-series-metadata/items/{chosen}", params={"f": "json"})
        return _normalize(features, location, metadata, site=site, first=first, last=last, trace=client.trace)


def compare_observations(before, after):
    """Audit rolling updates over the same scope; row UUID refresh is not change.

    Return counts, not an assertion that either version is scientifically valid.
    Both input snapshots remain untouched. Unit/statistic/contract changes are
    interpretation changes and must be reviewed, not merged as observations.
    """
    for key in ("interpretation_contract", "requested_start", "requested_end"):
        if before.attrs.get(key) != after.attrs.get(key):
            raise ValueError(f"Cannot compare different {key}")
    if before.streamflow.attrs != after.streamflow.attrs or before.station.item() != after.station.item():
        raise ValueError("Cannot compare different units/statistic/station")
    if before.time_series_id.item() != after.time_series_id.item():
        raise ValueError("Cannot compare different series")
    fields = ["streamflow", "approval_status", "qualifier"]
    fields += [key + suffix for key in ("approval_status", "qualifier") for suffix in ("_present", "_is_null")]
    def records(cube):
        result = {}
        for i, stamp in enumerate(cube.time.values):
            row = []
            for field in fields:
                value = cube[field].isel(time=i).item()
                row.append(None if isinstance(value, float) and np.isnan(value) else value)
            result[str(stamp)] = row
        return result
    left, right = records(before), records(after)
    common = left.keys() & right.keys()
    return {"added": len(right.keys() - left.keys()), "removed": len(left.keys() - right.keys()),
            "changed": sum(left[k] != right[k] for k in common),
            "unchanged": sum(left[k] == right[k] for k in common)}


__all__ = ["streamflow", "compare_observations"]
