"""Editorial reference facts for installed non-catalog noun loaders.

Documentation placement is independent of serving certification. Signatures
come from runtime callables; no catalog registration or revision is invented.
"""
from cubedynamics.data.three_dep import elevation
from cubedynamics.data.roads import roads
from cubedynamics.data.usgs import streamflow

NOUNS = {
    "elevation": {
        "callable": elevation, "module": "three_dep", "family": "Terrain",
        "meaning": "Surface elevation on a native raster grid.",
        "type": "Static continuous field", "units": "m; native vertical reference",
        "sources": ("usgs_3dep",), "lesson": "elevation_landscape",
        "returns": "An `xarray.DataArray` named `elevation`, with `y, x` native cell-center coordinates. North is up. There is no invented time axis. Attributes retain CRS, units, nodata, transform, tile metadata, query bounds, exact response provenance, and the interpretation contract.",
        "works": "Use `v.mean` over a spatial dimension, ordinary callables for explicit spatial transformations, and xarray maps. Temporal anomaly/event verbs require time and are not appropriate for this static surface.",
        "example": 'field = elevation(bbox=(-105.300, 39.985, -105.291, 39.994))\nfield.plot(cmap="terrain")',
        "parameters": {"bbox": "WGS84 west, south, east, north; <=0.02° per side in CONUS.", "source": "Only usgs_3dep.", "tile_id": "Optional exact ScienceBase version ID; otherwise require one Current-tagged tile."},
    },
    "roads": {
        "callable": roads, "module": "roads", "family": "Networks & infrastructure",
        "meaning": "Mapped road features with provider-native geometry, identifiers, and classes.",
        "type": "Vector features", "units": "Geometry in WGS84 degrees; project explicitly before measuring distance",
        "sources": ("overture", "osm"), "lesson": "roads_local_network",
        "returns": "A WGS84 `geopandas.GeoDataFrame`. Columns include `geometry`, `source`, `source_feature_id`, `source_classification`, `name`, and the complete provider record in `native` JSON. Attributes retain query bounds, source mode, interpretation contract and acquisition provenance. Features remain un-clipped until you explicitly clip them.",
        "works": "Use GeoPandas operations inside ordinary pipe callables or project-owned verbs. The lesson defines `within_area` and `length_by_class`; these are not new built-in verbs. Raster/time-series verbs and the cube viewer are not interchangeable with a vector workflow.",
        "example": 'frame = roads(source="overture", release="2026-08-19.0",\n              bbox=(-105.285, 40.008, -105.270, 40.020))\nframe.plot()',
        "parameters": {"bbox": "WGS84 west, south, east, north; <=0.02° per side.", "source": "overture or osm; preserves each provider's classes.", "release": "Explicit release required for Overture; not accepted for rolling OSM."},
    },
    "streamflow": {
        "callable": streamflow, "module": "usgs", "family": "Water & hydrology",
        "meaning": "Observed discharge at an identified streamgage through time.",
        "type": "Station time series", "units": "Native provider units; retained examples use ft^3/s",
        "sources": ("usgs",), "lesson": "streamflow_snapshots",
        "returns": "An `xarray.Dataset` with `streamflow(time, station)` for one station. Coordinates preserve station ID, location, time-series identity, record IDs, and native approval/qualifier/last-modified fields. Companion `_present` and `_is_null` flags distinguish absent, null, and empty values. UTC times, units, statistic, request window and raw-response provenance remain inspectable.",
        "works": "Use `v.anomaly(dim='time')` or `v.mean(dim='time')` and plot the streamflow variable. This is a point observation series, not a raster cube. Provisional values remain visible with warnings; comparison of stored snapshots is available through `compare_observations` in the same module.",
        "example": 'observed = streamflow(site="USGS-06730200",\n    start="2026-08-26T00:00:00Z", end="2026-08-26T23:59:59Z")\nobserved.streamflow.isel(station=0).plot()',
        "parameters": {"site": "One agency-prefixed monitoring location, e.g. USGS-06730200.", "start": "Timezone-aware beginning of the observation window.", "end": "Timezone-aware end, later than start; maximum 31 days.", "series_id": "Optional exact time-series identity; required if the query is ambiguous."},
    },
}

SOURCES = {
    "usgs_3dep": dict(provider="US Geological Survey", product="3DEP 1/3 arc-second elevation",
        coverage="CONUS; one fully covering native tile", resolution="1/3 arc-second; native cells",
        time="Static tile version, not a time series", access="TNM catalog + conditional HTTPS ranges",
        temporal_support="Not applicable: elevation has no time dimension; tile version is provenance, not observation support.",
        mode="Snapshot; strong ETag and exact tile identity", profile="continuous_raster_static",
        limits="256 native pixels per side; 80 requests / 8 MB bodies / 180 s. No mosaics, resampling, silent tile clipping, or vertical conversion. Requires Rasterio >=1.4. A requested historical tile is not asserted current.",
        citation="[USGS 3DEP](https://www.usgs.gov/3d-elevation-program)"),
    "overture": dict(provider="Overture Maps Foundation", product="Transportation / segment GeoParquet",
        coverage="Release-covered areas; bounded small-area queries", resolution="Native vector segments",
        time="Explicit release, e.g. 2026-08-19.0", access="Release STAC + pruned, conditional GeoParquet ranges",
        temporal_support="Not applicable: release identity is provenance for static vector features, not an observation interval.",
        mode="Explicit release plus object identities", profile="feature_line",
        limits="5,000 features; 3 partitions; 4 row groups per partition; 400 requests / 40 MB bodies / 300 s. Install cubedynamics[roads] for PyArrow. Native classes/segmentation retained; not routing or completeness certification.",
        citation="[Overture transportation schema](https://docs.overturemaps.org/schema/reference/transportation/segment/) · © Overture Maps Foundation / contributors; ODbL"),
    "osm": dict(provider="OpenStreetMap contributors", product="Mapped highway ways",
        coverage="Small query areas through Overpass", resolution="Native OSM way geometry",
        time="Rolling snapshot at retrieval; timestamp retained", access="Bounded anonymous Overpass request",
        temporal_support="Not applicable to feature time: retrieval time identifies the mapped snapshot and is not an observation-support coordinate.",
        mode="Rolling; retain exact raw response for exact replay", profile="feature_line",
        limits="5,000 features; 6 requests / 4 MB bodies / 90 s. Ways require a node inside the bbox: long crossing ways may be absent. Public Overpass is not a sustained application backend. No automatic road-class crosswalk.",
        citation="[OpenStreetMap attribution and license](https://www.openstreetmap.org/copyright) · © OpenStreetMap contributors; ODbL"),
    "usgs": dict(provider="US Geological Survey", product="Modern continuous water-data API; discharge parameter 00060",
        coverage="One supported USGS station per request", resolution="Point station; native observation intervals",
        time="Provider-available observations; <=31-day requests", access="Modern OGC JSON API, cursor pagination, seven-day batches",
        temporal_support="Unknown at this general source level: timestamps, statistic, and native metadata are retained, but the loader does not claim one physical support interval for every series.",
        mode="Rolling values/status; stable key is series ID plus time", profile="station_timeseries",
        limits="10,000 observations; 40 requests / 16 MB bodies / 180 s. Preserve native units/statistic and provisional flags; missing values are not filled. Multiple series require explicit selection. No synthetic fallback.",
        citation="[USGS Water Data APIs](https://api.waterdata.usgs.gov/)"),
}


def generate_helpers(table, section, signature, link):
    """Return pages and index rows in the existing reference format."""
    import inspect
    from source_lesson_content import LESSONS
    pages, noun_index, source_rows = {}, "", []
    for name, info in NOUNS.items():
        noun_index += section(info["family"], table(
            ["Noun", "Meaning", "Source flavors", "Coverage / resolution / time"],
            [(f"[{name}](nouns/{name}.md)", info["meaning"], info["sources"],
              "; ".join(SOURCES[s]["coverage"] + "; " + SOURCES[s]["resolution"] + "; " + SOURCES[s]["time"] for s in info["sources"]))]))
        page = f"library/nouns/{name}.md"
        text = f"# {name}\n\n{info['meaning']}\n"
        text += section("Quick facts", table(["Fact", "Value"], [("Semantic type", info["type"]),
            ("Units", info["units"]), ("Source flavors", info["sources"]), ("Access", "Explicit bounded acquisition; optional offline snapshot replay")]))
        text += section("Usage", f"```python\nfrom cubedynamics.data.{info['module']} import {name}\n\n{name}{signature(info['callable'])}\n```\n\n"
            "The signature above is generated from the installed loader. Call acquisition before composing the analysis pipe.")
        params = {"source": "Only usgs.", **info["parameters"], "snapshot_dir": "Optional new directory to retain exact responses; use a new directory for a live refresh.", "offline": "Replay verified snapshots only; never download missing content."}
        text += section("Arguments", table(["Argument", "Meaning", "Default"], [(n, params[n], "required" if p.default is inspect.Parameter.empty else repr(p.default)) for n, p in inspect.signature(info["callable"]).parameters.items()]))
        text += section("Available sources", table(["Source", "Coverage", "Resolution", "Time"], [(link(page, f"library/sources/{s}.md", s), SOURCES[s]["coverage"], SOURCES[s]["resolution"], SOURCES[s]["time"]) for s in info["sources"]]))
        if name == "roads":
            text += section("Differences among source flavors", "Overture uses a pinned release; OSM is a rolling mapped snapshot. Native identifiers, classes, and segmentation differ and are not silently harmonized. Overture incorporates OSM, so agreement is not independent ground truth. Both remain vector features; neither implies traffic, legal access, or routing connectivity.")
        text += section("Returned data", info["returns"])
        text += section("Order / grammar behavior", info["works"])
        text += section("Minimal reproducible example", "Live acquisition below requires network access and the source's optional dependencies. "
            f"The [complete offline lesson](../../vignettes/{info['lesson']}.ipynb) uses checksum-verified real inputs and shows a plot at every step.\n\n"
            f"```python\nfrom cubedynamics.data.{info['module']} import {name}\nimport matplotlib.pyplot as plt\n\n{info['example']}\nplt.show()\n```")
        if name in NOUNS:
            caption = LESSONS[name]["steps"][0][3] if name in LESSONS else "Real USGS Boulder Creek discharge on August 26, 2026; native units and provisional status retained."
            text += section("See the data", f'<figure class="cd-generated-result"><img src="../../../assets/generated/nouns/{name}-1.png" alt="{caption}" loading="lazy" decoding="async"><figcaption>{caption}</figcaption></figure>\n\n'
                f'[Code and interpretation](../../vignettes/{info["lesson"]}.ipynb) · [Figure and input hashes](../../assets/generated/nouns/manifest.json)')
        text += section("Quality and provenance", "Implemented and documented here as a scientific noun. Operational certification remains bounded: no production serving revision has been assigned. Retained real-data samples, numerical/schema checks, and replay tests are distinct from broad scientific suitability or live-service guarantees.\n\n"
            + "\n".join(f"- **{s}:** {SOURCES[s]['limits']}" for s in info["sources"])
            + "\n\n[Validation evidence and release gates](../../data/source_projects/production.md). No automatic source switching or synthetic substitution.")
        text += section("See also", f"- [Full lesson](../../vignettes/{info['lesson']}.ipynb)\n- [Learn: nouns](../../learn/nouns.md)\n- [Noun library](../index.md)\n- [Custom verbs](../../extending/custom_verbs.md)" + ("\n- [mean](../../reference/verbs/mean.md)" if name != "roads" else ""))
        pages[page] = text
    for source, info in SOURCES.items():
        nouns = [n for n, d in NOUNS.items() if source in d["sources"]]
        source_rows.append((f"[{source}]({source}.md)", info["provider"], ", ".join(nouns)))
        page = f"library/sources/{source}.md"
        text = f"# {source}\n"
        for title, key in (("Provider", "provider"), ("Product", "product"), ("Coverage", "coverage"), ("Resolution", "resolution"), ("Temporal coverage", "time"), ("Access method", "access")):
            text += section(title, info[key])
        text += section("Temporal support", info["temporal_support"] + " See [Temporal alignment](../../concepts/temporal_alignment.md).")
        text += section("What it provides", "; ".join(NOUNS[n]["meaning"] for n in nouns))
        text += section("Available CubeDynamics nouns", ", ".join(link(page, f"library/nouns/{n}.md", n) for n in nouns))
        text += section("Current QA/certification status", "Bounded real acquisition and offline checks passed for retained samples. Broader scientific review and sustained-load testing remain open; endpoint availability is independent. QA profile: `" + info["profile"] + "`. [Evidence and scope](../../data/source_projects/production.md).")
        text += section("Serving revision / provenance information", info["mode"] + ". No production serving revision assigned. Raw response hashes, request parameters, and source-specific metadata are preserved; a live refresh never overwrites an existing snapshot.")
        text += section("Important limitations", info["limits"] + "\n\n" + info["citation"])
        text += section("Examples using this source", "\n".join(f"- [{NOUNS[n]['meaning']}](../../vignettes/{NOUNS[n]['lesson']}.ipynb)" for n in nouns))
        pages[page] = text
    return pages, noun_index, source_rows
