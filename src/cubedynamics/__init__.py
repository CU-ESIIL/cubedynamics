"""cubedynamics: streaming-first climate cube math.

Core goals
----------
* Stream climate data (PRISM, gridMET, NDVI, etc.) into xarray cubes.
* Compute correlations, variance, and trends as cubes without full downloads.
* Prefer streaming/chunked access over eager IO whenever possible.
"""

from .version import __version__
from .gridmet_streaming import stream_gridmet_to_cube
from .prism_streaming import stream_prism_to_cube
from .correlation_cubes import correlation_cube

__all__ = [
    "__version__",
    "stream_gridmet_to_cube",
    "stream_prism_to_cube",
    "correlation_cube",
]
