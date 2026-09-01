#!/usr/bin/env python3
"""Exercise the public first-use path against an installed CubeDynamics wheel.

This script deliberately imports only public CubeDynamics names.  Run it with
``python -I`` from outside the checkout so a source tree cannot mask packaging
or import-time dependency failures.
"""

from __future__ import annotations

import argparse
import importlib.metadata
import json
from pathlib import Path
import subprocess
import sys
import tempfile

def run(output_dir: Path) -> dict[str, object]:
    blocked_import_check = r'''
import importlib.abc
import sys
class BlockOptionalGeo(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split(".", 1)[0] in {"cubo", "rasterio", "rioxarray"}:
            raise RuntimeError(f"eager optional geospatial import: {fullname}")
        return None
sys.meta_path.insert(0, BlockOptionalGeo())
import cubedynamics
from cubedynamics import data, pipe, verbs
assert callable(data.temperature) and callable(pipe) and callable(verbs.mean)
'''
    completed = subprocess.run(
        [sys.executable, "-I", "-c", blocked_import_check],
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode:
        raise AssertionError(
            "Core import still requires the optional compiled geospatial stack:\n"
            + completed.stderr
        )

    from cubedynamics import data, pipe, verbs as v

    import numpy as np
    import pandas as pd
    import xarray as xr

    source = data.describe("temperature", "prism")
    if source["source"] != "prism":
        raise AssertionError("Public noun discovery did not resolve PRISM")

    # A tiny observed-data-shaped value keeps this acceptance check offline.
    # The external quickstart gate separately retrieves and verifies the real,
    # checksum-pinned PRISM extract before running the same public grammar.
    temperature = xr.DataArray(
        np.array(
            [
                [[4.1, 5.2], [3.8, 4.9]],
                [[6.0, 7.1], [5.5, 6.4]],
                [[8.3, 9.0], [7.7, 8.8]],
            ]
        ),
        dims=("time", "y", "x"),
        coords={
            "time": pd.date_range("2024-01-01", periods=3, freq="D"),
            "y": [40.0, 40.1],
            "x": [-105.3, -105.2],
        },
        name="temperature",
        attrs={
            "units": "degC",
            "source": "PRISM first-use acceptance control",
            "is_synthetic": 0,
        },
    )

    analysis = pipe(temperature) | v.anomaly(over="time") | v.mean(
        over=("y", "x"), keep_dim=False
    )
    explanation = analysis.explain()
    validation = analysis.validate()
    if not analysis.semantic_trace or not validation.ok:
        raise AssertionError("First-use semantic inspection did not pass")

    spatial = pipe(temperature) | v.mean(over="time", keep_dim=False)
    plotted = spatial | v.plot(title="PRISM mean daily temperature")
    figure = plotted.unwrap()
    if not getattr(figure, "kind", None):
        raise AssertionError("Public plot verb did not return a renderable result")
    figure._repr_html_()

    output_dir.mkdir(parents=True, exist_ok=True)
    direct_path = output_dir / "first-use-direct.nc"
    temperature.to_netcdf(direct_path, engine="h5netcdf")
    condition = pipe(temperature) | v.threshold_state(
        threshold=6.0, direction="above", name="warm"
    )
    safe_path = output_dir / "first-use-condition.nc"
    (condition | v.to_netcdf(safe_path, engine="h5netcdf")).unwrap()
    with xr.open_dataset(safe_path, engine="h5netcdf") as restored:
        if restored["state"].dtype != np.dtype("int8"):
            raise AssertionError("Boolean condition was not safely encoded")

    return {
        "status": "PASS",
        "version": importlib.metadata.version("cubedynamics"),
        "noun": "temperature",
        "source": source["source"],
        "optional_compiled_stack_required_by_core_import": False,
        "semantic_state": analysis.semantic_state.semantic_kind,
        "semantic_trace_steps": len(analysis.semantic_trace),
        "explain_type": type(explanation).__name__,
        "plot_kind": figure.kind,
        "unwrap_type": type(analysis.unwrap()).__name__,
        "exports": [direct_path.name, safe_path.name],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.output:
        output_dir = args.output.resolve().parent
    else:
        output_dir = Path(tempfile.mkdtemp(prefix="cubedynamics-first-use-"))
    result = run(output_dir)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
