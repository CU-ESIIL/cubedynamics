# Spatial synchrony blocks

This recipe starts the path from one local synchrony cube to a spatial arena.
The core term is **block**: a block is any local cube footprint we want to build
with. It can be an AOI, a grid tile, an ecological region, a sampled
neighborhood around a pixel, or a named comparison site.

The first grammar is:

```python
block = pipe(local_cube) | v.block_signature(block_id="name")
blocks = pipe(block_a) | v.collect_blocks(block_b, block_c)
pairs = pipe(blocks) | v.compare_blocks()
```

## Build local synchrony cubes

```python
import cubedynamics as cd
from cubedynamics import pipe, verbs as v

def prism_temperature(bbox):
    return cd.load_prism_cube(
        variables=["tmin", "tmax"],
        bbox=bbox,
        start="1981-01-01",
        end="2025-12-31",
        freq="D",
        chunks={"time": 31, "y": 64, "x": 64},
    )

def synchrony_cube(cube):
    return (
        pipe(cube)
        | v.rolling_median_split_synchrony(
            lower_var="tmin",
            upper_var="tmax",
            window_days=90,
            min_t=10,
            output_stride=30,
        )
    ).unwrap()

boulder_sync = synchrony_cube(prism_temperature([-105.75, 39.5, -104.75, 40.5]))
desert_sync = synchrony_cube(prism_temperature([-112.5, 33.0, -111.5, 34.0]))
plains_sync = synchrony_cube(prism_temperature([-101.5, 38.5, -100.5, 39.5]))
```

## Turn each cube into a block

```python
boulder = (
    pipe(boulder_sync)
    | v.block_signature(block_id="boulder", reducer="median")
).unwrap()

desert = (
    pipe(desert_sync)
    | v.block_signature(block_id="desert", reducer="median")
).unwrap()

plains = (
    pipe(plains_sync)
    | v.block_signature(block_id="plains", reducer="median")
).unwrap()
```

The block signature keeps the rolling time axis and adds a length-one `block`
dimension. Spatial dimensions are summarized with a median by default, so each
block becomes one comparable time series per synchrony variable.

## Build and compare a block group

```python
block_group = (
    pipe(boulder)
    | v.collect_blocks(desert, plains)
).unwrap()

pairwise = (pipe(block_group) | v.compare_blocks()).unwrap()
print(pairwise)
```

The pairwise result has dimensions `(pair, variable)` and contains:

- `pearson_r`: correlation between block signatures through time.
- `mean_difference`: left block minus right block.
- `rmse`: root mean squared difference.
- `n`: number of shared finite timesteps.

Coordinates `left_block` and `right_block` preserve which two blocks define each
pair.

## Why blocks?

Pairwise comparison is the seed, but the block collection is the object we can
grow. The same representation can support:

- small arrays of named blocks,
- distance-aware spatial joins,
- preselected ecological or climatological comparison sets,
- graph or matrix summaries over many blocks,
- global meta-analysis once a global climate backend is added.

PRISM is useful for high-resolution CONUS work, but it is not global. For a
globe-scale arena, use the same block grammar with a global climate source such
as ERA5, TerraClimate, or another cloud-native gridded backend.

## Compatibility names

`v.aoi_signature(...)` and `v.compare_aoi_signature(...)` remain available for
older notebooks, but new spatial-arena workflows should prefer block language.
