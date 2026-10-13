---
description: "How CubeDynamics runs reproducible publication QA locally and in continuous integration."
---

# Validation methods

The suite has five modules—data, grammar, cube, vignettes, and contrasts—and a
single runner: `scripts/run_validation.py`.

Each module writes:

- `result.json`, containing named boolean acceptance checks;
- `diagnostic.png`, a human-inspectable view of the evidence; and
- a PASS or FAIL state consumed by the suite manifest.

The runner also writes `suite_manifest.json` and `validation_report.pdf`.
Failures raise immediately and produce a nonzero command exit. CI runs the
suite with `--run-vignettes`, so a notebook execution failure, missing plot,
data mismatch, grammar mismatch, or rendering mismatch blocks publication.

## Vignette contract

All supported core and source notebooks must:

- declare an explicitly supported real input and its provenance JSON in notebook metadata;
- pass SHA-256 checks for the NetCDF input or every retained USGS response/request record;
- run offline without credentials or private paths;
- contain no random data generation;
- use the public `pipe` and verb API; and
- emit at least one static plot.

The first lesson additionally embeds the repository-native interactive viewer.
Website figures and locally executed notebooks therefore come from the same
source cells and same real observations.

The eight core lessons retain the PRISM input. Streamflow uses three real USGS
response snapshots; elevation and roads use serialized native 3DEP and
Overture/OSM extracts with hashes. Unknown input/provenance combinations are
rejected, not accepted because a notebook claims to use real data. The runner
also executes the supported Decision Lab notebook, for twelve offline notebooks
in total; [Decision Lab QA](../decision_vignettes/validation.md) checks its inputs.
Notebook output is retained in `artifacts/validation/notebook-execution.log`.

The gate also scans the primary vignette, synchrony, Fire VASE, workflow, and
recipe entry pages so they do not promote generated cubes, generated fires, or
the old demo-only routes. Historical generated recipe sources and assets remain
available to software maintainers but are explicitly excluded from the MkDocs
publication build.

## Claim-to-evidence matrix

This matrix links software claims to executable checks. Test links identify
files; named cases identify checks within them. Development results apply to
the checkout/patch state recorded in the [readiness report](../JOSS_READINESS_REPORT.md),
not automatically to public rc3. [Release identity](../project/release_status.md)
separates those states. The retained August baseline has no exact Git binding.

| Claim and scope | Test or method and input | Expected result | Evidence and limit |
| --- | --- | --- | --- |
| Authored execution order | `test_pipe_executes_each_callable_once_in_exact_written_order`, fixed callables | Each stage once in written order | [Grammar tests](https://github.com/CU-ESIIL/cubedynamics/blob/main/tests/test_grammar_semantics.py); later Dask graph evaluation is separate |
| Threshold/mean changes the question | `test_threshold_then_mean_is_a_prevalence_summary_with_truthful_metadata`, `test_mean_then_threshold_is_allowed_and_defines_aggregate_condition`; fixed arrays | Fraction summary versus aggregate condition | [Grammar tests](https://github.com/CU-ESIIL/cubedynamics/blob/main/tests/test_grammar_semantics.py); not selection of scientifically correct order |
| Local state and trace | `test_semantic_trace_records_state_transitions_and_order_note` | Ordered transitions and meaning note | [Grammar tests](https://github.com/CU-ESIIL/cubedynamics/blob/main/tests/test_grammar_semantics.py); no complete branch/external lineage |
| Advisory metadata inspection | `test_suggestions_are_small_compatible_and_implemented`, `test_validation_report_is_structured_and_readable` | Implemented suggestions and structured report | [Grammar tests](https://github.com/CU-ESIIL/cubedynamics/blob/main/tests/test_grammar_semantics.py); no source/scientific certification |
| Condition denominator and mask cast | Documentation example, `[2, NaN, 4]` | Threshold `[false,false,true]`, indexed `1/3`, valid-only `1/2`; direct binary NaN casts true; pipe rejects continuous input | `tests/test_joss_documentation_contracts.py` in the readiness patch and [state implementation](https://github.com/CU-ESIIL/cubedynamics/blob/main/src/cubedynamics/synchrony/states.py); deterministic control, not weather measurements |
| Temporal support differs from labels | `test_overlap_requires_choice_for_exact_labels_but_different_support`, `test_overlap_unknown_support_proceeds_with_visible_check` | Known mismatch needs policy; unknown is visible | [Temporal tests](https://github.com/CU-ESIIL/cubedynamics/blob/main/tests/test_temporal_support.py); no equivalence or harmonization |
| Export preserves in-memory condition | `test_safe_export_encodes_boolean_condition_without_mutating_it` | Flagged int8 file; Boolean memory value unchanged | [First-use tests](https://github.com/CU-ESIIL/cubedynamics/blob/main/tests/test_first_use_acceptance.py); downstream interpretation not certified |
| Units/metadata follow statistic | Fixed-array variance/summary regressions | Known units squared, state-only proportion | [Hardening tests](https://github.com/CU-ESIIL/cubedynamics/blob/main/tests/test_release_hardening.py); not complete unit algebra |
| Adapter access contracts | Mock transport/engine cases | Supported signatures, lazy construction, defined retrieval seams | [PRISM tests](https://github.com/CU-ESIIL/cubedynamics/blob/main/tests/test_prism_ncss_streaming.py), [gridMET tests](https://github.com/CU-ESIIL/cubedynamics/blob/main/tests/test_gridmet_streaming_contract.py); not current endpoint health |
| Source QA on real retained bytes | `test_source_qa_writes_real_data_evidence`; PRISM/gridMET/Sentinel-2 fixtures | Hashes, structure and physical checks | [QA tests](https://github.com/CU-ESIIL/cubedynamics/blob/main/tests/test_source_qa.py), [source records](../data/phase1_qa.md); bounded products/places/dates, no general source equivalence |
| Working Lands screen | `test_working_lands_fixture_matches_provenance_and_physics`, `test_working_lands_pipeline_uses_current_public_apis` | Frozen inputs and direct/piped agreement | [Decision tests](https://github.com/CU-ESIIL/cubedynamics/blob/main/tests/test_decision_vignettes.py), [fixture record](../decision_vignettes/validation.md); no drought, risk or impact inference |
| Notebook execution | `run_validation.py --run-vignettes`; twelve supported real-data notebooks | Checked inputs and required inline plots | [Runner](https://github.com/CU-ESIIL/cubedynamics/blob/main/scripts/run_vignettes.py), [catalog tests](https://github.com/CU-ESIIL/cubedynamics/blob/main/tests/test_vignette_catalog.py); live seminar/exploratory notebooks excluded |
| Public rc3 installation | Fresh Python 3.11 environment, PyPI-hashed wheel, pinned public PRISM quickstart | External import, explanation, trace and finite result | Local `artifacts/joss_readiness/public-install.json` and `public-quickstart.log`; one platform, not every later development claim |

[Data validation](data.md), [source QA](../data/phase1_qa.md), and
[decision validation](../decision_vignettes/validation.md) own exact fixture
identities and acceptance criteria. Fresh raw reports remain outside Git
until curated and bound to the chosen submission revision. Tests demonstrate
software contracts, not independent validation of provider observations.

## What remains generated

Deterministic arrays remain appropriate inside unit tests and negative controls
because their exact truth is known. They are excluded from the publication
vignettes and are not presented as scientific evidence. This boundary keeps
software regression tests rigorous without confusing learners about the source
of the educational data.
