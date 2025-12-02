import importlib.util
import sys
import types
from pathlib import Path

import numpy as np
import xarray as xr

ROOT = Path(__file__).resolve().parent.parent


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    sys.modules[name] = module
    return module


# Stub the package to avoid importing heavy optional dependencies from cubedynamics.__init__
sys.modules["cubedynamics"] = types.ModuleType("cubedynamics")
sys.modules["cubedynamics"].__path__ = [str(ROOT / "src" / "cubedynamics")]

_load_module("cubedynamics.utils", ROOT / "src" / "cubedynamics" / "utils" / "__init__.py")
_load_module(
    "cubedynamics.plotting.progress", ROOT / "src" / "cubedynamics" / "plotting" / "progress.py"
)

cube_viewer = _load_module(
    "cubedynamics.plotting.cube_viewer", ROOT / "src" / "cubedynamics" / "plotting" / "cube_viewer.py"
)
cube_from_dataarray = cube_viewer.cube_from_dataarray


def test_cube_viewer_band_dim_defaults_to_first_band(tmp_path):
    time = np.arange(3)
    band = ["red", "nir"]
    y = np.arange(4)
    x = np.arange(5)

    data = np.random.rand(time.size, len(band), y.size, x.size)
    da = xr.DataArray(
        data,
        dims=("time", "band", "y", "x"),
        coords={"time": time, "band": band, "y": y, "x": x},
        name="test_cube",
    )

    html = cube_from_dataarray(
        da,
        out_html=str(tmp_path / "test_cube.html"),
        return_html=True,
    )

    assert isinstance(html, str)
    assert "html" in html.lower()
