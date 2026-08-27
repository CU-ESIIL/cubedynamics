# Assets

Place supporting images for the documentation inside this folder.

- Use `docs/assets/diagrams/` for diagrams and schematic figures referenced throughout the docs.
- Use `docs/assets/figures/` for illustrative figures or photos.

Filenames are referenced directly in Markdown pages, so update links when
replacing or renaming an asset.

Recommended formats: PNG or SVG for clarity in the MkDocs theme.

Do not add empty files or text placeholders with image extensions. Use a clear
text explanation until a reviewed diagram or real-data figure is available.
The [browser QA suite](../dev/ci_testing.md#website-browser-qa) decodes displayed
images and fails on corrupt or missing assets, including inside cube viewers.
