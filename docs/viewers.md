# Cube viewers

## Standalone HTML cube viewer

Generate a fully offline, self-contained cube viewer using:

```python
from cubedynamics.viewers import write_cube_viewer

write_cube_viewer(ndvi, "ndvi_cube.html")
```

The output HTML bundles all JavaScript and textures so it can be opened directly in
a browser or embedded into a notebook with `IFrame("ndvi_cube.html", width=900, height=900)`.
