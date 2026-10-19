"""Lazy access to user-managed files on local or mounted HPC storage."""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from glob import glob, has_magic
import json
import os
from pathlib import Path

import xarray as xr


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
    if not isinstance(dataset_id, str) or not dataset_id.strip():
        raise ValueError("dataset_id must be a nonempty project-owned identity")
    if revision is not None and (not isinstance(revision, str) or not revision.strip()):
        raise ValueError("revision must be a nonempty string or None")
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
    records = []
    for path in expanded:
        stat = path.stat()
        records.append({"path": str(path), "size_bytes": stat.st_size if path.is_file() else None,
                        "mtime_ns": stat.st_mtime_ns})
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
        result.attrs["local_source_provenance"] = json.dumps({
            "dataset_id": dataset_id, "revision": revision,
            "storage": "local_filesystem", "format": "zarr" if zarr else "netcdf",
            "files": records, "identity_method": "user_revision_and_path_stat_not_content_hash",
        }, sort_keys=True)
        if result is not opened:
            result.set_close(opened.close)
        return result
    except BaseException:
        opened.close()
        raise


__all__ = ["open_local_cube"]
