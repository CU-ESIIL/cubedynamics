# Operations Reference – IO Functions

IO verbs move cubes to disk or other systems without breaking the pipe chain. They live in `cubedynamics.ops.io`. Examples assume `import cubedynamics as cd` and a `cube` variable referencing an `xarray` object.

## `to_netcdf(path)`

Writes the upstream cube to a NetCDF file.

```python
(
    cd.pipe(cube)
    | cd.anomaly(dim="time")
    | cd.to_netcdf("out.nc")
).unwrap()
```

- **Parameters**
  - `path`: output file path.
- **Behavior**: saves the cube to NetCDF and returns the original object so you can continue chaining if desired.

Use `to_netcdf` at the end of a pipe to persist results, or in the middle if you want to checkpoint intermediate artifacts.
