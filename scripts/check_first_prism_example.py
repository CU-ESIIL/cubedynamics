#!/usr/bin/env python3
"""Run the bounded live PRISM request used by the current first-use docs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import tempfile

import numpy as np

from cubedynamics import data, pipe, verbs as v


def run(output_dir: Path) -> dict[str, object]:
    temperature = data.temperature(
        source="prism",
        statistic="maximum",
        bbox=[-105.35, 39.95, -105.20, 40.10],
        start="2024-01-01",
        end="2024-01-03",
        freq="D",
    )
    if temperature.attrs.get("is_synthetic") != 0:
        raise AssertionError("Live PRISM example did not return observed data")
    if temperature.sizes.get("time") != 3:
        raise AssertionError("Live PRISM example did not return three daily slices")
    if not np.isfinite(temperature).any():
        raise AssertionError("Live PRISM example contains no finite observations")

    analysis = pipe(temperature) | v.mean(over="time", keep_dim=False)
    report = analysis.validate()
    if not report.ok:
        raise AssertionError(f"Live PRISM grammar validation failed: {report}")
    output_dir.mkdir(parents=True, exist_ok=True)
    destination = output_dir / "first-prism-example.nc"
    (analysis | v.to_netcdf(destination, engine="h5netcdf")).unwrap()
    return {
        "status": "PASS",
        "source": temperature.attrs.get("source"),
        "source_mode": temperature.attrs.get("source_mode"),
        "is_synthetic": temperature.attrs.get("is_synthetic"),
        "time_count": temperature.sizes["time"],
        "frequency": "D",
        "export": str(destination),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    output_dir = args.output.resolve() if args.output else Path(
        tempfile.mkdtemp(prefix="cubedynamics-prism-first-use-")
    )
    result = run(output_dir)
    (output_dir / "result.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
