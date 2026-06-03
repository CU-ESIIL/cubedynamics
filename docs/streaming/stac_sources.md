# STAC Sources

STAC is one way to discover and assemble environmental assets.

CubeDynamics can benefit from STAC-backed sources, but it is not itself a STAC interface.

## The Distinction

STAC-oriented tools usually focus on:

- discovery
- asset selection
- cube assembly

CubeDynamics focuses on what happens after data enters a consistent streaming computation interface.

## Practical Framing

You can think of the relationship like this:

- STAC tools help build or retrieve data access paths
- CubeDynamics helps compute on the resulting environmental stream

## Why This Matters

This separation keeps the mental model clean for both scientists and AI agents:

- discovery is one concern
- computation is another

## Related Reading

- [Why CubeDynamics?](../why_cubedynamics.md)
- [Grammar of Streaming](../grammar/index.md)
