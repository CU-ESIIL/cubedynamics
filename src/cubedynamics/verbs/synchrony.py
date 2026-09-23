"""Pipe-friendly synchrony verbs."""

from __future__ import annotations

from ..synchrony.coupling import sync_with as _sync_with
from ..synchrony.diagnostics import panel_change_diagnostics as _panel_change_diagnostics
from ..synchrony.diagnostics import stack_radius_diagnostics as _stack_radius_diagnostics
from ..synchrony.diagnostics import stack_structure_diagnostics as _stack_structure_diagnostics
from ..synchrony.occurrence import occurrence_synchrony as _occurrence_synchrony
from ..synchrony.production import landscape_change_signature as _landscape_change_signature
from ..synchrony.production import local_synchrony_pairs as _local_synchrony_pairs
from ..synchrony.production import synchrony_signature as _synchrony_signature
from ..synchrony.severity import severity_synchrony as _severity_synchrony
from ..synchrony.stacks import local_synchrony_stack as _local_synchrony_stack
from ..synchrony.stacks import reduce_synchrony_stack as _reduce_synchrony_stack
from ..synchrony.stacks import (
    synchrony_landscape_similarity as _synchrony_landscape_similarity,
)
from ..synchrony.surfaces import local_synchrony_surface as _local_synchrony_surface
from ..synchrony.surfaces import synchrony_surface_diagnostics as _synchrony_surface_diagnostics
from ..synchrony.timing import duration_synchrony as _duration_synchrony
from ..synchrony.timing import timing_synchrony as _timing_synchrony


def local_synchrony_pairs(
    *,
    lower_var: str | None = None,
    upper_var: str | None = None,
    output_mask=None,
    max_radius_km: float = 100.0,
    window_days: int = 90,
    window_end=None,
    min_t: int = 10,
    split_quantile: float = 0.5,
    time_dim: str = "time",
    pair_batch_size: int = 16384,
):
    """Build a bounded canonical local-pair table for signature reduction.

    Grammar contract
    ----------------
    Climate cube -> sparse local relationship Dataset. Pair values preserve the
    validated cold/warm tail-Spearman semantics and are computed once per
    canonical edge within the bounded input domain.
    """

    def _op(obj):
        return _local_synchrony_pairs(
            obj,
            lower_var=lower_var,
            upper_var=upper_var,
            output_mask=output_mask,
            max_radius_km=max_radius_km,
            window_days=window_days,
            window_end=window_end,
            min_t=min_t,
            split_quantile=split_quantile,
            time_dim=time_dim,
            pair_batch_size=pair_batch_size,
        )

    return _op


def synchrony_signature(
    *, radii_km=(25.0, 50.0, 75.0, 100.0), include_directional: bool = True
):
    """Reduce local pairs to a nested-radius baseline compression.

    This diagnostic is retained for comparison. It does not define the local
    synchrony surface or infer a characteristic synchrony scale.
    """

    def _op(obj):
        return _synchrony_signature(
            obj, radii_km=radii_km, include_directional=include_directional
        )

    return _op


def local_synchrony_surface(
    *,
    focal_y_index: int | None = None,
    focal_x_index: int | None = None,
    focal_index: int | None = None,
):
    """Recover one complete focal ``S_p(dx, dy)`` surface from sparse pairs."""

    def _op(obj):
        return _local_synchrony_surface(
            obj,
            focal_y_index=focal_y_index,
            focal_x_index=focal_x_index,
            focal_index=focal_index,
        )

    return _op


def synchrony_surface_diagnostics(
    *,
    metric: str = "delta_s",
    radial_bin_width_km: float = 5.0,
    angular_bin_width_degrees: float = 15.0,
    min_count: int = 3,
):
    """Evaluate candidate radial, directional, and low-order 2-D descriptors."""

    def _op(obj):
        return _synchrony_surface_diagnostics(
            obj,
            metric=metric,
            radial_bin_width_km=radial_bin_width_km,
            angular_bin_width_degrees=angular_bin_width_degrees,
            min_count=min_count,
        )

    return _op


def landscape_change_signature(
    *,
    metric: str = "delta_s",
    deadband: float = 0.02,
    near_tie_epsilon: float = 0.005,
    min_overlap: int = 25,
):
    """Compare neighboring center landscapes along separate change axes."""

    def _op(obj):
        return _landscape_change_signature(
            obj,
            metric=metric,
            deadband=deadband,
            near_tie_epsilon=near_tie_epsilon,
            min_overlap=min_overlap,
        )

    return _op


def panel_change_diagnostics(
    *, adjacency: int = 4, deadband: float = 0.02, near_tie_epsilon: float = 0.005
):
    """Compare adjacent cold, warm, and Delta synchrony landscapes.

    Returns complementary magnitude, rank, sign, distributional, and spatial
    gradient metrics. No universal panel-change scalar is constructed.
    """

    def _op(obj):
        return _panel_change_diagnostics(
            obj,
            adjacency=adjacency,
            deadband=deadband,
            near_tie_epsilon=near_tie_epsilon,
        )

    return _op


def stack_radius_diagnostics(
    *, radii_km=None, stable_tolerance: float = 0.02, stable_min_centers: int = 25
):
    """Describe how focal stack summaries change across nested support radii."""

    def _op(obj):
        return _stack_radius_diagnostics(
            obj,
            radii_km=radii_km,
            stable_tolerance=stable_tolerance,
            stable_min_centers=stable_min_centers,
        )

    return _op


def stack_structure_diagnostics(
    *, metric: str = "delta_s", distance_bin_edges_km=None, minimum_group_size: int = 20
):
    """Describe distance, direction, modality, and spatial group coherence.

    KDE modes and two-group fields are experimental diagnostics. They do not
    classify climate regimes and must be interpreted with center-geography maps.
    """

    def _op(obj):
        return _stack_structure_diagnostics(
            obj,
            metric=metric,
            distance_bin_edges_km=distance_bin_edges_km,
            minimum_group_size=minimum_group_size,
        )

    return _op


def local_synchrony_stack(
    *,
    lower_var: str | None = None,
    upper_var: str | None = None,
    window_days: int = 90,
    window_end=None,
    min_t: int = 5,
    split_quantile: float = 0.5,
    time_dim: str = "time",
    center_y_indices=None,
    center_x_indices=None,
    max_radius_km: float | None = None,
    distance_bands_km=(25.0, 50.0, 100.0, 250.0),
    pair_batch_size: int = 4096,
):
    """Build unreduced moving-center synchrony stacks.

    Grammar contract
    ----------------
    Climate cube -> relationship stack with dimensions ``center, y, x``.
    Cold synchrony uses the lower tail of ``lower_var``; warm synchrony uses
    the upper tail of ``upper_var``. The output contains the full stack plus
    distance, bearing, direction, and joint-count diagnostics.

    Notes
    -----
    One bounded rolling window is materialized. Apply this verb to a center
    tile plus halo; do not request a dense national center-by-focal matrix.
    """

    def _op(obj):
        return _local_synchrony_stack(
            obj,
            lower_var=lower_var,
            upper_var=upper_var,
            window_days=window_days,
            window_end=window_end,
            min_t=min_t,
            split_quantile=split_quantile,
            time_dim=time_dim,
            center_y_indices=center_y_indices,
            center_x_indices=center_x_indices,
            max_radius_km=max_radius_km,
            distance_bands_km=distance_bands_km,
            pair_batch_size=pair_batch_size,
        )

    return _op


def reduce_synchrony_stack(
    *,
    metric: str = "delta_s",
    near_field_km: float = 50.0,
    distance_decay_km: float = 100.0,
):
    """Reduce a stack to distribution, coverage, distance, and direction maps."""

    def _op(obj):
        return _reduce_synchrony_stack(
            obj,
            metric=metric,
            near_field_km=near_field_km,
            distance_decay_km=distance_decay_km,
        )

    return _op


def synchrony_landscape_similarity(
    *, metric: str = "delta_s", adjacency: int = 4, min_overlap: int = 5
):
    """Compare adjacent centers' full landscapes using panel similarity Q.

    ``Q(A, B)`` is a Spearman comparison of two panels and is scientifically
    distinct from the pixel-pair synchrony value ``S(A, B)``.
    """

    def _op(obj):
        return _synchrony_landscape_similarity(
            obj, metric=metric, adjacency=adjacency, min_overlap=min_overlap
        )

    return _op


def occurrence_synchrony(
    *,
    spatial_mode: str = "neighbors",
    radius_km: float | None = None,
    k_neighbors: int | None = None,
    reference=None,
    method: str = "jaccard",
    window: int | str | None = None,
    stride: int | str | None = None,
    state_var: str = "state",
):
    """Summary
    Measure whether states occur at the same times across locations.

    Grammar contract
    State cube -> synchrony Dataset. Reference/neighborhood modes return maps;
    all-pairs returns edge data; regional returns time-series summaries.
    """

    def _op(obj):
        return _occurrence_synchrony(
            obj,
            state_var=state_var,
            spatial_mode=spatial_mode,
            radius_km=radius_km,
            k_neighbors=k_neighbors,
            reference=reference,
            method=method,
            window=window,
            stride=stride,
        )

    return _op


def severity_synchrony(
    *,
    magnitude_var: str = "magnitude",
    state_var: str = "state",
    condition: str = "joint",
    method: str = "spearman",
    spatial_mode: str = "neighbors",
    radius_km: float | None = None,
    k_neighbors: int | None = None,
    reference=None,
    min_joint_events: int = 10,
    window: int | str | None = None,
    stride: int | str | None = None,
):
    """Summary
    Measure magnitude co-variation during jointly active states.

    Grammar contract
    State cube -> synchrony Dataset with joint-observation diagnostics.
    """

    def _op(obj):
        return _severity_synchrony(
            obj,
            state_var=state_var,
            magnitude_var=magnitude_var,
            condition=condition,
            method=method,
            spatial_mode=spatial_mode,
            radius_km=radius_km,
            k_neighbors=k_neighbors,
            reference=reference,
            min_joint_events=min_joint_events,
            window=window,
            stride=stride,
        )

    return _op


def timing_synchrony(
    *,
    event_anchor: str = "start",
    match_tolerance: str | int = "7D",
    score: str = "exponential",
    timescale: str | int = "3D",
    spatial_mode: str = "neighbors",
    radius_km: float | None = None,
    k_neighbors: int | None = None,
    reference=None,
):
    """Summary
    Measure whether one-to-one matched events happen at similar label times.

    Grammar contract
    EventResult -> synchrony Dataset with lag and unmatched-event diagnostics.
    ``event_anchor`` selects start, peak, or end event labels. This is event-time
    alignment and does not establish equality of source observation windows.
    """

    def _op(obj):
        return _timing_synchrony(
            obj,
            event_anchor=event_anchor,
            match_tolerance=match_tolerance,
            score=score,
            timescale=timescale,
            spatial_mode=spatial_mode,
            radius_km=radius_km,
            k_neighbors=k_neighbors,
            reference=reference,
        )

    return _op


def duration_synchrony(
    *,
    match_on: str = "overlap",
    match_tolerance: str | int = "7D",
    method: str = "spearman",
    spatial_mode: str = "neighbors",
    radius_km: float | None = None,
    k_neighbors: int | None = None,
    reference=None,
    min_matched_events: int = 3,
):
    """Summary
    Compare durations of one-to-one matched events.

    Grammar contract
    EventResult -> synchrony Dataset with duration and match diagnostics.
    """

    def _op(obj):
        return _duration_synchrony(
            obj,
            match_on=match_on,
            match_tolerance=match_tolerance,
            method=method,
            spatial_mode=spatial_mode,
            radius_km=radius_km,
            k_neighbors=k_neighbors,
            reference=reference,
            min_matched_events=min_matched_events,
        )

    return _op


def sync_with(
    other,
    *,
    synchrony: str = "occurrence",
    spatial_relation: str = "same_pixel",
    lags=("0D",),
    state_var: str = "state",
):
    """Summary
    Compare one state cube with another using coordinate-label lags.

    Grammar contract
    State cube + aligned state cube -> coupling Dataset. Positive lags shift
    the comparison so ``+5D`` means left at ``t`` is compared with right at
    ``t+5D``: the right-hand condition occurs five days later. Negative lags
    mean the right-hand condition occurs earlier. Lags do not shift or
    harmonize the physical observation support represented by either source.
    """

    def _op(obj):
        return _sync_with(
            obj,
            other,
            synchrony=synchrony,
            spatial_relation=spatial_relation,
            lags=lags,
            state_var=state_var,
        )

    return _op


__all__ = [
    "duration_synchrony",
    "landscape_change_signature",
    "local_synchrony_pairs",
    "local_synchrony_stack",
    "occurrence_synchrony",
    "panel_change_diagnostics",
    "reduce_synchrony_stack",
    "severity_synchrony",
    "stack_radius_diagnostics",
    "stack_structure_diagnostics",
    "sync_with",
    "synchrony_landscape_similarity",
    "synchrony_signature",
    "timing_synchrony",
]
