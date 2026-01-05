"""Regression tests for core runtime dependencies."""


def test_cubo_is_installed():
    """Ensure cubo is available after installing cubedynamics."""
    import cubo  # noqa: F401

