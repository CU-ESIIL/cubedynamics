"""Statistical pipeable operations."""

from __future__ import annotations

from ..verbs.stats import anomaly, mean, variance, zscore


def correlation_cube(other: xr.DataArray | xr.Dataset | None, dim: str = "time"):
    """Factory placeholder for a future correlation cube operation.

    Parameters
    ----------
    other:
        The comparison cube captured by the factory.
    dim:
        Dimension over which correlations would be computed once implemented.
    """

    if other is None or not isinstance(dim, str):
        raise NotImplementedError("correlation_cube is not implemented yet.")

    def _inner(da: xr.DataArray | xr.Dataset):  # pragma: no cover - stub
        raise NotImplementedError("correlation_cube is not implemented yet.")

    return _inner


__all__ = ["anomaly", "mean", "variance", "correlation_cube", "zscore"]
