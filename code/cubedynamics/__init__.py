"""Top-level API for the :mod:`cubedynamics` package."""

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
from .viz.lexcube_viz import show_cube_lexcube
from .viz.qa_plots import plot_median_over_space
from .utils.chunking import coarsen_and_stride

__all__ = [
    "load_s2_cube",
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
]
