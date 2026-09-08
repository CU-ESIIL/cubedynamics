#!/usr/bin/env python3
"""Prepare the participant and worked EDS seminar notebooks."""

from __future__ import annotations

import argparse
from copy import deepcopy
from pathlib import Path

import nbformat


ROOT = Path(__file__).resolve().parents[1]
SEMINAR_DIR = ROOT / "docs" / "vignettes" / "eds_seminar"
PARTICIPANT = SEMINAR_DIR / "participant.ipynb"
ANSWERS = SEMINAR_DIR / "answers.ipynb"
RC3_COMMIT = "f777eb07d3ada8bd407b027f560727c90f6d3731"
INSTALL = (
    "%pip install -q --upgrade \"cubedynamics @ "
    f"git+https://github.com/CU-ESIIL/cubedynamics.git@{RC3_COMMIT}\""
)
HEADER_END = "<!-- /eds-seminar-variant -->"


def _set_source(cell, text: str) -> None:
    cell.source = text.rstrip() + "\n"


def _clear_outputs(notebook) -> None:
    for cell in notebook.cells:
        if cell.cell_type == "code":
            cell.execution_count = None
            cell.outputs = []


def _variant_header(notebook, *, answers: bool) -> None:
    base = notebook.cells[0].source
    if HEADER_END in base:
        base = base.split(HEADER_END, 1)[1].lstrip()
    if answers:
        links = (
            "[Download this completed notebook](answers.ipynb?download=1) · "
            "[Open the participant version](participant.ipynb)"
        )
        label = "EDS SEMINAR • COMPLETE WORKED NOTEBOOK"
    else:
        links = (
            "[Download this participant notebook](participant.ipynb?download=1) · "
            "[Open the complete worked version](answers.ipynb)"
        )
        label = "EDS SEMINAR • PARTICIPANT NOTEBOOK"
    prefix = (
        "<!-- eds-seminar-variant -->\n"
        f'<div class="cd-kicker">{label}</div>\n\n'
        f"{links}\n"
        f"{HEADER_END}\n\n"
    )
    _set_source(notebook.cells[0], prefix + base)


def prepare_participant(source) -> nbformat.NotebookNode:
    notebook = deepcopy(source)
    _clear_outputs(notebook)
    notebook.metadata["cubedynamics"] = {
        "seminar_material": True,
        "supported_vignette": False,
        "network": True,
        "version": "0.1.0rc3",
        "revision": RC3_COMMIT,
        "variant": "participant",
    }
    notebook.metadata.setdefault("kernelspec", {}).update(
        {"display_name": "Python 3", "language": "python", "name": "python3"}
    )
    _variant_header(notebook, answers=False)
    _set_source(
        notebook.cells[1],
        """## 0 · Install the exact release candidate

This install is pinned to the public commit tagged `v0.1.0rc3` and requires an
internet connection. If this kernel previously imported another CubeDynamics
version, restart it after installation and resume at section 1.
""",
    )
    _set_source(notebook.cells[2], INSTALL)
    notebook.cells[2].metadata["tags"] = sorted(
        set(notebook.cells[2].metadata.get("tags", [])) | {"skip-execution"}
    )
    return notebook


def prepare_answers(participant) -> nbformat.NotebookNode:
    notebook = deepcopy(participant)
    _clear_outputs(notebook)
    notebook.metadata["cubedynamics"]["variant"] = "answers"
    _variant_header(notebook, answers=True)
    return notebook


def _preserve_matching_outputs(generated, existing) -> bool:
    """Keep the reviewed execution only when every code cell is unchanged."""
    generated_code = [cell for cell in generated.cells if cell.cell_type == "code"]
    existing_code = [cell for cell in existing.cells if cell.cell_type == "code"]
    if len(generated_code) != len(existing_code):
        return False
    if any(new.source != old.source for new, old in zip(generated_code, existing_code)):
        return False
    for new, old in zip(generated_code, existing_code):
        new.execution_count = old.execution_count
        new.outputs = deepcopy(old.outputs)
    return True


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source",
        type=Path,
        default=PARTICIPANT,
        help="Notebook to normalize as the participant version",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    source = nbformat.read(args.source, as_version=4)
    participant = prepare_participant(source)
    answers = prepare_answers(participant)
    preserved = False
    if ANSWERS.exists():
        preserved = _preserve_matching_outputs(
            answers, nbformat.read(ANSWERS, as_version=4)
        )
    SEMINAR_DIR.mkdir(parents=True, exist_ok=True)
    nbformat.write(participant, PARTICIPANT)
    nbformat.write(answers, ANSWERS)
    print(f"Wrote {PARTICIPANT.relative_to(ROOT)}")
    suffix = " (preserved matching saved outputs)" if preserved else ""
    print(f"Wrote {ANSWERS.relative_to(ROOT)}{suffix}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
