# Preparing the next CubeDynamics release candidate

CubeDynamics `0.1.0rc1` is public on PyPI and has completed outside-user
validation. This checklist is now for a subsequent candidate. Do not overwrite
or describe a locally rebuilt rc1 wheel as the public rc1 artifact. Update the
target version and every version-bound release record in a separately reviewed
release-management change before publishing the next candidate.

## Non-publishing gate

Use Python 3.11 with development and browser tooling. From a **clean committed
checkout** of the intended release commit:

```bash
python -m pip install -e ".[dev,browser]"
python -m playwright install chromium
python scripts/run_release_gate.py --output artifacts/release-0.1.0rc1
```

The gate refuses dirty sources and mismatched version tags. It builds with
`python -m build`, checks wheel/sdist with Twine and archive inspection,
creates a new external environment, upgrades that environment's pip, installs
only the wheel plus declared dependencies, and runs `pip check`. It validates
package-only grammar, help/discovery, the actual README with an external
reviewed fixture, and the actual no-checkout quickstart using its public pinned
input. Then it adds the vignette extra and runs all twelve supported notebooks
against the exact wheel, auditing imports and file hashes in every kernel.

It also runs offline pytest, streaming contracts, ordinary notebooks,
publication/source/decision QA, generated reference/figure/gallery checks,
strict docs, links/anchors, all Chromium checks, size policy and diff checks.
Build/dependency installation and the public quickstart require network;

scientific fixture QA remains offline. Live provider certification is separate.

The result includes filenames, byte sizes and SHA256s; `dist/SHA256SUMS`
covers exactly the wheel and sdist. Old files elsewhere in `dist/` are not
automatically uploaded. The prepared files are:

- `cubedynamics-0.1.0rc1-py3-none-any.whl`
- `cubedynamics-0.1.0rc1.tar.gz`

For a local pre-commit review, `scripts/prepare_release_snapshot.py --output
artifacts/release-0.1.0rc1/snapshot.json` copies tracked and commit-eligible
inputs to a new temporary Git repository and records a local snapshot commit.
Run the gate there with a development environment installed there. This does
not stage or commit the user's checkout, and **the snapshot is not the eventual
public release SHA**. Re-run on the reviewed release commit before publication.

## Exact artifact check

```bash
python -m twine check dist/cubedynamics-0.1.0rc1-py3-none-any.whl dist/cubedynamics-0.1.0rc1.tar.gz
python scripts/check_release_artifact.py --wheel dist/cubedynamics-0.1.0rc1-py3-none-any.whl --sdist dist/cubedynamics-0.1.0rc1.tar.gz --inspect-only --output artifacts/release-0.1.0rc1/distributions.json
```

Installed-wheel validation must use an external environment's Python with
`-I`, not this checkout's editable environment. Upgrade the fresh environment's
pip before installation: old venv-seeded pip can omit the required archive hash.
Missing SHA256 evidence remains an error; modern and legacy hash formats are
both checked. Runtime viewer templates, serving history, compatibility imports,
and every packaged runtime byte must match. Repository fixtures/tests are
deliberately absent from distributions.

## Publication workflow — explicit authorization only

`.github/workflows/publish.yml` runs the full gate on the selected commit and
then checks the **same wheel** across Python 3.9, 3.10, 3.11 and 3.12. Tag pushes
and a default manual dispatch verify only; they perform no public writes.
Neither a successful gate nor this document authorizes publication.

After a separate maintainer approval:

1. Review/commit the prepared changes, integrate any newer main commits, and
   require the full gate and existing test matrix to pass on that final SHA.
2. Create `v0.1.0rc1` at exactly that SHA. No tag is created by the gate.
3. Dispatch **Prepare or publish a release** on that existing tag with
   `destination=github`. The job refuses branch refs and mismatched tags,
   creates a prerelease, and attaches the tested wheel, sdist and SHA256SUMS.
   It does not overwrite an existing release. Its job-scoped `contents: write`
   token is needed for assets; no repository settings/permissions are changed.
4. Confirm an unauthenticated user can download/install the wheel by the
   [documented command](docs/getting_started/install.md), and rerun the
   independent `cubedynamics_test_user` acceptance test without a clone.
5. Only if separately authorized and PyPI configured, dispatch on the same
   tag with `destination=pypi`. That run also gates its exact
   tested artifacts before upload. Never upload a different local build.
6. After actual availability is confirmed, update the public installation
   status. Keep final-release commands distinct from the RC. Assign a DOI only
   after an archive genuinely issues one; update both citations together.

## PyPI manual configuration still remains to be verified

The code uses PyPI trusted publishing (`id-token: write`), not an API token.
No PyPI credentials, name reservation, or account-side publisher configuration
has been demonstrated here. Public JSON returning 404 does not prove the name
can be registered.

For a first project, an authorized PyPI maintainer must set up a
[pending trusted publisher](https://docs.pypi.org/trusted-publishers/creating-a-project-through-oidc/)
with these exact values:

| Field | Value |
| --- | --- |
| PyPI project | `cubedynamics` |
| Repository owner | `CU-ESIIL` |
| Repository | `cubedynamics` |
| Workflow filename | `publish.yml` |
| GitHub environment | `pypi` |

Verify that the repository's existing `pypi` environment and its tag/approval
rules permit the approved run. No secrets, environments, branch protection or
permissions are changed by this preparation. A pending publisher does not
reserve a name or prove an upload will succeed; see
[PyPI trusted-publisher instructions](https://docs.pypi.org/trusted-publishers/adding-a-publisher/).

After successful PyPI publication only, outside users can run:

```bash
python -m pip install cubedynamics==0.1.0rc1
# Unpinned alternative that also admits later prereleases:
python -m pip install --pre cubedynamics
```

## Review boundaries

Read [RC notes](docs/project/release_0_1_0.md),
[0.1 support](docs/project/api_support_0_1.md), and the curated records in
`manifests/releases/`. Historical 0.1.0 evidence does not validate 0.1.0rc1.
Report actual Python/platform runs separately from configured Linux CI targets.
USGS, 3DEP, Overture and OSM remain candidates; Daymet remains BLOCKED.
Offline fixture passes do not certify live providers or scientific suitability.
