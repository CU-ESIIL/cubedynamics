#!/usr/bin/env python3
"""Build website-native interactive assets from the reviewed PRISM fixture."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import xarray as xr

from cubedynamics.plotting.cube_viewer import cube_from_dataarray


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "real_data" / "prism_boulder_january_2024.nc"
PROVENANCE = FIXTURE.with_suffix(".provenance.json")
OUTPUT = ROOT / "docs" / "assets" / "figures" / "prism_boulder_tmax_cube.html"


def main() -> int:
    provenance = json.loads(PROVENANCE.read_text(encoding="utf-8"))
    digest = hashlib.sha256(FIXTURE.read_bytes()).hexdigest()
    if digest != provenance["fixture_sha256"]:
        raise RuntimeError("PRISM website fixture does not match its provenance hash")

    dataset = xr.open_dataset(FIXTURE, engine="scipy").load()
    if dataset.attrs.get("source") != "PRISM Group, Oregon State University":
        raise RuntimeError("Website asset requires the reviewed PRISM source")
    if dataset.attrs.get("is_synthetic") != 0:
        raise RuntimeError("Website asset refuses generated measurement data")

    cube = dataset["tmax"]
    html = cube_from_dataarray(
        cube,
        cmap="magma",
        title="Observed PRISM daily maximum temperature · Boulder region",
        legend_title="tmax (degC)",
        thin_time_factor=1,
        show_progress=False,
        return_html=True,
    )
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(html, encoding="utf-8")
    print(f"wrote {OUTPUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
