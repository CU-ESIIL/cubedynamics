# Learn

These short lessons build from finding environmental information to composing
and checking an analysis. They use the same reviewed PRISM observations.

| Lesson | What you will learn |
| --- | --- |
| [1. Nouns are environmental things](nouns.md) | Find data by scientific meaning |
| [2. Verbs do things](verbs.md) | Turn a cube into an answer |
| [3. Pipes establish order](pipes.md) | Compose small operations |
| [4. Order can change meaning](order.md) | Distinguish similar-looking questions |
| [5. Compose a question](compose.md) | Combine states explicitly |
| [6. Inspect the result](inspect.md) | Check dimensions, units and computation |
| [7. Provenance and source choice](provenance.md) | Keep an analysis reproducible |

## Shared setup

For an immediate live-data example, use the [quickstart](../quickstart.md).
For these offline lessons, clone the repository and install from its root:

```bash
git clone https://github.com/CU-ESIIL/cubedynamics.git
cd cubedynamics
python -m pip install -e ".[vignettes]"
```

Run this Python setup before any lesson. The fixture contains actual PRISM
observations, not generated example measurements.

```python
from pathlib import Path
import xarray as xr
import matplotlib.pyplot as plt
from cubedynamics import data, pipe, verbs as v

path = Path("tests/fixtures/real_data/prism_boulder_january_2024.nc")
with xr.open_dataset(path, engine="scipy") as observed:
    cube = observed["tmax"].load()
assert cube.attrs["units"] == "degC"
```

The deliberate `.load()` closes this small local file safely; live or large
cubes need not be materialized. See [installation options](../getting_started/install.md)
and the [fixture's provenance and checks](../validation/data.md).

## After the lessons

- [Library](../library/index.md): find a noun and compare source flavors.
- [Documents](../documentation/index.md): look up arguments and contracts.
- [Vignettes](../vignettes/index.md): run a complete scientific analysis.

Additional context: [cube concepts](../concepts/cubes.md) and
[core/project boundaries](../concepts/core_and_projects.md).
