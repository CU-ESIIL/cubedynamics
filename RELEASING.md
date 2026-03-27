# Releasing CubeDynamics

This checklist is the shortest reliable path from a green main branch to a publishable release.

## Before tagging

1. Update the version in `pyproject.toml` and `src/cubedynamics/version.py`.
2. Sanity-check install and packaging metadata:

   ```bash
   python -m pip install -e ".[dev]"
   pytest -m "not integration and not online" -q
   mkdocs build --strict
   python -m build
   python -m twine check dist/*
   ```

3. Smoke-test the built wheel in a clean environment:

   ```bash
   python -m venv .release-venv
   .release-venv/bin/pip install --upgrade pip
   .release-venv/bin/pip install dist/*.whl
   .release-venv/bin/python -c "import cubedynamics; import cubedynamics.verbs"
   ```

## Tag and publish

1. Commit the release metadata updates.
2. Create and push a tag such as `v0.1.0`.
3. Publish to PyPI with trusted publishing or:

   ```bash
   python -m twine upload dist/*
   ```

4. Draft a GitHub Release for the tag.
5. Update `CITATION.cff`, `.zenodo.json`, and `paper/paper.md` with the minted DOI once Zenodo finishes archiving the release.

## After release

1. Verify `pip install cubedynamics` works from a fresh environment.
2. Confirm the docs site matches the released version.
3. Announce any breaking changes or deprecations in the changelog and release notes.
