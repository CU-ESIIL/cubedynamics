#!/usr/bin/env python3
"""Anonymous, size-capped Daymet access experiment; not a public noun loader.

Never reads tokens, .netrc, browser sessions, or cookies. Never follows a
redirect, retries another backend, or downloads an unconstrained granule.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from io import BytesIO
import math
from pathlib import Path
from urllib.parse import urljoin, urlsplit, urlunsplit

import requests
import xarray as xr

from cubedynamics.data.certification import blocked_live_certification, write_live_certification
from cubedynamics.data.lifecycle import CertificationOutcome, CertificationRecord, LiveHealth
from cubedynamics.data.schema import normalize_xarray_schema

ROOT = Path(__file__).resolve().parents[1]
REVISION = "temperature.daymet@2026-08-26.1"  # Existing, unpromoted candidate.
ENDPOINT = (
    "https://opendap.earthdata.nasa.gov/collections/C2532426483-ORNL_CLOUD/"
    "granules/Daymet_Daily_V4R1.daymet_v4_daily_na_{variable}_{year}.nc.dap.nc4"
)
MAX_BYTES = 1024 * 1024
MAX_CELLS = 100
GUIDANCE = "https://forum.earthdata.nasa.gov/viewtopic.php?t=7585"


def build_request(*, variable="tmin", year=2024, time_index=0,
                  y_indices=(5000, 5002), x_indices=(4000, 4002)):
    """Inclusive, unit-stride indices only; reject large/invalid requests locally.

    Domain bounds cannot be asserted until the provider grid has been read.
    This function validates syntax and size, not geographic coverage.
    """
    if variable not in {"tmin", "tmax"}:
        raise ValueError("This experiment accepts only tmin or tmax.")
    if len(y_indices) != 2 or len(x_indices) != 2:
        raise ValueError("Index windows require inclusive (start, end) pairs.")
    indices = (year, time_index, *y_indices, *x_indices)
    if any(type(value) is not int for value in indices):
        raise ValueError("Year and indices must be integers.")
    if not 1980 <= year <= 2100 or not 0 <= time_index < 365:
        raise ValueError("Invalid year or daily index for this experiment.")
    if any(start < 0 or end < start for start, end in (y_indices, x_indices)):
        raise ValueError("Indices must be nonnegative and increasing.")
    shape = (1, y_indices[1] - y_indices[0] + 1, x_indices[1] - x_indices[0] + 1)
    if math.prod(shape) > MAX_CELLS:
        raise ValueError("Refusing more than 100 requested data cells.")
    yrange = f"[{y_indices[0]}:1:{y_indices[1]}]"
    xrange = f"[{x_indices[0]}:1:{x_indices[1]}]"
    # Follow the provider example exactly, narrowed to nine data values.
    ce = f"/y{yrange};/x{xrange};/{variable}[{time_index}:1:{time_index}]{yrange}{xrange}"
    return ENDPOINT.format(variable=variable, year=year), {"dap4.ce": ce}, shape


def safe_endpoint(url):
    """Never persist OAuth query/state or any userinfo in evidence."""
    parts = urlsplit(url)
    return urlunsplit((parts.scheme, parts.hostname or "", parts.path, "", ""))


def probe():
    endpoint, params, shape = build_request()
    result = {
        "source_flavor": "daymet", "access_strategy": "opendap",
        "backend": "Earthdata OPeNDAP", "subset_mode": "projected-grid index ranges",
        "provider_access_guidance": GUIDANCE,
        "requested_identity": {"product": "Daymet Daily V4R1", "provider": "NASA ORNL DAAC",
                               "collection": "C2532426483-ORNL_CLOUD"},
        "request": {"endpoint": endpoint, "params": params, "variable": "tmin", "year": 2024,
                    "time_index": 0, "y_indices_inclusive": [5000, 5002],
                    "x_indices_inclusive": [4000, 4002], "expected_shape": list(shape)},
        "anonymous": True, "redirects_followed": False, "maximum_response_bytes": MAX_BYTES,
        "response_body_bytes_read": 0, "http_status": None,
        "scientific_sample_retrieved": False, "returned_dimensions": None,
        "coordinates": None, "observed_upstream_identity": None,
        "grid_translation_status": "NOT_TESTED",
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "historical_ncss": {"status": "BLOCKED", "retested": False,
                            "evidence": "artifacts/source_qa/daymet/access_probe.json"},
    }
    payload = None
    reason = ""
    failure = ""
    with requests.Session() as session:
        session.trust_env = False  # Disables implicit .netrc authentication too.
        try:
            with session.get(endpoint, params=params, stream=True, allow_redirects=False,
                             timeout=(10, 30), headers={"User-Agent": "cubedynamics-daymet-opendap-probe/1",
                                                       "Accept-Encoding": "identity"}) as response:
                result.update(http_status=response.status_code,
                              content_type=response.headers.get("Content-Type"),
                              content_length_header=response.headers.get("Content-Length"))
                if response.status_code in {401, 403}:
                    failure, reason = "authentication", f"Anonymous request returned HTTP {response.status_code}."
                elif 300 <= response.status_code < 400:
                    location = safe_endpoint(urljoin(endpoint, response.headers.get("Location", "")))
                    result["redirect_endpoint"] = location
                    failure = "authentication" if "login" in location or "urs.earthdata.nasa.gov" in location else "redirect"
                    reason = f"HTTP {response.status_code} redirect to {location}; not followed."
                elif response.status_code != 200:
                    failure, reason = "http_error", f"Endpoint returned HTTP {response.status_code}."
                elif int(response.headers.get("Content-Length", "0")) > MAX_BYTES:
                    failure, reason = "size_limit", "Response exceeds 1 MiB; body not downloaded."
                else:
                    chunks = []
                    for chunk in response.iter_content(chunk_size=8192):
                        result["response_body_bytes_read"] += len(chunk)
                        if result["response_body_bytes_read"] > MAX_BYTES:
                            failure, reason = "size_limit", "Response exceeded 1 MiB; stream closed immediately."
                            break
                        chunks.append(chunk)
                    if not failure:
                        payload = b"".join(chunks)
        except requests.RequestException as exc:
            # Exception messages can contain URLs/headers; retain only the type.
            failure, reason = "network", f"Transport failed: {type(exc).__name__}."
        except ValueError:
            failure, reason = "http_metadata", "Invalid HTTP Content-Length header."

    if payload is not None:
        try:
            engine = "h5netcdf" if payload.startswith(b"\x89HDF\r\n\x1a\n") else "scipy"
            with xr.open_dataset(BytesIO(payload), engine=engine, decode_cf=False) as raw:
                if tuple(raw["tmin"].dims) != ("time", "y", "x") or tuple(raw["tmin"].shape) != shape:
                    raise ValueError("Unexpected shape: provider may not have applied the constraint.")
                if any(v.size > MAX_CELLS for v in raw.variables.values()):
                    raise ValueError("Response contains an unexpected large coordinate or variable.")
                result["returned_dimensions"] = dict(raw.sizes)
                result["coordinates"] = {name: raw[name].values.tolist() for name in ("x", "y", "time") if name in raw}
                result["raw_schema"] = normalize_xarray_schema(raw)
                result["variable_metadata"] = {key: str(value) for key, value in raw.tmin.attrs.items()}
                result["provider_global_metadata"] = {key: str(value) for key, value in raw.attrs.items()}
                result["scientific_sample_retrieved"] = True
        except (ValueError, KeyError, OSError) as exc:
            failure, reason = "payload_validation", f"Invalid subset payload ({type(exc).__name__})."
            payload = None

    if failure:
        result.update(blocked_live_certification(serving_revision=REVISION, reason=reason))
        if failure in {"size_limit", "payload_validation"}:
            result["certification"]["outcome"] = "FAIL"
            result["certification"]["gates"]["bounded_access_verified"] = "FAIL"
            result["live_health"] = LiveHealth.DEGRADED.value
        result["failure_category"] = failure
        payload = None
    else:
        # A readable, bounded response is not a scientific certification.
        gates = {name: CertificationOutcome.NOT_TESTED for name in (
            "upstream_identity_verified", "schema_validated", "numerical_qa", "visual_qa", "grid_translation")}
        gates.update({name: CertificationOutcome.PASS for name in (
            "endpoint_verified", "sample_retrieved", "bounded_access_verified")})
        record = CertificationRecord(mode="live_source", outcome=CertificationOutcome.PASS_WITH_CAVEATS,
            gates=gates, serving_revision=REVISION, last_validated=result["checked_at"],
            caveats=("Transport proof only; identity, scientific QA and projection/index translation require review.",))
        result.update(live_health=LiveHealth.DEGRADED.value, certification=record.as_dict())
    result["access_strategy_status"] = result["certification"]["outcome"]
    return result, payload


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "artifacts/source_qa/daymet/opendap_probe.json")
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Refusing to overwrite evidence; choose a new --output path.")
    result, payload = probe()
    if payload is not None:
        sample = args.output.with_suffix(".nc")
        if sample.exists():
            parser.error("Refusing to overwrite an existing sample.")
        sample.parent.mkdir(parents=True, exist_ok=True)
        sample.write_bytes(payload)
        result["sample_path"] = str(sample)
    write_live_certification(result, args.output)
    print(f"OPeNDAP: {result['access_strategy_status']}; HTTP {result['http_status']}; "
          f"body bytes read: {result['response_body_bytes_read']}; evidence: {args.output}")
    return 0 if result["access_strategy_status"] in {"PASS", "PASS_WITH_CAVEATS"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
