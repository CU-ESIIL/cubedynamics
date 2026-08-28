#!/usr/bin/env python3
"""Build/check the homepage gallery from checksum-controlled real-data fixtures."""

from __future__ import annotations

import hashlib
import json
import argparse
import re
from html import escape
from pathlib import Path

import numpy as np
import xarray as xr

from cubedynamics import pipe, verbs as v
from cubedynamics.plotting.axis_rig import AxisRigSpec
from cubedynamics.plotting.cube_plot import CoordCube, CubeTheme
from cubedynamics.plotting.cube_viewer import cube_from_dataarray
try:
    from .hero_examples import EXAMPLES, SENTINEL
except ImportError:  # Direct script execution.
    from hero_examples import EXAMPLES, SENTINEL


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "real_data" / "prism_boulder_january_2024.nc"
PROVENANCE = FIXTURE.with_suffix(".provenance.json")
OUTPUT = ROOT / "docs" / "assets" / "figures" / "prism_boulder_tmax_cube.html"
MANIFEST = OUTPUT.with_name("hero_examples.json")


def build_hero_html(cube: xr.DataArray, example: dict | None = None) -> str:
    """Style the canonical viewer; keep all six faces and real measurements."""
    example = example or EXAMPLES[0]
    lo, hi = example["limits"]
    ticks = [0, 1] if example.get("transform") == "state" else np.linspace(lo, hi, 5).tolist()
    if cube.attrs.get("units") != example["units"]:
        raise RuntimeError(f"Review {example['id']} units before rebuilding")
    if not bool(np.isfinite(cube).all()) or not (lo <= float(cube.min()) <= float(cube.max()) <= hi):
        raise RuntimeError(f"Review {example['id']} value range before rebuilding")
    projected = example["fixture"] == SENTINEL
    html = cube_from_dataarray(
        cube,
        cmap=example["cmap"], title=escape(example["title"]), legend_title=escape(example["legend"]),
        x_label="Easting (m)" if projected else "Longitude",
        y_label="Northing (m)" if projected else "Latitude",
        axis_meta={"x": {"name": "Easting (m)"}, "y": {"name": "Northing (m)"}, "time": {"name": "Time"}} if projected else None,
        fill_limits=(lo, hi), fill_breaks=ticks,
        fill_labels=[f"{tick:g}".replace("-", "−") for tick in ticks],
        size_px=260,
        coord=CoordCube(elev=-22, azim=-32, zoom=1.1),
        theme=CubeTheme(
            bg_color="#f4f6f3", panel_color="#ffffff",
            title_color="#213e46", axis_color="#213e46", legend_color="#213e46",
            title_font_size=22, axis_scale=0.55, legend_scale=0.6,
        ),
        axis_rig=AxisRigSpec(show_ticks=False, out_x_px=24, time_format="%d %b %Y"),
        thin_time_factor=1,
        show_progress=False,
        return_html=True,
    )
    # Only presentation is specialized. Rotation, keyboard controls, geometry,
    # textures and scientific metadata remain owned by the library viewer.
    html = html.replace("</head>", '<link rel="stylesheet" href="../styles/hero-cube.css">\n</head>')
    html = html.replace('<div class="cube-title">',
                        f'<p class="hero-kicker">{escape(example["kicker"])}</p><div class="cube-title">', 1)
    html = html.replace('<div class="cube-main">', f'''<p class="hero-description">{escape(example["description"])}</p>
    <div class="hero-controls" aria-label="Cube view controls">
      <span>Drag to explore</span>
      <button type="button" data-cube-control="out" aria-label="Zoom out">−</button>
      <button type="button" data-cube-control="in" aria-label="Zoom in">+</button>
      <button type="button" data-cube-control="reset">Reset view</button>
    </div>
    <div class="cube-main">''', 1)
    # Runtime viewers keep random IDs. Standalone gallery assets have stable,
    # per-example IDs to avoid unrelated diffs on every rebuild.
    viewer_id = re.search(r'id="cube-figure-([a-f0-9]{32})"', html).group(1)
    html = html.replace(viewer_id, hashlib.sha256(example["id"].encode()).hexdigest()[:32])
    return html


def load_fixture(stem: str) -> xr.Dataset:
    path = FIXTURE.parent / f"{stem}.nc"
    provenance = json.loads(path.with_suffix(".provenance.json").read_text(encoding="utf-8"))
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != provenance["fixture_sha256"]:
        raise RuntimeError(f"Website fixture {stem} does not match its provenance hash")
    with xr.open_dataset(path, engine="scipy") as opened:
        dataset = opened.load()
    if stem == FIXTURE.stem and dataset.attrs.get("source") != "PRISM Group, Oregon State University":
        raise RuntimeError("Website asset requires the reviewed PRISM source")
    if dataset.attrs.get("is_synthetic") != 0:
        raise RuntimeError("Website asset refuses generated measurement data")
    if not bool((dataset.time.diff("time") > np.timedelta64(0, "ns")).all()):
        raise RuntimeError(f"Website fixture {stem} requires increasing acquisition times")
    return dataset


def example_cube(example: dict, dataset: xr.Dataset) -> xr.DataArray:
    """Use the existing lesson definitions; never manufacture a time dimension."""
    cube = dataset[example["variable"]].copy(deep=True)
    cube.attrs = {**dataset.attrs, **cube.attrs}
    transform = example.get("transform")
    if transform in ("B04", "B08"):
        cube = cube.sel(band=transform, drop=True)
    elif transform == "ndvi":
        red, nir = cube.sel(band="B04", drop=True), cube.sel(band="B08", drop=True)
        cube = ((nir - red) / (nir + red).where((nir + red) != 0)).rename("ndvi")
        cube.attrs = {**dataset.attrs, "units": "1", "processing": "(B08 - B04) / (B08 + B04), retained provider scale; no pixel cloud mask"}
    elif transform == "array":
        cube = cube.isel(time=slice(0, 18), y=slice(8, 13), x=slice(8, 14))
    elif transform in ("anomaly", "zscore"):
        window = cube.sel(time=slice("2024-01-10", "2024-01-20"))
        operation = v.anomaly if transform == "anomaly" else v.zscore
        cube = (pipe(window) | operation(dim="time")).unwrap()
        cube.attrs = {**window.attrs, "units": example["units"], "processing": f"{transform}(dim='time'), baseline 10–20 January 2024"}
    elif transform == "state":
        cube = (pipe(cube) | v.threshold_state(threshold=-10.0, direction="below", name="severe_cold")).unwrap()["state"].astype(float)
        cube.attrs = {**dataset.attrs, "units": "1", "processing": "PRISM tmax below -10 degC"}
    if cube.dims != ("time", "y", "x") or cube.sizes["time"] < 2:
        raise RuntimeError(f"{example['id']} is not a spatiotemporal raster cube")
    return cube


def evidence_inputs() -> dict:
    paths = [Path(__file__), Path(__file__).with_name("hero_examples.py"),
             ROOT / "docs/assets/styles/hero-cube.css",
             ROOT / "src/cubedynamics/plotting/cube_viewer.py",
             ROOT / "src/cubedynamics/plotting/axis_rig.py"]
    for stem in sorted({e["fixture"] for e in EXAMPLES if e["kind"] == "cube"}):
        paths.extend([FIXTURE.parent / f"{stem}.nc", FIXTURE.parent / f"{stem}.provenance.json"])
    return {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}


def check_gallery() -> None:
    manifest = json.loads(MANIFEST.read_text())
    if manifest["inputs"] != evidence_inputs():
        raise RuntimeError("Stale homepage gallery inputs: run scripts/build_real_data_assets.py")
    if manifest["examples"] != json.loads(json.dumps(EXAMPLES)):
        raise RuntimeError("Stale homepage gallery inventory")
    if set(manifest["outputs"]) != {example["path"] for example in EXAMPLES}:
        raise RuntimeError("Incomplete homepage viewer evidence")
    for name, digest in manifest["outputs"].items():
        if hashlib.sha256((ROOT / "docs" / name).read_bytes()).hexdigest() != digest:
            raise RuntimeError(f"Stale homepage viewer: {name}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.check:
        check_gallery()
        print(f"Checked {len(EXAMPLES)} homepage examples; no network")
        return 0
    datasets = {stem: load_fixture(stem) for stem in {e["fixture"] for e in EXAMPLES if e["kind"] == "cube"}}
    outputs = {}
    for example in EXAMPLES:
        path = ROOT / "docs" / example["path"]
        if example["kind"] == "cube":
            html = build_hero_html(example_cube(example, datasets[example["fixture"]]), example)
            path.write_text(html, encoding="utf-8")
        # The published FIRED hull remains its original, explicitly named backend.
        outputs[example["path"]] = hashlib.sha256(path.read_bytes()).hexdigest()
    MANIFEST.write_text(json.dumps({"examples": EXAMPLES, "inputs": evidence_inputs(), "outputs": outputs}, indent=2) + "\n")
    print(f"Built {len(EXAMPLES) - 1} real-data cubes; retained the published FIRED hull")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
