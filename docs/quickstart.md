# Getting started with CubeDynamics

**In plain English:**  
This guide installs CubeDynamics, shows the pipe `|` rhythm, and now explains how VirtualCube streams very large climate or NDVI requests. You get runnable code you can paste into a notebook and tips for debugging huge pulls.

**What this page helps you do:**
- Install CubeDynamics from PyPI or GitHub
- Run your first pipe + verbs chain
- Stream and inspect very large cubes with VirtualCube

> 🔍 **Just want the shortest possible example?**  
> See the [Minimal NDVI vignette](vignette_minimal_ndvi.md) for a one-page example that shows install → stream a cube → 3D plot.

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

## 6. Where to go next

Now that you have a working cube and basic transformations, explore:

- **Concepts**  
  - [What is a cube?](concepts/cubes.md)  
  - [Pipe & verbs](concepts/grammar.md)  
  - [VirtualCubes](concepts/virtual_cubes.md)  

- **How-to Guides**  
  - [NDVI anomalies](howto/ndvi_anomalies.md)  
  - [Climate variance](howto/climate_variance.md)  
  - [Correlation cubes](howto/correlation_cubes.md)  

- **Visualization**  
  - [Cube viewer (`v.plot`)](viz/cube_viewer.md)  
  - [Map viewer (`v.map`)](viz/maps.md)  

- **API Reference**  
  - [API overview](api/index.md)

CubeDynamics provides a unified, cube-native way to work with spatiotemporal environmental data—simple enough for quick exploration, powerful enough for large-scale scientific analysis.
