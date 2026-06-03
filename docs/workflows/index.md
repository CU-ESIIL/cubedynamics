# Workflows

Workflows are where streaming and grammar meet scientific questions.

CubeDynamics is not just about loading cubes or defining verbs. It is about applying a stable computation interface to environmental analysis.

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
    | v.anomaly()
    | v.aggregate()
    | v.detrend()
)
```
