# Contributing

Thanks for your interest in improving CubeDynamics!

- Read the full guidelines in [docs/dev/contributing.md](docs/dev/contributing.md).
- Set up a development environment with:
- `pip install -e .[dev]`
  - `pytest -m "not integration" -q`
- Build docs locally with `mkdocs serve` to preview changes.
- Open issues or pull requests on GitHub for discussion and review.

We follow the Contributor Covenant Code of Conduct (see `CODE_OF_CONDUCT.md`).

## Releasing

1. Install build tooling: `python -m pip install build twine`
2. Build the artifacts: `python -m build`
3. Upload to PyPI (requires an API token): `python -m twine upload dist/*`
4. Optionally create a Git tag and GitHub release that matches the PyPI version.
