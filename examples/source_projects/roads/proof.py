"""Independent Overture snapshot and OSM rolling-source proofs for one AOI.

Contract: mapped road-like linear corridors, not routing topology or complete
road inventories. Native segmentation, classes, names and attributes survive.
Only major/local motor-road classes below are included. Service/living streets
are explicit inclusions; paths/tracks/trails/rail/ferries/construction are not.
No assertion that identically spelled source classes are scientifically equal.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import io
import json
from pathlib import Path
import re

import geopandas as gpd
import numpy as np
from shapely.geometry import LineString, box
from shapely import from_wkb

from cubedynamics import pipe
from cubedynamics.data.qa import evaluate_qa_profile
from cubedynamics.data.lifecycle import UpstreamIdentity
from cubedynamics.data.schema import normalize_vector_schema, fingerprint_normalized_schema
from examples.source_projects._evidence import AccessBlocked, fetch, json_get, save_report

BBOX = (-105.285, 40.008, -105.270, 40.020)
CLASSES = ("motorway", "trunk", "primary", "secondary", "tertiary", "residential",
           "unclassified", "service", "living_street")
# OSM link categories have explicit native names; not renamed to Overture classes.
OSM_CLASSES = CLASSES + ("motorway_link", "trunk_link", "primary_link", "secondary_link", "tertiary_link")
OVERPASS = "https://overpass-api.de/api/interpreter"
STAC = "https://stac.overturemaps.org/catalog.json"
MAX_FEATURES = 5000
MAX_TRANSFER = 32_000_000


def validate_bbox(bbox):
    w, s, e, n = bbox
    if not (-180 <= w < e <= 180 and -90 <= s < n <= 90 and e-w <= .02 and n-s <= .02):
        raise ValueError("Proof requires a geographic bbox no larger than .02° per side")
    return tuple(float(x) for x in bbox)


def intersects(a, b):
    return a[0] <= b[2] and a[2] >= b[0] and a[1] <= b[3] and a[3] >= b[1]


def osm_query(bbox):
    w, s, e, n = validate_bbox(bbox)
    # Full geometry retains way segmentation; cap+1 detects truncation.
    return (f'[out:json][timeout:25][maxsize:33554432];'
            f'way["highway"~"^({"|".join(OSM_CLASSES)})$"]["area"!="yes"]({s},{w},{n},{e});'
            f'out body geom {MAX_FEATURES + 1};')


def normalize(records, source, bbox, provenance):
    validate_bbox(bbox)
    if source not in ("osm", "overture"):
        raise ValueError("Unknown roads source")
    if len(records) > MAX_FEATURES:
        raise ValueError("Feature cap exceeded; no partial success")
    rows = []
    for record in records:
        if source == "osm":
            native = record.get("tags", {})
            if record.get("type") != "way" or native.get("highway") not in OSM_CLASSES or native.get("area") == "yes":
                continue
            geometry = LineString([(p["lon"], p["lat"]) for p in record["geometry"]])
            ident, classification, name = f'way/{record["id"]}', native["highway"], native.get("name")
            native = {**record, "geometry": "retained in geometry column"}
        else:
            if record.get("subtype") != "road" or record.get("class") not in CLASSES:
                continue
            geometry = from_wkb(record["geometry"])
            ident, classification = record["id"], record["class"]
            name = (record.get("names") or {}).get("primary")
            native = {k: v for k, v in record.items() if k != "geometry"}
        if geometry.geom_type not in ("LineString", "MultiLineString") or not geometry.is_valid or geometry.is_empty:
            raise ValueError("Invalid/nonlinear/empty road geometry")
        if geometry.intersects(box(*bbox)):
            rows.append({"geometry": geometry, "source": source, "source_feature_id": ident,
                         "source_classification": classification, "name": name,
                         "native": json.dumps(native, sort_keys=True, default=str)})
    if not rows:
        raise ValueError("No qualifying roads in AOI")
    result = gpd.GeoDataFrame(rows, geometry="geometry", crs="EPSG:4326")
    if result.source_feature_id.duplicated().any():
        raise ValueError("Duplicate source feature IDs; no silent deduplication")
    result.attrs.update(scientific_noun="roads", source=source, requested_bbox=list(bbox),
                        source_mode="snapshot" if source == "overture" else "rolling",
                        provenance=provenance, inclusion=list(CLASSES if source == "overture" else OSM_CLASSES))
    return result


class ParquetRanges(io.RawIOBase):
    """Private Overture reader: audited, hard-capped HTTP ranges for PyArrow.

    It cannot download an entire object as a convenience fallback. No general
    filesystem API or global cloud credentials are introduced.
    """
    def __init__(self, url, trace, budget):
        self.url, self.trace, self.budget, self.position = url, trace, budget, 0
        data = fetch(url, headers={"Range": "bytes=0-0"}, max_bytes=1, evidence=trace)
        header = trace[-1]["headers"]["Content-Range"] or ""
        match = re.fullmatch(r"bytes 0-0/(\d+)", header)
        if trace[-1]["status"] != 206 or len(data) != 1 or not match:
            raise ValueError("Parquet server did not honor HTTP Range")
        self.size = int(match[1])
        budget[0] -= 1

    def readable(self): return True
    def seekable(self): return True
    def tell(self): return self.position
    def seek(self, offset, whence=0):
        position = offset if whence == 0 else self.position + offset if whence == 1 else self.size + offset
        if not 0 <= position <= self.size:
            raise ValueError("Invalid seek")
        self.position = position
        return position

    def read(self, size=-1):
        if size < 0:
            raise ValueError("Unbounded Parquet read refused")
        size = min(size, self.size-self.position)
        if not size: return b""
        if size > self.budget[0] or size >= self.size:
            raise ValueError("Parquet transfer budget exceeded before request")
        start, end = self.position, self.position + size - 1
        data = fetch(self.url, headers={"Range": f"bytes={start}-{end}"}, max_bytes=size, evidence=self.trace)
        if self.trace[-1]["status"] != 206 or self.trace[-1]["headers"]["Content-Range"] != f"bytes {start}-{end}/{self.size}" or len(data) != size:
            raise ValueError("Incorrect/short range response")
        self.budget[0] -= len(data)
        self.position += len(data)
        return data


def row_group_intersects(group, bbox):
    bounds = {}
    for i in range(group.num_columns):
        col = group.column(i)
        if col.path_in_schema in ("bbox.xmin", "bbox.ymin", "bbox.xmax", "bbox.ymax"):
            if not col.statistics or not col.statistics.has_min_max:
                raise ValueError("No bbox statistics; refusing unpruned scan")
            bounds[col.path_in_schema] = col.statistics
    if len(bounds) != 4:
        raise ValueError("Missing row-group bbox columns")
    return intersects((bounds["bbox.xmin"].min, bounds["bbox.ymin"].min,
                       bounds["bbox.xmax"].max, bounds["bbox.ymax"].max), bbox)


def overture_records(bbox, evidence):
    import pyarrow.parquet as pq  # Optional, project-local requirements.txt.
    trace = evidence.setdefault("http", [])
    catalog = json_get(STAC, evidence=trace)
    current = next(x["href"] for x in catalog["links"] if x.get("latest") and x["rel"] == "child")
    release = json_get(current, evidence=trace)
    theme = json_get(next(x["href"] for x in release["links"] if x.get("title") == "transportation"), evidence=trace)
    collection = json_get(next(x["href"] for x in theme["links"] if x.get("title") == "segment"), evidence=trace)
    links = [x["href"] for x in collection["links"] if x["rel"] == "item"]
    if len(links) > 256:
        raise ValueError("Catalog exceeds this proof's metadata-request budget")
    with ThreadPoolExecutor(max_workers=4) as pool:
        items = list(pool.map(lambda url: json_get(url, evidence=trace, max_bytes=100_000), links))
    selected = [item for item in items if intersects(item["bbox"], bbox)]
    if not 0 < len(selected) <= 3:
        raise ValueError("Refusing more than three candidate partitions")
    evidence.update(release=release, collection={k:v for k,v in collection.items() if k != "links"},
                    selected_items=selected, partitions_total=len(items), partitions_opened=len(selected))
    rows, scans, budget = [], [], [MAX_TRANSFER]
    for item in selected:
        url = item["assets"]["aws"]["href"]
        if not url.startswith("https://overturemaps-us-west-2.s3.us-west-2.amazonaws.com/release/"):
            raise ValueError("Unexpected asset origin")
        with ParquetRanges(url, trace, budget) as remote:
            parquet = pq.ParquetFile(remote, pre_buffer=False)
            groups = [i for i in range(parquet.num_row_groups) if row_group_intersects(parquet.metadata.row_group(i), bbox)]
            if len(groups) > 4:
                raise ValueError("Refusing more than four row groups per partition")
            evidence["native_arrow_schema"] = str(parquet.schema_arrow)
            scans.append({"asset":url, "file_bytes":remote.size, "row_groups_total":parquet.num_row_groups,
                          "row_groups_read":groups, "file_rows":parquet.metadata.num_rows})
            for group in groups:
                if parquet.metadata.row_group(group).total_byte_size > 32_000_000:
                    raise ValueError("Decoded row group exceeds memory budget")
                table = parquet.read_row_group(group, use_threads=False)
                # Row-group pruning is coarse. Apply exact bbox and native
                # class filters before Python materialization of selected rows.
                import pyarrow.compute as pc
                bounds = table["bbox"]
                mask = (pc.greater_equal(pc.struct_field(bounds,"xmax"),bbox[0]))
                for part in (pc.less_equal(pc.struct_field(bounds,"xmin"),bbox[2]),
                             pc.greater_equal(pc.struct_field(bounds,"ymax"),bbox[1]),
                             pc.less_equal(pc.struct_field(bounds,"ymin"),bbox[3])):
                    mask = pc.and_(mask, part)
                local = table.filter(mask)
                if len(local)+len(rows) > MAX_FEATURES:
                    raise ValueError("Feature cap exceeded")
                rows.extend(local.to_pylist())
    evidence.update(scans=scans, parquet_bytes=MAX_TRANSFER-budget[0])
    return rows


def roads(*, source, bbox=BBOX, evidence=None):
    """Project noun returning a GeoDataFrame; network IO occurs explicitly here."""
    bbox = validate_bbox(bbox)
    evidence = evidence if evidence is not None else {}
    if source == "osm":
        query = osm_query(bbox)
        body = json_get(OVERPASS, params={"data":query}, max_bytes=4_000_000,
                        evidence=evidence.setdefault("http", []))
        if body.get("remark"):
            raise AccessBlocked(f'Overpass returned a partial/error response: {body["remark"]}')
        evidence.update(query=query, osm_timestamp=body.get("osm3s"), license="ODbL-1.0; © OpenStreetMap contributors")
        records = body["elements"]
    elif source == "overture":
        records = overture_records(bbox, evidence)
    else:
        raise ValueError("source must be overture or osm")
    evidence["upstream_identity"] = UpstreamIdentity(
        provider="Overture Maps" if source=="overture" else "OpenStreetMap contributors",
        product="transportation/segment" if source=="overture" else "OSM ways",
        endpoint=STAC if source=="overture" else OVERPASS,
        strategy={"kind":"release_partition" if source=="overture" else "rolling_query_timestamp"},
        observed={"release":evidence.get("release",{}).get("release:version"),
                  "assets":[s["asset"] for s in evidence.get("scans",[])],
                  "osm_timestamp":evidence.get("osm_timestamp"),"bbox":bbox,
                  "response_sha256":[h.get("sha256") for h in evidence["http"]]},
        retrieved_at=evidence["http"][0]["retrieved_at"]).as_dict()
    return normalize(records, source, bbox, evidence)


def within_aoi_length(bbox=BBOX):
    """Project verb: explicit clip for comparison, then metres in local UTM 13N.

    Input geometry and segmentation are not mutated. This proof deliberately
    restricts its projection to the Boulder test area.
    """
    validate_bbox(bbox)
    if not (-108 < bbox[0] < bbox[2] < -102 and 0 < bbox[1] < bbox[3] < 84):
        raise ValueError("Length verb is limited to UTM 13N")
    def stage(frame):
        clipped = frame.geometry.intersection(box(*bbox))
        return clipped.to_crs("EPSG:32613").length
    return stage


def run(output):
    import matplotlib.pyplot as plt
    output.mkdir(parents=True, exist_ok=True)
    frames, results = {}, {}
    for source in ("overture", "osm"):
        evidence = {"source":source, "bbox":BBOX, "source_mode":"snapshot" if source == "overture" else "rolling"}
        gates = {k:"NOT_TESTED" for k in ("retrieval", "bounded_access", "identity", "schema", "semantics", "numerical_qa", "visual_qa")}
        try:
            frame = roads(source=source, evidence=evidence)
            frames[source] = frame
            lengths = (pipe(frame) | within_aoi_length()).unwrap()
            profile = evaluate_qa_profile("feature_line", {"feature_count":len(frame),
                "geometry_types":frame.geom_type.unique().tolist(), "crs":str(frame.crs),
                "identifier_field":"source_feature_id", "valid_geometry_fraction":float(frame.is_valid.mean())})
            evidence.update(feature_count=len(frame), within_aoi_length_m=float(lengths.sum()),
                min_length_m=float(lengths.min()), max_length_m=float(lengths.max()),
                native_feature_length_m=float(frame.to_crs(32613).length.sum()),
                duplicate_ids=int(frame.source_feature_id.duplicated().sum()),
                naming_fraction=float(frame.name.notna().mean()),
                classifications=frame.source_classification.value_counts().to_dict(),
                memory_bytes=int(frame.memory_usage(deep=True).sum()), qa_profile=profile.as_dict())
            schema = normalize_vector_schema(fields={k:str(v) for k,v in frame.dtypes.items()},
                geometry_type="LineString", crs=str(frame.crs), layer_id=f"roads/{source}")
            evidence.update(schema=schema, schema_fingerprint=fingerprint_normalized_schema(schema))
            gates.update({k:"PASS" for k in ("retrieval", "bounded_access", "identity", "schema", "semantics")})
            gates["numerical_qa"] = "PASS" if profile.passed and np.isfinite(lengths).all() and (lengths > 0).all() else "FAIL"
            frame.to_file(output / f"{source}.geojson", driver="GeoJSON")
        except (AccessBlocked, ImportError) as exc:
            gates["retrieval"] = "BLOCKED"
            evidence["blocker"] = str(exc)
        except Exception as exc:
            # Record unexpected schema/decoder faults independently so a bad
            # Overture response cannot suppress the separate OSM evaluation.
            gates["retrieval"] = "FAIL"
            evidence["failure"] = f"{type(exc).__name__}: {exc}"
        results[source] = save_report(output/f"{source}-report.json", gates=gates, evidence=evidence,
            caveats=("One small AOI; no completeness/topology certification.",
                     "Overture incorporates OSM; these are not independent observations.",
                     "No automatic class harmonization; native features may extend outside bbox."))
        print(source, results[source]["certification"]["outcome"], flush=True)
    render_plots(frames, output)
    return results


def render_plots(frames, output):
    """Render acquired real features without additional provider requests."""
    import matplotlib.pyplot as plt
    from matplotlib.ticker import MaxNLocator
    for source, frame in frames.items():
        fig, ax = plt.subplots(figsize=(8,5), layout="constrained")
        frame.plot(ax=ax, column="source_classification", legend=True, linewidth=1.5,
                   legend_kwds={"loc":"upper left","bbox_to_anchor":(1.01,1),"fontsize":9})
        ax.set(xlim=(BBOX[0],BBOX[2]), ylim=(BBOX[1],BBOX[3]), title=f"Real {source} roads · native classes",
               xlabel="Longitude (WGS84)",ylabel="Latitude (WGS84)")
        ax.xaxis.set_major_locator(MaxNLocator(4))
        ax.ticklabel_format(useOffset=False, style="plain")
        fig.savefig(output / f"{source}.png", dpi=140)
        plt.close(fig)
    if len(frames) == 2:
        fig, axes = plt.subplots(1,2,figsize=(10,5),sharex=True,sharey=True,layout="constrained")
        for ax,(source,frame) in zip(axes,frames.items()):
            frame.plot(ax=ax, color="#236d81", linewidth=1.2)
            ax.set(title=f"{source}: {len(frame)} native features", xlim=(BBOX[0],BBOX[2]), ylim=(BBOX[1],BBOX[3]))
            ax.ticklabel_format(useOffset=False, style="plain")
            ax.xaxis.set_major_locator(MaxNLocator(4))
            ax.set(xlabel="Longitude (WGS84)",ylabel="Latitude (WGS84)")
        fig.suptitle("Same AOI, different native segmentation · © OSM contributors / Overture")
        fig.savefig(output/"comparison.png", dpi=150)
        plt.close(fig)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("artifacts/source_qa/roads"))
    args = parser.parse_args()
    results = run(args.output)
    raise SystemExit(0 if all(r["certification"]["outcome"].startswith("PASS") for r in results.values()) else 2)
