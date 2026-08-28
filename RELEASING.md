# Preparing a CubeDynamics release candidate

Target: **0.1.0, first public alpha**. A green checkout is not an artifact test.
Nothing in this checklist tags, publishes, changes permissions or promotes sources.
Publishing and DOI archival require a separate explicit maintainer decision.

## Candidate gate

Use Python 3.11 and a development environment with browser tooling installed:

```bash
python -m pip install -e ".[dev,browser]"
python -m playwright install chromium
python scripts/run_release_gate.py --output artifacts/release-0.1.0
```

The gate builds wheel and sdist, runs Twine and archive-content checks, creates
a new virtual environment outside the checkout, installs only the wheel and
declared dependencies, tests the package-only grammar, and then adds the
documented vignette extra. It checks the actual README example against
external reviewed PRISM input and all twelve notebooks against that wheel.
Each notebook kernel uses an explicit isolated Python and verifies installed
package paths, file bytes, version and wheel SHA before and after execution.

It also runs offline pytest, streaming contracts, ordinary vignette execution,
publication/source/decision QA, generated-content checks, strict MkDocs,
internal links, the Chromium browser suite, and repository-size checks.
Distribution builds and fresh dependency installation need network access;
scientific examples are offline. Reports preserve command exit codes and logs.

For a focused manual artifact check after `python -m build`:

```bash
python -m twine check dist/*
python scripts/check_release_artifact.py \
  --wheel dist/cubedynamics-0.1.0-py3-none-any.whl \
  --sdist dist/cubedynamics-0.1.0.tar.gz --inspect-only \
  --output artifacts/release-0.1.0/distributions.json
```

Using an already installed, external wheel environment (replace the example
absolute Python path; do not use the checkout's editable `.venv`):

```bash
/absolute/wheel-env/bin/python -I scripts/check_release_artifact.py \
  --wheel dist/cubedynamics-0.1.0-py3-none-any.whl --repo-example \
  --output artifacts/release-0.1.0/installed-example.json
python scripts/run_vignettes.py \
  --wheel dist/cubedynamics-0.1.0-py3-none-any.whl \
  --kernel-python /absolute/wheel-env/bin/python \
  --output-dir artifacts/release-0.1.0/wheel-notebooks
```

The `.ipynb` sources and reviewed fixtures stay in Git, not the distributions.
The package-only smoke intentionally uses a tiny deterministic unit input;
the scientist-facing README and notebook checks use real observations.

## Review before any tag

- Synchronize pyproject/runtime version and both CITATION.cff copies; inspect
  README, [release notes](docs/project/release_0_1_0.md), and
  [0.1 support contract](docs/project/api_support_0_1.md).
- Confirm wheel/sdist hashes, exact tested source snapshot, actual Python
  versions and resolved dependencies. Configured CI versions are not observed
  results; rerun the gate after packaging/runtime changes.
- Review the curated record under `manifests/releases/`. A dirty-tree record
  names the base commit and hashes the overlay; it is not a release commit.
- Keep USGS, 3DEP, Overture and OSM as candidates, and Daymet BLOCKED, unless a
  separately reviewed promotion explicitly changes that state.
- Keep DOI absent until an archive assigns one. No invented release date.
- Never upload `dist/*` blindly when it also contains old artifacts or a site.

## Separate future publication decision

Commit and review the changes first. An eventual `0.1.0rc1` package requires a
deliberate version update and new validation, not relabeling a `0.1.0` wheel.
The existing publishing workflow can publish on `v*` tags or manual dispatch;
do not trigger it during preparation. Only after explicit approval should a
maintainer create a tag/release, publish, archive, and synchronize the assigned
DOI in both citation files. Branch protection remains the maintainer's choice.
