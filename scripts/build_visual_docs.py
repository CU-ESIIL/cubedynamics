#!/usr/bin/env python3
"""Generate/check the small first-pass scientific documentation results offline."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import platform
import subprocess

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image

from visual_examples import EXAMPLES, FIXTURES, LESSON, OUTPUT, ROOT, STYLE, prerequisites, render_examples, setup_code


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inputs():
    files = [Path(__file__), ROOT / "scripts/visual_examples.py"]
    files += sorted((ROOT / "src/cubedynamics").rglob("*.py"))
    for stem in FIXTURES:
        base = ROOT / "tests/fixtures/real_data" / stem
        files.extend([base.with_suffix(".nc"), base.with_suffix(".provenance.json")])
    return {str(p.relative_to(ROOT)): digest(p) for p in files}


def validate_image(path):
    with Image.open(path) as image:
        image.verify()
    with Image.open(path) as image:
        pixels = np.asarray(image.convert("RGB"))
        if image.width < 500 or image.height < 300 or pixels.std() < 10:
            raise ValueError(f"Empty or undersized scientific figure: {path}")


def generate(output=OUTPUT):
    output.mkdir(parents=True, exist_ok=True)
    namespace = {"__name__": "__visual_docs__"}
    records = {}
    with plt.rc_context(STYLE):
        exec(compile(setup_code(()), "visual_examples/setup", "exec"), namespace)
        namespace["display"] = lambda value: None
        # The displayed code still calls show(); the script saves that same
        # figure, whereas nbclient publishes it inline in the existing runner.
        original_show = plt.show
        plt.show = lambda: None
        try:
            for key in prerequisites(tuple(EXAMPLES)):
                example = EXAMPLES[key]
                before = set(plt.get_fignums())
                exec(compile(example.code, f"visual_examples/{key}", "exec"), namespace)
                figures = set(plt.get_fignums()) - before
                target = output / f"{key}.{'png' if example.kind == 'figure' else 'json'}"
                if example.kind == "figure":
                    if len(figures) != 1:
                        raise RuntimeError(f"{key} must produce exactly one figure")
                    figure = plt.figure(figures.pop())
                    figure.savefig(target, dpi=140, metadata={"Software": "CubeDynamics visual documentation"})
                    plt.close(figure)
                    validate_image(target)
                else:
                    if figures:
                        raise RuntimeError(f"{key} should produce a table, not a redundant plot")
                    table = namespace["output_table"]
                    target.write_text(json.dumps({"columns": list(table.columns), "rows": table.astype(str).values.tolist()}, indent=2) + "\n")
                records[key] = {"kind": example.kind, "output": target.name, "sha256": digest(target),
                    "caption": example.caption, "interpretation": example.interpretation,
                    "input_type": "REAL DATA", "fixtures": list(example.fixtures),
                    "source_code": "scripts/visual_examples.py", "example_key": key,
                    "execution_code": setup_code((key,)) + "\n" + example.code,
                    "producer": "scripts/build_visual_docs.py", "requires": list(example.requires)}
        finally:
            plt.show = original_show
            plt.close("all")
    manifest = {"schema_version": 1, "inputs": inputs(), "results": records,
        "input_provenance": {stem: json.loads((ROOT / "tests/fixtures/real_data" / f"{stem}.provenance.json").read_text()) for stem in FIXTURES},
        "scientific_qa": "python scripts/run_source_qa.py (same reviewed PRISM/gridMET inputs)",
        "generation_context": {"python": platform.python_version(), "matplotlib": matplotlib.__version__,
            "git_sha": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()},
        "policy": "Generated real-data teaching results; fixture QA is not live-source certification."}
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    return manifest


def check(output=OUTPUT):
    manifest = json.loads((output / "manifest.json").read_text())
    if manifest["inputs"] != inputs():
        raise ValueError("Stale visual results: run scripts/build_visual_docs.py")
    if set(manifest["results"]) != set(EXAMPLES):
        raise ValueError("Missing/unowned visual examples")
    for key, record in manifest["results"].items():
        path = output / record["output"]
        if digest(path) != record["sha256"]:
            raise ValueError(f"Changed result bytes: {key}")
        if record["kind"] == "figure":
            validate_image(path)
        else:
            table = json.loads(path.read_text())
            if not table["columns"] or not table["rows"]:
                raise ValueError(f"Empty table: {key}")
    return manifest


def update_pages(check_only=False):
    # Only these delimited examples are owned here; surrounding narrative stays
    # editorial. Reference pages remain owned by build_reference_docs.py.
    for page, keys in {"learn/verbs.md": LESSON, "datasets/which_dataset.md": ("sources",)}.items():
        path = ROOT / "docs" / page
        text = path.read_text()
        start, end = "<!-- visual-example:start -->", "<!-- visual-example:end -->"
        prefix, tail = text.split(start)
        _, suffix = tail.split(end)
        expected = prefix + start + "\n" + render_examples(keys, page) + "\n" + end + suffix
        if check_only and expected != text:
            raise ValueError(f"Stale visual documentation: {page}")
        if not check_only:
            path.write_text(expected)


def check_notebook():
    from build_vignette_notebooks import NOTEBOOKS
    from vignette_shell import with_shell
    path = "docs/vignettes/grammar_basics.ipynb"
    expected = with_shell(NOTEBOOKS["grammar_basics.ipynb"], path)
    if json.loads((ROOT / path).read_text()) != expected:
        raise ValueError("Stale visual vignette: run scripts/build_vignette_notebooks.py")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    manifest = check() if args.check else generate()
    update_pages(args.check)
    if args.check:
        check_notebook()
    figures = sum(r["kind"] == "figure" for r in manifest["results"].values())
    print(f"{'Checked' if args.check else 'Generated'} {len(manifest['results'])} visual results ({figures} figures); no network")


if __name__ == "__main__":
    main()
