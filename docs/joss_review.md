# For JOSS reviewers

CubeDynamics adds source-qualified names, ordered transformations, semantic
state and a local trace around ordinary scientific Python objects. It addresses
the difficulty of recovering the analytical question from otherwise rerunnable
environmental code. It does not verify scientific suitability or replace
xarray, Dask, geospatial libraries, or workflow schedulers.

The JOSS software note is a **draft**. The public candidate is rc3, while the
development documentation includes later work. Start with
[exact release and review identity](project/release_status.md); no unified final
JOSS revision has been assigned by this documentation pass.

## Suggested review path

| Question | Canonical documentation |
| --- | --- |
| What is it and why build this layer? | [Scientific inspectability](concepts/scientific_inspectability.md), [related systems](related/related_work.md) |
| What is implemented? | [Public API/support](project/public_api.md), [verbs by purpose](reference/verbs/index.md), [noun library](library/index.md) |
| How do I install and run it? | [Installation](getting_started/install.md), [ten-minute quickstart](quickstart.md) |
| What does a stage mean? | [Semantic model](concepts/semantic_grammar.md) |
| Where can interpretation change? | [Order](learn/order.md), [conditions and missingness](concepts/condition_contracts.md), [scientific data contract](concepts/scientific_data_contract.md) |
| What does the trace leave out? | [Branch and workflow provenance](concepts/trace_and_workflow_provenance.md) |
| What evidence supports a claim? | [Claim-to-evidence matrix](validation/methods.md#claim-to-evidence-matrix), [source QA](data/phase1_qa.md) |
| What does a bounded scientific example show? | [Working Lands notebook](decision_vignettes/working_lands.ipynb), [input/acceptance record](decision_vignettes/validation.md) |
| What are the limits? | [Contract boundaries](concepts/scientific_data_contract.md#where-protection-stops), [public maturity](project/api_support_0_1.md) |
| How do I reproduce it? | [Reproducibility](reproducibility.md) |
| How do I cite/report it? | [Methods and citation](methods_and_citation.md) |

The longer manuscripts remain [dated originals](documentation/overview_manuscript.md).
Their [content map](documentation/manuscript_content_map.md) is an archive
index, not a parallel reference. The runtime and generated references own
current behavior. The repository owns executable tests, fixtures and builders.

## Review and contribution

Use [GitHub Issues](https://github.com/CU-ESIIL/cubedynamics/issues) for problems,
with runtime identity, platform, minimal code and traceback. See
[contributing](dev/contributing.md) and the
[code of conduct](https://github.com/CU-ESIIL/cubedynamics/blob/main/CODE_OF_CONDUCT.md).
The repository includes an MIT license, declared dependencies, tests and CI;
local checks establish only the environment and scope recorded in the
[readiness report](JOSS_READINESS_REPORT.md).
