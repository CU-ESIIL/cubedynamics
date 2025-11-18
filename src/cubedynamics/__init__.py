"""cubedynamics: streaming-first climate cube math.

Core goals
----------
* Stream climate data (PRISM, gridMET, NDVI, etc.) into xarray cubes.
* Compute correlations, variance, and trends as cubes without full downloads.
* Prefer streaming/chunked access over eager IO whenever possible.
"""

from .version import __version__

# Legacy, fully implemented APIs -------------------------------------------------
from .data.gridmet import load_gridmet_cube
from .data.prism import load_prism_cube
from .data.sentinel2 import load_s2_cube
from .indices.vegetation import compute_ndvi_from_s2
from .stats.anomalies import (
    rolling_mean,
    temporal_anomaly,
    temporal_difference,
    zscore_over_time,
)
from .stats.correlation import rolling_corr_vs_center
from .stats.spatial import mask_by_threshold, spatial_coarsen_mean, spatial_smooth_mean
from .stats.tails import rolling_tail_dep_vs_center
from .utils.chunking import coarsen_and_stride
from .viz.lexcube_viz import show_cube_lexcube
from .viz.qa_plots import plot_median_over_space

# Streaming-first stubs for the new architecture ---------------------------------
from .gridmet_streaming import stream_gridmet_to_cube
from .prism_streaming import stream_prism_to_cube
from .correlation_cubes import correlation_cube

__all__ = [
    "__version__",
    # Legacy surface area ---------------------------------------------------------
    "load_s2_cube",
    "load_gridmet_cube",
    "load_prism_cube",
    "compute_ndvi_from_s2",
    "zscore_over_time",
    "temporal_anomaly",
    "temporal_difference",
    "rolling_mean",
    "rolling_corr_vs_center",
    "rolling_tail_dep_vs_center",
    "spatial_coarsen_mean",
    "spatial_smooth_mean",
    "mask_by_threshold",
    "show_cube_lexcube",
    "plot_median_over_space",
    "coarsen_and_stride",
    # Streaming-first stubs -------------------------------------------------------
    "stream_gridmet_to_cube",
    "stream_prism_to_cube",
    "correlation_cube",
]
