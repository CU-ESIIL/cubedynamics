# 1. Nouns are environmental things

## Concept

A noun identifies the environmental information you want; a required source
flavor identifies the provider and product that give it observational meaning.
Begin with the [shared setup](index.md#shared-setup).

## Tiny example

```python
data.sources("temperature")
```

## Explanation

Available flavors come from the implemented catalog. The
[temperature reference](../library/nouns/temperature.md) defines units,
coverage and returned data. `cube` here is a frozen observed extract that
avoids a network request while teaching.

A shared noun is a common entry point, not a claim that sources are equivalent.
PRISM and gridMET temperature retain their native variables, units, grids,
statistics, revisions, and provenance. Always inspect the source flavor before
treating a noun as a scientific observation.

## Try it / worked example

```python
cube.isel(time=0).plot()  # Inspect one day before summarizing the month.
plt.show()
```

Find the spatial coordinates and units. The noun describes the measurements;
selecting one day is an explicit analytical choice.

Not every noun is a space–time raster. [Elevation](../library/nouns/elevation.md)
is a static field, [roads](../library/nouns/roads.md) are vector features, and
[streamflow](../library/nouns/streamflow.md) is a station time series. Their
references document the installed imports, source flavors, and compatible
operations. Follow the [noun lessons](../vignettes/index.md#explore-a-noun)
to see each object used in a short, reproducible pipe.

## What to learn next

[2. Verbs do things](verbs.md) · [All nouns](../library/index.md) ·
[Array vignette](../vignettes/cube_from_arrays.ipynb)
