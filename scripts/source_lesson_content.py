"""Executable editorial examples shared by noun pages and source notebooks."""

SETUP = '''from pathlib import Path
import hashlib
import json
import numpy as np
import xarray as xr
import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
from shapely.geometry import box
from cubedynamics import pipe, verbs as v

# Frozen outputs of the real bounded loaders, not generated measurements.
root = next(p for p in (Path.cwd(), *Path.cwd().parents)
            if (p / "tests/fixtures/real_data/source_lessons").is_dir())
fixture = root / "tests/fixtures/real_data/source_lessons"

def verify_input(name):
    record = json.loads((fixture / f"{name}.provenance.json").read_text())
    assert record["is_synthetic"] is False
    for relative, expected in record["files"].items():
        assert hashlib.sha256((fixture / relative).read_bytes()).hexdigest() == expected
    return record
'''

ELEVATION = [
    ("Read the landscape in its native cells", "What is high and low within this small Boulder hillside?", SETUP + '''
record = verify_input("elevation")
with xr.open_dataarray(fixture / "elevation.nc", engine="scipy") as source:
    terrain = source.load()  # Only the retained 99 by 99 window.
assert terrain.dims == ("y", "x") and terrain.attrs["units"] == "m"

fig, ax = plt.subplots(figsize=(7, 4), layout="constrained")
terrain.plot(ax=ax, cmap="terrain", cbar_kwargs={"label": "Elevation (m; native vertical datum)"})
ax.set(title="3DEP · Boulder hillside · native cells", xlabel="Longitude (EPSG:4269)", ylabel="Latitude")
ax.ticklabel_format(useOffset=False, style="plain")
ax.xaxis.set_major_locator(MaxNLocator(4))
plt.show()
''', "A real 3DEP window, north up. This is static terrain: no invented time axis, resampling, or vertical-datum conversion."),
    ("Describe relief relative to this window", "Where is terrain above or below the local window mean?", '''def center_on_window_mean(surface):
    # A spatial baseline, not the time-based anomaly verb or a sea-level reference.
    return surface - surface.mean(("y", "x"))

relief = (pipe(terrain) | center_on_window_mean).unwrap()
np.testing.assert_allclose(relief, terrain - terrain.mean(), rtol=0, atol=1e-9)

fig, ax = plt.subplots(figsize=(7, 4), layout="constrained")
relief.plot(ax=ax, cmap="RdBu_r", center=0, cbar_kwargs={"label": "Departure from window mean (m)"})
ax.set(title="Same cells · a local relief baseline", xlabel="Longitude (EPSG:4269)", ylabel="Latitude")
ax.ticklabel_format(useOffset=False, style="plain")
ax.xaxis.set_major_locator(MaxNLocator(4))
plt.show()
''', "The pipe changes the reference level, not the terrain. Negative departures are below the selected window mean; changing the window changes that baseline."),
    ("Reduce the map to a west–east profile", "How does average elevation vary across the window?", '''# Collapse only y. This is a cell mean, not an area-weighted regional statistic.
profile = (pipe(terrain) | v.mean(dim="y", keep_dim=False)).unwrap()
np.testing.assert_allclose(profile, terrain.mean("y"))

fig, ax = plt.subplots(figsize=(7, 3.5), layout="constrained")
profile.plot(ax=ax, color="#236d81")
ax.set(title="Mean elevation by longitude", xlabel="Longitude (EPSG:4269)", ylabel="Elevation (m)")
ax.ticklabel_format(useOffset=False, style="plain")
ax.xaxis.set_major_locator(MaxNLocator(4))
plt.show()
''', "A simpler profile makes the broad gradient legible but removes north–south structure. It is not a road grade, slope map, or watershed delineation."),
]

ROADS = [
    ("Inspect two native road descriptions", "Do these sources describe the same analysis area in the same way?", SETUP + '''
record = verify_input("roads")
networks = {}
for name in ("overture", "osm"):
    body = json.loads((fixture / f"roads_{name}.geojson").read_text())
    networks[name] = gpd.GeoDataFrame.from_features(body, crs="EPSG:4326")
    networks[name].attrs.update(record["native_metadata"][name])
    assert networks[name].source_feature_id.is_unique

# Use one query boundary for both displays; keep full native features.
area = box(*networks["osm"].attrs["requested_bbox"])
def maps(frames, title):
    fig, axes = plt.subplots(1, 2, figsize=(10, 4), layout="constrained")
    for (name, frame), ax in zip(frames.items(), axes):
        frame.plot(ax=ax, color="#236d81", linewidth=1)
        west, south, east, north = area.bounds
        ax.set(xlim=(west, east), ylim=(south, north), title=name,
               xlabel="Longitude (WGS84)", ylabel="Latitude")
        ax.ticklabel_format(useOffset=False, style="plain")
        ax.xaxis.set_major_locator(MaxNLocator(3))
    fig.suptitle(title)
    fig.text(.5, -.035, "© OpenStreetMap contributors · Overture Maps Foundation · ODbL", ha="center", fontsize=9)
    plt.show()

maps(networks, "Boulder roads · retained native segments")
''', "These are mapped features, not evidence of traffic or road condition. Overture incorporates OSM; apparent agreement is not independent validation."),
    ("Make the analysis boundary explicit", "Which parts of the retained features fall inside our area?", '''def within_area(boundary):
    # Project-owned verb: preserve feature attributes and clip geometry explicitly.
    def operation(frame):
        return frame.clip(boundary).copy()
    return operation

clipped = {name: (pipe(frame) | within_area(area)).unwrap()
           for name, frame in networks.items()}
assert all(frame.geometry.covered_by(area).all() for frame in clipped.values())
maps(clipped, "Same boundary · explicitly clipped geometries")
''', "Clipping is a deliberate analytical change, not an invisible loader operation. It cannot recover a crossing OSM way omitted by the provider's node-in-bbox query."),
    ("Measure length without inventing a class crosswalk", "How is retained road length distributed among each provider's own classes?", '''def length_by_class(crs):
    def operation(frame):
        # Geographic degrees are not distances. UTM 13N is local to this Boulder example.
        projected = frame.to_crs(crs)
        return (projected.assign(length_km=projected.length / 1000)
                .groupby("source_classification").length_km.sum().sort_values())
    return operation

lengths = {name: (pipe(frame) | within_area(area) | length_by_class("EPSG:32613")).unwrap()
           for name, frame in networks.items()}
fig, axes = plt.subplots(1, 2, figsize=(10, 4), layout="constrained")
for (name, result), ax in zip(lengths.items(), axes):
    result.plot.barh(ax=ax, color="#236d81")
    ax.set(title=f"{name} · native classes", xlabel="Mapped length inside area (km)", ylabel="")
plt.show()
''', "Native classes and segmentation remain different. These lengths describe the retained mapped sample, not completeness, accessibility, routing connectivity, or a source-quality ranking."),
]

LESSONS = {
    "elevation": {"stem": "elevation_landscape", "title": "Elevation · read a landscape at its native scale",
        "context": "A terrain surface is useful before it becomes a time series. Start with a small real 3DEP window near Boulder and ask what can be learned without changing its grid.",
        "question": "How does elevation vary within this hillside, and what is lost when we summarize it?",
        "pipe": 'pipe(terrain) | v.mean(dim="y", keep_dim=False)',
        "steps": ELEVATION, "fixture": "source_lessons/elevation.nc",
        "provenance": "source_lessons/elevation.provenance.json", "source": "usgs_3dep"},
    "roads": {"stem": "roads_local_network", "title": "Roads · compare mapped networks without erasing their differences",
        "context": "Mapped roads are vector features with provider-specific classes and segment boundaries. Two maps can look similar while answering subtly different questions.",
        "question": "What road length is represented inside a small Boulder area, using each source's native meaning?",
        "pipe": 'pipe(frame) | within_area(area) | length_by_class("EPSG:32613")',
        "steps": ROADS, "fixture": "source_lessons/roads_overture.geojson",
        "provenance": "source_lessons/roads.provenance.json", "source": "overture"},
}
