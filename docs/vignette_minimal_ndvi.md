# Minimal vignette: install → stream a cube → plot

This example shows how to:

1. Install **CubeDynamics**
2. Stream an NDVI cube from a real data source
3. Visualize it with the 3D cube viewer (`v.plot()`)

---

## 1. Install CubeDynamics

Using `pip` (works in a fresh conda env or a regular Python environment):

```bash
pip install --upgrade pip wheel
pip install "git+https://github.com/CU-ESIIL/cubedynamics.git@main"
If you prefer conda, you can first create an environment:
conda create -n cubedynamics-env python=3.10 -y
conda activate cubedynamics-env

pip install --upgrade pip wheel
pip install "git+https://github.com/CU-ESIIL/cubedynamics.git@main"
```

## 2. Stream an NDVI cube
This call builds a streaming NDVI cube over a small region near Boulder, CO, for 2023–2024.
The returned object is an xarray.DataArray backed by a streaming/virtual cube under the hood.
```python
import cubedynamics as cd
from cubedynamics import pipe, verbs as v

# ------------------------------------------------------------------
# Load a streaming NDVI cube (time, y, x)
# ------------------------------------------------------------------
ndvi = cd.ndvi(
    lat=40.0,
    lon=-105.25,
    start="2023-01-01",
    end="2024-12-31",
)

ndvi
```
You should see something like:
```
<xarray.DataArray 'NDVI' (time: T, y: Y, x: X)>
dask.array<...>
Coordinates:
  * time (time) datetime64[ns] ...
  * y    (y) float64 ...
  * x    (x) float64 ...
```

## 3. Plot the cube (3D interactive viewer)
Now send the cube through the pipe + verbs interface and call v.plot():
```python
# Default: 3D cube viewer for (time, y, x)
pipe(ndvi) | v.plot()
```
This opens an interactive 3D cube:
- drag to rotate
- scroll to zoom

Only the needed data are streamed as you interact with the viewer.

If you’re in JupyterLab and don’t see the widget, make sure:
- The notebook is “trusted”
- JavaScript is allowed (no script blockers)

That’s the minimal path: install → cd.ndvi(...) → pipe(ndvi) | v.plot().
