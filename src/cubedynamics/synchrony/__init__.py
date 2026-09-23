"""Synchrony primitives for state and event cubes."""

from .coupling import sync_with
from .diagnostics import (
    compare_panels,
    panel_change_diagnostics,
    stack_radius_diagnostics,
    stack_structure_diagnostics,
)
from .occurrence import occurrence_synchrony
from .production import (
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
    "binary_state",
    "angular_profile",
    "build_spatial_pairs",
    "change_state",
    "compare_panels",
    "duration_synchrony",
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
    "timing_synchrony",
    "write_stack_checkpoint",
    "write_signature_checkpoint",
]
