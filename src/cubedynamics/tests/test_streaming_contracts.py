"""Streaming-first contract tests for cubedynamics."""

import inspect

import pytest

import cubedynamics

STREAMING_FUNCTIONS = [
    cubedynamics.stream_gridmet_to_cube,
    cubedynamics.stream_prism_to_cube,
]


@pytest.mark.streaming
@pytest.mark.parametrize("func", STREAMING_FUNCTIONS)
def test_streaming_functions_expose_chunks_argument(func):
    """Every streaming helper must expose a ``chunks`` keyword."""
    signature = inspect.signature(func)
    assert "chunks" in signature.parameters
    assert signature.parameters["chunks"].kind in {
        inspect.Parameter.KEYWORD_ONLY,
        inspect.Parameter.POSITIONAL_OR_KEYWORD,
    }


@pytest.mark.streaming
def test_streaming_helpers_accept_file_like_objects():
    """Streamers should allow file-like objects instead of local paths only."""
    dummy_file_like = object()
    for func in STREAMING_FUNCTIONS:
        try:
            func(dummy_file_like, chunks={"time": 1})
        except NotImplementedError:
            continue
        else:
            raise AssertionError("Streaming helpers must raise NotImplementedError for now.")


@pytest.mark.download
def test_full_download_paths_are_opt_in():
    """Full downloads should be clearly marked as optional fallback behavior."""
    for func in STREAMING_FUNCTIONS:
        with pytest.raises(NotImplementedError):
            func("/tmp/local-prism-stack.nc", chunks=None, force_download=True)
