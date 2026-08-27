"""Small editorial taxonomy; signatures and scientific contracts stay in code.

Only grouping and exceptions live here. Factory detection inspects, but never
executes, public callables. Unknown functions remain visible as other helpers.
"""
import ast
import inspect
import textwrap

from cubedynamics.grammar import get_verb_spec

CATEGORIES = {
    "Transform": "anomaly zscore mean variance apply flatten_space flatten_cube month_filter ndvi_from_s2".split(),
    "State and events": "threshold_state quantile_state binary_state change_state detect_events".split(),
    "Synchrony and comparison": "occurrence_synchrony timing_synchrony duration_synchrony severity_synchrony sync_with overlap compare_blocks rolling_median_split_synchrony rolling_tail_dep_vs_center".split(),
    "Spatial and alignment": "align_cube rasterize_observations block_signature collect_blocks extract vase_extract vase_mask".split(),
    "Visualization": "plot plot_mean vase tubes fire_plot fire_panel fire_vase_panel fire_derivative climate_hist diagnostic_panel landsat_ndvi_plot".split(),
    "Output and side effects": ["to_netcdf", "show_cube_lexcube"],
}
PLACEHOLDERS = {"correlation_cube", "fit_model"}
COMPATIBILITY = {
    "month_filter": "Deprecated implementation: the public export currently resolves to the warning-emitting ops.transforms shim. Its warning points back to the same public name; no distinct replacement is claimed here.",
    "aoi_signature": "Compatibility name: prefer block_signature for new workflows; its block_id/block dimension differs from unit_id/unit.",
    "compare_aoi_signature": "Compatibility workflow: new code can collect_blocks then compare_blocks. This is not a drop-in signature replacement.",
    "exceedance": "Alias for threshold_state; no deprecation warning is implied.",
    "vase_demo": "Legacy demonstration using synthetic geometry, not a real-data analysis verb.",
}
# The lazy Landsat proxy forwards to @pipeable; exceedance forwards to a factory.
FACTORY_OVERRIDES = {"landsat8_mpc", "exceedance"}
KIND_LABELS = {
    "stage": "Grammar verb / pipe stage",
    "helper": "Direct helper function",
    "visualization_helper": "Visualization helper (direct call)",
    "placeholder": "Reserved / planned API",
}


def returns_stage(func):
    tree = ast.parse(textwrap.dedent(inspect.getsource(func))).body[0]
    local_functions = {n.name for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
    for node in tree.body:
        if (isinstance(node, ast.Assign) and isinstance(node.value, ast.Call)
                and isinstance(node.value.func, ast.Name) and node.value.func.id == "Verb"):
            local_functions.update(t.id for t in node.targets if isinstance(t, ast.Name))

    def outer_returns(node):
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
                continue
            if isinstance(child, ast.Return):
                yield child.value
            yield from outer_returns(child)

    return any(
        isinstance(value, ast.Lambda)
        or isinstance(value, ast.Name) and value.id in local_functions
        or isinstance(value, ast.Call) and isinstance(value.func, ast.Name) and value.func.id == "Verb"
        for value in outer_returns(tree)
    )


def classify(name, func):
    spec = get_verb_spec(name)
    category = next((title for title, names in CATEGORIES.items() if name in names), "Other helpers")
    if name in PLACEHOLDERS:
        kind, status = "placeholder", "placeholder"
    else:
        kind = "stage" if name in FACTORY_OVERRIDES or returns_stage(func) else "helper"
        if kind == "helper" and category == "Visualization":
            kind = "visualization_helper"
        deprecated = (inspect.getdoc(func) or "").lstrip().startswith("Deprecated.")
        status = "deprecated" if deprecated else "compatibility" if name in COMPATIBILITY else "implemented"
    return {
        "category": category, "kind": kind, "status": status,
        "description": spec.human_description if spec and status == "implemented" else None,
    }
