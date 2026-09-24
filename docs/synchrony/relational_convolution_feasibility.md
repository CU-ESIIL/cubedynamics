# Relational-convolution feasibility experiment

## Scope and status

This note defines a bounded experiment, not a production CubeDynamics API. The
working phrase *relational convolution* describes the translation of the same
pairwise climate-synchrony operation across a grid. It does not imply a fixed
kernel, learned filter, optimization objective, or convolutional neural
network.

The experiment asks whether overlapping local synchrony surfaces contain
geographically coherent information that is lost when each surface is reduced
independently. It must allow the answer to be no.

## Repository audit

The current checkout already provides:

- the validated conditional Spearman calculation in
  `cubedynamics.stats.tails.one_tail_spearman`;
- dense moving-center stacks in `synchrony.local_synchrony_stack` and canonical
  undirected pair tables in `synchrony.local_synchrony_pairs`;
- exact endpoint symmetry, signed displacement, distance, bearing, and
  tile/halo checkpoint contracts in `synchrony.production`;
- reconstruction of a complete `S_p(dx,dy)` surface plus fine radial,
  radially-adjusted angular, low-order 2-D, and surface-shape diagnostics in
  `synchrony.surfaces`;
- median, IQR, MAD, nested-radius, direction, and coverage summaries in the
  stack and Phase 2 signature implementations;
- adjacent-center landscape change in `landscape_change_signature`, which
  compares full center landscapes but does not yet contrast relative with
  absolute geographic alignment;
- the Phase 2 held-out PCA/SVD experiment and reconstruction comparisons in
  `scripts/analyze_synchrony_surfaces_phase2.py`;
- restartable PRISM acquisition and production tiling with spatial halos;
- exact real PRISM artifacts for 2023-11-01 through 2024-01-30, including the
  400-center by 20 by 20 Front Range stack and the statewide 100 km signature.

No current implementation builds an absolute-geography overlap-support object,
compares relative-coordinate with geographic alignment, or tests translated
edge gradients against smoothing across controlled synthetic fields. The word
"overlap" elsewhere in the package refers either to Boolean temporal-state
intersection or to ordinary shared support, not this experiment.

## Experiment added here

The primary real-data experiment reuses the exact 20 by 20 Phase 1 PRISM stack.
It contains 400 complete local landscapes and 160,000 directed surface entries
from 80,200 canonical pairs. This is the smallest existing real artifact with
many contiguous overlapping surfaces and complete inspectability. Observation
windows of 20, 40, and 60 km are practical for this block; support and edge
censoring are reported explicitly. The statewide 100 km products remain
context and are not recomputed.

For each metric (cold, warm, and Delta), the experiment produces:

1. a long, inspectable relationship table with focal and comparison absolute
   coordinates, relative offsets, distance, bearing, valid counts, and a
   canonical pair identifier;
2. an absolute-location support table retaining contributor identities and
   all values before reduction;
3. neighboring-surface similarity in both relative coordinates and shared
   absolute geography;
4. absolute edge-gradient support with signed differences, sign agreement,
   robust dispersion, and contribution counts;
5. overlap-coherence, translated-gradient, focal-surface-change, and
   transition candidates kept as separate diagnostics;
6. the existing independent-surface reductions and a held-out PCA/SVD
   comparison;
7. ten labeled synthetic cases, null replications, and observation-window
   sensitivity; and
8. a frozen-method station feasibility branch using quality-controlled
   GHCN-Daily observations and PRISM values sampled at station locations.

## Objects and coordinate systems

Let `X(p,t)` be a daily temperature series at geographic cell `p`, and let `f`
be the validated conditional synchrony operator. The unreduced object is

```text
S(p, delta) = f(X(p,t), X(p + delta,t))
S(x,y,dx,dy) = {S_cold, S_warm, S_cold - S_warm, valid_n}
```

Relative coordinates `(dx,dy)` describe surface shape around the focal cell.
Absolute coordinates map the same entry to comparison cell `q = p + delta`.
For adjacent focal cells `p` and `p'`, relative alignment compares
`S(p,delta)` with `S(p',delta)`, while geographic alignment compares
`S(p,q)` with `S(p',q)` at the same absolute `q`. Neither comparison is assumed
to be preferable in advance.

The absolute edge object is also retained. For a geographic neighbor edge
`e=(q_1,q_2)` and focal cell `p`,

```text
G(p,e) = S(p,q_2) - S(p,q_1).
```

Agreement among different focal cells about `G(p,e)` is translated-gradient
evidence at a known location. Distance remains an observed coordinate. No
exponential, Gaussian, monotonic, or other fixed decay law is fitted.

Every directed surface entry carries `canonical_pair_id=min(p,q),max(p,q)`.
The reverse endpoint view of one pair is mathematical symmetry, not independent
evidence. Reports therefore distinguish directed entries, unique canonical
pairs, unique focal contributors, and geographic edges. Transition support is
formed from different pair combinations sharing an absolute edge; reverse
copies are never counted as replicate evidence.

## Baselines and candidates

Independent-surface baselines are median, median plus IQR/MAD, nested radii,
fine radial profile, radial plus direction, PCA/SVD, and existing landscape
change. A naive spatially smoothed median map is the required non-relational
baseline.

Experimental candidates are intentionally plural:

- **overlap coherence:** robust agreement of distinct focal contributions at
  the same absolute location;
- **translated gradient:** sign and vector agreement for the same absolute
  geographic edge across focal surfaces;
- **surface change:** the change in the full relational surface as the focal
  cell moves, reported separately for relative and absolute alignment;
- **transition evidence:** repeated, distance-stratified signed change at a
  common absolute edge; this is one candidate, not an assumed boundary map.

No learned model is required. PCA/SVD is tested first. An autoencoder is added
only if PCA leaves a clear, decision-relevant gap and the existing dependency
policy supports it.

## Decision criteria

The hypothesis receives support only if all of the following are observed:

- geographic alignment improves coherence or prediction over relative
  alignment in real data and in synthetic cases where fixed geography should
  matter;
- a candidate distinguishes transition, gradient, anisotropy, distance-only,
  nonmonotonic, varying-distance, uniform, and noise cases without a fixed
  distance-decay law;
- the gain is not reproduced by smoothing an independently reduced median map;
- conclusions survive practical changes in the maximum observation window and
  are not confined to edge-censored cells;
- canonical-pair reversal is not treated as replicate support; and
- the added scientific information is material enough to justify storage and
  computation beyond radial plus directional summaries.

Candidate statuses are `KEEP`, `KEEP AS DIAGNOSTIC`, `EXPERIMENTAL`, or `DROP`.
A result can recommend no production relational-convolution verb.

## Explicit non-goals

This work does not run Colorado or CONUS through a second-stage model, infer
climate regions, declare boundaries, choose a universal radius or decay law,
train a large neural network, tune methods to stations, or expose a new public
verb. It does not alter validated cold/warm synchrony semantics. GHCN-Daily
stations are an external evaluation target, but because PRISM uses station
observations, contribution status is `UNKNOWN` unless product-period evidence
establishes `PRISM INPUT` or `APPARENTLY INDEPENDENT`.

## External-observation rules

GHCN-Daily temperature values with nonblank quality flags are excluded and all
measurement, quality, source, and observation-time attributes are retained.
Station thresholds are calculated from station observations, never from PRISM.
The PRISM daily product uses a 1200-1200 UTC day-ending convention, whereas a
GHCN-Daily observation is associated with local station observation time when
reported. Same-label and +/- one-day sensitivity are reported; no silent date
shift is made. Pair-level results remain descriptive because edges share
stations and are not independent observations.

## Reproduction boundary

The experiment is run by a dedicated script under `scripts/` and writes to
`artifacts/relational-convolution-feasibility/`; its report is written under
`output/pdf/`. Network retrieval is a separate explicit step with cached raw
NOAA responses and checksums. Offline synthetic and existing-PRISM analyses can
be rerun without network access.
