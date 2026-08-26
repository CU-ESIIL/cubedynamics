"""Scientific nouns and source-specific loading helpers.

Use noun functions such as :func:`temperature` in new analyses.  The
``load_*`` functions remain public for workflows that deliberately need a
provider-specific product.
"""

from .catalog import describe, list_sources, sources
from .gridmet import load_gridmet_cube
from .nouns import (
    humidity,
    precipitation,
    radiation,
    surface_reflectance,
    temperature,
    vegetation_index,
    vpd,
    wind,
)
from .prism import load_prism_cube
from .sentinel2 import load_s2_cube, load_s2_ndvi_cube

__all__ = [
    "describe",
    "humidity",
    "list_sources",
    "load_gridmet_cube",
    "load_prism_cube",
    "load_s2_cube",
    "load_s2_ndvi_cube",
    "precipitation",
    "radiation",
    "sources",
    "surface_reflectance",
    "temperature",
    "vegetation_index",
    "vpd",
    "wind",
]
