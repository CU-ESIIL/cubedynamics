"""Re-export cubedynamics data loaders under the legacy namespace."""

from cubedynamics.data import (
    load_gridmet_cube,
    load_prism_cube,
    load_s2_cube,
    load_s2_ndvi_cube,
)

__all__ = ["load_s2_cube", "load_s2_ndvi_cube", "load_gridmet_cube", "load_prism_cube"]
