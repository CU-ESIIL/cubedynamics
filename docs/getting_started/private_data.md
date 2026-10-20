# Use proprietary data on HPC scratch

Use project-owned cubes, geometry layers and tables to supplement public
sources without registering them in the public catalog. `data.open_local_cube`
reads NetCDF datasets and Zarr stores. Run Python on the HPC, or mount scratch where
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

## Point and polygon layers

`data.open_local_features` returns a GeoPandas GeoDataFrame with native geometry,
attribute columns and CRS. It accepts GeoJSON, a named GeoPackage layer, and
GeoParquet. Point, polygon and multipart geometry remain vector features.

```python
points = data.open_local_features(
    "/scratch/my_lab/project/stations.geojson",
    dataset_id="my_lab/stations",
    revision="survey-42",
)
plots = data.open_local_features(
    "/scratch/my_lab/project/boundaries.gpkg",
    layer="study_plots",
    dataset_id="my_lab/study_plots",
    revision="boundaries-v2",
    max_features=20_000,
)
```

Feature reads are **eager**, with a default limit of 100,000 features. Exceeding
the limit raises an error rather than returning a partial layer. This limits
rows, not geometry complexity or bytes. Partition very large layers into
smaller files; GeoParquet requires the `local` extra. A GeoPackage always needs
an explicit layer name. Missing, empty or invalid geometry fails explicitly.

A missing CRS requires `crs=` supplied from your dataset contract. An explicit
CRS must agree with any stored CRS; it never silently overrides or reprojects.
Use GeoPandas `to_crs` explicitly when comparing spatial sources. A point table
with longitude/latitude columns remains a table until you explicitly construct
geometry and assign its known CRS. The loader does not guess coordinate fields.

## Batched attribute and observation tables

`data.open_local_table` yields pandas DataFrames from CSV, TSV or Parquet files.
It reads measurements during iteration, with at most `batch_size` rows per
batch. Parquet supports column projection and requires the `local` extra.
GeoParquet uses the feature loader to preserve geometry and CRS.

```python
from contextlib import closing

with closing(data.open_local_table(
    "/scratch/my_lab/project/station_attributes.csv",
    dataset_id="my_lab/station_attributes",
    revision="survey-42",
    columns=["site_id", "land_use"],
    dtype={"site_id": "string"},
    batch_size=10_000,
)) as batches:
    for batch in batches:
        print(batch.dtypes)  # Apply your project analysis to each batch.
```

Explicit CSV/TSV dtypes preserve identifiers such as `001`; otherwise pandas
performs its usual inference separately in each batch. Parquet uses Arrow-backed
pandas dtypes to preserve nullable types and does not accept `dtype=`. This keeps
large integer identifiers exact even alongside missing values. Header-only delimited files yield no data
batches. Use `closing` when stopping early; exhausting the iterator also closes
the file. Row batches are not a strict memory/byte budget for large strings or
nested values, and are not distributed Dask DataFrames.

To augment a cube, choose an explicit relationship: station or plot ID for an
attribute join, spatial membership for geometry, and known observation support
for time alignment. Check key uniqueness and join cardinality. Rasterization,
spatial joins, geometry construction, unit conversion and missing-value policies
remain authored analysis steps. These loaders do not assume that vector rows,
table records and raster cells share the same scientific meaning. Plain project
callables can operate on tables and GeoDataFrames through `pipe`; individual
verbs still require their documented input types.

All three loaders use the same `local_source_provenance` policy described
above; tables carry it in each batch's `.attrs` and features in `.attrs`.

See the [loader reference](../api/data.md#private-and-local-storage).
