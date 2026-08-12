# Runnable vignettes

Vignettes are the supported, narrative examples for CubeDynamics. Each page is
a real Jupyter notebook, uses deterministic synthetic data, runs without
network access or credentials, and is executed in CI.

| Vignette | What it establishes | Runtime |
| --- | --- | --- |
| [The core grammar](grammar_basics.ipynb) | Cubes, `pipe`, built-in verbs, and unwrapping results | Offline, under a minute |
| [A custom verb project](custom_verb_project.ipynb) | How a domain project adds its own tested vocabulary | Offline, under a minute |
| [Lazy composition](lazy_composition.ipynb) | Dask-backed inputs stay lazy across ordinary verbs | Offline, under a minute |

## Run them locally

From a repository checkout:

```bash
python -m pip install -e ".[vignettes]"
python scripts/run_vignettes.py
```

The runner executes clean copies in a temporary directory and does not write
outputs into the source notebooks. Open and edit them in any Jupyter-capable
editor. To use JupyterLab:

```bash
python -m pip install jupyterlab
jupyter lab docs/vignettes/
```

The repository's `uv.lock` can be used when an exactly resolved development
environment is needed. The notebooks themselves record a Python 3 kernelspec,
fixed random seeds, and no hidden local paths.

## Support boundary

The notebooks in this section are publication-verified. Older notebooks under
the top-level `notebooks/` directory are exploratory records: they may require
network services, optional renderers, or historical APIs. See
[`notebooks/README.md`](https://github.com/CU-ESIIL/cubedynamics/blob/main/notebooks/README.md)
for that distinction.
