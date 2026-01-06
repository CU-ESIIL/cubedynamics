"""Compatibility package that re-exports :mod:`cubedynamics` helpers.

The original repository shipped small ruled-time-hull utilities under the
``climate_cube_math`` namespace.  The modern package exposes a much richer
set of streaming cube math helpers under :mod:`cubedynamics`.  To keep older
imports working we re-export the cubedynamics API here while still exposing
the legacy demo helpers.  Users should migrate to the ``cubedynamics`` import
path, as this shim will be removed in a future release.
"""

from __future__ import annotations

import warnings

import cubedynamics as _cubedynamics

warnings.warn(
    "`climate_cube_math` has been renamed to `cubedynamics`; please update your imports.",
    DeprecationWarning,
    stacklevel=2,
)

from cubedynamics import *  # noqa: F401,F403 - intentionally mirror the API

_cubedynamics_all = getattr(_cubedynamics, "__all__", tuple())

from .demo import make_demo_event
from .hulls import plot_ruled_time_hull

__all__ = sorted(
    set(_cubedynamics_all) | {"make_demo_event", "plot_ruled_time_hull", "__version__"}
)
__version__ = _cubedynamics.__version__
