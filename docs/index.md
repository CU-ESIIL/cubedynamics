# 🌍 Climate Cube Math
**A grammar-of-graphics for spatiotemporal environmental data**

Climate Cube Math is a Python framework for analyzing environmental data as **spatiotemporal volumes**, not disconnected maps and time series. It is designed for scientists and data practitioners who want to reason explicitly about **space, time, scale, and events**—and do so reproducibly, efficiently, and at scale.

## Why Climate Cube Math Exists
Most environmental datasets already *are* data cubes:
- climate grids evolving through time  
- vegetation indices measured repeatedly over landscapes  
- disturbance footprints (fires, droughts, floods) unfolding in space and time  

But most workflows **break the cube apart**:
- spatial analysis happens in GIS
- temporal analysis happens in tables
- statistics happen elsewhere
- visualization happens last

Climate Cube Math keeps these dimensions **together**.

The result is a framework that lets you ask questions like:
- *How does climate variability change inside vs. outside an event?*  
- *Where and when does synchrony emerge across a landscape?*  
- *How does variance propagate through space over time?*  

These are fundamentally **spatiotemporal questions**—and they require spatiotemporal tools.

## What Is a Climate Data Cube?
A **climate data cube** is a 3-dimensional object:

```
value(x, y, time)
```

Instead of treating space and time separately, Climate Cube Math treats them as **co-equal axes** of analysis.

This allows operations like:
- computing statistics *through time at every pixel*
- aggregating *space through time*
- extracting *volumes* rather than slices
- defining events as **regions in space–time**

The cube is not just a storage format.  
It is the **unit of reasoning**.

## What Climate Cube Math Enables
### 🔹 Spatiotemporal Operations
Operations are defined on the cube itself—not on slices or tables derived from it.

Examples:
- anomalies
- rolling statistics
- variance and synchrony
- trends and seasonality

### 🔹 Grammar-Based Pipelines
Analyses are expressed as **composable pipelines**:

```python
from cubedynamics import pipe, verbs as v

result = (
    pipe(cube)
    | v.anomaly()
    | v.variance()
    | v.plot(title="Spatiotemporal Variance")
)
```

This makes workflows readable, reproducible, inspectable, and easy to extend.

### 🔹 Streaming-First by Design
Large datasets are handled via VirtualCubes that stream data chunk-by-chunk instead of loading everything into memory.

The same code works for:
- small local datasets
- continental-scale climate archives
- cloud-hosted data

### 🔹 Event-Based Analysis
Events like fires, droughts, or phenological windows are treated as volumes in space–time, not just polygons or date ranges.
This enables:

- inside vs. outside comparisons
- event-aligned climate analysis
- causal framing of spatiotemporal patterns

## Who This Is For
Climate Cube Math is designed for:

- Climate & Earth system scientists
- Ecologists and macrosystems researchers
- Environmental data scientists
- Anyone working with gridded time series data

If your data has space and time, and your questions involve structure, scale, or dynamics, this framework is for you.

## A Minimal Example
```python
from cubedynamics import pipe, verbs as v

result = (
    pipe(cube)
    | v.anomaly()
    | v.variance()
    | v.plot(title="Spatiotemporal Variance")
)
```

## Next Steps
- [Concepts](concepts/index.md)
- [Getting Started / Quickstart](quickstart.md)
- [Recipes / How-tos](howto/index.md)
- [API Reference](api/index.md)
