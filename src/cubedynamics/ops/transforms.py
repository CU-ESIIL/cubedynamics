"""Transform-style pipeable operations."""

from __future__ import annotations

from collections.abc import Iterable

from ..verbs.stats import anomaly as _anomaly
from ..verbs.stats import month_filter as _month_filter
from ..deprecations import warn_deprecated


def anomaly(dim: str = "time", *, keep_dim: bool = True):
    """Deprecated. Use :func:`cubedynamics.verbs.anomaly` instead.

    This shim exists for backward compatibility and simply forwards arguments
    to the canonical verb implementation.
    """

    warn_deprecated(
        "cubedynamics.ops.transforms.anomaly",
        "cubedynamics.verbs.anomaly",
        since="0.2.0",
        removal="0.3.0",
    )
    return _anomaly(dim=dim, keep_dim=keep_dim)


def month_filter(months: Iterable[int]):
    """Deprecated. Use :func:`cubedynamics.verbs.month_filter` instead.

    This shim exists for backward compatibility. It keeps only the requested
    calendar months on a ``time`` coordinate with datetime-like values.

    Parameters
    ----------
    months:
        Sequence of integers (1-12) to keep.
    """

    warn_deprecated(
        "cubedynamics.ops.transforms.month_filter",
        "cubedynamics.verbs.month_filter",
        since="0.2.0",
        removal="0.3.0",
    )

    return _month_filter(months)


__all__ = ["anomaly", "month_filter"]
