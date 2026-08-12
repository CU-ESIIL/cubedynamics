# Custom verb project scaffold

This directory models a project-owned CubeDynamics vocabulary. The project verb
is ordinary Python: a configured outer factory returns an inner callable that
accepts the current pipe value.

```python
from cubedynamics import pipe
from examples.custom_verb_project import heat_stress

states = (pipe(temperature_cube) | heat_stress(threshold=35)).unwrap()
```

In a standalone project, place the module under that project's `src/` package,
declare `cubedynamics` as a dependency, and keep direct-call plus pipe tests
beside it. The matching website vignette is
`docs/vignettes/custom_verb_project.ipynb`.
