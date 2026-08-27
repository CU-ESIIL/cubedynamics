# 2. Verbs do things

## Concept

A verb factory configures an operation; the returned callable applies it to
data. Run the [shared setup](index.md#shared-setup) first.

## Tiny example

```python
average_over_time = v.mean(dim="time", keep_dim=False)
monthly_map = average_over_time(cube)
```

## Explanation

The factory does not know which cube it will receive. Applying it reduces the
named dimension. The [mean reference](../reference/verbs/mean.md) is the
canonical description of its arguments and behavior.

## Try it / worked example

```python
monthly_map.plot()
plt.show()
assert "time" not in monthly_map.dims
```

This is a mean over the fixture's observed dates, not a long-term climatology.
The short call still needs that scientific interpretation.

## What to learn next

[3. Pipes establish order](pipes.md) · [Verb index](../reference/verbs/index.md) ·
[Verb gallery vignette](../vignettes/verbs_gallery.ipynb)
