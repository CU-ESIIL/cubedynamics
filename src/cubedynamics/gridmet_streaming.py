"""Streaming-first helpers for gridMET data sources.

This module intentionally focuses on documenting the streaming contract so that
future implementations prioritize chunked IO over eager downloads.  The actual
implementation can live elsewhere, but the public API lives here so downstream
packages can rely on it.
"""

from __future__ import annotations

from typing import Iterable, Mapping, Sequence

import xarray as xr


def stream_gridmet_to_cube(
    source: str | Mapping[str, str] | Iterable[str],
    variables: Sequence[str] | None = None,
    time_range: tuple[str, str] | None = None,
    *,
    chunks: dict | str | None = None,
    chunk_reader=None,
    **stream_kwargs,
) -> xr.Dataset:
    """Stream gridMET data into an xarray dataset.

    Streaming-first design requirements
    -----------------------------------
    * ``source`` should accept iterables of URLs, file-like objects, or other
      descriptors that can be opened lazily.
    * ``chunks`` hints how data should be partitioned for Dask/xarray and must
      be honored when possible.
    * ``chunk_reader`` allows callers to provide a custom iterator for streaming
      bytes so that local caching is optional.

    TODO: implement the streaming pipeline.
    """
    raise NotImplementedError("stream_gridmet_to_cube not implemented yet.")


__all__ = ["stream_gridmet_to_cube"]
