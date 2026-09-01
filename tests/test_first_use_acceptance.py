"""Regression coverage for naive-user installation and export blockers."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys

import numpy as np
import pandas as pd
import pytest
import xarray as xr

from cubedynamics import pipe, verbs as v
from cubedynamics.serialization import METADATA_ENCODING, sanitize_netcdf_attrs


ROOT = Path(__file__).resolve().parents[1]


def _public_cube() -> xr.DataArray:
    cube = xr.DataArray(
        np.arange(12.0).reshape(3, 2, 2),
        dims=("time", "y", "x"),
        coords={
            "time": pd.date_range("2024-01-01", periods=3, freq="D"),
            "y": [40.0, 40.1],
            "x": [-105.3, -105.2],
        },
        name="precipitation",
        attrs={
            "units": "mm",
            "source": "prism_streaming",
            "is_synthetic": False,
            "semantic_temporal": np.bool_(True),
        },
    )
    return sanitize_netcdf_attrs(cube, copy=False)


def test_core_import_does_not_load_sentinel_compiled_stack() -> None:
    code = r'''
import importlib.abc
import sys

class BlockOptionalGeo(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split(".", 1)[0] in {"cubo", "rasterio", "rioxarray"}:
            raise RuntimeError(f"eager optional geospatial import: {fullname}")
        return None

sys.meta_path.insert(0, BlockOptionalGeo())
import cubedynamics
from cubedynamics import pipe, verbs, data
assert callable(pipe)
assert callable(verbs.mean)
assert callable(data.precipitation)
assert not ({"cubo", "rasterio", "rioxarray"} & set(sys.modules))
print(cubedynamics.__version__)
'''
    completed = subprocess.run(
        [sys.executable, "-I", "-c", code],
        check=False,
        text=True,
        capture_output=True,
    )
    assert completed.returncode == 0, completed.stderr


def test_public_style_source_and_continuous_results_write_directly(tmp_path: Path) -> None:
    cube = _public_cube()
    products = {
        "raw": cube,
        "mean": (pipe(cube) | v.mean(dim="time", keep_dim=False)).unwrap(),
        "anomaly": (pipe(cube) | v.anomaly(dim="time")).unwrap(),
    }
    for name, product in products.items():
        path = tmp_path / f"{name}.nc"
        product.to_netcdf(path, engine="h5netcdf")
        with xr.open_dataarray(path, engine="h5netcdf") as restored:
            assert restored.attrs["is_synthetic"] == 0
            assert restored.attrs["semantic_temporal"] == 1
            assert restored.attrs["source"] == "prism_streaming"


def test_safe_export_encodes_boolean_condition_without_mutating_it(tmp_path: Path) -> None:
    condition = (
        pipe(_public_cube())
        | v.threshold_state(threshold=5, direction="above", name="wet")
    ).unwrap()
    assert condition["state"].dtype == bool
    path = tmp_path / "condition.nc"

    returned = (pipe(condition) | v.to_netcdf(path, engine="h5netcdf")).unwrap()

    assert returned is condition
    assert condition["state"].dtype == bool
    with xr.open_dataset(path, engine="h5netcdf") as restored:
        assert restored["state"].dtype == np.dtype("int8")
        assert restored["state"].attrs["cubedynamics_original_dtype"] == "bool"
        assert json.loads(restored.attrs["cubedynamics_boolean_variables"]) == ["state"]
        assert restored.attrs["cubedynamics_metadata_encoding"] == METADATA_ENCODING
        xr.testing.assert_equal(restored["state"].astype(bool), condition["state"])


def test_safe_export_preserves_structured_metadata_as_canonical_json(tmp_path: Path) -> None:
    cube = _public_cube()
    cube.attrs.update(
        {
            "provenance": {"provider": "PRISM", "reviewed": True},
            "choices": ["daily", None, 3],
            "bounds": (-105.3, 40.0, -105.2, 40.1),
            "retrieved": datetime(2024, 1, 4, tzinfo=timezone.utc),
        }
    )
    path = tmp_path / "structured.nc"

    (pipe(cube) | v.to_netcdf(path, engine="h5netcdf")).unwrap()

    with xr.open_dataarray(path, engine="h5netcdf") as restored:
        assert json.loads(restored.attrs["provenance"]) == {
            "provider": "PRISM",
            "reviewed": True,
        }
        assert json.loads(restored.attrs["choices"]) == ["daily", None, 3]
        assert json.loads(restored.attrs["bounds"]) == [-105.3, 40.0, -105.2, 40.1]
        assert restored.attrs["retrieved"].startswith("2024-01-04")


def test_safe_export_rejects_unstable_custom_metadata(tmp_path: Path) -> None:
    cube = _public_cube()
    cube.attrs["opaque"] = object()
    with pytest.raises(TypeError, match="NetCDF attribute 'opaque'.*unsupported type"):
        (pipe(cube) | v.to_netcdf(tmp_path / "bad.nc", engine="h5netcdf")).unwrap()


def test_current_first_use_docs_state_daily_prism_and_complete_public_path() -> None:
    getting_started = (ROOT / "docs/getting_started.md").read_text(encoding="utf-8")
    quickstart = (ROOT / "docs/quickstart.md").read_text(encoding="utf-8")
    compatibility = (ROOT / "docs/getting_started/first_prism_cube.md").read_text(
        encoding="utf-8"
    )
    audit = (ROOT / "docs/project/public_docs_generation_audit.md").read_text(
        encoding="utf-8"
    )

    for text in (getting_started, quickstart):
        assert 'source="prism"' in text
        assert 'freq="D"' in text
        assert "explain()" in text
        assert "validate()" in text
        assert "semantic_trace" in text
        assert "unwrap()" in text
        assert "to_netcdf" in text
    assert "v.plot" in getting_started
    assert "Compatibility URL" in compatibility
    assert "CURRENT" in audit
    assert "LEGACY / COMPATIBILITY" in audit
    assert "DEPRECATED" in audit
    assert "REMOVE FROM PUBLICATION" in audit
