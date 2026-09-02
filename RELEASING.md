# Preparing and publishing a CubeDynamics release

CubeDynamics `0.1.0rc1` is public on PyPI. The current release candidate is
`0.1.0rc2`; it must not be described as public until publication is separately
authorized and confirmed. PyPI files are immutable, so every new candidate or
stable release needs a new committed version and matching tag.

## One release identity

`pyproject.toml` (`[project].version`) is canonical. The runtime mirror in
`src/cubedynamics/version.py`, the active citation files, and `uv.lock` must be
updated in the same reviewed version change. `scripts/release_metadata.py`
requires canonical PEP 440 spelling and derives all active release names:

- tag: `v${VERSION}`
- wheel: `cubedynamics-${VERSION}-py3-none-any.whl`
- sdist: `cubedynamics-${VERSION}.tar.gz`
- gate evidence: `artifacts/release-${VERSION}`
- candidate manifest: `manifests/releases/v${VERSION}-candidate.json`

It never changes the version from a tag. A mismatched tag, runtime mirror, or
noncanonical version is an error. Historical manifests and release notes remain
historical; do not bulk-replace old version strings.

## Maintainer sequence

After scientific and documentation changes are reviewed, update the canonical
version and its active mirrors. For `0.1.0rc2`:

```bash
python scripts/release_metadata.py
python -m pytest tests/test_release_candidate.py tests/test_release_hardening.py tests/test_release_workflow.py -q
git diff --check
```

Review and commit all intended release inputs. From that clean commit:

```bash
python scripts/check_release_source.py
python scripts/run_release_gate.py
```

The gate derives its output directory and distribution names from the project
version. It builds wheel and sdist, writes SHA256SUMS for exactly those two
files, checks both archives, creates a fresh external environment, installs the
exact wheel, runs `pip check`, exercises package-only and external quickstarts,
runs every supported notebook against that wheel, and completes offline,
streaming, publication, source, decision, generated-documentation, strict-site,
link, Chromium, size, and diff checks. It writes a versioned candidate manifest
whose artifact hashes are checked after installed-wheel validation.

When the reviewed release commit and CI are green, create and push the tag:

```bash
git tag -a v0.1.0rc2 -m "CubeDynamics 0.1.0rc2"
git push origin v0.1.0rc2
```

The tag push automatically runs the complete non-publishing gate and the Python
3.9–3.12 compatibility matrix. It does **not** create a release or upload to
PyPI.

## Explicit GitHub or PyPI publication

After the tag-triggered verification is green and publication is authorized:

1. Open **Actions → Prepare or publish a release → Run workflow**.
2. Enter the existing tag, for example `v0.1.0rc2`.
3. Choose `destination=github` or, under separate authorization,
   `destination=pypi`. The default `verify` performs no public write.

A dispatch checks out the selected tag, reruns the complete gate and matrix,
and assembles one release-specific, commit-specific artifact containing the
wheel, sdist, SHA256SUMS, and candidate manifest. Publication jobs download
only that artifact from the **same workflow run**. They rerun
`check_release_source.py` and `verify_release_bundle.py` immediately before the
public write. The verifier rejects branches, missing or extra files, tag/version
or commit mismatches, incomplete gates, wrong filenames, manifest/hash
mismatches, and changed bytes. Therefore the published bytes are exactly the
bytes that passed the gate and matrix in that authorized dispatch; no package
rebuild occurs after testing.

For GitHub, PEP 440 prereleases (`a`, `b`, `rc`, or development prereleases) are
created with `prerelease=true`; stable versions use ordinary release behavior.
The workflow refuses to overwrite an existing GitHub release.

For PyPI, `pypa/gh-action-pypi-publish` uses the existing `pypi` environment and
Trusted Publisher OIDC (`id-token: write`). No token or password is stored or
passed. Verify the PyPI project-side publisher configuration and environment
approval rules before authorizing the run. PyPI releases and uploaded files are
immutable; a correction requires another version.

## Local pre-commit review

The complete gate requires a clean commit. Before the final release commit,
`scripts/prepare_release_snapshot.py` can copy tracked and commit-eligible files
into a temporary local Git repository:

```bash
python scripts/prepare_release_snapshot.py \
  --output artifacts/release-0.1.0rc2/snapshot.json
```

Run the gate in the reported snapshot with a Python 3.11 development/browser
environment. The snapshot commit is local evidence only—not the eventual
public release SHA. The gate must run again on the final reviewed tag.

## Review boundaries

No release command promotes candidate data sources, certifies provider
availability, assigns a DOI, changes scientific support, or authorizes a public
write. Read the [0.1 support contract](docs/project/api_support_0_1.md), the
historical [RC1 notes](docs/project/release_0_1_0.md), and curated records in
`manifests/releases/`. Offline fixture QA is not live-provider certification.
