# Contributing

Thank you for helping build CubeDynamics! This project aims to keep climate cube
math lightweight, streaming-first, and well documented. To contribute:

1. Fork or branch from `main` and create feature branches for your work.
2. Install dependencies in editable mode (`python -m pip install -e .[dev]` once
   extras are defined) and run the test suite via `pytest`.
3. Add or update documentation in `docs/` for every new feature or API change.
4. Prefer streaming and chunked operations. If you add a function that downloads
   data, ensure it can operate lazily with `dask` when possible.
5. Open a pull request describing the change, test coverage, and any data access
   requirements.

Issues and discussions are also welcome for roadmap ideas, new data sources, or
lexcube visualizations.
