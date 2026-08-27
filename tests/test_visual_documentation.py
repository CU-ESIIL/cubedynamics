"""Scientific, reproducibility and deliberate failure controls for visual docs."""
from dataclasses import replace
from io import BytesIO
from pathlib import Path
import base64
import json
import shutil
import sys

import matplotlib.pyplot as plt
import nbformat
import numpy as np
from PIL import Image
import pytest
import requests
import xarray as xr

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import build_visual_docs as builder
from run_vignettes import validate_visual_cells
from visual_examples import EXAMPLES, FIXTURES, LESSON, OUTPUT, render_examples, setup_code


def test_committed_results_and_shared_sources_are_current():
    manifest = builder.check()
    builder.update_pages(check_only=True)
    builder.check_notebook()
    assert len(manifest["results"]) == 8
    assert set(manifest["input_provenance"]) == set(FIXTURES)
    notebook = nbformat.read(ROOT / "docs/vignettes/grammar_basics.ipynb", as_version=4)
    cells = [c for c in notebook.cells if c.metadata.get("visual_example")]
    assert [c.metadata.visual_example.key for c in cells] == list(LESSON)
    for cell in cells:
        key = cell.metadata.visual_example.key
        assert cell.source == EXAMPLES[key].code
        assert f"```python\n{cell.source}\n```" in render_examples(LESSON, "learn/verbs.md")
    for key, record in manifest["results"].items():
        assert record["input_type"] == "REAL DATA"
        assert record["execution_code"] == setup_code((key,)) + "\n" + EXAMPLES[key].code


def test_figures_regenerate_from_displayed_code_without_network(tmp_path, monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("Visual documentation must not acquire data from a network")
    monkeypatch.setattr(requests.sessions.Session, "request", forbidden)
    manifest = builder.generate(tmp_path)
    builder.check(tmp_path)
    assert len(list(tmp_path.glob("*.png"))) == 7
    assert manifest["results"]["export"]["kind"] == "table"
    assert "Identical (asserted)" in (tmp_path / "export.json").read_text()


def test_analysis_values_match_direct_operations_on_reviewed_observations():
    namespace = {}
    exec(setup_code(LESSON), namespace)
    original = namespace["cube"].copy(deep=True)
    for key in (*LESSON, "threshold", "sources"):
        exec(EXAMPLES[key].analysis, namespace)
    window = original.sel(time=slice("2024-01-10", "2024-01-20"))
    xr.testing.assert_identical(namespace["window"], window)
    expected = window - window.mean("time")
    xr.testing.assert_allclose(namespace["departures"], expected)
    xr.testing.assert_allclose(namespace["regional_anomaly"], expected.mean(("y", "x")))
    np.testing.assert_allclose(namespace["standardized"], expected / window.std("time"), atol=1e-6)
    assert namespace["standardized"].attrs["units"] == "1"
    xr.testing.assert_identical(namespace["saved"], namespace["restored"])
    np.testing.assert_array_equal(namespace["cold"].state, original <= 0)
    xr.testing.assert_identical(namespace["cube"], original)
    assert namespace["gridmet"].attrs["units"] == "K"
    assert not np.intersect1d(original.time, namespace["gridmet"].time).size
    assert "not evidence of source bias" in EXAMPLES["sources"].caption


@pytest.mark.parametrize("damage", ["missing", "corrupt", "blank", "stale-code", "empty-table"])
def test_required_outputs_fail_closed(tmp_path, monkeypatch, damage):
    output = tmp_path / "results"
    shutil.copytree(OUTPUT, output)
    manifest_path = output / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    target = output / "observed.png"
    if damage == "missing":
        target.unlink()
    elif damage == "corrupt":
        target.write_bytes(b"not a PNG")
    elif damage == "blank":
        Image.new("RGB", (756, 532), "white").save(target)
        # Even an internally consistent hash must not bless an empty figure.
        manifest["results"]["observed"]["sha256"] = builder.digest(target)
    elif damage == "stale-code":
        monkeypatch.setattr(builder, "inputs", lambda: {"changed.py": "new-code"})
    else:
        target = output / "export.json"
        target.write_text('{"columns": [], "rows": []}')
        manifest["results"]["export"]["sha256"] = builder.digest(target)
    manifest_path.write_text(json.dumps(manifest))
    with pytest.raises((ValueError, FileNotFoundError)):
        builder.check(output)


def test_generator_does_not_hide_execution_errors(tmp_path, monkeypatch):
    monkeypatch.setitem(EXAMPLES, "observed", replace(EXAMPLES["observed"], analysis="raise RuntimeError('deliberate control')"))
    with pytest.raises(RuntimeError, match="deliberate control"):
        builder.generate(tmp_path)
    assert not (tmp_path / "manifest.json").exists()
    assert not plt.get_fignums()


def visual_notebook(kind, payload):
    cell = nbformat.v4.new_code_cell("# Test output only", metadata={"visual_example": {"key": "test", "kind": kind}})
    if payload:
        cell.outputs = [nbformat.v4.new_output("display_data", data=payload)]
    return nbformat.v4.new_notebook(cells=[cell])


@pytest.mark.parametrize("damage", ["missing", "blank", "corrupt", "missing-table"])
def test_each_marked_notebook_cell_requires_a_nonempty_result(damage):
    payload = {}
    kind = "table" if damage == "missing-table" else "figure"
    if damage == "blank":
        buffer = BytesIO()
        Image.new("RGB", (756, 532), "white").save(buffer, format="PNG")
        payload = {"image/png": base64.b64encode(buffer.getvalue()).decode()}
    elif damage == "corrupt":
        payload = {"image/png": base64.b64encode(b"bad image").decode()}
    with pytest.raises((RuntimeError, OSError)):
        validate_visual_cells(visual_notebook(kind, payload))


def test_notebook_accepts_decoded_plot_and_actual_table():
    payload = {"image/png": base64.b64encode((OUTPUT / "observed.png").read_bytes()).decode()}
    validate_visual_cells(visual_notebook("figure", payload))
    validate_visual_cells(visual_notebook("table", {"text/html": "<table><tr><td>Verified</td></tr></table>"}))
