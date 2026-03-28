from __future__ import annotations

import importlib
import sys


def _clear_cubedynamics_modules() -> None:
    for name in list(sys.modules):
        if name == "cubedynamics" or name.startswith("cubedynamics."):
            sys.modules.pop(name, None)


def test_verbs_import_does_not_eager_import_viz_modules():
    """Importing verbs for custom plotting should not eagerly load lexcube viz modules."""

    _clear_cubedynamics_modules()

    verbs = importlib.import_module("cubedynamics.verbs")

    assert callable(verbs.plot)
    assert "cubedynamics.viz" not in sys.modules
    assert "cubedynamics.viz.lexcube_viz" not in sys.modules
