# Installation & setup

## Current development state — not published

CubeDynamics is preparing its first public release candidate, **0.1.0rc1**.
No CubeDynamics wheel/sdist is currently published on PyPI or attached to the
existing GitHub Releases. A new user cannot yet install a public release.
Do not interpret a green source checkout or a GitHub source ZIP as a tested
package release. Python **3.9–3.12** remains the supported test matrix.

For pre-publication acceptance testing, a maintainer must provide the exact
tested wheel and its SHA256. In a fresh folder outside any source checkout:

```bash
python3.11 -m venv cube-env
source cube-env/bin/activate
python -m pip install --upgrade pip
# First compare this file with the maintainer's SHA256 record.
python -m pip install ./cubedynamics-0.1.0rc1-py3-none-any.whl
python -m pip check
```

On Windows use `cube-env\Scripts\activate`. The wheel installs its
declared dependencies; neither Git nor an editable installation is needed.
If you have not received an artifact, wait for publication rather than
silently switching to a source clone.

## Release candidate install — after GitHub publication

**Future command, unavailable until the v0.1.0rc1 release is published.**
In the fresh environment above, install the wheel asset directly:

```bash
python -m pip install "https://github.com/CU-ESIIL/cubedynamics/releases/download/v0.1.0rc1/cubedynamics-0.1.0rc1-py3-none-any.whl"
python -m pip check
```

The [GitHub Releases page](https://github.com/CU-ESIIL/cubedynamics/releases)
will expose the wheel, `cubedynamics-0.1.0rc1.tar.gz`, and `SHA256SUMS`.
For an explicit checksum check, download those assets and use
`shasum -a 256 -c SHA256SUMS` (macOS) or `sha256sum -c SHA256SUMS` (Linux)
before installing the local wheel. The sdist is for users who need to build;
the wheel is the primary outside-user path.

## PyPI prerelease — after separate PyPI publication

**Future commands; PyPI publication has not occurred.** Once uploaded:

```bash
python -m pip install cubedynamics==0.1.0rc1
# Or opt into the newest prerelease:
python -m pip install --pre cubedynamics
```

Pin `==0.1.0rc1` to reproduce this RC. `--pre` can select a later prerelease.
The [PyPA prerelease specification](https://packaging.python.org/en/latest/specifications/version-specifiers/#handling-of-pre-releases)
explains selection. Package-name availability and trusted publishing must be
confirmed by the maintainer; a missing public project is not a reservation.

## Final release — future only

After a final release is published, `python -m pip install cubedynamics`
will be the ordinary stable-release command. It does not work today.

## Verify and start an analysis

```python
import cubedynamics
from cubedynamics import data, pipe, verbs as v

print(cubedynamics.__version__)  # 0.1.0rc1
print(cubedynamics.__file__)     # your environment's site-packages
print(data.describe("temperature", "prism"))
help(v.mean)
```

Continue to the [Quickstart](../quickstart.md). Its first real-data example
downloads a small, checksum-pinned public PRISM extract into memory;
it does not require repository files or package-internal fixtures. A separate
live noun request explains network and provider limitations.

## Notebook and contributor environments

The `vignettes` extra adds execution tooling and a kernel; JupyterLab is a
separate frontend. To add the extra to a supplied wheel, use
`python -m pip install './cubedynamics-0.1.0rc1-py3-none-any.whl[vignettes]'`.
The canonical HTML viewer does not require Lexcube. Complete supported
notebooks use external reviewed inputs, not bundled package data.

An editable source checkout is only for contributors and full notebook replay;
see the [Learn setup](../learn/index.md#shared-setup) and
[contributing guide](../dev/contributing.md). It is not the primary RC install
or an acceptable fallback for the outside-user package acceptance test.

Read the [RC release notes](../project/release_0_1_0.md) for support boundaries,
candidate adapters, known limitations, and problem reporting.
