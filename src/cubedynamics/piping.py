"""Pipe wrapper enabling ``|`` composition for cube operations."""

from __future__ import annotations

from typing import Callable, Generic, TypeVar


T = TypeVar("T")


U = TypeVar("U")


class Pipe(Generic[T]):
    """Wrap a value so it can flow through ``|`` pipe stages."""

    def __init__(self, value: T) -> None:
        self.value = value

    def __or__(self, func: Callable[[T], U]) -> "Pipe[U]":
        """Apply ``func`` to the wrapped value and return a new :class:`Pipe`."""

        new_value = func(self.value)
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


__all__ = ["Pipe", "pipe"]
