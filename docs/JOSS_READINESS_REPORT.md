# CubeDynamics JOSS Readiness Report

## Summary

Audit and implementation dated **October 13, 2026**, based on checkout
`72d862952a78d8c79d259c4b4cd576d0b12e0e9e` plus the readiness changes.
Public rc3 is verified independently from the newer checkout. The five-site
architecture is preserved; the reviewer path uses canonical documentation,
with duplicate manuscript routes consolidated and historical evidence labeled.
This is a readiness assessment, not JOSS acceptance or a new release.

## Critical issues fixed

- Corrected rc1 installation/current-release text in README, home, setup,
  quickstart, runtime identity, changelog and release process. The seminar
  commit pin remains intentional; its false claim that rc3 is unavailable on
  PyPI is removed. Historical rc1/rc2 records and supplied manuscripts remain.
- Verified rc3 tag/attestation source commit and both published artifact hashes.
  A same-numbered later checkout is explicitly a different evidence state.
- Corrected the glossary's false equivalences between co-occurrence and
  synchrony, functions and verbs, and workflow and pipe. Scoped the legacy
  raster/fire CRS contract rather than implying every source shape needs time.
- Made threshold missing-as-false, indexed denominators, numeric NaN mask
  casting on direct invocation (piped continuous fields are rejected), unit
  limitations, unknown support and local branch lineage explicit.
  No scientific runtime behavior was silently changed.
- Dated the retained August validation baseline and stopped presenting it as
  a complete current-release certification.
- Reproduced a fresh-clone failure caused by synchrony-deck tests reading
  ignored research artifacts. Kept the empirical assertions as explicit
  integration checks, added deterministic loader controls and a missing-input
  failure check, and documented the separate research reproduction route.

## Documentation architecture

| Canonical page | Responsibility |
| --- | --- |
| [Scientific inspectability](concepts/scientific_inspectability.md) | Motivation, scientific choices, executable versus appropriate |
| [Semantic grammar](concepts/semantic_grammar.md) | State, trace, implemented/advisory/planned behavior and inspection |
| [Conditions](concepts/condition_contracts.md) | Masks, missingness, reductions, denominators |
| [Data contract](concepts/scientific_data_contract.md) | Dimensions, CRS, support, units, metadata and serialization |
| [Branch provenance](concepts/trace_and_workflow_provenance.md) | Separate branch/callable/environment records |
| [Generated Library](library/index.md) | Source/noun inventory and scientific differences |
| [Source QA](data/phase1_qa.md) | Bounded fixtures/serving contracts; candidate gates separate |
| [Validation methods](validation/methods.md#claim-to-evidence-matrix) | Claim-to-test/fixture/evidence matrix |
| [Reproducibility](reproducibility.md) | Fast, full offline, network and artifact routes |
| [Release identity](project/release_status.md) | Public artifact, development and unselected final JOSS archive |

Related systems are consolidated into one page. Source-comparison, protocol
and design-context companion URLs remain short cross-link routes; original
PDFs and the content map remain manuscript history rather than another API.

## JOSS reviewer path

Homepage → [reviewer guide](joss_review.md) → scientific motivation → implemented
API → install/quickstart → semantic/data contracts → evidence and bounded
Working Lands → reproduce → exact version → citation. No new top-level tab.

## Scientific content migrated

Long-form material now informs canonical motivation, semantic transitions,
order, conditions/denominators, product comparability, branch records,
ecosystem/design tradeoffs and evidence boundaries. Manuscripts remain intact
as dated scholarly products. The Working Lands notebook and acceptance page
own its protocol; no weather screen is recast as drought, stress, impact or risk.

## Validation and evidence

Public rc3 was installed with its dependencies in a fresh Python 3.11
environment on macOS arm64. The wheel and sdist match PyPI hashes; the actual
pinned-data quickstart ran, and dependency compatibility passed. The patched
development checkout passed offline tests, all five validation modules with
twelve notebooks, source/decision QA, reference freshness, strict MkDocs and
internal links. A temporary clean checkout with the readiness patch, excluding
ignored local artifacts, passed **1,029 offline tests, 3 skips** using default
source-before-tests discovery. Four controlled synchrony checks and the two
original empirical integration checks passed in their separate scopes.
The three skips are optional Lexcube, PyVista and Trimesh renderer checks;
their missing-dependency reasons are retained in the local logs.

The final full browser suite passed **445 checks** in two independent groups
(223 and 222), following syntax-highlighting and content changes. Reviewer and
contract pages were inspected at 1440 and 390 px. Fenced-code highlighting is
enabled through Material's bundled extensions. Original scientific figure bytes are unchanged; only the shared
notebook-shell input hash changed in the generated noun-figure manifest.

Local evidence is retained under ignored `artifacts/joss_readiness/`; it must
be curated with the final revision before serving as archival submission
evidence. A local pass does not assert a fresh hosted CI pass or live-source
scientific certification.

Reference generation checked 93 pages; source-lesson and source-project
evidence checks passed. Internal links and repository policy passed, including
new commit-eligible files. The bounded external audit initially found one
not-yet-published test URL, which was replaced with an existing implementation
link, and an Overpass documentation timeout. The final retry checked **81
external links, all available**. This is availability evidence,
not a claim that every provider or external page is continuously reachable.

GitHub's existing Tests run for base `72d8629` failed all four Python offline
jobs; package, clean slim import, streaming and documentation jobs passed, and
Pages deployed successfully. A separate earlier USGS live job failed. Public
job summaries are readable but raw failure logs require authentication.
The clean-checkout defect above is demonstrated locally; its identification
as the hosted traceback's cause remains an inference until that log is read.
No hosted workflow was rerun or new code pushed by this pass.

## Reproducibility

[The canonical commands](reproducibility.md) reproduce development tests,
fixture checks, twelve offline notebooks, source/decision QA, API generation,
strict documentation and browser/link checks. Published rc3 installation uses
a separately downloaded, hashed wheel outside the checkout. Full evidence
reproduction is more extensive than the fast core check; seminar/exploratory
network material remains separately scoped.

## Remaining human decisions

- Select the exact JOSS review revision and decide whether paper claims refer
  to public rc3, later development, or explicitly separated layers. Bind the
  selected evidence/environment and fixture redistribution terms accordingly.
- Review paper authorship/affiliations, funding, impact/community-use evidence,
  build-versus-contribute rationale and AI disclosures. The supplied drafts
  disagree about completed human review and use a prior model-family label;
  this pass cannot attest to author review or invent adoption.
- Confirm sustained public development history with dated evidence. Git commit
  dates and repository creation in November 2025 do not independently prove
  that the repository was public throughout the period required by JOSS.
- Decide whether to revise the paper's within-prose pre-submission directions
  and shorten its approximately 1,400-word body for the requested concise note.
  This count is editorial guidance, not a claimed journal word limit. Supplied collaborator files
  are preserved; the stale directive is not silently converted into a claim.
- Choose a confidential Code of Conduct reporting contact if desired; the
  existing policy currently directs incident reports to public GitHub Issues.

## JOSS readiness

**BLOCKING:** exact final review scope and author verification are unresolved.
If later development claims are submitted as one artifact, their revision and
evidence must first be joined. Missing/branch limitations are disclosed rather
than misrepresented as implemented solutions.

**SHOULD FIX BEFORE SUBMISSION:** finalize the concise paper and the required
design, comparative rationale, impact/community significance and AI statements.
Current [JOSS review criteria](https://joss.readthedocs.io/en/latest/review_criteria.html)
leave scope/significance to editors. The repository has development history
from November 2025, MIT license, CFF metadata, contributions/behavior guidance,
tests/CI, examples and generated API. These signals do not guarantee acceptance.
Obtain a passing hosted Tests run on the selected readiness revision before
submission; the old failed run is not superseded by a local pass. Keep separate
USGS endpoint failures visible as source access evidence rather than treating
them as offline fixture or hydrologic-suitability findings.

**OPTIONAL POLISH:** reconcile the legacy cloud-hosted PyPI README on the next
authorized release; make remaining dated inventories easier to browse. A final
archive DOI is normally supplied after successful review, according to
[JOSS submission guidance](https://joss.readthedocs.io/en/latest/submitting.html#review-process);
no DOI or publication status was fabricated.
