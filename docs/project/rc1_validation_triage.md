# RC1 comprehensive validation triage

This table classifies the apparent failures recorded by the external
`cubedynamics==0.1.0rc1` black-box validation. It separates defects from
scientifically useful rejection and from problems in the validation design.
The classification was written before this maintainer pass changed runtime
code.

| Finding | Classification | Maintainer determination |
| --- | --- | --- |
| A. A condition followed by `mean` retains condition/Boolean metadata and generically averages `magnitude` and `threshold` | **REAL DEFECT** | A condition mean is an occurrence proportion summary. Generic averaging of the auxiliary fields has no declared scientific meaning. The canonical reduction should return a summary Dataset whose `state` is the reduced proportion; condition-definition metadata remains inspectable. |
| B. Variance retains source units such as `degC` | **REAL DEFECT** | Variance units must be squared in both xarray attrs and semantic state. Missing and explicitly unknown units must remain missing/unknown rather than being fabricated. |
| C1. `v.plot()` rejects the canonical condition Dataset | **REAL DEFECT** | Grammar and implementation disagree. A condition Dataset has a canonical `state` variable and should render it by default. |
| C2. A condition-frequency Dataset cannot be plotted naturally | **REAL DEFECT** | This is the combined consequence of A and C1. The state proportion should remain a canonical, directly renderable field. |
| C3. A 2-D continuous summary constructs a `CubePlot` but fails in `_repr_html_()` | **REAL DEFECT** | Dimensional support must be validated and selected before returning a viewer. A spatial summary should use a real 2-D map renderer; a temporal vector should use a line renderer. |
| D. Lexcube is absent from a core installation | **OPTIONAL DEPENDENCY / ENVIRONMENT** | Lexcube correctly remains outside core dependencies. CubeDynamics must translate the raw import failure into installation guidance for the `viz` extra. |
| E. Conditions have incompatible DataArray/Dataset representations | **REAL DEFECT** | Canonical conditions are Datasets exposing `state`. Threshold conditions may also expose meaningful `magnitude` and `threshold`; Boolean overlap has no meaningful magnitude or threshold and should expose only `state` plus operand/alignment metadata. |
| F1. Overlap rejects shifted spatial or temporal coordinates | **CORRECT SEMANTIC GUARDRAIL** | Exact alignment is a scientific invariant and must remain enforced. |
| F2. A shifted-time input is reported as a dimension-order mismatch | **REAL DEFECT** | Dataset dimension-map order is not reliable evidence of selected-variable order. Runtime diagnostics must identify temporal coordinates, spatial coordinates, or dimension names accurately; harmless axis order can be normalized. |
| G. Many unconstrained random verb strings fail | **TEST DESIGN ISSUE** | Exception count is not a grammar quality metric. Registry-derived legal paths should succeed and known illegal transitions should be rejected with semantic guidance. |
| H. `mean(...)` followed by `threshold_state(...)` was rejected | **REAL DEFECT** | The manuscript-facing order lesson already teaches both orders as distinct scientific questions. The broader grammar is therefore the repository-consistent design: summaries may be thresholded, producing a new condition and an `ORDER_CHANGES_MEANING` note. |
| I. Fire environmental attachment receives a climate cube outside the fire dates | **EXPECTED DATA / TEMPORAL MISMATCH** | No-overlap rejection is correct. The error should report both ranges, and an overlapping multi-variable regression should prove the positive path. |
| J. The release routes a documented cube-first `FireEventDaily` call to a legacy error | **REAL DEFECT** | The current checkout already binds `v.fire_plot` to the canonical cube-first implementation, unlike the tested release. Preserve compatibility for `fired_daily`/`event_id`, but document `FireEventDaily -> FireHull -> attach_environment -> plot` as the object path and `v.fire_plot(cube, fired_event=...)` as the high-level convenience path. |

## Preserved validation baselines

The successful advertised live noun/source matrix, missing-value handling,
Dask laziness, unwrap/repipe interoperability, event detection, flattening,
and custom `apply` behavior are regression constraints. They are not failures
and are not reclassified to make this table look more favorable.

## Canonical decisions for this pass

- A condition is an xarray Dataset with a Boolean `state` variable. Threshold
  and quantile conditions additionally carry scientifically defined
  `magnitude` and `threshold` variables.
- `condition | mean(...)` returns a summary Dataset containing the reduced
  floating-point `state` proportion. It does not implicitly average auxiliary
  condition fields. Users may select and reduce `magnitude` explicitly when
  that is their stated scientific question.
- `overlap` returns a condition Dataset containing only Boolean `state`, with
  exact-alignment and left/right operand metadata.
- `mean | threshold_state` remains supported because current educational
  material treats it as a valid, order-sensitive scientific expression.
- General `v.plot` dispatches by selected DataArray shape: an interactive cube
  for 3-D time-space data, a static spatial map for 2-D data, and a line plot
  for a 1-D temporal field. Other shapes fail before a viewer is returned.
- Fire geometry, climate attribution, and rendering remain separate:
  `FireEventDaily.to_hull()`, `FireHull.attach_environment(...)`, and
  `FireHull.plot(...)` are the preferred object path; `v.fire_plot` is the
  cube-first high-level convenience path. The older fire-first keywords remain
  compatibility inputs, not the preferred teaching route.

## Implemented resolution

- Result attrs, semantic state, trace, and `explain()` now agree for reductions,
  anomalies, z-scores, conditions, and overlaps. Condition means expose only a
  floating `state` proportion; variance units are squared deterministically.
- `v.plot()` selects canonical condition/event fields and dispatches 3-D cubes,
  2-D spatial maps, and 1-D temporal lines before returning a notebook object.
- Exact overlap alignment remains mandatory, with separate temporal, spatial,
  dimension-name, and harmless-axis-order behavior.
- Missing Lexcube raises install/restart guidance for `cubedynamics[viz]`.
- `FireHull.plot()` can inspect geometry colored by event day without inventing
  climate. Environmental colors require an attached or supplied overlapping
  cube, and mismatches report both time ranges.
- `v.fire_plot(cube, fired_event=event)` is regression-tested as the public
  high-level route; compatibility inputs remain available.

The public `0.1.0rc1` artifact predates these fixes. Release-management must
assign and review the next candidate version before publication; this triage
does not overwrite, upload, tag, or republish rc1.

## 2026-09-01 naive-user first-use follow-up

An independent clean-environment run found three additional P0 blockers that
the broad semantic suite did not exercise:

| Finding | Root cause | Resolution and acceptance boundary |
| --- | --- | --- |
| Core wheel import failed on Debian 13/aarch64 with `libexpat.so.1` missing | `cubedynamics.data.sentinel2` eagerly imported Cubo; Cubo imported Rasterio; Rasterio 1.4.4's aarch64 wheel loaded bundled GDAL that retained an unresolved `libexpat.so.1` dependency. | Sentinel/Cubo loading is deferred until the Sentinel source is called. A `python:3.11-slim` x86_64/aarch64 installed-wheel job blocks Cubo/Rasterio/Rioxarray and proves the core public import and first-use path remain usable. This does not certify Sentinel-2 on a system with a broken Rasterio runtime. |
| Ordinary NetCDF export rejected `is_synthetic=False` | h5netcdf rejects Boolean attributes, while provenance and noun normalization emitted Python/NumPy Boolean metadata. NetCDF also has no native Boolean variable type for semantic state. | Public source metadata uses portable scalar encodings. The explicit output verb applies canonical JSON/scalar attribute encoding and writes Boolean variables as flagged `int8` on a shallow copy. Unsupported opaque objects fail clearly; metadata is never silently dropped. |
| The first-discovered PRISM example selected monthly semantics | The modern public loader inherited the legacy positional default `time_res="ME"`, while the maintained real NcSS path supports daily requests only; duplicated old getting-started pages omitted `freq`. | Modern keyword calls default to daily and reject other frequencies before provider access. Current examples state `freq="D"`, old first-use URLs are labeled compatibility bridges, and a bounded live script executes the maintained PRISM request in online CI. |

The installed-wheel gate now covers import, noun/source discovery, composition,
semantic explanation/validation/trace, dimensional plotting, unwrap, direct
continuous export, and condition-safe export. The checksum-pinned external
quickstart independently supplies real PRISM retrieval; the online PRISM check
is availability evidence, not scientific certification.
