# Contributing

## Start with the ownership layer

Before adding a verb, decide whether it is:

- part of the small cross-project grammar vocabulary;
- an integration with a data source, renderer, or file format; or
- a project-owned scientific verb.

Most domain methods should begin in the project that owns their assumptions.
They can still compose with `cubedynamics.pipe` without being added to the
`cubedynamics.verbs` namespace. See
[`docs/extending/custom_verbs.md`](docs/extending/custom_verbs.md) and the
[`examples/custom_verb_project/`](examples/custom_verb_project/) scaffold.

New built-in verbs need a clear cube-to-cube contract, direct-call and pipe
tests, laziness behavior, and a justification for cross-project ownership.

Thanks for your interest in improving CubeDynamics!

- Read the full guidelines in [docs/dev/contributing.md](docs/dev/contributing.md).
- Set up a development environment with:
- `python -m pip install -e ".[dev]"`
  - `pytest -m "not integration and not online" -q`
- Build docs locally with `mkdocs serve` to preview changes.
- Open issues or pull requests on GitHub for discussion and review.

We follow the Contributor Covenant Code of Conduct (see `CODE_OF_CONDUCT.md`).

## Releasing

1. Install release tooling: `python -m pip install -e ".[test]"`
2. Build the artifacts: `python -m build`
3. Validate metadata: `python -m twine check dist/*`
4. Run the complete [non-publishing release gate](RELEASING.md), including clean-wheel acceptance.
5. Publication is separate and requires explicit authorization; follow RELEASING.md.
   Do not upload arbitrary `dist/*` or treat a source ZIP as a wheel release.
