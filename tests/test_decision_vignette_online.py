"""Opt-in source smoke test for the South Dakota Decision Lab fixture query."""

from __future__ import annotations

import numpy as np
import pytest

from cubedynamics import data


@pytest.mark.online
@pytest.mark.integration
def test_public_prism_nouns_return_observations_for_decision_aoi() -> None:
    bbox = (-101.2, 43.7, -100.4, 44.3)
    temperature = data.temperature(
        source="prism",
        statistic="maximum",
        bbox=bbox,
        start="2024-07-01",
        end="2024-07-02",
        show_progress=False,
    ).compute()
    precipitation = data.precipitation(
        source="prism",
        bbox=bbox,
        start="2024-07-01",
        end="2024-07-02",
        show_progress=False,
    ).compute()

    assert temperature.attrs["is_synthetic"] == 0
    assert precipitation.attrs["is_synthetic"] == 0
    assert temperature.attrs["scientific_noun"] == "temperature"
    assert precipitation.attrs["scientific_noun"] == "precipitation"
    assert bool(np.isfinite(temperature).all())
    assert bool(np.isfinite(precipitation).all())
    assert temperature.sizes == precipitation.sizes
