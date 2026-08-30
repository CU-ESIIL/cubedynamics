# 7. Provenance and source choice

## Concept

Connect the readable statement to the evidence underneath it: record what was
observed, which interpretation revision was used, and what the analysis changed.
Run the [shared setup](index.md#shared-setup) first.

## Tiny example

```python
description = data.describe("temperature", source="prism")
print(description["current_serving_revision"], description["live_health"])
```

## Explanation

The catalog describes supported access; it does not prove a server is healthy
now. A frozen fixture's checksum identifies its bytes. Providers can differ
in units, grids, methods and revisions even when the noun name is the same.
Compare them in [Library](../library/nouns/temperature.md).

Keep the evidence questions separate: retrieval shows that bytes were obtained;
structural checks show how an adapter interpreted them; numerical and visual
review support a bounded plausibility claim. None alone establishes provider
accuracy or fitness for a decision.

## Try it / worked example

```python
import hashlib
import json

provenance_path = path.with_suffix(".provenance.json")
provenance = json.loads(provenance_path.read_text())
print("Fixture SHA-256:", hashlib.sha256(path.read_bytes()).hexdigest())
print(provenance)
cube.mean(("y", "x")).plot()
plt.show()
```

The [validation report](../validation/data.md) defines acceptance checks;
printing a checksum alone is not validation. Save your query, code revision,
environment and outputs alongside source evidence.

## What to learn next

[Run a vignette](../vignettes/index.md) · [Provenance API](../api/data.md) ·
[Custom nouns](../extending/custom_nouns.md) · [Custom verbs](../extending/custom_verbs.md)
