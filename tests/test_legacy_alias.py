"""Ensure the legacy ``climate_cube_math`` import remains functional."""

from __future__ import annotations

import importlib
import sys
import warnings


def test_legacy_alias_warns_and_reexports_api():
    sys.modules.pop("climate_cube_math", None)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always", DeprecationWarning)
        legacy = importlib.import_module("climate_cube_math")

    assert any(
        issubclass(w.category, DeprecationWarning)
        and "renamed to `cubedynamics`" in str(w.message)
        for w in caught
    )

    cubedynamics = importlib.import_module("cubedynamics")
    assert legacy.__version__ == cubedynamics.__version__
    assert legacy.pipe is cubedynamics.pipe
