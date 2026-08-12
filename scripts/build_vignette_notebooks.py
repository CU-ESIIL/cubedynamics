#!/usr/bin/env python3
"""Build the small, source-controlled publication vignettes.

The notebook content is kept here as plain text so metadata and cell structure
can be reviewed and regenerated consistently. Run this script only when editing
the vignettes; normal validation uses ``scripts/run_vignettes.py``.
"""

from __future__ import annotations

import json
import hashlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VIGNETTE_DIR = ROOT / "docs" / "vignettes"


def markdown(source: str) -> dict:
    source = source.strip()
    return {
        "cell_type": "markdown",
        "id": hashlib.sha256(f"markdown:{source}".encode()).hexdigest()[:12],
        "metadata": {},
        "source": source.splitlines(keepends=True),
    }


def code(source: str) -> dict:
    source = source.strip()
    return {
        "cell_type": "code",
        "id": hashlib.sha256(f"code:{source}".encode()).hexdigest()[:12],
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": source.splitlines(keepends=True),
    }


def notebook(*cells: dict) -> dict:
    return {
        "cells": list(cells),
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
            "language_info": {"name": "python", "version": "3.11"},
            "cubedynamics": {
                "network": False,
                "supported_vignette": True,
            },
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }


NOTEBOOKS = {
    "grammar_basics.ipynb": notebook(
        markdown(
            """
# The core CubeDynamics grammar

This vignette is the smallest complete CubeDynamics workflow. It builds a
deterministic in-memory cube, composes public verbs, and unwraps the result.
It needs no network access, credentials, or local data.
"""
        ),
        markdown(
            """
## Build a small cube

CubeDynamics works with xarray objects. The conventional dimensions are
`time`, `y`, and `x`; the values can be NumPy- or Dask-backed.
"""
        ),
        code(
            """
import numpy as np
import pandas as pd
import xarray as xr

from cubedynamics import pipe, verbs as v

rng = np.random.default_rng(42)
time = pd.date_range("2024-01-01", periods=12, freq="MS")
season = np.sin(np.linspace(0, 2 * np.pi, time.size, endpoint=False))[:, None, None]
spatial = np.array([[0.0, 0.2, 0.4], [0.1, 0.3, 0.5]])[None, :, :]
noise = rng.normal(0, 0.02, size=(time.size, 2, 3))

cube = xr.DataArray(
    season + spatial + noise,
    dims=("time", "y", "x"),
    coords={"time": time, "y": [40.1, 40.0], "x": [-105.2, -105.1, -105.0]},
    name="environmental_signal",
    attrs={"units": "1", "source": "deterministic synthetic vignette"},
)
cube
"""
        ),
        markdown(
            """
## Compose verbs

The outer verb call stores configuration; the pipe passes the current value to
the returned callable. `unwrap()` marks the boundary where ordinary Python and
xarray use resumes.
"""
        ),
        code(
            """
spatial_anomaly_series = (
    pipe(cube)
    | v.anomaly(dim="time")
    | v.mean(dim=("y", "x"), keep_dim=False)
).unwrap()

assert spatial_anomaly_series.dims == ("time",)
assert abs(float(spatial_anomaly_series.mean())) < 1e-12
spatial_anomaly_series
"""
        ),
        markdown(
            """
## The grammar is regular Python

A pipe may contain built-in verbs and ordinary callables. A reusable scientific
callable is usually moved into the project that owns its assumptions and given
direct-call and pipe tests.
"""
        ),
        code(
            """
def name_result(name):
    def _op(value):
        return value.rename(name)
    return _op

named = (pipe(spatial_anomaly_series) | name_result("regional_anomaly")).unwrap()
assert named.name == "regional_anomaly"
named.to_dataframe().head()
"""
        ),
        markdown(
            """
The stable idea is the composition protocol—not this synthetic dataset. Replace
`cube` with a local xarray object, a maintained data adapter, or a project-owned
stream and keep the same grammar.
"""
        ),
    ),
    "custom_verb_project.ipynb": notebook(
        markdown(
            """
# Build a project-specific verb

Domain add-ons are usually projects that define their own verbs. This vignette
implements a heat-stress vocabulary without modifying or registering anything
inside CubeDynamics.
"""
        ),
        markdown(
            """
## A verb factory

The outer function captures configuration. The inner `_op` receives the current
pipe value and returns the next value. Here the return type is a Dataset with an
occurrence state and an exceedance magnitude.
"""
        ),
        code(
            """
import numpy as np
import pandas as pd
import xarray as xr

from cubedynamics import pipe, verbs as v


def heat_stress(*, threshold: float = 35.0):
    \"\"\"Classify temperature values at or above ``threshold``.\"\"\"
    def _op(cube: xr.DataArray) -> xr.Dataset:
        if "time" not in cube.dims:
            raise ValueError("heat_stress requires a 'time' dimension")

        state = (cube >= threshold).rename("state")
        magnitude = (cube - threshold).where(state, 0).rename("magnitude")
        result = xr.Dataset({"state": state, "magnitude": magnitude})
        result.attrs.update(cube.attrs)
        result.attrs.update(project_verb="heat_stress", threshold=float(threshold))
        return result

    return _op
"""
        ),
        markdown("## Compose shared and project vocabularies"),
        code(
            """
time = pd.date_range("2025-07-01", periods=5, freq="D")
temperature = xr.DataArray(
    np.array(
        [
            [[32.0, 34.0], [33.0, 35.0]],
            [[33.0, 35.0], [34.0, 36.0]],
            [[35.0, 37.0], [36.0, 38.0]],
            [[34.0, 36.0], [35.0, 37.0]],
            [[31.0, 33.0], [32.0, 34.0]],
        ]
    ),
    dims=("time", "y", "x"),
    coords={"time": time, "y": [1, 0], "x": [0, 1]},
    name="air_temperature",
    attrs={"units": "degC", "source": "deterministic synthetic vignette"},
)

states = (pipe(temperature) | heat_stress(threshold=35.0)).unwrap()
daily_fraction = (
    pipe(states["state"])
    | v.mean(dim=("y", "x"), keep_dim=False)
).unwrap()

assert set(states.data_vars) == {"state", "magnitude"}
assert states.attrs["threshold"] == 35.0
assert daily_fraction.dims == ("time",)
daily_fraction.to_dataframe(name="heat_stress_fraction")
"""
        ),
        markdown("## Test direct use and pipe use"),
        code(
            """
direct = heat_stress(threshold=35.0)(temperature)
through_pipe = (pipe(temperature) | heat_stress(threshold=35.0)).unwrap()
xr.testing.assert_identical(direct, through_pipe)
print("The project verb has the same result in direct and pipe use.")
"""
        ),
        markdown(
            """
In a real add-on, move `heat_stress` into `my_project.verbs`, document the
threshold's scientific meaning, and keep this regression test with the project.
The repository's `examples/custom_verb_project/` directory provides that small
module layout.
"""
        ),
    ),
    "lazy_composition.ipynb": notebook(
        markdown(
            """
# Lazy composition with Dask

The grammar should not force eager evaluation. This vignette constructs a
Dask-backed xarray cube, applies ordinary CubeDynamics verbs, and verifies that
the result remains lazy until an explicit `compute()` boundary.
"""
        ),
        code(
            """
import dask.array as da
import numpy as np
import pandas as pd
import xarray as xr

from cubedynamics import pipe, verbs as v

rng = np.random.default_rng(7)
values = rng.normal(size=(24, 8, 10)).astype("float32")
lazy_values = da.from_array(values, chunks=(6, 4, 5))

cube = xr.DataArray(
    lazy_values,
    dims=("time", "y", "x"),
    coords={
        "time": pd.date_range("2023-01-01", periods=24, freq="MS"),
        "y": np.arange(8),
        "x": np.arange(10),
    },
    name="signal",
    attrs={"source": "deterministic synthetic vignette"},
)

assert cube.chunks is not None
cube
"""
        ),
        markdown("## Build a lazy graph"),
        code(
            """
result = (
    pipe(cube)
    | v.anomaly(dim="time")
    | v.variance(dim="time", keep_dim=False)
).unwrap()

assert result.dims == ("y", "x")
assert result.chunks is not None
graph_tasks = len(result.data.__dask_graph__())
print(f"Lazy result with {graph_tasks} graph tasks and chunks {result.chunks}")
"""
        ),
        markdown(
            """
No values have been materialized by the pipe. Compute only the small final
product when the workflow reaches an intentional execution boundary.
"""
        ),
        code(
            """
materialized = result.compute()
assert materialized.chunks is None
assert materialized.shape == (8, 10)
assert np.isfinite(materialized.values).all()
materialized
"""
        ),
    ),
}


def main() -> None:
    VIGNETTE_DIR.mkdir(parents=True, exist_ok=True)
    for name, content in NOTEBOOKS.items():
        path = VIGNETTE_DIR / name
        path.write_text(json.dumps(content, indent=1) + "\n", encoding="utf-8")
        print(f"wrote {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
