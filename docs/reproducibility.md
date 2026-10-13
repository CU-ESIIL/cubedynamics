# Reproduce the software and evidence

Choose the software state first. [Release identity](project/release_status.md)
separates public rc3 from later development and the pending JOSS archive.
The following commands are for the **development checkout**, Python 3.11,
from the repository root. Checkout an exact reviewed commit before installing,
then record `git rev-parse HEAD`, `git status --short`, Python/platform,
`cubedynamics.version_info()` and resolved dependency versions.

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
python -m pip check
```

Windows activation is `.venv\Scripts\activate`. Package installation needs
network access or a prepared wheelhouse; offline refers to the subsequent
fixture-based analyses. Fixtures and scripts are in Git, deliberately excluded
from distributions. Restart notebook kernels after installing.

## Fast local checks

```bash
python -m pytest tests/test_public_api_smoke.py tests/test_piping_verbs.py tests/test_grammar_semantics.py -q
python scripts/build_reference_docs.py --check
git diff --check
```

These inspect core behavior and reference freshness; they do not reproduce all
scientific QA. [The evidence matrix](validation/methods.md#claim-to-evidence-matrix)
names tests and their boundaries.

## Full offline validation

```bash
python -m pytest -m "not integration and not online" --maxfail=1 --disable-warnings -q
python scripts/run_validation.py --run-vignettes
python scripts/run_source_qa.py
python scripts/run_decision_qa.py
python -m mkdocs build --strict
python scripts/check_site_links.py site
python scripts/check_repository_size.py --mode tracked
```

The validation command executes the twelve supported offline notebooks; run
`python scripts/run_vignettes.py` separately for notebook-only work. Its kernel
uses an inline backend, verifies declared fixture identities and required
plots, and does not rewrite source notebooks. Core/source/decision builders
own their narrative; the seminar and exploratory notebooks have separate
network/environment scopes and are not this offline suite.

Evidence goes to ignored `artifacts/validation/`, `artifacts/source_qa/` and
`artifacts/decision_qa/`. Retain raw logs and reports with the tested revision
before using them as publication evidence. The older assets on the website
remain dated historical results. Missing or mismatched fixtures fail; never
repair an acceptance run by generating replacement measurements or changing
expected hashes. See [fixture provenance](validation/data.md).

For website changes, also run:

```bash
python -m pip install -e ".[browser]"
python -m playwright install chromium
python -m pytest tests/browser -m browser --site-dir site --browser chromium --tracing retain-on-failure --output artifacts/browser/playwright -q
python scripts/check_external_links.py site --crawl-report artifacts/browser/crawl.json
```

On Linux use `python -m playwright install --with-deps chromium`. Internal
links, decoded assets, responsive journeys and viewer interactions are gated;
external availability is advisory. Browser checks are not scientific figure
review. See [CI](dev/ci_testing.md) for platform and workflow scope.

## Network-dependent tests

Online and integration markers are separate; `not integration` alone is not
offline. Use the explicit environment gates described by each online test.
Live source checks use `scripts/run_live_source_certification.py` and candidate
checks use `scripts/check_source_candidates.py`. Inspect each command's help
and budgets before acquisition. Record query, retrieval date, credentials
availability, transport and source revision. A missing token is a blocked
check, and endpoint health is not scientific validity.

Long climate records, remote annual files, terrain tiles, road extraction and
rendering can be expensive. Their bounded tests do not demonstrate nationwide
or many-product scalability. No live refresh is needed to replay retained
fixtures.

The synchrony teaching-deck research checks require the previously acquired
stack/feasibility bundle under ignored `artifacts/`. Run them explicitly with
`python -m pytest tests/test_synchrony_pedagogy.py -m integration -q` when that
bundle is available. Missing inputs fail, and the test does not acquire or
generate substitute research data. Default offline tests exercise its loader
with labeled deterministic controls; they do not reproduce empirical deck
numbers or certify the research bundle.

## Archival and JOSS reproduction

Public artifact reproduction installs the exact hashed wheel outside a source
checkout; development evidence uses the exact corresponding Git revision.
`scripts/check_release_artifact.py`, the wheel-pinned mode of
`scripts/run_vignettes.py`, and [the release gate](https://github.com/CU-ESIIL/cubedynamics/blob/main/RELEASING.md)
audit installed paths and tested artifact bytes. A source test pass cannot
stand in for a wheel test.

The final JOSS evidence selection remains pending. Preserve source/artefact
identity, environment, fixture licenses/hashes, generated figures, branch and
final trace records, raw results and skips, and exact tested claims. See
[archival requirements](project/manuscript_evidence_2026_10.md). Archiving or
publishing a new release requires separate author authorization.
