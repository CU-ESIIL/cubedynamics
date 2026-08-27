# 6. Inspect the result

## Concept

A short pipe should produce an inspectable result. Check dimensions,
coordinates, values and metadata. Run the [shared setup](index.md#shared-setup).

## Tiny example

```python
lazy_cube = cube.chunk({"time": 10})
result = (pipe(lazy_cube) | v.mean(dim="time", keep_dim=False)).unwrap()
print(result.dims, result.attrs.get("units"), result.chunks)
```

## Explanation

Dask chunks describe deferred computation, not proof of efficient remote
access. This lesson starts with an already-loaded local fixture. In a live
workflow, inspect the [source access method](../library/sources/index.md) too.
The [lazy evaluation reference](../grammar/lazy_evaluation.md) explains this boundary.

## Try it / worked example

```python
assert result.dims == ("y", "x")
assert result.chunks is not None
result.compute().plot()  # Explicit evaluation for this small final figure.
plt.show()
```

Metadata retention does not replace interpretation: variance has squared
units even if a generic operation retains the input's unit label.

## What to learn next

[7. Provenance and source choice](provenance.md) · [Lazy composition vignette](../vignettes/lazy_composition.ipynb)
