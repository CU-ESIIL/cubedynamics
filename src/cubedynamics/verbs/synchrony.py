"""Pipe-friendly synchrony verbs."""

from __future__ import annotations

from ..synchrony.adaptive import adaptive_synchrony_experiment as _adaptive_synchrony_experiment
from ..synchrony.coupling import sync_with as _sync_with
from ..synchrony.diagnostics import panel_change_diagnostics as _panel_change_diagnostics
from ..synchrony.diagnostics import stack_radius_diagnostics as _stack_radius_diagnostics
from ..synchrony.diagnostics import stack_structure_diagnostics as _stack_structure_diagnostics
from ..synchrony.decay import empirical_synchrony_decay as _empirical_synchrony_decay
from ..synchrony.occurrence import occurrence_synchrony as _occurrence_synchrony
from ..synchrony.production import landscape_change_signature as _landscape_change_signature
from ..synchrony.production import local_synchrony_pairs as _local_synchrony_pairs
from ..synchrony.production import synchrony_signature as _synchrony_signature
from ..synchrony.ranges import empirical_synchrony_range as _empirical_synchrony_range
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
    computation_mask=None,
    max_radius_km: float = 100.0,
    window_days: int = 90,
    window_end=None,
    min_t: int = 10,
    split_quantile: float = 0.5,
    time_dim: str = "time",
    pair_batch_size: int = 16384,
    distance_sampling=None,
    sampling_seed: int = 0,
):
    """Build a bounded canonical local-pair table for signature reduction.

    Grammar contract
    ----------------
    Climate cube -> sparse local relationship Dataset. Pair values preserve the
    validated cold/warm tail-Spearman semantics and are computed once per
    canonical edge within the bounded input domain. ``computation_mask`` can
    exclude unsupported spatial nodes independently of the focal
    ``output_mask``. ``distance_sampling`` may cap uniformly sampled pairs in
    successive physical-distance strata before the temporal kernel executes;
    retained pairs carry their design inclusion probability.
    """

    def _op(obj):
        return _local_synchrony_pairs(
            obj,
            lower_var=lower_var,
            upper_var=upper_var,
            output_mask=output_mask,
            computation_mask=computation_mask,
            max_radius_km=max_radius_km,
            window_days=window_days,
            window_end=window_end,
            min_t=min_t,
            split_quantile=split_quantile,
            time_dim=time_dim,
            pair_batch_size=pair_batch_size,
            distance_sampling=distance_sampling,
            sampling_seed=sampling_seed,
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


def empirical_synchrony_range(
    *,
    bin_width_km: float = 20.0,
    min_annulus_count: int = 30,
    background_shell_count: int = 4,
    background_method: str = "outer_annuli",
    persistence_bins: int = 3,
    annular_abs_tolerance: float = 0.03,
    cumulative_abs_tolerance: float = 0.01,
    min_profile_range: float = 0.04,
    censor_fraction: float = 0.80,
    fixed_radius_km: float = 100.0,
):
    """Estimate empirical cold/warm ranges and adaptive reductions.

    Grammar contract
    ----------------
    Sparse local relationship Dataset -> range/adaptive summary Dataset. The
    input discovery radius is search support, not a fitted scale. The reducer
    uses empirical annuli and cumulative medians, applies no parametric kernel
    or distance weighting, and reports boundary-limited results as unresolved.

    Parameters
    ----------
    bin_width_km : float
        Width of empirical physical-distance annuli.
    min_annulus_count : int
        Minimum finite pair relationships required to summarize an annulus.
    background_shell_count : int
        Number of outer supported annuli used by the robust background rules.
    background_method : str
        Selected empirical background: ``outer_annuli``,
        ``smoothed_outer_annuli``, or ``distant_pairs``.
    persistence_bins : int
        Consecutive supported annuli required before declaring convergence.
    annular_abs_tolerance : float
        Minimum absolute tolerance around the empirical background.
    cumulative_abs_tolerance : float
        Maximum allowed change between successive cumulative medians.
    min_profile_range : float
        Smaller supported profile ranges are classified as flat/unidentified.
    censor_fraction : float
        Candidate ranges at or beyond this fraction of discovery support are
        reported as unresolved.
    fixed_radius_km : float
        Physical radius of the fixed-control reduction retained in the output.

    Returns
    -------
    callable
        Pipe stage returning a summary Dataset with empirical curves,
        cold/warm/common range estimates and statuses, fixed controls, and
        unweighted adaptive reductions.

    Notes
    -----
    ``R_common`` is the maximum of cold and warm ranges only when both resolve.
    Primary adaptive Delta uses the same neighbors for both tails. Discovery
    support, range, and kernel weighting are distinct; this verb applies no
    parametric kernel and no distance weights.
    """

    def _op(obj):
        return _empirical_synchrony_range(
            obj,
            bin_width_km=bin_width_km,
            min_annulus_count=min_annulus_count,
            background_shell_count=background_shell_count,
            background_method=background_method,
            persistence_bins=persistence_bins,
            annular_abs_tolerance=annular_abs_tolerance,
            cumulative_abs_tolerance=cumulative_abs_tolerance,
            min_profile_range=min_profile_range,
            censor_fraction=censor_fraction,
            fixed_radius_km=fixed_radius_km,
        )

    return _op


def empirical_synchrony_decay(
    *,
    discovery_radius_km: float | None = None,
    bin_width_km: float = 20.0,
    min_annulus_count: int = 30,
    background_shell_count: int = 4,
    background_method: str = "outer_annuli",
    local_shell_count: int = 2,
    crossing_persistence_bins: int = 2,
    min_local_excess: float = 0.04,
    initial_window_km: float = 100.0,
):
    """Characterize empirical cold and warm synchrony decay.

    Grammar contract
    ----------------
    Sparse local relationship Dataset -> focal spatial-decay summary Dataset.
    The reducer reuses saved pair values, retains non-monotonic annular curves,
    and applies no parametric kernel or distance weighting.

    Returns
    -------
    callable
        Pipe stage returning fractional-decay distances, effective synchrony
        length, robust initial and multiscale slopes, 100 km diagnostics, and
        cold-minus-warm contrasts where both component metrics are valid.

    Notes
    -----
    ``d50`` is the distance at which half the locally elevated synchrony above
    the empirical background has been lost. Effective length is an integrated
    curve property, not a hard cutoff. Initial slope is background-free. None
    of these metrics is a dispersal distance, kernel bandwidth, or adaptive
    neighborhood rule.
    """

    def _op(obj):
        return _empirical_synchrony_decay(
            obj,
            discovery_radius_km=discovery_radius_km,
            bin_width_km=bin_width_km,
            min_annulus_count=min_annulus_count,
            background_shell_count=background_shell_count,
            background_method=background_method,
            local_shell_count=local_shell_count,
            crossing_persistence_bins=crossing_persistence_bins,
            min_local_excess=min_local_excess,
            initial_window_km=initial_window_km,
        )

    return _op


def adaptive_synchrony_experiment(
    *,
    discovery_radius_km: float = 1000.0,
    fixed_radius_km: float = 500.0,
    bin_width_km: float = 25.0,
    min_annulus_count: int = 30,
    smoothing_bins: int = 3,
    common_rule: str = "max",
    time_window_id: str | None = None,
):
    """Discover empirical breaks and compare adaptive with fixed synchrony.

    Grammar contract
    ----------------
    Sparse local relationship Dataset -> four-round adaptive summary Dataset.
    The discovery radius is observation support, not an inferred scale. Cold
    and warm breaks are estimated independently; the default common radius is
    their maximum when both are valid. Primary Delta remains the median of
    pairwise cold-minus-warm values over one shared neighbor set.
    """

    def _op(obj):
        return _adaptive_synchrony_experiment(
            obj,
            discovery_radius_km=discovery_radius_km,
            fixed_radius_km=fixed_radius_km,
            bin_width_km=bin_width_km,
            min_annulus_count=min_annulus_count,
            smoothing_bins=smoothing_bins,
            common_rule=common_rule,
            time_window_id=time_window_id,
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
    "adaptive_synchrony_experiment",
    "duration_synchrony",
    "empirical_synchrony_decay",
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
