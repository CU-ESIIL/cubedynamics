# Synchrony from pixels to planet

This bundle accompanies `output/pdf/synchrony_from_pixels_to_planet.pdf`.

## Contents

- `figures/page_01.png` through `figures/page_55.png`: the complete generated page figures.
- `speaker_guide.md`: purpose, main point, likely confusion, and discussion question for every page.
- `glossary.md`: concise one-page glossary.
- `unresolved_scientific_decisions.md`: decisions intentionally left open.
- `empirical_values.json`: every empirical number used by the deck plus source hashes.
- `figure_manifest.json`: page classification and empirical-key provenance.

## Regenerate

From the repository root:

```bash
.venv/bin/python scripts/build_synchrony_pedagogy.py
```

The build requires the current PRISM stack, Colorado signature, and bounded
feasibility artifacts already present under `artifacts/`. It performs no live
network access. Cold/warm pair values are recomputed with the installed
`one_tail_spearman` implementation and asserted against the stored stack.

## Validate

```bash
.venv/bin/python -m pytest tests/test_synchrony_pedagogy.py -q
pdfinfo output/pdf/synchrony_from_pixels_to_planet.pdf
```

Render for visual inspection:

```bash
mkdir -p tmp/pdfs/synchrony_from_pixels_to_planet_rendered
pdftoppm -png -r 100 output/pdf/synchrony_from_pixels_to_planet.pdf tmp/pdfs/synchrony_from_pixels_to_planet_rendered/page
```

Every page carries one of four data labels: `REAL PRISM`, `REAL GHCN`,
`SYNTHETIC`, or `CONCEPTUAL`. CONUS, global, and proposed multiscale products
are intentionally conceptual.
