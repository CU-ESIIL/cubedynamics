# Reference and deprecated shims
> **See also:**  \
> - [API Reference](reference.md)  \
> - [Inventory (User)](../function_inventory.md)  \
> - [Inventory (Full / Dev)](inventory_full.md)

This section links to symbol inventories and lists legacy shims kept for
backward compatibility.

## Function and class inventory

* [Inventory (User)](../function_inventory.md) — short, verb-first overview for
  day-to-day usage.
* [Inventory (Full / Dev)](inventory_full.md) — exhaustive listing of public,
  internal, and test symbols generated from the source tree.

## Deprecated modules and replacements

* ``cubedynamics.ops.transforms.anomaly`` – use :func:`cubedynamics.verbs.anomaly`.
* ``cubedynamics.ops.transforms.month_filter`` – use :func:`cubedynamics.verbs.month_filter`.
* ``cubedynamics.ops.viz.plot`` – use :func:`cubedynamics.verbs.plot`.
* ``cubedynamics.stats.anomalies.zscore_over_time`` – prefer
  :func:`cubedynamics.verbs.zscore`.
* Legacy positional GRIDMET loading is supported but deprecated; prefer the
  keyword-only API in :func:`cubedynamics.data.gridmet.load_gridmet_cube`.
