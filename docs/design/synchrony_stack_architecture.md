# Spatial synchrony stacks: phase-one architecture

Status: bounded implementation design. This phase ends at the pre-CONUS
decision gate; it does not authorize or attempt a national run.

## Scientific object and invariants

For a center location `c` and focal location `p`, the pair value is
`S(c, p)`. A focal stack is the vector of those values over every requested
center. A center landscape is the raster of values over all focal locations
for one center. The primary output therefore has explicit `center`, `y`, and
`x` dimensions. It is not reduced to one statistic and it is not presented as
a graph, even though a unique undirected edge table is the efficient internal
calculation form.

The cold value uses `tmin`, each series' own lower quantile, the joint
`<=` tail, and Spearman correlation. The warm value uses `tmax`, each series'
own upper quantile, the joint `>` tail, and Spearman correlation. `delta_s` is
cold minus warm. Paired missing-value filtering, average ranks for ties, and
the existing `min_t` rule are inherited directly from
`partial_tail_spearman`. The inclusive rolling window uses the existing
coordinate-label definition: `t_end - window_days` through `t_end`.

## Phase-one API

- `v.local_synchrony_stack(...)`: cube to an unreduced `center x y x` stack
  Dataset for one requested window end. Optional center indexers define the
  moving-center block, while the input cube defines the focal domain.
- `v.reduce_synchrony_stack(...)`: stack Dataset to per-focal maps of count,
  mean, median, standard deviation, IQR, MAD, minimum, maximum, quantiles,
  distance-weighted mean, and near-field median.
- `v.synchrony_landscape_similarity(...)`: stack Dataset to adjacent-center
  comparisons of entire synchrony landscapes. Panel similarity is a distinct
  quantity `Q(A, B)`; it is never named or interpreted as `S(A, B)`.
- `cubedynamics.synchrony.stack_edges(...)`: lossless unique-pair form for
  checkpointing, diagnostics, or optional network analysis.

The public verb returns the literal storyboard object. The edge representation
is exposed as a synchrony utility for users who need sparse storage, but it is
not the primary scientific API.

## Symmetry and unique computation

The statistic is symmetric because paired validity, per-series quantiles,
joint tail selection, and Spearman correlation are invariant to swapping the
two series. The implementation canonicalizes each pair as `(min(i, j),
max(i, j))`, includes one self-pair per node, evaluates each canonical pair
once, then gathers the result into every requested center landscape. Tests
cover cold, warm, difference, missing values, ties, and `min_t`, and compare
the reconstructed center landscape with the validated center-reference verb.

This arrangement gives a 20 by 20 block exactly 400 stack layers while
avoiding the 160,000 directed calculations that a naive block would perform.
For a coincident 400-pixel center and focal domain, only
`400 * 401 / 2 = 80,200` pairs are evaluated, including self-pairs.

## Metadata and diagnostics

Every center carries its spatial indices and coordinate values. The stack
also includes center-to-focal distance, forward bearing, compass-direction
class, and configurable distance band. Reversing an edge preserves synchrony,
preserves distance, and rotates bearing by 180 degrees. Self-pairs have zero
distance and undefined bearing/direction.

Reductions preserve valid-count and coverage maps alongside summaries so
missing tails cannot masquerade as low variability. Distributional summaries
are preferred over a single median. Histogram entropy or multimodality scores
remain experimental until their sensitivity to binning, missingness, and
sample size is evaluated; phase one supplies quantiles and focal-stack plots
instead of declaring one of those scores scientifically validated.

## Tile, halo, and checkpoint plan

Production work is organized by inclusive window end and center tile. A center
tile contains the locations that emit landscapes. Its focal halo is selected
from the spatial neighborhood required by `radius_km`; full-domain focal maps
are allowed only for bounded experiments. Canonical global pixel identifiers
deduplicate pairs shared by neighboring center tiles. Coarse pair batches are
the scheduler unit; individual pairs are not Dask tasks.

Each checkpoint is keyed by a deterministic analysis fingerprint containing:
source identity and revision, variables, coordinate hashes, window bounds,
quantile, `min_t`, center tile, halo/radius policy, distance bands, code/API
version, and output schema version. A resume operation must reject rather than
mix checkpoints with different fingerprints. NetCDF is sufficient for the
bounded phase-one evidence; production should write chunked Zarr groups by
window and center tile, plus a small manifest that records completed batches.

## Memory and scheduling assumptions

The kernel materializes one bounded time window and one spatial tile plus halo,
not a national time cube. Series are reshaped to `(pixel, time)` and pairs are
processed in coarse NumPy batches. Output memory is proportional to the
requested center-focal relationships, while working memory is proportional to
one pair batch. A dense national center-by-focal stack is explicitly forbidden:
national scaling requires a finite neighborhood radius or another scientifically
declared sparse support.

## Failure and resume behavior

Input validation fails on absent dimensions, mismatched `tmin`/`tmax` grids,
ambiguous spatial coordinates, invalid center indices, invalid quantiles, or
insufficient window data. A failed batch leaves earlier fingerprint-matching
checkpoints intact and does not mark the tile complete. Resume discovers only
complete batches, validates their schema and fingerprint, and recomputes
missing batches. Partial output is never silently interpreted as full coverage.

## Validation and stopping rule

Phase one must demonstrate: exact symmetry, agreement with the old center map,
the audited real PRISM focal values, one real 20 by 20 center block, four focal
stack diagnostics, two contrasting center landscapes, a landscape-change map,
basic reductions, and benchmark/resource estimates. Results then support a
go/no-go choice among exact local neighborhoods, a scientifically justified
approximation, or a stop. No CONUS run begins in this phase.
