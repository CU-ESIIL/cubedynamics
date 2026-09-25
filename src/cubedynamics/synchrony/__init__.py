"""Synchrony primitives for state and event cubes."""

from .adaptive import (
    BREAK_STATUS,
    VALID_BREAK_CODES,
    adaptive_synchrony_experiment,
    empirical_break_curve,
)
from .coupling import sync_with
from .diagnostics import (
    compare_panels,
    panel_change_diagnostics,
    stack_radius_diagnostics,
    stack_structure_diagnostics,
)
from .decay import DECAY_STATUS, empirical_decay_curve, empirical_synchrony_decay
from .occurrence import occurrence_synchrony
from .production import (
    distance_stratified_pair_sample,
    expand_spatial_domain,
    landscape_change_signature,
    load_signature_checkpoint,
    local_synchrony_pairs,
    spatial_output_mask,
    synchrony_signature,
    tiled_landscape_change_signature,
    tiled_synchrony_signature,
    write_signature_checkpoint,
)
from .ranges import (
    RANGE_STATUS,
    empirical_range_curve,
    empirical_synchrony_range,
    tiled_empirical_synchrony_range,
)
from .severity import severity_synchrony
from .spatial import build_spatial_pairs
from .stacks import (
    load_stack_checkpoint,
    local_synchrony_stack,
    reduce_synchrony_stack,
    stack_edges,
    synchrony_landscape_similarity,
    write_stack_checkpoint,
)
from .surfaces import (
    angular_profile,
    local_synchrony_surface,
    low_order_surface_reconstruction,
    radial_profile,
    synchrony_surface_diagnostics,
)
from .states import binary_state, change_state, quantile_state, threshold_state
from .timing import duration_synchrony, timing_synchrony

__all__ = [
    "adaptive_synchrony_experiment",
    "binary_state",
    "angular_profile",
    "build_spatial_pairs",
    "change_state",
    "compare_panels",
    "distance_stratified_pair_sample",
    "duration_synchrony",
    "BREAK_STATUS",
    "DECAY_STATUS",
    "empirical_decay_curve",
    "empirical_break_curve",
    "empirical_synchrony_decay",
    "empirical_range_curve",
    "empirical_synchrony_range",
    "expand_spatial_domain",
    "landscape_change_signature",
    "load_signature_checkpoint",
    "local_synchrony_pairs",
    "local_synchrony_surface",
    "low_order_surface_reconstruction",
    "occurrence_synchrony",
    "panel_change_diagnostics",
    "local_synchrony_stack",
    "load_stack_checkpoint",
    "quantile_state",
    "radial_profile",
    "severity_synchrony",
    "reduce_synchrony_stack",
    "stack_edges",
    "stack_radius_diagnostics",
    "stack_structure_diagnostics",
    "spatial_output_mask",
    "sync_with",
    "synchrony_landscape_similarity",
    "synchrony_signature",
    "synchrony_surface_diagnostics",
    "tiled_landscape_change_signature",
    "tiled_synchrony_signature",
    "threshold_state",
    "tiled_empirical_synchrony_range",
    "timing_synchrony",
    "VALID_BREAK_CODES",
    "RANGE_STATUS",
    "write_stack_checkpoint",
    "write_signature_checkpoint",
]
