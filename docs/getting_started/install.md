# Installation & setup

## Public release candidate

CubeDynamics **0.1.0rc1** is published on PyPI. It is an alpha prerelease, not
a final stable release. Do not interpret a green source checkout as evidence
that the public artifact contains later changes. Python **3.9–3.12** remains
the supported test matrix.

For reproducible acceptance testing, pin the public version in a fresh folder
outside any source checkout:

```bash
python3.11 -m venv cube-env
source cube-env/bin/activate
python -m pip install --upgrade pip
python -m pip install cubedynamics==0.1.0rc1
python -m pip check
```

On Windows use `cube-env\Scripts\activate`. The wheel installs its
declared dependencies; neither Git nor an editable installation is needed.
If you have not received an artifact, wait for publication rather than
silently switching to a source clone.

## Artifact-specific install

When reproducing a maintainer-supplied candidate artifact rather than the
public rc1, compare its SHA256 record and install that exact local wheel:

```bash
python -m pip install ./cubedynamics-0.1.0rc1-py3-none-any.whl
python -m pip check
```

The local wheel path is for an explicitly supplied artifact; do not silently
substitute a source clone. The PyPI release page exposes hashes for its public
wheel and sdist.

## PyPI prerelease

```bash
python -m pip install cubedynamics==0.1.0rc1
# Or opt into the newest prerelease:
python -m pip install --pre cubedynamics
```

Pin `==0.1.0rc1` to reproduce this RC. `--pre` can select a later prerelease.
The [PyPA prerelease specification](https://packaging.python.org/en/latest/specifications/version-specifiers/#handling-of-pre-releases)
explains selection. Package-name availability and trusted publishing must be
confirmed by the maintainer; a missing public project is not a reservation.

## Final release

After a final stable release is published, `python -m pip install cubedynamics`
will be the ordinary stable-release command. Until then, pin or opt into a
prerelease explicitly.

## Verify and start an analysis

```python
import cubedynamics
from cubedynamics import data, pipe, verbs as v

print(cubedynamics.__version__)  # 0.1.0rc1
print(cubedynamics.version_info())
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

Lexcube is a separate optional notebook widget. Add it only when you need
`v.show_cube_lexcube()`:

```bash
python -m pip install "cubedynamics[viz]"
```

Restart the notebook kernel after installation. Without the extra,
`v.show_cube_lexcube()` raises a CubeDynamics error with this guidance rather
than exposing a raw `ModuleNotFoundError`.

An editable source checkout is only for contributors and full notebook replay;
see the [Learn setup](../learn/index.md#shared-setup) and
[contributing guide](../dev/contributing.md). It is not the primary RC install
or an acceptable fallback for the outside-user package acceptance test.

Read the [RC release notes](../project/release_0_1_0.md) for support boundaries,
candidate adapters, known limitations, and problem reporting.

## Testing current `main` in a notebook

`main` intentionally still declares `0.1.0rc1` until a release-management
decision changes the version. The version string alone therefore cannot tell
you whether a notebook imported the published RC or later source.

Use a dedicated kernel and pin the exact commit under review:

```bash
python3.11 -m venv .venv-cubedynamics-main
source .venv-cubedynamics-main/bin/activate
python -m pip install --upgrade pip
python -m pip install \
  "cubedynamics @ git+https://github.com/CU-ESIIL/cubedynamics.git@<full-commit-sha>"
python -m pip install ipykernel
python -m ipykernel install --user \
  --name cubedynamics-main --display-name "CubeDynamics main"
```

Select **CubeDynamics main** in Jupyter and verify the running process:

```python
import cubedynamics as cd
print(cd.version_info())
```

The output includes the version, imported package path, artifact kind, and Git
commit when VCS metadata is available. A kernel that imported CubeDynamics
before installation must be restarted: Python does not replace already loaded
modules merely because `%pip` finished.

Do not use `--ignore-installed` to force this workflow. It can replace unrelated
packages and leave environments such as NumPy/Zarr internally inconsistent. If
an existing dedicated CubeDynamics environment already has reviewed compatible
dependencies, `%pip install --no-deps --upgrade "cubedynamics @
git+https://github.com/CU-ESIIL/cubedynamics.git@<full-commit-sha>"` updates only
CubeDynamics; restart the kernel immediately afterward. A fresh dedicated
environment is the safer default.

See [Runtime identity in notebooks](runtime_identity.md) for interpreting each
field and distinguishing a public artifact from development source.
