"""Pipe wrapper enabling ``|`` composition for cube operations."""

from __future__ import annotations

from typing import Any, Callable, Generic, TypeVar


T = TypeVar("T")


U = TypeVar("U")


def _attach_viewer(target: Any, viewer: Any) -> None:
    try:
        setattr(target, "_cd_last_viewer", viewer)
        return
    except Exception:
        pass
    try:
        if hasattr(target, "attrs"):
            target.attrs["_cd_last_viewer"] = viewer
    except Exception:
        pass


class Verb(Generic[T, U]):
    """Wrapper for callables used in pipe chains."""

    def __init__(self, func: Callable[[T], U]):
        self.func = func

    def __call__(self, value: T) -> U:
        result = self.func(value)
        if getattr(self, "_cd_passthrough_on_call", False):
            _attach_viewer(value, result)
            return value  # type: ignore[return-value]
        return result


class Pipe(Generic[T]):
    """Wrap a value so it can flow through ``|`` pipe stages."""

    def __init__(self, value: T) -> None:
        self.value = value

    def __or__(self, func: Callable[[T], U]) -> "Pipe[U]":
        """Apply ``func`` to the wrapped value and return a new :class:`Pipe`."""

        new_value = func(self.value)
        if getattr(func, "_cd_passthrough_on_pipe", False):
            viewer = new_value
            _attach_viewer(self.value, viewer)
            new_value = self.value
        return Pipe(new_value)

    def unwrap(self) -> T:
        """Return the wrapped value, ending the pipe chain."""

        return self.value

    def __repr__(self) -> str:
        """Return the repr of the wrapped value for plain-text displays."""

        return repr(self.value)

    def _repr_html_(self):
        """Rich HTML representation for Jupyter notebooks."""

        val = self.value
        viewer = getattr(val, "_cd_last_viewer", None)
        if viewer is None:
            viewer = getattr(getattr(val, "attrs", {}), "_cd_last_viewer", None)
        if viewer is not None and hasattr(viewer, "_repr_html_"):
            return viewer._repr_html_()
        if hasattr(val, "_repr_html_"):
            return val._repr_html_()
        return repr(val)

    @property
    def v(self) -> T:
        """Convenience alias for :pyattr:`value`."""

        return self.value


def pipe(value: T) -> Pipe[T]:
    """Wrap ``value`` in a :class:`Pipe`, enabling ``Pipe | op(...)`` syntax.

    Example
    -------
    >>> result = (pipe(1) | (lambda x: x + 2)).unwrap()
    >>> assert result == 3
    """

    return Pipe(value)


__all__ = ["Pipe", "pipe", "Verb"]
