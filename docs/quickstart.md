# Getting started with CubeDynamics

**In plain English:**  
This guide installs CubeDynamics, shows the pipe `|` rhythm, and now explains how VirtualCube streams very large climate or NDVI requests. You get runnable code you can paste into a notebook and tips for debugging huge pulls.

**What this page helps you do:**  
- Install CubeDynamics from PyPI or GitHub
- Run your first pipe + verbs chain
- Stream and inspect very large cubes with VirtualCube

## Quick install steps

```bash
pip install cubedynamics
# or the latest main branch
pip install "git+https://github.com/CU-ESIIL/climate_cube_math.git@main"
```

CubeDynamics runs anywhere `xarray` runs: laptops, HPC clusters, or hosted notebooks.

## First streaming pipeline

```python
import cubedynamics as cd
from cubedynamics import pipe, verbs as v

cube = cd.load_prism_cube(
    lat=40.0,
    lon=-105.25,
    start="2000-01-01",
    end="2020-12-31",
    variable="ppt",
)

# This is small, but the syntax stays identical for 50-year cubes
pipe(cube) \
    | v.anomaly(dim="time") \
    | v.month_filter([6, 7, 8]) \
    | v.variance(dim="time")
```

If you request a larger AOI or longer date range, the loader silently returns a VirtualCube that streams tiles through the same verbs.

## Working With Large Datasets (New in 2025)

CubeDynamics can now work with extremely large climate or NDVI datasets — 
even decades of data or very large spatial areas — without loading everything 
into memory at once.

It does this using a new system called **VirtualCube**, which streams data in 
small 'tiles'. You can think of these tiles as puzzle pieces. CubeDynamics 
processes each piece, keeps track of running statistics, and never holds the 
whole puzzle in memory.

## Debugging and control

Most users never need to configure streaming. When you do, use these helpers:

```python
ndvi = cd.ndvi(
    lat=40.0,
    lon=-105.25,
    start="1970",
    end="2020",
    streaming_strategy="virtual",
    time_tile="5y",
)
print(ndvi)           # shows that it is a VirtualCube
ndvi.debug_tiles()    # prints time + space tiles
ndvi.materialize()    # forces full load; only for small areas
```

Try smaller `time_tile` or spatial bounds if you see slow progress or rate limits.

## Behind the scenes

When a request is too large for a normal in-memory cube, CubeDynamics:
- Splits the timeline into tiles (for example, five-year windows).
- Splits the AOI into spatial tiles when needed.
- Streams each tile through the verbs, tracking running statistics like variance or mean.
- Returns a normal-looking DataArray/Dataset at the end.

You do not have to change your code when streaming kicks in.

## Next steps

- Browse the [Virtual Cubes](concepts/virtual_cubes.md) page for a full tour of streaming.
- Read [Streaming Large Data](streaming_large_data.md) for debugging checklists and provider considerations.
- Grab a semantic loader from [semantic_variables.md](semantic_variables.md) if you want NDVI or temperature without memorizing provider names.

---

This material has been moved to the Legacy Reference page.
