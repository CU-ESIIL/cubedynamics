"""Notebook-friendly progress helpers for cube rendering."""

from __future__ import annotations

from IPython.display import HTML, display, update_display


class _CubeProgress:
    """Simple progress helper that updates a notebook display in-place."""

    def __init__(self, total: int, enabled: bool = True, style: str = "bar") -> None:
        self.total = max(int(total), 0)
        self.enabled = enabled
        self.style = style
        self.completed = 0
        self.display_id = None
        if self.enabled:
            html = self._render(0.0)
            handle = display(HTML(html), display_id=True)
            self.display_id = handle.display_id
            self._handle = handle

    def _render(self, pct: float) -> str:
        pct_clamped = max(0.0, min(1.0, pct))
        pct_label = f"{int(pct_clamped * 100):02d}%"
        if self.style == "bar":
            return (
                "<div style='font-family: system-ui, sans-serif; width: 260px;'>"
                "<div style='font-size: 12px; margin-bottom: 6px;'>Preparing cube…" + pct_label + "</div>"
                "<div style='width:100%; height:10px; background:#eee; border-radius:6px; overflow:hidden;'>"
                f"<div style='height:10px; width:{pct_clamped*100:.1f}%; background:linear-gradient(90deg,#4caf50,#8bc34a);'></div>"
                "</div>"
                "</div>"
            )
        return f"Preparing cube… {pct_label}"

    def step(self) -> None:
        if not self.enabled or self.display_id is None:
            return
        self.completed += 1
        pct = self.completed / self.total if self.total else 1.0
        html = self._render(pct)
        update_display(HTML(html), display_id=self.display_id)

    def done(self) -> None:
        if not self.enabled or self.display_id is None:
            return
        html = self._render(1.0)
        update_display(HTML(html), display_id=self.display_id)


__all__ = ["_CubeProgress"]
