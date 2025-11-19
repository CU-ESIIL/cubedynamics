# Operations – IO verbs

**In plain English:**  
IO verbs save cubes to disk or other systems without breaking your pipe chain.
They let you checkpoint results and still keep working with the same cube.

**You will learn:**  
- How to write cubes to NetCDF inside a pipe
- How to keep chaining after a save
- Where to find the original reference details

## What this is

IO helpers live in `cubedynamics.ops.io` and are re-exported as `cubedynamics.verbs`.
They accept any `xarray` cube and return the same object so your pipeline can continue.

## Why it matters

Saving intermediate results is useful when you share data, restart a notebook, or move computations to the cloud.
IO verbs keep that step explicit without forcing you to break the readable pipe syntax.

## How to use it

### `to_netcdf(path)`
Writes the incoming cube to a NetCDF file.

```python
from cubedynamics import pipe, verbs as v

pipe(cube) \
    | v.anomaly(dim="time") \
    | v.to_netcdf("out.nc")
```
The verb saves the cube and hands back the original object so you can keep chaining if needed.
Point `path` to a temporary directory when experimenting.

---

## Original Reference (kept for context)
# Operations Reference – IO Functions

IO verbs move cubes to disk or other systems without breaking the pipe chain. They live in `cubedynamics.ops.io` and are re-exported via `cubedynamics.verbs`. Examples assume `from cubedynamics import pipe, verbs as v` and a `cube` variable referencing an `xarray` object.

## `to_netcdf(path)`

Writes the upstream cube to a NetCDF file.

```python
pipe(cube) \
    | v.anomaly(dim="time") \
    | v.to_netcdf("out.nc")
```

- **Parameters**
  - `path`: output file path.
- **Behavior**: saves the cube to NetCDF and returns the original object so you can continue chaining if desired.

Use `to_netcdf` at the end of a pipe to persist results, or in the middle if you want to checkpoint intermediate artifacts.
