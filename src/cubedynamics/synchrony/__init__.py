"""Synchrony primitives for state and event cubes."""

from .coupling import sync_with
from .diagnostics import (
    compare_panels,
    panel_change_diagnostics,
    stack_radius_diagnostics,
    stack_structure_diagnostics,
)
from .occurrence import occurrence_synchrony
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
from .states import binary_state, change_state, quantile_state, threshold_state
from .timing import duration_synchrony, timing_synchrony

__all__ = [
    "binary_state",
    "build_spatial_pairs",
    "change_state",
    "compare_panels",
    "duration_synchrony",
    "occurrence_synchrony",
    "panel_change_diagnostics",
    "local_synchrony_stack",
    "load_stack_checkpoint",
    "quantile_state",
    "severity_synchrony",
    "reduce_synchrony_stack",
    "stack_edges",
    "stack_radius_diagnostics",
    "stack_structure_diagnostics",
    "sync_with",
    "synchrony_landscape_similarity",
    "threshold_state",
    "timing_synchrony",
    "write_stack_checkpoint",
]
