"""Transform-style pipeable operations."""

from __future__ import annotations

from collections.abc import Iterable

import xarray as xr

from ..verbs.stats import anomaly as _anomaly


def anomaly(dim: str = "time", *, keep_dim: bool = True):
    """Deprecated shim forwarding to :func:`cubedynamics.verbs.stats.anomaly`."""

    return _anomaly(dim=dim, keep_dim=keep_dim)


def month_filter(months: Iterable[int]):
    """Factory for filtering calendar months from a ``time`` coordinate.

    Parameters
    ----------
    months:
        Sequence of integers (1-12) to keep. Requires that the object has a
        ``time`` coordinate with datetime-like values.
    """

    months = tuple(int(m) for m in months)

    def _inner(da: xr.DataArray | xr.Dataset):
        if "time" not in da.coords:
            raise ValueError("month_filter requires a 'time' coordinate.")
        time = da["time"]
        try:
            month_vals = time.dt.month
        except Exception as exc:  # pragma: no cover - dt errors raised as ValueError below
            raise ValueError("month_filter: 'time' coordinate must be datetime-like.") from exc
        mask = month_vals.isin(months)
        return da.where(mask, drop=True)

    return _inner


__all__ = ["anomaly", "month_filter"]
