"""Smoke tests for website panel examples."""

from __future__ import annotations

import sys

from examples import climate_synchrony_cube_panel_demo, fire_vase_panel_demo


def test_climate_synchrony_cube_panel_example_writes_html(tmp_path, monkeypatch):
    output = tmp_path / "climate_synchrony_cube_panel.html"
    monkeypatch.setattr(
        sys,
        "argv",
        ["climate_synchrony_cube_panel_demo.py", "--output", str(output)],
    )

    climate_synchrony_cube_panel_demo.main()

    html = output.read_text(encoding="utf-8")
    assert "cube-facet-panel" in html
    assert "block = Front Range" in html
    assert "block = San Juans" in html
    assert "cold - hot synchrony" in html


def test_fire_vase_panel_example_writes_html(tmp_path, monkeypatch):
    output = tmp_path / "fire_vase_panel_sample.html"
    monkeypatch.setattr(
        sys,
        "argv",
        ["fire_vase_panel_demo.py", "--output", str(output)],
    )

    fire_vase_panel_demo.main()

    html = output.read_text(encoding="utf-8")
    assert "Synthetic prescribed-burn VASE panel" in html
    assert "event 101" in html
    assert "event 104" in html
    assert "time (days)" in html


def test_climate_sync_page_documents_cube_panel_example():
    page = "docs/recipes/climate_tail_dep_center.md"

    text = open(page, encoding="utf-8").read()

    assert "Interactive panel of synchrony cubes" in text
    assert "climate_synchrony_cube_panel.html" in text
    assert "examples/climate_synchrony_cube_panel_demo.py" in text
    assert '.facet_wrap("block"' in text


def test_fire_vase_page_documents_real_data_example():
    page = "docs/capabilities/fire-vase.md"

    text = " ".join(open(page, encoding="utf-8").read().split())

    assert "real FIRED event paired with streamed gridMET" in text
    assert "fire_vase_gridmet_interactive.html" in text
    assert "examples/real_fire_vase_gridmet_smoke.py" in text
    assert "does not substitute" in text
    assert "generated perimeters" in text
