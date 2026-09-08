"""Contracts for the live EDS seminar notebook pair."""

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SEMINAR = ROOT / "docs" / "vignettes" / "eds_seminar"
REVISION = "f777eb07d3ada8bd407b027f560727c90f6d3731"


def load(name):
    return json.loads((SEMINAR / name).read_text(encoding="utf-8"))


def test_seminar_notebooks_are_distinct_live_materials():
    participant = load("participant.ipynb")
    answers = load("answers.ipynb")

    for variant, notebook in (("participant", participant), ("answers", answers)):
        metadata = notebook["metadata"]["cubedynamics"]
        assert metadata == {
            "network": True,
            "revision": REVISION,
            "seminar_material": True,
            "supported_vignette": False,
            "variant": variant,
            "version": "0.1.0rc3",
        }
        install = notebook["cells"][2]
        assert REVISION in "".join(install["source"])
        assert "skip-execution" in install["metadata"]["tags"]

    participant_code = [
        "".join(cell["source"])
        for cell in participant["cells"]
        if cell["cell_type"] == "code"
    ]
    answer_code = [
        "".join(cell["source"])
        for cell in answers["cells"]
        if cell["cell_type"] == "code"
    ]
    assert participant_code == answer_code
    assert all(
        cell.get("outputs", []) == []
        for cell in participant["cells"]
        if cell["cell_type"] == "code"
    )
    narrative = "\n".join(
        "".join(cell["source"])
        for cell in participant["cells"]
        if cell["cell_type"] == "markdown"
    )
    for story in ("Working Lands", "Boulder Cold Snap", "Multivariate Weather", "Remote Sensing"):
        assert story in narrative


def test_seminar_navigation_and_live_execution_exclusion():
    config = (ROOT / "mkdocs.yml").read_text(encoding="utf-8")
    assert "EDS seminar:" in config
    assert "vignettes/eds_seminar/index.md" in config
    assert "vignettes/eds_seminar/participant.ipynb" in config
    assert "vignettes/eds_seminar/answers.ipynb" in config
    assert '"**/vignettes/eds_seminar/*.ipynb"' in config


def test_complete_notebook_keeps_saved_figures():
    notebook = load("answers.ipynb")
    png_outputs = [
        output["data"]["image/png"]
        for cell in notebook["cells"]
        for output in cell.get("outputs", [])
        if "image/png" in output.get("data", {})
    ]
    assert len(png_outputs) >= 10
    assert all(len(payload) > 1_000 for payload in png_outputs)
