"""Bounded road-source candidates: native Overture segments or OSM ways.

Not routing networks or certified complete inventories. Overture requires an
explicit release. OSM is a small interactive query route, not a production
application backend. Native segmentation, restrictions and classes survive.
"""
from __future__ import annotations

import json
import re
from urllib.parse import urljoin

import geopandas as gpd
from shapely.geometry import LineString, box
from shapely import from_wkb

from ._transport import SourceClient, ReadLimits, SourceSchemaError, SourceBudgetError, SourceUnavailable
from ._ranges import RangeFile

CLASSES = ("motorway", "trunk", "primary", "secondary", "tertiary", "residential",
           "unclassified", "service", "living_street")
OSM_CLASSES = CLASSES + ("motorway_link", "trunk_link", "primary_link", "secondary_link", "tertiary_link")
OVERPASS = "https://overpass-api.de/api/interpreter"
MAX_FEATURES = 5000
CONTRACT = "native-motor-road-features-v1"

def validate_bbox(bbox):
    w, s, e, n = bbox
    if not (-180 <= w < e <= 180 and -90 <= s < n <= 90 and e-w <= .02 and n-s <= .02):
        raise ValueError("Candidate requires a geographic bbox no larger than .02° per side")
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
        w, s, e, n = geometry.bounds
        if not (-180 <= w <= e <= 180 and -90 <= s <= n <= 90):
            raise ValueError("Road geometry outside WGS84 bounds")
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


def _child(document, title, base):
    links = [link["href"] for link in document.get("links", [])
             if link.get("rel") == "child" and link.get("title") == title]
    if len(links) != 1:
        raise SourceSchemaError(f"Expected exactly one {title} catalog child")
    return urljoin(base, links[0])


def _overture(client, bbox, release, evidence):
    try:
        import pyarrow.parquet as pq
        import pyarrow.compute as pc
        import pyarrow as pa
    except ImportError as exc:
        raise ImportError("Overture candidate requires pip install 'cubedynamics[roads]'") from exc
    url = f"https://stac.overturemaps.org/{release}/catalog.json"
    catalog = client.json(url)
    if catalog.get("release:version") != release:
        raise SourceSchemaError("Catalog release differs from requested snapshot")
    theme_url = _child(catalog, "transportation", url)
    theme = client.json(theme_url)
    collection_url = _child(theme, "segment", theme_url)
    collection = client.json(collection_url)
    links = [urljoin(collection_url, link["href"]) for link in collection.get("links", []) if link.get("rel") == "item"]
    if not links or len(links) > 256 or len(set(links)) != len(links):
        raise SourceBudgetError("Missing/duplicate or more than 256 partition metadata links")
    # Deliberately sequential: one query-wide budget, no unbounded parallelism.
    # Explicit snapshots replay catalog metadata without issuing requests.
    selected = []
    for link in links:
        item = client.json(link, max_bytes=100_000)
        if intersects(item["bbox"], bbox):
            selected.append(item)
    if not 0 < len(selected) <= 3:
        raise SourceBudgetError("Expected 1–3 candidate partitions")
    rows, scans, schemas = [], [], set()
    for item in selected:
        asset = item["assets"]["aws"]["href"]
        prefix = f"https://overturemaps-us-west-2.s3.us-west-2.amazonaws.com/release/{release}/theme=transportation/type=segment/"
        if not asset.startswith(prefix) or not asset.endswith(".parquet"):
            raise SourceSchemaError("Asset does not belong to requested release/theme/type")
        with RangeFile(asset, client) as remote:
            parquet = pq.ParquetFile(remote, pre_buffer=False)
            schemas.add(str(parquet.schema_arrow))
            if len(schemas) != 1:
                raise SourceSchemaError("Inconsistent schemas across selected partitions")
            groups = [i for i in range(parquet.num_row_groups)
                      if row_group_intersects(parquet.metadata.row_group(i), bbox)]
            if len(groups) > 4:
                raise SourceBudgetError("More than four intersecting row groups per partition")
            scans.append({"asset": asset, "etag": remote.etag, "file_bytes": remote.size,
                          "row_groups_read": groups, "row_groups_total": parquet.num_row_groups})
            for group in groups:
                metadata = parquet.metadata.row_group(group)
                if metadata.total_byte_size > 32_000_000:
                    raise SourceBudgetError("Row group exceeds 32 MB declared decoded size")
                # Coalesce the selected group's contiguous compressed column
                # chunks. Preserve all native fields without hundreds of tiny
                # HTTP requests. Validate offsets instead of scanning gaps.
                spans = []
                for i in range(metadata.num_columns):
                    column = metadata.column(i)
                    offsets = [n for n in (column.dictionary_page_offset, column.data_page_offset) if n is not None and n >= 0]
                    if not offsets or column.total_compressed_size <= 0:
                        raise SourceSchemaError("Missing Parquet column offsets/sizes")
                    start = min(offsets)
                    spans.append((start, start + column.total_compressed_size))
                begin, end = min(a for a,b in spans), max(b for a,b in spans)
                if end-begin > 32_000_000 or end > remote.size:
                    raise SourceBudgetError("Compressed row-group span exceeds bounds")
                remote.prefetch(begin, end-begin)
                table = parquet.read_row_group(group, use_threads=False)
                bounds = table["bbox"]
                mask = pc.greater_equal(pc.struct_field(bounds, "xmax"), bbox[0])
                for part in (pc.less_equal(pc.struct_field(bounds, "xmin"), bbox[2]),
                             pc.greater_equal(pc.struct_field(bounds, "ymax"), bbox[1]),
                             pc.less_equal(pc.struct_field(bounds, "ymin"), bbox[3]),
                             pc.equal(table["subtype"], "road"), pc.is_in(table["class"], value_set=pa.array(CLASSES))):
                    mask = pc.and_(mask, part)
                local = table.filter(mask)
                if len(rows) + len(local) > MAX_FEATURES:
                    raise SourceBudgetError("Feature count exceeds 5000; no partial result")
                rows.extend(local.to_pylist())
    evidence.update(release=release, native_arrow_schema=next(iter(schemas)), scans=scans,
                    partitions_total=len(links), partitions_opened=len(selected),
                    schema_version=catalog.get("schema:version"))
    return rows


def roads(*, source, bbox, release=None, snapshot_dir=None, offline=False):
    """Load <=5000 native road features within a <=0.02° WGS84 query bbox.

    Candidate API, not production catalog registration. Overture requires an
    explicit date-based ``release`` and the optional ``roads`` extra. OSM uses
    public Overpass only for small queries; way selection requires a node in
    the bbox, so a long crossing way may be absent. Neither flavor promises
    inventory completeness, shared class semantics or routing topology.

    Eager, anonymous, no fallback. Whole-feature geometry is retained. Overture
    has a 40 MB total body budget (including metadata), 400 request budget and
    300 s between-read deadline. OSM has a 4 MB body / 6 request / 90 s budget.
    Explicit raw snapshots support offline replay on the same decoder stack.
    """
    bbox = validate_bbox(bbox)
    if source not in ("osm", "overture"):
        raise ValueError("source must be overture or osm")
    if source == "overture" and (not isinstance(release, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}\.\d+", release)):
        raise ValueError("Overture requires an explicit release such as '2026-08-19.0'")
    if source == "osm" and release is not None:
        raise ValueError("OSM is rolling; release is not a supported historical selector")
    limits = ReadLimits(requests=400, bytes=40_000_000, seconds=300) if source == "overture" else ReadLimits(requests=6, bytes=4_000_000, seconds=90)
    origins = {"https://stac.overturemaps.org", "https://overturemaps-us-west-2.s3.us-west-2.amazonaws.com"} if source == "overture" else {"https://overpass-api.de"}
    with SourceClient(origins=origins, limits=limits, snapshot_dir=snapshot_dir, offline=offline) as client:
        evidence = {"source": source, "interpretation_contract": CONTRACT}
        if source == "overture":
            records = _overture(client, bbox, release, evidence)
        else:
            query = osm_query(bbox)
            body = client.json(OVERPASS, params={"data": query}, max_bytes=4_000_000)
            if body.get("remark"):
                raise SourceUnavailable("Overpass returned a partial/error response; no partial result")
            if not (body.get("osm3s") or {}).get("timestamp_osm_base"):
                raise SourceSchemaError("Missing OSM database timestamp")
            records = body["elements"]
            evidence.update(query=query, osm_timestamp=body["osm3s"],
                            selection="OSM ways with >=1 node in bbox; exact geometry intersection afterward")
        evidence.update(http=client.trace, body_bytes=client.bytes,
                        license="ODbL-1.0; retain provider attribution", release_status="candidate_not_certified")
        frame = normalize(records, source, bbox, evidence)
        frame.attrs.update(source_flavor=source, interpretation_contract=CONTRACT,
                           release_status="candidate_not_certified", geometry_type="line features")
        return frame


__all__ = ["roads"]
