# Manuscript evidence and archival requirements

This is the developer evidence companion to the October 12, 2026 manuscript
intake. Main §§5–8 and SI S1, S13–S18 report evidence accessed September 25,
2026. Their release, repository, and submission states are distinct.
This page carries editorial evidence requirements into the website; it does
not grant release approval or assert that missing records were assembled.

## Software states and first use

| State | Establishes | Boundary |
| --- | --- | --- |
| Historical rc1 | First prerelease and outside-user findings | Excludes subsequent repairs |
| Public rc3 | Published artifact reported from `f777eb07d3ada8bd407b027f560727c90f6d3731` | Excludes later `main` and final-release status |
| Later repository | Dated development and bounded analyses | Requires its own exact revision and environment |
| Future final release | Possible archived release after gates | No final DOI or unified archive reported in the supplied manuscripts |

SI S16 records three rc1 first-use findings: an eager optional geospatial
import needed `libexpat.so.1` in the tested Debian/aarch64 Python 3.11 image;
the encountered PRISM path implied unsupported monthly access; Boolean
metadata blocked ordinary NetCDF serialization. Internal regressions report
core import and bounded PRISM operation in that affected image after repair,
while the optional Sentinel-2 path remains unsupported there. This is not a
repeated independent outside-user acceptance exercise for rc3.

The recorded repairs separate core imports from optional compiled dependencies,
default PRISM nouns to daily observations, explicitly reject unsupported monthly
access, and retain NetCDF-safe scalar metadata. Condition export encodes
Boolean variables as flagged int8 in a write-only copy, preserving the
in-memory semantic object. Export does not establish downstream scientific
interpretation. Exact current behavior belongs to runtime and serialization
tests.

## Verification and triage

Implementation verification checks the documented computation. Semantic
consistency tests check agreement among values, dimensions, units, state,
trace, and diagnostics. Neither verifies environmental truth or decision fitness.
The main manuscript describes reference/direct comparisons, properties and
invariants, relations among controlled runs, and expected rejection/regression.
An order-semantics comparison is narrower than a universal correctness oracle.

| Recorded finding | Classification and response |
| --- | --- |
| Condition mean retained Boolean interpretation and averaged definition arrays | Semantic defect: return state-only summary |
| Variance retained original units | Semantic defect: square known units |
| Condition/2D plots did not compose | Implementation defect: semantic/dimension dispatch |
| Overlap returned inconsistent forms | Interface/semantic defect: canonical Dataset |
| Alignment error omitted axis class | Diagnostic defect: distinguish names, time, space |
| Mean then threshold was rejected | Grammar defect: allow both meaningful orders |
| Misaligned overlap rejected | Correct guardrail: retain exact alignment |
| Events after time variation was removed rejected | Correct guardrail: retain rejection |
| Arbitrary random verb chains failed | Test-design issue: generate admissible chains or expected failures |
| Fire data did not overlap event dates | Expected data mismatch: require temporal overlap |
| Optional Lexcube absent | Environment issue: retain optional integration |

This preserves SI Tables S18–S20 and the S2 triage figure's distinction:
repair defects; retain guardrails and improve messages; correct the test,
data, or environment for other issues. See [RC1 triage](rc1_validation_triage.md).

## Claims and evidence boundaries

| Claim from SI Tables S24–S25 | Supporting check family | Limit |
| --- | --- | --- |
| Authored order | Pipe/order regressions | Not all order relations cataloged |
| Both threshold/mean orders | Direct/piped and meaning checks | Results are not equivalent |
| Canonical conditions | Threshold, quantile, overlap, reduction, plot tests | Not every relationship has magnitude/threshold |
| Condition mean is occurrence proportion | State-only direct agreement | Unweighted; missing comparisons false and in denominator |
| Variance units follow statistic | Unit regressions | Unknown remains unknown |
| Invalid event transitions rejected | Expected failures | Rule catalog incomplete |
| Local/regional scopes distinct | Detection, consolidation, metrics | Connectivity remains scientific choice |
| No silent overlap harmonization | Exact-coordinate and support diagnostics | Equality does not establish comparability |
| Nouns retain source | Metadata, fixtures, provenance, QA | Shared name does not establish equivalence |
| Working Lands protocol | Separately reviewed revision and checksum | Submission lacks unified map/records/fixture bundle; branches separate |
| Semantic visualization | Selection/rendering regressions | Optional backend dependent |
| NetCDF retains in-memory semantics | Serialization and first-use gate | Written encoding does not certify downstream use |
| Development evidence exists | Dated internal reports | Submission totals require frozen environment, raw reports, skip list |

These are the manuscript's claim categories, not an exact test manifest.
Source reports, runtime, generated references, and actual test identifiers must
be bound at the chosen submission revision before claiming a unified evaluation.

## Reproduction routes

For the development checkout use Python 3.11, an exact commit, and the
documented developer environment. Public-artifact evaluation needs a separate
installed artifact and import audit; see [runtime identity](../getting_started/runtime_identity.md)
and [release checklist](https://github.com/CU-ESIIL/cubedynamics/blob/main/RELEASING.md).

```bash
python -m pytest -m "not integration and not online" -q
python scripts/run_validation.py --run-vignettes
python scripts/run_source_qa.py
python scripts/run_decision_qa.py
python scripts/build_reference_docs.py --check
python -m mkdocs build --strict
python scripts/check_site_links.py site
python scripts/check_repository_size.py --mode tracked
```

`run_validation.py --run-vignettes` already executes vignettes; the standalone
runner is useful for notebook-only work. The offline filter excludes both
integration and online tests. Validation, source-QA, and decision-QA artifacts
have distinct ignored output roots. Generated-reference freshness and fixture
passes establish neither live health nor broad scientific validity.

## Submission bundle still required

Freeze the exact code revision for each post-rc3 claim, artifact hashes,
operating system and resolved environment, fixture/vignette manifest and
redistribution terms, generated figures, serialized branch and final records,
quantile method, marginal counts and tie diagnostics, raw test identifiers and
results, skip reasons, source-certification timestamps, first-use/serialization
evidence, and contract-to-test mapping. Mark each contract as enforced,
diagnosed, inferred, or documentary. Persistent identifiers and a checksum
manifest should bind the manuscript, evidence, source revision, and tested
release bytes. The intake checksum manifest only identifies the supplied files.

The cross-cutting limitations remain missing-as-false conditions, incomplete
branch lineage, reliance on supplied metadata, unresolved comparability,
callable-specific responsibility, no uncertainty propagation, and aging source
records. Wider synthesis and language-model tool use are aspirations, with no
agent experiment, tool-schema evaluation, or performance improvement reported.

Later synchrony diagnostics are bounded development work, Fire VASE is domain
vocabulary, optional integrations depend on environments/services, and aliases
remain compatibility interfaces. Reserved `correlation_cube` and `fit_model`
names do not establish implemented analyses. The SI proposes isolating or
removing placeholders before a stable release; it is not authorization to
remove compatible exports during documentation intake.

Source: [main, pp. 9–13](../assets/manuscripts/2026-10-12/main-39.pdf#page=9)
and [SI, pp. 20–27](../assets/manuscripts/2026-10-12/supplement-11.pdf#page=20).
