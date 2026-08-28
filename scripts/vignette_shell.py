"""Shared publication shell; never changes an analysis code cell."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def with_shell(notebook, relative_path):
    notebook = deepcopy(notebook)
    metadata = notebook["metadata"]["cubedynamics"]
    provenance = json.loads((ROOT / metadata["provenance"]).read_text())
    source = provenance["source"]
    provider = source["provider"] if isinstance(source, dict) else source
    product = source["product"] if isinstance(source, dict) else provenance.get("source_product", source)
    time_coverage = provenance.get("time_coverage") or [provenance["start"], provenance["end"]]
    source_reference = metadata.get("source_reference", "../library/sources/prism.md")
    source_label = metadata.get("source_label", "PRISM source reference")
    source_support_label = metadata.get("source_support_label", "catalog support")
    related_nouns = metadata.get("related_nouns", "[temperature](../library/nouns/temperature.md) · [precipitation](../library/nouns/precipitation.md)")
    code = "\n".join("".join(c["source"]) for c in notebook["cells"] if c["cell_type"] == "code")
    verbs = sorted(set(re.findall(r"\bv\.(\w+)\(", code)))
    links = [f"[{name}](../reference/verbs/{name}.md)" for name in verbs]
    # Project-local functions are intentionally not presented as package verbs.
    links = [link for link, name in zip(links, verbs) if name != "departure_from"]
    if "decision_vignettes" in relative_path:
        equivalents = {"Question": "The decision", "Grammar / pipeline": "The analytical sentence", "Plain-language interpretation": "Read it left to right", "Analysis": "The missing information", "Result": "What this does and does not tell us"}
    else:
        equivalents = {"Question": "Question", "Grammar / pipeline": "Pipe", "Plain-language interpretation": "Analysis story", "Analysis": "Analysis story", "Result": "What the figure tells us"}
    metadata["documentation_sections"] = {**equivalents, "Data used": "Data used", "Reproduce": "Reproduce", "See also": "See also"}
    text = f'''## Data used

| Field | Frozen analysis input |
| --- | --- |
| Provider | {provider} |
| Product | {product} |
| Dates | {" to ".join(time_coverage)} |
| Fixture | `{metadata["data_fixture"]}` |
| Provenance record | `{metadata["provenance"]}` |

The [{source_label}]({source_reference}) describes current
{source_support_label}; the fixture record above identifies the observations used
here. [Data validation](../validation/data.md) documents checksums and acceptance
checks. The analytical baseline and thresholds belong to this story, not the provider.

## Reproduce

Clone the repository, then run these commands from its root:

```bash
python -m pip install -e ".[vignettes]"
python scripts/run_vignettes.py {relative_path}
```

No network is needed after installation. Open the downloaded notebook in
Jupyter and run all cells to see the same figures. The website executes these
cells during its strict build. [Environment setup](../learn/index.md#shared-setup)
and the [vignette contract](../vignettes/structure.md) explain the workflow.

## See also

{related_nouns} ·
{" · ".join(links)}

[Learn the grammar](../learn/index.md) · [All vignettes](../vignettes/index.md)
'''
    notebook["cells"].append({"cell_type": "markdown", "id": hashlib.sha256(text.encode()).hexdigest()[:12], "metadata": {}, "source": text.splitlines(keepends=True)})
    return notebook
