# Pipe API
> **See also:**  \
> - [API Reference](reference.md)  \
> - [Inventory (User)](../function_inventory.md)  \
> - [Inventory (Full / Dev)](inventory_full.md)

Pipe wraps values so cube operations can be chained with the ``|`` operator. The
helpers below are the public entry points; internal helpers stay out of the user
surface.

## Pipe mental model

1. Wrap a value with :func:`cubedynamics.pipe` to opt into piping.
2. Apply verbs or callables with ``|``; each stage receives the previous value.
3. Optionally inspect the semantic trace with ``explain()``, ``suggest()``, or
   ``validate()``.
4. Finish with :meth:`Pipe.unwrap` (or rely on rich reprs in notebooks).

```python
import cubedynamics as cd
from cubedynamics import pipe, verbs as v

cube = cd.gridmet(lat=40.0, lon=-105.2, start="2020-06-01", end="2020-07-01", variable="tmmx")
analysis = pipe(cube) | v.anomaly(over="time") | v.mean(over=("y", "x"))
print(analysis.explain())
result = analysis.unwrap()
```

Rich repr example that keeps the viewer attached:

```python
from cubedynamics import pipe, verbs as v

cube = cd.variables.ndvi(lat=40.0, lon=-105.2, start="2020-07-01", end="2020-07-10")
pipe(cube) | v.plot(title="NDVI cube")  # Jupyter renders the HTML viewer
```

## API surface

### ``cubedynamics.pipe(value) -> Pipe``
Wrap ``value`` so downstream operations can be composed with ``|``. Returns a
:class:`Pipe` instance that keeps the original object accessible via
:meth:`Pipe.unwrap` or :pyattr:`Pipe.v`.

### ``cubedynamics.piping.Pipe``
Container holding the wrapped value. Key methods:

* ``__or__(func)`` – apply ``func`` to the wrapped value and return a new Pipe; respects passthrough verbs that attach viewers without replacing the object.
* ``unwrap()`` – return the wrapped value.
* ``v`` – property alias for the wrapped value.
* ``semantic_state`` – metadata-only description of the current result.
* ``semantic_trace`` – immutable record of executed pipe stages.
* ``explain()`` – deterministic plain-language read-back of the analysis.
* ``suggest()`` – a short list of compatible, implemented next verbs.
* ``validate()`` – structured metadata, dimension, provenance, and order checks.

These inspection methods never reorder or execute pipeline stages. The result
of each verb remains the object on which the next written verb acts. See
[Semantic grammar and analysis coaching](../concepts/semantic_grammar.md).

### ``cubedynamics.piping.Verb``
Lightweight wrapper for callables used in pipe chains. A verb can flag itself as
passthrough (viewer side effects) via ``_cd_passthrough_on_call`` or
``_cd_passthrough_on_pipe``. Users generally construct verbs via helpers in the
``cubedynamics.verbs`` namespace instead of instantiating :class:`Verb`
directly.
