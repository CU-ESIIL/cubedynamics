#!/usr/bin/env python3
"""Independent bounded candidate checks; never certifies or promotes sources.

Acquisition is explicit. Existing snapshots are replayed with --offline, never
silently refreshed. --export-usgs-fixture deliberately installs the small real
USGS snapshots after successful raw-value/metadata and serialization checks.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import shutil
import time

import numpy as np
import xarray as xr

from cubedynamics import pipe, verbs as v
from cubedynamics.data import usgs, three_dep, roads
from cubedynamics.data._transport import SourceUnavailable, SourceAccessError
from cubedynamics.data._transport import SourceClient
from cubedynamics.data.lifecycle import CertificationRecord
from cubedynamics.data.qa import evaluate_qa_profile

ROOT = Path(__file__).resolve().parents[1]
START, END = "2026-08-26T00:00:00Z", "2026-08-26T23:59:59Z"
SITES = {"boulder": "USGS-06730200", "potomac": "USGS-01646500", "lees_ferry": "USGS-09380000"}
BBOX = (-105.285, 40.008, -105.270, 40.020)


def usgs_check(output, offline):
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    results = {}
    for name, site in SITES.items():
        cube = usgs.streamflow(site=site, start=START, end=END,
                               snapshot_dir=output/name, offline=offline)
        # Reconstruct a reference independently from retained provider JSON,
        # not a second call to the adapter normalization function.
        native = []
        for record_path in (output/name/"requests").glob("*.json"):
            record = json.loads(record_path.read_text())
            if "/continuous/items?" in record["request"]["url"]:
                raw = (output/name/"bodies"/f"{record['sha256']}.bin").read_bytes()
                assert hashlib.sha256(raw).hexdigest() == record["sha256"]
                native.extend(json.loads(raw)["features"])
        native.sort(key=lambda f: f["properties"]["time"])
        expected = [float(f["properties"]["value"]) if f["properties"]["value"] is not None else np.nan for f in native]
        np.testing.assert_allclose(cube.streamflow.values[:, 0], expected, rtol=0, atol=0, equal_nan=True)
        assert cube.approval_status.values.tolist() == [f["properties"].get("approval_status") or "" for f in native]
        assert cube.streamflow.attrs["units"] == native[0]["properties"]["unit_of_measure"]
        profile = evaluate_qa_profile("station_timeseries", cube)
        assert profile.passed, profile
        target = output/name/"roundtrip.nc"
        cube.to_netcdf(target, engine="h5netcdf")
        with xr.open_dataset(target, engine="h5netcdf") as restored:
            xr.testing.assert_equal(cube, restored.load())
        mean = (pipe(cube) | v.mean(dim="time")).unwrap().streamflow.item()
        fig, ax = plt.subplots(figsize=(8, 3.5), layout="constrained")
        cube.streamflow.isel(station=0).plot(ax=ax)
        ax.axhline(mean, ls=":", color="#555", label="Window mean")
        ax.set(title=f"Real USGS discharge · {site}", xlabel="2026-08-26 · UTC",
               ylabel=f"Discharge ({cube.streamflow.attrs['units']})")
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
        ax.legend()
        fig.savefig(output/f"{name}.png", dpi=140)
        plt.close(fig)
        results[name] = {"site": site, "rows": cube.sizes["time"], "units": cube.streamflow.attrs["units"],
                         "min": float(cube.streamflow.min()), "max": float(cube.streamflow.max()),
                         "raw_value_equality": True, "netcdf_roundtrip": True, "pipe_mean": mean,
                         "statuses": sorted(set(cube.approval_status.values.tolist()))}
    # Exercise provider pagination with a deliberately small page size, then
    # real multi-batch loading. Both retain their own raw snapshots.
    with SourceClient(origins={"https://api.waterdata.usgs.gov"},
                      snapshot_dir=output/"pagination",offline=offline) as client:
        params={"f":"json","monitoring_location_id":SITES["boulder"],"parameter_code":"00060",
                "time":f"{START}/{END}","limit":50}
        rows=usgs._pages(client,params)
        assert len(rows)==results["boulder"]["rows"]
        assert len(client.trace)>=2
        results["pagination"]={"rows":len(rows),"pages":len(client.trace),"page_size":50}
    batched=usgs.streamflow(site=SITES["boulder"],start="2026-08-19T00:00:00Z",end=END,
                           snapshot_dir=output/"eight_days",offline=offline)
    assert batched.sizes["time"]>96
    results["batching"]={"rows":batched.sizes["time"],"start":batched.attrs["requested_start"],
                         "end":batched.attrs["requested_end"]}
    return results


def terrain_check(output, offline):
    import matplotlib.pyplot as plt
    results = {}
    # Same tile and an independent region; no automatic mosaic/reprojection.
    for name, bbox, tile_id in (("boulder", (-105.300,39.985,-105.291,39.994), None),
                               ("asheville", (-82.56,35.58,-82.555,35.585), "627f3798d34e3bef0c9a3198")):
        cube = three_dep.elevation(bbox=bbox, tile_id=tile_id, snapshot_dir=output/name, offline=offline)
        assert evaluate_qa_profile("continuous_raster_static", cube).passed
        assert np.isfinite(cube.values).any() and (np.diff(cube.y.values) < 0).all()
        fig, ax = plt.subplots(figsize=(6,4), layout="constrained")
        cube.plot(ax=ax, cmap="terrain", cbar_kwargs={"label":"Elevation (m; native vertical reference)"})
        ax.set(title=f"Real 3DEP · {name}", xlabel="Native x", ylabel="Native y")
        ax.ticklabel_format(useOffset=False, style="plain")
        fig.savefig(output/f"{name}.png", dpi=140)
        plt.close(fig)
        results[name] = {"shape":list(cube.shape), "body_bytes":cube.attrs["body_bytes"],
                         "min":float(cube.min()), "max":float(cube.max()), "crs":cube.attrs["crs"],
                         "selection":cube.attrs["catalog_selection"]}
    return results


def roads_check(output, offline, source):
    import matplotlib.pyplot as plt
    from matplotlib.ticker import MaxNLocator
    frame = roads.roads(source=source, bbox=BBOX, release="2026-08-19.0" if source=="overture" else None,
                        snapshot_dir=output/"boulder", offline=offline)
    assert frame.is_valid.all() and not frame.source_feature_id.duplicated().any()
    fig, ax = plt.subplots(figsize=(7,4), layout="constrained")
    frame.plot(ax=ax, color="#236d81", linewidth=1)
    ax.set(xlim=(BBOX[0],BBOX[2]), ylim=(BBOX[1],BBOX[3]),
           title=f"Real {source} roads · native segments", xlabel="Longitude", ylabel="Latitude")
    ax.ticklabel_format(useOffset=False, style="plain")
    ax.xaxis.set_major_locator(MaxNLocator(4))
    fig.savefig(output/"boulder.png",dpi=140)
    plt.close(fig)
    return {"rows":len(frame), "body_bytes":frame.attrs["provenance"]["body_bytes"],
            "native_class_counts":frame.source_classification.value_counts().to_dict()}


def export_fixture(output):
    target = ROOT/"tests/fixtures/real_data/usgs_streamflow"
    if target.exists():
        raise ValueError("Fixture already exists: review/update it deliberately, never overwrite")
    files = {}
    for name in SITES:
        for folder in ("requests", "bodies"):
            for path in sorted((output/name/folder).iterdir()):
                relative = path.relative_to(output)
                destination = target/relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(path, destination)
                files[str(relative)] = hashlib.sha256(path.read_bytes()).hexdigest()
    (target/"provenance.json").write_text(json.dumps({"source":"USGS modern OGC continuous",
        "source_url":usgs.BASE, "start":START, "end":END, "sites":SITES, "files":files,
        "acquired_by":"scripts/check_source_candidates.py", "contract":usgs.CONTRACT,
        "scope":"Three stations, one day; exact raw-value and metadata checks, not hydrologic suitability",
        "limitations":"Provisional observations may change; original raw snapshots retained."},indent=2)+"\n")


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project",required=True,choices=("usgs","three_dep","overture","osm"))
    parser.add_argument("--output",type=Path,required=True,help="New acquisition root, or an existing root with --offline")
    parser.add_argument("--offline",action="store_true")
    parser.add_argument("--export-usgs-fixture",action="store_true")
    args=parser.parse_args()
    args.output.mkdir(parents=True,exist_ok=True)
    started=time.monotonic()
    report={"project":args.project,"mode":"offline_replay" if args.offline else "live",
            "started_at":datetime.now(timezone.utc).isoformat(),"python":platform.python_version(),
            "promoted":False,"scientific_review":"NOT_TESTED","visual_review":"NOT_TESTED"}
    try:
        if args.project=="usgs": report["checks"]=usgs_check(args.output,args.offline)
        elif args.project=="three_dep": report["checks"]=terrain_check(args.output,args.offline)
        else: report["checks"]=roads_check(args.output,args.offline,args.project)
        report["outcome"]="PASS_WITH_CAVEATS"
        if args.export_usgs_fixture:
            if args.project!="usgs": raise ValueError("Only USGS has an approved small fixture export format")
            export_fixture(args.output)
    except Exception as exc:
        report["outcome"]="BLOCKED" if isinstance(exc,(SourceUnavailable,SourceAccessError,ImportError)) else "FAIL"
        report["error"]=f"{type(exc).__name__}: {exc}"
    report["elapsed_seconds"]=round(time.monotonic()-started,3)
    success=report["outcome"]=="PASS_WITH_CAVEATS"
    gates={"retrieval":"PASS" if success else report["outcome"],
           "bounded_access":"PASS" if success else "NOT_TESTED",
           "scientific_review":"NOT_TESTED","visual_review":"NOT_TESTED"}
    report["certification"]=CertificationRecord(mode="offline_baseline" if args.offline else "live_source",
        outcome=report["outcome"],gates=gates,serving_revision=None,last_validated=datetime.now(timezone.utc).isoformat(),
        evidence={"checks":report.get("checks",{}),"error":report.get("error")},
        caveats=("Bounded adapter check, not scientific suitability or production promotion.",)).as_dict()
    filename="replay-report.json" if args.offline else "candidate-report.json"
    (args.output/filename).write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report,indent=2))
    return 0 if report["outcome"]=="PASS_WITH_CAVEATS" else 1


if __name__=="__main__":
    raise SystemExit(main())
