# Workflows

Workflows are projects where the shared grammar meets scientific questions.

The workflows in this section are demonstrations and project extensions. The
stable center of CubeDynamics is the `pipe | verb` contract; a workflow can add
its own verbs without adding every domain assumption to the core package.

## Workflow Families

- [Climate analysis](climate_analysis.md)
- [Fire analysis](fire_analysis.md)
- [Vegetation analysis](vegetation_analysis.md)
- [Remote sensing analysis](remote_sensing_analysis.md)

## Shared Pattern

Scientists and AI agents should both be able to read the same workflow structure:

```python
cube = load_data(...)

result = (
    pipe(cube)
    | v.anomaly(dim="time")
    | v.mean(dim=("y", "x"), keep_dim=False)
)
```

See [Core grammar, integrations, and project verbs](../concepts/core_and_projects.md)
before treating any case study as a stability guarantee.
