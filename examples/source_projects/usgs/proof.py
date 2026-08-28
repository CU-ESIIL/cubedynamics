"""One-site streamflow noun for the modern USGS OGC API, not WaterServices.

Schema: /collections/continuous/queryables (verified 2026-08-27).
approval_status is Approved or Provisional; qualifiers remain provider-native.
Record id and last_modified can change during routine database refreshes.
Stable observation identity is (time_series_id, time), NOT the row UUID.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import warnings

import numpy as np
import pandas as pd
import xarray as xr

from cubedynamics import pipe, verbs as v
from cubedynamics.data.lifecycle import UpstreamIdentity
from cubedynamics.data.qa import evaluate_qa_profile
from cubedynamics.data.schema import normalize_xarray_schema, schema_fingerprint
from examples.source_projects._evidence import AccessBlocked, json_get, save_report
from .probe import BASE, SITE, START, END

MAX_ROWS = 2000


def query(site, start, end):
    if not isinstance(site,str) or not re.fullmatch(r"USGS-\d{8,15}",site):
        raise ValueError("Exactly one agency-prefixed USGS site is required")
    first,last=pd.Timestamp(start),pd.Timestamp(end)
    if pd.isna(first) or pd.isna(last) or first.tzinfo is None or last.tzinfo is None:
        raise ValueError("Explicit timezone-aware start/end required")
    if not pd.Timedelta(0)<last-first<=pd.Timedelta(days=3):
        raise ValueError("Proof requires a positive interval no longer than three days")
    return {"f":"json","monitoring_location_id":site,"parameter_code":"00060",
            "time":f"{first.tz_convert('UTC').isoformat()}/{last.tz_convert('UTC').isoformat()}","limit":MAX_ROWS}


def complete_features(body):
    """Explicit bounded pagination policy: fail closed, never return a partial series."""
    features=body.get("features")
    if not isinstance(features,list) or not 0<len(features)<=MAX_ROWS:
        raise ValueError("No discharge observations or response exceeds 2000 rows")
    if any(x.get("rel")=="next" for x in body.get("links",[])):
        raise ValueError("Paginated response exceeds this single-page proof; shorten interval")
    matched=body.get("numberMatched")
    if isinstance(matched,int) and matched>len(features):
        raise ValueError("Response is incomplete; refusing partial series")
    return features


def normalize(body, location, metadata, *, site, start, end, provenance):
    params=query(site,start,end)
    features=complete_features(body)
    rows=[f["properties"] for f in features]
    series={row["time_series_id"] for row in rows}
    if len(series)!=1:
        raise ValueError("Multiple time series: select explicitly, do not silently merge")
    series_id=next(iter(series))
    meta=metadata["properties"]
    if location["id"]!=site or metadata["id"]!=series_id or meta["monitoring_location_id"]!=site or meta["parameter_code"]!="00060":
        raise ValueError("Site/series metadata identity mismatch")
    if any(row["monitoring_location_id"]!=site or row["parameter_code"]!="00060" for row in rows):
        raise ValueError("Observation site or parameter differs from requested scope")
    units={row.get("unit_of_measure") for row in rows}
    if units!={meta.get("unit_of_measure")} or not meta.get("unit_of_measure"):
        raise ValueError("Missing or inconsistent units")
    if {row.get("statistic_id") for row in rows}!={meta.get("statistic_id")}:
        raise ValueError("Mixed observation statistic context")
    if any(pd.Timestamp(row["time"]).tzinfo is None for row in rows):
        raise ValueError("Provider time must include a timezone; no silent UTC assumption")
    times=pd.to_datetime([row["time"] for row in rows],utc=True,errors="raise")
    if times.isna().any() or times.duplicated().any() or (times<pd.Timestamp(start)).any() or (times>pd.Timestamp(end)).any():
        raise ValueError("Missing/duplicate/out-of-window observation time")
    order=np.argsort(times.asi8)
    # Only explicit missing values become NaN. Text such as 'Ice' is not
    # quietly interpreted as numeric discharge or discarded.
    values=np.asarray([float(row["value"]) if row.get("value") is not None else np.nan for row in rows])
    if np.isinf(values).any():
        raise ValueError("Infinite discharge value")
    if location["geometry"]["type"]!="Point":
        raise ValueError("Monitoring location must have point geometry")
    lon,lat=location["geometry"]["coordinates"][:2]
    if not (-180<=lon<=180 and -90<=lat<=90):
        raise ValueError("Invalid monitoring location coordinates")
    def native_field(key):
        # JSON distinguishes missing/null/empty strings and preserves unusual
        # future lists or qualifier codes without inventing a crosswalk.
        # Object dtype avoids fingerprint drift merely because status/qualifier
        # strings grow or shorten as this rolling source receives updates.
        return np.asarray([json.dumps(row.get(key),sort_keys=True) for row in rows],dtype=object)[order]
    cube=xr.Dataset({"streamflow":(("time","station"),values[order,None],
                                  {"units":meta["unit_of_measure"],"long_name":"Discharge","parameter_code":"00060"})},
        coords={"time":times[order].tz_localize(None).to_numpy(), "station":[site],
                "longitude":("station",[lon]),"latitude":("station",[lat]),
                "time_series_id":("station",[series_id]),
                "record_id":("time",np.asarray([str(f["id"]) for f in features],dtype=object)[order]),
                "approval_status":("time",native_field("approval_status")),
                "qualifier":("time",native_field("qualifier")),
                "last_modified":("time",native_field("last_modified"))},
        attrs={"source":"USGS","scientific_noun":"streamflow","source_flavor":"usgs",
               "source_mode":"rolling","crs":"EPSG:4326","is_synthetic":False,
               "requested_start":start,"requested_end":end,"time_zone":"UTC",
               "source_url":BASE+"/continuous/items","query":json.dumps(params,sort_keys=True),
               "site_metadata":json.dumps(location,sort_keys=True),"series_metadata":json.dumps(metadata,sort_keys=True),
               "provenance":json.dumps(provenance,sort_keys=True),
               "stable_observation_key":"time_series_id + time",
               "interpretation_contract":"project-usgs-streamflow-v1; no serving revision assigned",
               "reproducibility":"Rolling content may be revised; preserve raw response and checksum."})
    cube.coords["time"].attrs["timezone"]="UTC"
    for key in ("approval_status","qualifier","last_modified"):
        cube.coords[key].attrs["encoding"]="JSON of provider-native value; null means unavailable"
    if any(row.get("approval_status")=="Provisional" for row in rows):
        warnings.warn("USGS provisional discharge retained; values are subject to revision.",UserWarning,stacklevel=2)
    return cube


def streamflow(*, source="usgs", site=SITE, start, end, evidence=None):
    """Project-owned noun: one short, eager station time series, native units/status.

    Calls only modern OGC endpoints, anonymously. No automatic pagination,
    credentials, legacy fallback, filtering of provisional data or unit conversion.
    """
    if source!="usgs": raise ValueError("This proof supports source='usgs' only")
    params=query(site,start,end)
    evidence=evidence if evidence is not None else {}
    trace=evidence.setdefault("http",[])
    body=json_get(BASE+"/continuous/items",params=params,evidence=trace)
    rows=complete_features(body)
    series={row["properties"]["time_series_id"] for row in rows}
    if len(series)!=1: raise ValueError("Expected exactly one time series")
    series_id=next(iter(series))
    if not re.fullmatch(r"[a-fA-F0-9-]{32,36}",series_id):
        raise ValueError("Invalid time-series ID")
    location=json_get(BASE+f"/monitoring-locations/items/{site}",params={"f":"json"},evidence=trace)
    metadata=json_get(BASE+f"/time-series-metadata/items/{series_id}",params={"f":"json"},evidence=trace)
    evidence.update(observations=body,location=location,series=metadata)
    identity=UpstreamIdentity(provider="USGS",product="continuous discharge",endpoint=BASE+"/continuous/items",
        strategy={"kind":"rolling_site_parameter_series_query"},
        observed={"monitoring_location_id":site,"parameter_code":"00060","time_series_id":series_id,
                  "query":params,"response_sha256":trace[0]["sha256"]},retrieved_at=trace[0]["retrieved_at"])
    evidence["upstream_identity"]=identity.as_dict()
    return normalize(body,location,metadata,site=site,start=start,end=end,provenance=identity.as_dict())


def run(output, *, saved=False):
    output.mkdir(parents=True,exist_ok=True)
    evidence={"source_mode":"rolling","site":SITE,"start":START,"end":END}
    gates={k:"NOT_TESTED" for k in ("retrieval","bounded_access","identity","schema","semantics","numerical_qa","visual_qa","rolling_source")}
    try:
        if saved:
            acquisition=json.loads((output/"acquisition.json").read_text())
            evidence.update(acquisition)
            cube=normalize(json.loads((output/"observations.json").read_text()),json.loads((output/"site.json").read_text()),
                json.loads((output/"series.json").read_text()),site=SITE,start=START,end=END,provenance=acquisition)
        else:
            cube=streamflow(start=START,end=END,evidence=evidence)
            for key,name in (("observations","observations"),("location","site"),("series","series")):
                (output/f"{name}.json").write_text(json.dumps(evidence.pop(key),indent=2))
        profile=evaluate_qa_profile("station_timeseries",cube)
        values=cube.streamflow.values[:,0]
        delta=np.diff(cube.time.values).astype("timedelta64[s]").astype(float)
        statuses=Counter(cube.approval_status.values.tolist())
        qualifiers=Counter(cube.qualifier.values.tolist())
        gaps=float(delta.max()) if len(delta) else None
        metadata=json.loads(cube.attrs["series_metadata"])["properties"]
        threshold=pd.Timedelta(metadata["data_gap_interval"]).total_seconds() if metadata.get("data_gap_interval") else None
        evidence.update(qa_profile=profile.as_dict(),rows=len(values),units=cube.streamflow.attrs["units"],
            min=float(np.nanmin(values)),max=float(np.nanmax(values)),missing=int(np.isnan(values).sum()),
            finite_fraction=float(np.isfinite(values).mean()),negative_count=int((values<0).sum()),
            largest_gap_seconds=gaps,provider_gap_threshold_seconds=threshold,
            gaps_exceeding_provider_threshold=int((delta>threshold).sum()) if threshold else None,
            statuses=dict(statuses),qualifiers=dict(qualifiers),
            actual_start=str(cube.time.values[0]),actual_end=str(cube.time.values[-1]),
            provenance=dict(cube.attrs),schema=normalize_xarray_schema(cube),schema_fingerprint=schema_fingerprint(cube))
        gates.update({k:"PASS" for k in ("retrieval","bounded_access","identity","schema","semantics","rolling_source")})
        gates["numerical_qa"]="PASS" if profile.passed and np.isfinite(values).all() else "FAIL"
        import matplotlib.pyplot as plt
        import matplotlib.dates as mdates
        fig,ax=plt.subplots(figsize=(8,4),layout="constrained")
        ax.plot(cube.time,values,color="#336678",lw=1,label="Discharge")
        for status in statuses:
            keep=cube.approval_status.values==status
            ax.scatter(cube.time.values[keep],values[keep],s=9,label=json.loads(status) or "Status unavailable")
        mean=(pipe(cube[["streamflow"]]) | v.mean(dim="time")).unwrap().streamflow.item()
        ax.axhline(mean,ls=":",color="#555555",label="Window mean")
        ax.set(title="Real USGS discharge · Boulder Creek at N. 75th St.",xlabel="2026-08-26 · UTC",ylabel="Discharge (ft³/s)")
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
        ax.legend(fontsize=8)
        fig.savefig(output/"streamflow.png",dpi=150)
        plt.close(fig)
        evidence["figure"]="streamflow.png"
    except AccessBlocked as exc:
        gates["retrieval"]="BLOCKED"
        evidence["blocker"]=str(exc)
    except (ValueError,KeyError) as exc:
        gates["retrieval"]="FAIL"
        evidence["failure"]=str(exc)
    return save_report(output/"report.json",gates=gates,evidence=evidence,
        caveats=("One station/day; not hydrologic suitability or station-completeness certification.",
                 "Provisional data are retained; identical later queries need not be byte-identical.",
                 "No serving revision assigned: observation updates do not change the interpretation contract."))


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--output",type=Path,default=Path("artifacts/source_qa/usgs"))
    parser.add_argument("--saved",action="store_true",help="Evaluate already-acquired real responses without network")
    args=parser.parse_args()
    result=run(args.output,saved=args.saved)
    print(result["certification"]["outcome"])
    raise SystemExit(0 if result["certification"]["outcome"].startswith("PASS") else 2)
