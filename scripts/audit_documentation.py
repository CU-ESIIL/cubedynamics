#!/usr/bin/env python3
"""Snapshot the documentation inventory before an information-architecture change."""
from pathlib import Path
import argparse
from datetime import date
import json

ROOT = Path(__file__).resolve().parents[1]


def classify(path: Path) -> str:
    name = path.as_posix()
    if name == "index.md":
        return "Home"
    if name.startswith(("vignettes/", "decision_vignettes/", "recipes/", "examples/", "workflows/", "howto/", "synchrony/", "capabilities/", "projects/")) or name == "examples_gallery.md":
        return "Vignette / analysis collection"
    if name.startswith(("data/", "library/")):
        return "Library noun / discovery"
    if name.startswith("datasets/"):
        return "Library source / legacy adapter"
    if name.startswith(("dev/", "developer/", "project/", "design/", "related/")) or name == "changelog.md":
        return "Development / About (inside Documents)"
    if name.startswith(("concepts/", "getting_started/", "learn/")) or name in {"quickstart.md", "why_cubedynamics.md", "start_here.md", "reading_paths.md"}:
        return "Learn / concept supplement"
    return "Documents verb / API / technical reference"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="New snapshot path; existing snapshots are never overwritten")
    args = parser.parse_args()
    rows = []
    for path in sorted((ROOT / "docs").rglob("*")):
        if path.suffix not in {".md", ".ipynb"}:
            continue
        rel = path.relative_to(ROOT / "docs")
        text = path.read_text()
        if path.suffix == ".ipynb":
            text = "\n".join("".join(c["source"]) for c in json.loads(text)["cells"] if c["cell_type"] == "markdown")
        title = next((line.lstrip("# ") for line in text.splitlines() if line.startswith("# ")), rel.stem)
        rows.append(f"| `{rel}` | {classify(rel)} | {title.replace('|', '/')} |")
    report = f"""# Documentation inventory · {date.today().isoformat()}

Point-in-time snapshot. This inventories every Markdown page and notebook,
including compatibility pages and unpublished examples; inclusion is not a
claim that an example is validated. See the [migration plan](documentation_refactor.md)
for canonical destinations, generated ownership, and retained legacy routes.

| Existing path | Page type / proposed destination | Existing title |
| --- | --- | --- |
""" + "\n".join(rows) + "\n"
    if args.output is None:
        print(report)
    else:
        # Keep the original pre-refactor evidence immutable on routine reruns.
        with args.output.open("x", encoding="utf-8") as output:
            output.write(report)
        print(f"Inventoried {len(rows)} documentation sources")


if __name__ == "__main__":
    main()
