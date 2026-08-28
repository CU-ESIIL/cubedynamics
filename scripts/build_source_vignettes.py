#!/usr/bin/env python3
"""Generate terrain/roads lessons and their small first-result reference figures."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from source_lesson_content import LESSONS
from vignette_shell import with_shell

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "docs/assets/generated/nouns"


def notebook(noun, lesson):
    cells = []
    def add(kind, text, key=None):
        cell = {"cell_type": kind, "id": hashlib.sha256(text.encode()).hexdigest()[:12],
                "metadata": {}, "source": text.splitlines(keepends=True)}
        if kind == "code":
            cell.update(execution_count=None, outputs=[])
            cell["metadata"]["visual_example"] = {"kind": "figure", "key": key}
        cells.append(cell)
    add("markdown", f"# {lesson['title']}\n\n## Context\n\n{lesson['context']}\n\n"
        f"## Question\n\n{lesson['question']}\n\n## Pipe\n\n`{lesson['pipe']}`\n\n"
        "Acquisition and input checks come before the analytical sentence. The cells below use "
        "frozen real loader outputs, so running the lesson does not depend on provider availability. "
        f"For live acquisition, see the [{noun} reference](../library/nouns/{noun}.md). "
        f"[Download this notebook]({lesson['stem']}.ipynb?download=1).\n\n## Analysis story\n")
    for index, (title, question, code, interpretation) in enumerate(lesson["steps"], 1):
        add("markdown", f"### {index}. {title}\n\n{question}\n")
        add("code", code, f"{noun}-{index}")
        add("markdown", f"{interpretation}\n")
    add("markdown", "## Figure\n\nEach of the three analytical steps displays its own result.\n\n"
        "## What the figure tells us\n\n" + lesson["steps"][-1][3] + "\n\n"
        "Input integrity and numerical checks are reproducible; these teaching results do not "
        "establish broader scientific suitability. Preserve the scope and source metadata when reusing them.\n")
    meta = {"supported_vignette": True, "network": False, "plot_required": True, "minimum_plot_outputs": 3,
            "data_fixture": "tests/fixtures/real_data/" + lesson["fixture"],
            "provenance": "tests/fixtures/real_data/" + lesson["provenance"],
            "source_reference": f"../library/sources/{lesson['source']}.md", "source_label": "source reference",
            "source_support_label": "supported scope, quality checks, and limits",
            "related_nouns": f"[{noun}](../library/nouns/{noun}.md)"}
    nb = {"nbformat": 4, "nbformat_minor": 5, "cells": cells,
          "metadata": {"cubedynamics": meta, "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
                       "language_info": {"name": "python"}}}
    return with_shell(nb, f"docs/vignettes/{lesson['stem']}.ipynb")


def evidence_inputs():
    paths = [ROOT / "scripts/source_lesson_content.py", ROOT / "scripts/build_source_vignettes.py",
             ROOT / "scripts/build_streamflow_vignette.py", ROOT / "scripts/vignette_shell.py"]
    paths += list((ROOT / "tests/fixtures/real_data/source_lessons").iterdir())
    paths += [p for p in (ROOT / "tests/fixtures/real_data/usgs_streamflow").rglob("*") if p.is_file()]
    return {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths)}


def check_evidence_inputs(recorded):
    """Name missing checkout inputs before comparing the current file inventory."""
    missing = sorted(name for name in recorded if not (ROOT / name).is_file())
    if missing:
        raise SystemExit("Missing noun figure inputs:\n- " + "\n- ".join(missing)
                         + "\nRestore these repository inputs; do not regenerate evidence to bypass missing data.")
    current = evidence_inputs()
    changed = sorted(name for name in recorded if current.get(name) != recorded[name])
    added = sorted(current.keys() - recorded.keys())
    if changed or added:
        details = [f"changed: {name}" for name in changed] + [f"unrecorded: {name}" for name in added]
        raise SystemExit("Stale noun figure inputs:\n- " + "\n- ".join(details))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    for noun, lesson in LESSONS.items():
        path = ROOT / f"docs/vignettes/{lesson['stem']}.ipynb"
        text = json.dumps(notebook(noun, lesson), indent=1, ensure_ascii=False) + "\n"
        if args.check:
            if not path.exists() or path.read_text() != text:
                raise SystemExit(f"Stale source lesson: {path}")
        else:
            path.write_text(text)
    manifest_path = ASSETS / "manifest.json"
    if args.check:
        manifest = json.loads(manifest_path.read_text())
        check_evidence_inputs(manifest["inputs"])
        for name, digest in manifest["outputs"].items():
            assert hashlib.sha256((ASSETS / name).read_bytes()).hexdigest() == digest
    else:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        ASSETS.mkdir(parents=True, exist_ok=True)
        outputs = {}
        for noun, lesson in LESSONS.items():
            namespace = {}
            for index, (_, _, code, _) in enumerate(lesson["steps"], 1):
                exec(compile(code, f"{noun}-step-{index}", "exec"), namespace)
                image = ASSETS / f"{noun}-{index}.png"
                plt.gcf().savefig(image, dpi=130, bbox_inches="tight")
                plt.close("all")
                outputs[image.name] = hashlib.sha256(image.read_bytes()).hexdigest()
        from build_streamflow_vignette import build
        first = next(c for c in build()["cells"] if c["cell_type"] == "code")
        exec(compile("".join(first["source"]), "streamflow-step-1", "exec"), {})
        image = ASSETS / "streamflow-1.png"
        plt.gcf().savefig(image, dpi=130, bbox_inches="tight")
        plt.close("all")
        outputs[image.name] = hashlib.sha256(image.read_bytes()).hexdigest()
        manifest_path.write_text(json.dumps({"inputs": evidence_inputs(), "outputs": outputs,
            "scope": "Real frozen loader outputs; exact code shared by notebooks. Not production certification."}, indent=2) + "\n")
    print("Source notebooks and seven figure artifacts " + ("checked" if args.check else "generated"))


if __name__ == "__main__":
    main()
