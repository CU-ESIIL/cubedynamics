# Installation Guide

This guide shows how to set up a stable environment for CubeDynamics (the `cubedynamics` package) using conda/mamba. It avoids dependency thrash by installing heavy geospatial libraries with conda-forge and installing `cubedynamics` separately via pip with `--no-deps`.

## 1. Prerequisites
- A recent version of **conda** or **mamba** (e.g., Miniconda, Anaconda, or Mambaforge).
- **Git** if installing directly from GitHub.
- All heavy geo/system dependencies (e.g., `rasterio`, `pyproj`) are handled via **conda-forge**.

## 2. Quickstart: Create the environment
```bash
# 1. Clone the repo (optional for end users; required for devs)
git clone https://github.com/CU-ESIIL/cubedynamics.git
cd cubedynamics

# 2. Create the conda environment using conda-forge
conda env create -f envs/cube-env.yml

# or, if the user has mamba:
# mamba env create -f envs/cube-env.yml

# 3. Activate the environment
conda activate cube-env
```

## 3. Install cubedynamics into that env (pip, no deps)
We intentionally keep the Python package install separate from the conda environment to avoid pip re-resolving heavy dependencies.

```bash
# install cubedynamics from GitHub in the active environment
pip install --no-deps "git+https://github.com/CU-ESIIL/cubedynamics.git@main"
```

Notes:
- The `--no-deps` flag keeps `numpy`, `dask`, `rasterio`, and other heavy dependencies managed by conda-forge.
- Once tagged releases are available on PyPI, you can instead run:

```bash
pip install --no-deps cubedynamics
```

## 4. Verify the install
Copy-paste this snippet inside the activated `cube-env`:

```python
import numpy as np
import dask
import xarray as xr
import cubedynamics

print("numpy:", np.__version__)
print("dask:", dask.__version__)
print("cubedynamics:", cubedynamics.__version__)
```

Minimal usage example:

```python
from cubedynamics import pipe, verbs as v

# Suppose `ndvi` is a small (time, y, x) xarray.DataArray
pipe(ndvi) | v.plot()
```

## 5. Using the environment in Jupyter
Add the environment as a Jupyter kernel:

```bash
python -m ipykernel install --user --name cube-env --display-name "Cube Env"
```

In Jupyter, choose the **Cube Env** kernel for your notebooks.

## 6. Cloud / Docker usage (short note)
In Docker or cloud environments, reuse the same `envs/cube-env.yml`:

```Dockerfile
COPY envs/cube-env.yml /tmp/
RUN conda env create -f /tmp/cube-env.yml

# install cubedynamics without touching conda-managed deps
RUN /opt/conda/envs/cube-env/bin/pip install --no-deps "git+https://github.com/CU-ESIIL/cubedynamics.git@main"
```

This keeps the environment consistent across local machines and containerized deployments.
