# Hackathon notebook lab

This collection is a visual, executable introduction to CubeDynamics. Every
notebook is independent, uses deterministic synthetic data, runs without
network access or credentials, and produces at least one plot that makes the
effect of the code visible.

The first three notebooks show common ways to bring data into the cube model.
The remaining notebooks show what the grammar can do and how a hackathon team
can extend it.

## Bring data into the grammar

| Notebook | Starting point | What participants see |
| --- | --- | --- |
| [01 · Build a cube from arrays](cube_from_arrays.ipynb) | NumPy values plus coordinate arrays | A map, a pixel time series, and the interactive HTML cube viewer |
| [02 · Build a cube from a tidy table](cube_from_tidy_table.ipynb) | A pandas table with time, y, and x columns | The reshaped series and the effect of temporal standardization |
| [03 · Work with a multi-variable Dataset](cube_from_dataset.ipynb) | Aligned temperature and precipitation cubes | A temperature-anomaly map and regional precipitation series |

## Compose and extend verbs

| Notebook | Main idea | Verbs and concepts |
| --- | --- | --- |
| [04 · The core grammar](grammar_basics.ipynb) | Direct calls, pipe calls, and ordinary functions agree | `pipe`, `unwrap`, `v.zscore`, `v.anomaly`, `v.apply` |
| [05 · Visual gallery of core verbs](verbs_gallery.ipynb) | One cube can answer several questions | `v.mean`, `v.variance`, `v.anomaly`, `v.zscore`, `v.apply`, `v.flatten_space` |
| [06 · States, events, and synchrony](states_and_events.ipynb) | Continuous measurements can become episodes and relationships | `v.threshold_state`, `v.detect_events`, `v.occurrence_synchrony` |
| [07 · Build a project-specific verb](custom_verb_project.ipynb) | A research project can own its scientific vocabulary | Verb factories, Dataset outputs, direct-versus-pipe tests |
| [08 · Lazy composition with Dask](lazy_composition.ipynb) | Pipelines can stay lazy until an intentional result is needed | Chunking, graph construction, `compute()` boundaries |

## Suggested hackathon routes

For a **45-minute orientation**, run notebooks 01, 04, and 05. Participants
learn the cube data model, the composition syntax, and the main vocabulary.

For a **90-minute hands-on lab**, add notebook 02 or 03 based on the data people
usually bring, then let each team choose notebook 06, 07, or 08 as its extension.

For an **open build session**, ask teams to replace one synthetic cube with
their own xarray object and author one project-owned verb that ends in an
explanatory plot.

## Run the complete lab locally

From a repository checkout:

```bash
python -m pip install -e ".[vignettes]"
python scripts/run_vignettes.py
```

The runner executes clean copies in a temporary directory. It checks that each
notebook is marked offline, finishes without an exception, and emits a portable
PNG or SVG plot. It does not write execution outputs into the source notebooks.

To explore and edit the notebooks interactively:

```bash
python -m pip install jupyterlab
jupyter lab docs/vignettes/
```

The documentation build executes the notebooks when it renders the website, so
the published pages include their figures. Each page also provides its source
`.ipynb` for download.

## Reproducibility contract

- Python 3 kernel metadata is recorded in every notebook.
- Random examples use fixed seeds; other examples are fully deterministic.
- No notebook needs a token, account, network service, or private local path.
- All inputs are small enough for a laptop and all plots use standard package
  dependencies.
- Assertions live next to the examples so a broken API fails loudly.

The supported vignettes are the publication-facing examples. Older notebooks
under the top-level `notebooks/` directory are exploratory records and may use
network services, optional renderers, or historical APIs.
