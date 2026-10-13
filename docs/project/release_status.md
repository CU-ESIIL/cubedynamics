# Release identity and review scope

Verified **October 13, 2026** against [PyPI release files and attestation](https://pypi.org/project/cubedynamics/0.1.0rc3/),
the PyPI JSON API, local tags, package metadata, and runtime version metadata.

| Layer | Exact identity | What it covers |
| --- | --- | --- |
| Current public software | `cubedynamics==0.1.0rc3`, alpha prerelease, published September 2, 2026 | Immutable wheel and sdist |
| Release source | `v0.1.0rc3` resolves to `f777eb07d3ada8bd407b027f560727c90f6d3731` | Matches PyPI's source attestation |
| Development documentation | Later checkout also declares rc3; record full Git SHA and dirty state | Later tests/features are not retroactively included in the published wheel |
| JOSS draft | `paper/joss/2026-10-12/paper.md` | Names public rc3 and separately reviewed Working Lands revision; not accepted or published |
| Final JOSS review/archive | **Not yet selected** | Author must choose the reviewed revision and bind paper, code, environment, inputs and reports |
| Historical material | rc1, rc2, dated audits and manuscript PDFs | Development history, not current installation guidance |

The absence of a final archive DOI is not a fabricated publication blocker:
[JOSS assigns the archive step after successful review](https://joss.readthedocs.io/en/latest/submitting.html#review-process).
An exact source revision and reproducible evidence scope must nevertheless be
clear during review. No final stable release or accepted-paper DOI is claimed.

## Published bytes

| File | SHA-256 |
| --- | --- |
| `cubedynamics-0.1.0rc3-py3-none-any.whl` | `319ca84f5354ebdd71f360f3fe7c888a4437f439b5cca6fe53b399c8b67ab7f6` |
| `cubedynamics-0.1.0rc3.tar.gz` | `6ed0cccefa211297ef03fb8d4f38e2f7c7bdd6234a3190da4226ad4269755928` |

The readiness check downloaded both files and verified these hashes against
PyPI metadata. The project description embedded on PyPI still contains older
rc1 installation text; file/version metadata and attestations establish actual
publication. Fixing repository text cannot rewrite an immutable uploaded README.

## Installation choices

For the verified public candidate:

```bash
python -m pip install cubedynamics==0.1.0rc3
```

For its exact source (including checkout fixtures and scripts):

```bash
git clone https://github.com/CU-ESIIL/cubedynamics.git
cd cubedynamics
git checkout --detach f777eb07d3ada8bd407b027f560727c90f6d3731
python -m pip install -e ".[dev]"
```

Run the commands available at that revision. Later documentation instructions
must not imply that newer tests, adapters or analyses existed at this commit.
For current development reproduction, substitute the full reviewed development
SHA and use [reproducibility](../reproducibility.md). Do not install mutable
`main` while claiming exact artifact reproduction.

Record `cubedynamics.version_info()` in every analysis. Semantic version alone
cannot identify a checkout, installed wheel, or stale notebook import. See
[runtime identity](../getting_started/runtime_identity.md).
