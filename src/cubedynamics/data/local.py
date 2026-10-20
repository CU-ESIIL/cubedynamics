"""Private cubes, features and batched tables on local or mounted storage."""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from glob import glob, has_magic
import json
import os
from pathlib import Path

import xarray as xr


def _validate_identity(dataset_id, revision):
    if not isinstance(dataset_id, str) or not dataset_id.strip():
        raise ValueError("dataset_id must be a nonempty project-owned identity")
    if revision is not None and (not isinstance(revision, str) or not revision.strip()):
        raise ValueError("revision must be a nonempty string or None")


def _provenance(paths, dataset_id, revision, format, **details):
    records = []
    for path in paths:
        stat = path.stat()
        records.append({"path": str(path), "size_bytes": stat.st_size if path.is_file() else None,
                        "mtime_ns": stat.st_mtime_ns})
    return json.dumps({
        "dataset_id": dataset_id, "revision": revision,
        "storage": "local_filesystem", "format": format, "files": records,
        "identity_method": "user_revision_and_path_stat_not_content_hash", **details,
    }, sort_keys=True)


def _single_file(path):
    name = os.fspath(path)
    if "://" in name or has_magic(name):
        raise ValueError("Supply one explicit local filesystem path, not a URL or glob")
    result = Path(name).expanduser().resolve(strict=True)
    if not result.is_file():
        raise ValueError("Supply one local file")
    return result


def _positive_rows(value, name):
    if type(value) is not int or value < 1:
        raise ValueError(f"{name} must be a positive integer")


def _arrow_parquet():
    try:
        import pyarrow.parquet as pq
    except ImportError as exc:
        raise ImportError("Parquet reads require pip install 'cubedynamics[local]'") from exc
    return pq


def open_local_cube(
    paths: str | os.PathLike | Sequence[str | os.PathLike],
    *,
    dataset_id: str,
    revision: str | None = None,
    variables: Sequence[str] | None = None,
    chunks: Mapping[str, int] | None = None,
    engine: str | None = None,
) -> xr.Dataset:
    """Open private NetCDF files or one Zarr store with deferred data reads.

    Parameters
    ----------
    paths : path or sequence of paths
        A NetCDF file, explicit file list, local glob, or a single directory
        ending in ``.zarr``. Paths must be visible to the Python process,
        including mounted HPC scratch. No SSH connection or transfer is made.
    dataset_id : str
        Project-owned dataset identity, for example ``lab/soil-moisture``.
    revision : str, optional
        User-supplied version or acquisition identity. No version is inferred
        from a scratch filename; an omitted revision remains unspecified.
    variables : sequence of str, optional
        Data variables to retain. Coordinate metadata is preserved.
    chunks : mapping, optional
        Native dimension names to Dask chunk sizes. Default uses backend
        chunks; unchunked NetCDF may need explicit sizes to bound task memory.
    engine : str, optional
        xarray NetCDF engine. Zarr uses its own backend; install
        ``cubedynamics[local]`` for Zarr support.

    Returns
    -------
    xarray.Dataset
        Dask-backed data with native dimensions, units, CRS and attributes.
        Multiple NetCDF files combine by coordinates with exact non-concat
        alignment. No regridding, coordinate renaming, unit conversion,
        publication, or scientific certification is performed.

    Notes
    -----
    Opening reads metadata and coordinate indexes. Computation reads the source
    chunks directly; it does not copy the dataset into a package cache. Keep
    files unchanged and accessible until computation finishes, then call
    ``close()`` (or use the Dataset as a context manager). Distributed workers
    need the same paths and permissions. Scratch storage may be purged.

    ``local_source_provenance`` is JSON containing resolved paths, dataset ID,
    declared revision and file size/mtime (directory mtime for Zarr). These are
    discovery records, not content checksums or an immutable snapshot. Existing
    scientific provenance and synthetic flags are retained without inventing
    an observational or publication status. Paths may be private; review
    metadata before sharing results.
    """
    _validate_identity(dataset_id, revision)
    if chunks is not None and not isinstance(chunks, Mapping):
        raise TypeError("chunks must be a dimension mapping or None")
    if isinstance(variables, str):
        raise TypeError("variables must be a sequence of names, not a string")
    if variables is not None and not variables:
        raise ValueError("variables must contain at least one name")
    requested = [paths] if isinstance(paths, (str, os.PathLike)) else list(paths)
    expanded = []
    for value in requested:
        name = os.fspath(value)
        if "://" in name:
            raise ValueError("Use filesystem paths visible on this host, not remote URLs")
        name = os.path.expanduser(name)
        matches = sorted(glob(name)) if has_magic(name) else [name]
        if not matches:
            raise FileNotFoundError(f"No local files match {name!r}")
        expanded.extend(Path(item).resolve(strict=True) for item in matches)
    if not expanded:
        raise ValueError("Supply at least one local path")
    if len(set(expanded)) != len(expanded):
        raise ValueError("Duplicate local paths would repeat observations")
    zarr = len(expanded) == 1 and expanded[0].is_dir() and expanded[0].suffix == ".zarr"
    if not zarr and any(not path.is_file() or path.suffix.lower() not in {".nc", ".nc4", ".cdf"} for path in expanded):
        raise ValueError("Supply NetCDF files or one directory ending in .zarr")
    provenance = _provenance(expanded, dataset_id, revision, "zarr" if zarr else "netcdf")
    chunk_map = {} if chunks is None else dict(chunks)
    if zarr:
        if engine is not None:
            raise ValueError("engine applies only to NetCDF files")
        try:
            import zarr as _zarr  # noqa: F401
        except ImportError as exc:
            raise ImportError("Zarr scratch reads require pip install 'cubedynamics[local]'") from exc
        opened = xr.open_zarr(str(expanded[0]), chunks=chunk_map)
    elif len(expanded) == 1:
        opened = xr.open_dataset(expanded[0], chunks=chunk_map, engine=engine)
    else:
        opened = xr.open_mfdataset(
            [str(path) for path in expanded], chunks=chunk_map, engine=engine,
            combine="by_coords", join="exact", compat="no_conflicts",
            data_vars="minimal", coords="minimal",
        )
    try:
        result = opened if variables is None else opened[list(variables)]
        result.attrs = dict(opened.attrs)
        result.attrs["local_source_provenance"] = provenance
        if result is not opened:
            result.set_close(opened.close)
        return result
    except BaseException:
        opened.close()
        raise


def open_local_features(
    path: str | os.PathLike,
    *,
    dataset_id: str,
    revision: str | None = None,
    layer: str | None = None,
    crs: str | None = None,
    max_features: int = 100_000,
):
    """Read a private geometry layer as an eager GeoPandas GeoDataFrame.

    Parameters
    ----------
    path : path
        One local GeoJSON (.geojson/.json), GeoPackage (.gpkg), or GeoParquet
        (.parquet/.geoparquet) file, visible to this Python process.
    dataset_id : str
        Project-owned dataset identity.
    revision : str, optional
        Declared acquisition/version identity, not inferred from the filename.
    layer : str, optional
        Required named layer for GeoPackage; unsupported for other formats.
    crs : str, optional
        Explicit CRS when the file lacks one. If already declared, it must
        agree. This never overrides a different CRS or reprojects coordinates.
    max_features : int
        Positive row limit (default 100000). GeoJSON/GeoPackage reads request
        at most limit + 1 rows to detect overflow; GeoParquet counts come from
        metadata before loading. This is a feature-count, not a byte budget.

    Returns
    -------
    geopandas.GeoDataFrame
        Native point, polygon, multipart or other geometry and attribute
        columns, with a known CRS. Empty layers, missing/empty/invalid geometry,
        unknown/conflicting CRS and excess rows raise errors; no repair or
        rasterization is implicit. This read materializes the selected layer.
        Prefer spatially partitioned layers when a whole layer is too large.

    Notes
    -----
    Uses the same filesystem visibility and JSON provenance policy as
    ``open_local_cube``. Units and observation dates remain source columns;
    project-specific validation and explicit alignment/joins are still needed.
    No public registration, transfer or certification is performed.
    """
    import geopandas as gpd
    from pyproj import CRS

    _validate_identity(dataset_id, revision)
    _positive_rows(max_features, "max_features")
    source = _single_file(path)
    suffix = source.suffix.lower()
    if suffix not in {".geojson", ".json", ".gpkg", ".parquet", ".geoparquet"}:
        raise ValueError("Use GeoJSON, a named GeoPackage layer, or GeoParquet")
    if suffix == ".gpkg":
        if not isinstance(layer, str) or not layer.strip():
            raise ValueError("GeoPackage requires an explicit layer name")
    elif layer is not None:
        raise ValueError("layer applies only to GeoPackage")
    provenance = _provenance([source], dataset_id, revision, suffix[1:], layer=layer)
    if suffix in {".parquet", ".geoparquet"}:
        pq = _arrow_parquet()
        with pq.ParquetFile(source) as reader:
            if reader.metadata.num_rows > max_features:
                raise ValueError("Layer exceeds max_features; select a smaller partition")
        frame = gpd.read_parquet(source)
    else:
        options = {"layer": layer} if layer is not None else {}
        frame = gpd.read_file(source, rows=slice(0, max_features + 1), **options)
    if len(frame) > max_features:
        raise ValueError("Layer exceeds max_features; select a smaller partition")
    if not isinstance(frame, gpd.GeoDataFrame) or frame.empty:
        raise ValueError("Expected a nonempty geometry layer")
    if frame.geometry.isna().any() or frame.geometry.is_empty.any() or not frame.geometry.is_valid.all():
        raise ValueError("Layer contains missing, empty or invalid geometry; review it explicitly")
    if frame.crs is None:
        if crs is None:
            raise ValueError("Layer has no CRS; supply crs explicitly")
        frame = frame.set_crs(crs)
    elif crs is not None and not CRS.from_user_input(frame.crs).equals(CRS.from_user_input(crs)):
        raise ValueError("Explicit crs conflicts with the layer CRS; reproject explicitly")
    frame.attrs["local_source_provenance"] = provenance
    return frame


def open_local_table(
    path: str | os.PathLike,
    *,
    dataset_id: str,
    revision: str | None = None,
    columns: Sequence[str] | None = None,
    batch_size: int = 100_000,
    dtype: Mapping[str, object] | None = None,
):
    """Iterate through a private CSV, TSV or Parquet file in row batches.

    Parameters
    ----------
    path : path
        One local .csv, .tsv or .parquet file. No implicit remote access.
    dataset_id : str
        Project-owned dataset identity.
    revision : str, optional
        Declared acquisition/version identity.
    columns : sequence of str, optional
        Columns to read, in the requested order; missing names raise errors.
    batch_size : int
        Positive maximum rows per returned DataFrame (default 100000).
        CSV/TSV uses pandas chunks; Parquet uses Arrow record batches with
        column projection. Variable-length values can still be large; this
        is not a byte budget. Empty files with a header yield no data batches.
    dtype : mapping, optional
        Explicit pandas CSV/TSV dtypes, e.g. {"site_id": "string"} to preserve
        leading zeros. Parquet uses Arrow-backed pandas dtypes to retain
        nullable stored types and rejects this option.
        Dates, units, keys and coordinates are never inferred scientifically.

    Returns
    -------
    iterator of pandas.DataFrame
        Measurement reads occur during iteration. Each batch has the same
        ``local_source_provenance`` JSON attribute as the cube/feature loaders.
        Use ``contextlib.closing`` if iteration may stop early, or explicitly
        close the iterator. Exhaustion closes the underlying reader. Keep
        source files fixed until iteration finishes. GeoParquet must use
        ``open_local_features`` so geometry/CRS metadata is not silently lost.

    Notes
    -----
    Pandas performs ordinary CSV type inference unless dtype is supplied.
    No join, deduplication, geometry construction or xarray conversion occurs.
    Parquet requires the ``local`` extra. The iterator is local and synchronous;
    it is not a distributed Dask DataFrame or a public-catalog registration.
    """
    import pandas as pd

    _validate_identity(dataset_id, revision)
    _positive_rows(batch_size, "batch_size")
    source = _single_file(path)
    suffix = source.suffix.lower()
    if suffix not in {".csv", ".tsv", ".parquet"}:
        raise ValueError("Use CSV, TSV or Parquet for tabular data")
    if columns is not None:
        if isinstance(columns, str) or not columns or any(not isinstance(c, str) for c in columns):
            raise ValueError("columns must be a nonempty sequence of names")
        columns = list(columns)
        if len(set(columns)) != len(columns):
            raise ValueError("columns must be unique")
    if dtype is not None and not isinstance(dtype, Mapping):
        raise TypeError("dtype must be a column mapping or None")
    if suffix == ".parquet" and dtype is not None:
        raise ValueError("dtype applies only to CSV/TSV; Parquet retains stored types")
    provenance = _provenance([source], dataset_id, revision, suffix[1:])

    def batches():
        if suffix == ".parquet":
            pq = _arrow_parquet()
            with pq.ParquetFile(source) as reader:
                if b"geo" in (reader.schema_arrow.metadata or {}):
                    raise ValueError("GeoParquet requires open_local_features to preserve geometry and CRS")
                if columns is not None and set(columns) - set(reader.schema_arrow.names):
                    raise ValueError("Requested columns are missing from the Parquet schema")
                for batch in reader.iter_batches(batch_size=batch_size, columns=columns):
                    frame = batch.to_pandas(types_mapper=pd.ArrowDtype)
                    frame.attrs["local_source_provenance"] = provenance
                    yield frame
        else:
            with pd.read_csv(source, sep="\t" if suffix == ".tsv" else ",",
                             chunksize=batch_size, usecols=columns, dtype=dtype) as reader:
                for frame in reader:
                    if frame.empty:
                        continue
                    if columns is not None:
                        frame = frame[columns]
                    frame.attrs["local_source_provenance"] = provenance
                    yield frame

    return batches()


__all__ = ["open_local_cube", "open_local_features", "open_local_table"]
