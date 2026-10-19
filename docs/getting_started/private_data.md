# Use proprietary data on HPC scratch

Use `data.open_local_cube` to supplement public sources with a project-owned
NetCDF dataset or Zarr store. Run Python on the HPC, or mount scratch where
Python and its Dask workers can read it. The loader uses filesystem access;
your existing HPC account and filesystem permissions control access.

```python
from cubedynamics import data, pipe, verbs as v

with data.open_local_cube(
    "/scratch/my_lab/project/soil_moisture/run_42/*.nc",
    dataset_id="my_lab/soil_moisture",
    revision="run-42",
    variables=["soil_moisture"],
    chunks={"time": 24, "y": 256, "x": 256},
) as cube:
    # Use the actual variable and dimension names in your files.
    result = (pipe(cube) | v.mean(dim="time")).unwrap().compute()
```

This example names your own files; it does not acquire or invent observations.
A single filename or explicit list of NetCDF filenames also works. Multiple
files combine by coordinate labels and require identical coordinates along
non-concatenated dimensions. Missing paths, incompatible grids and missing
variables raise errors. Explicitly select the intended acquisition: a broad
glob is not a dataset revision.

For a chunked Zarr directory, install the optional backend into your HPC
Python environment:

```bash
python -m pip install 'cubedynamics[local]'
```

Use a checkout containing this helper until it is included in a published
release (`python -m pip install -e '.[local]'` from that checkout).

```python
with data.open_local_cube(
    "/scratch/my_lab/project/private_product.zarr",
    dataset_id="my_lab/private_product",
    revision="acquisition-2026-10-01",
) as cube:
    result = cube.isel(time=slice(0, 24)).mean("time").compute()
```

Opening reads metadata and coordinate indexes. Measurement arrays remain
Dask-backed until computation or a consuming plot/output operation. Default
chunks follow the storage backend; an unchunked NetCDF variable may otherwise
be one large task, so choose explicit chunk sizes for your workload. Workers
need the same paths, permissions and backend libraries. Compute before closing
the Dataset. The loader performs no SSH login, transfer, upload or package
cache write.

Native variable names, dimension names, units, CRS, temporal support and
existing provenance are retained. Select, rename and align them explicitly for
your scientific question before combining them with public data. File access
does not harmonize products or certify their suitability. A project noun can
wrap this helper with your own schema and scientific checks; see
[custom nouns](../extending/custom_nouns.md), the
[scientific data contract](../concepts/scientific_data_contract.md) and
[temporal alignment](../concepts/temporal_alignment.md).

The `local_source_provenance` JSON attribute records your dataset identity,
optional revision, resolved file paths, sizes and modification times. These
records do not hash the contents, snapshot scratch, or establish immutability.
Keep the source fixed during computation and preserve an authorized durable
copy for reproducibility before scratch is purged. This helper does not add
private datasets to `data.list_sources()` or claim a public serving revision.
Review path and scientific metadata before sharing outputs: private paths are
included in this provenance attribute. Dataset access permissions and any
restrictions on derived results remain project responsibilities.

See the [loader reference](../api/data.md#private-and-local-storage).
