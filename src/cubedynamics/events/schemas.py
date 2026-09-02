"""Public event result schema."""

from __future__ import annotations

from dataclasses import dataclass
from html import escape

import pandas as pd
import xarray as xr


@dataclass(frozen=True)
class EventResult:
    """Event data plus a catalog whose row scope is scientifically explicit."""

    dataset: xr.Dataset
    catalog: pd.DataFrame
    event_scope: str = "local_cell"
    spatial_identity_fields: tuple[str, ...] = ("y_index", "x_index")

    def __post_init__(self) -> None:
        if not self.event_scope:
            raise ValueError("event_scope must be a non-empty scientific scope")
        metadata = {
            "event_scope": self.event_scope,
            "event_row_meaning": self.row_meaning,
            "spatial_identity_fields": list(self.spatial_identity_fields),
        }
        self.catalog.attrs.update(metadata)
        self.dataset.attrs.update(
            {
                "event_scope": self.event_scope,
                "event_row_meaning": self.row_meaning,
                "event_spatial_identity_fields": ",".join(self.spatial_identity_fields),
            }
        )

    def unwrap(self) -> xr.Dataset:
        """Return the cube-form event Dataset."""

        return self.dataset

    @property
    def row_meaning(self) -> str:
        """Describe the scientific entity represented by one catalog row."""

        if self.event_scope == "local_cell":
            return "one contiguous event instance at one spatial grid cell"
        if self.event_scope == "regional_episode":
            return "one consolidated regional spatiotemporal episode"
        return f"one event instance with scope {self.event_scope!r}"

    def explain(self) -> str:
        """Return a concise scope-aware explanation without expanding the catalog."""

        noun = "events" if self.event_scope != "regional_episode" else "episodes"
        lines = [
            "EventResult",
            f"- {len(self.catalog)} {self.event_scope.replace('_', '-')} {noun}",
            f"- One catalog row means {self.row_meaning}.",
            "- Spatial identity fields: "
            + (", ".join(self.spatial_identity_fields) or "not applicable"),
        ]
        if not self.catalog.empty and {"start", "end"}.issubset(self.catalog.columns):
            lines.append(
                f"- Label range: {self.catalog['start'].min()} through "
                f"{self.catalog['end'].max()}"
            )
        if self.event_scope == "local_cell":
            lines.append(
                "- This count is not a count of independent regional environmental episodes."
            )
        return "\n".join(lines)

    def __repr__(self) -> str:
        preview = self.catalog.head(5).to_string(index=False) if not self.catalog.empty else "(empty catalog)"
        omitted = max(len(self.catalog) - 5, 0)
        suffix = f"\n... {omitted} additional rows" if omitted else ""
        return f"{self.explain()}\n\nCatalog preview\n{preview}{suffix}"

    def _repr_html_(self) -> str:
        preview = self.catalog.head(5)._repr_html_() if not self.catalog.empty else "<p>(empty catalog)</p>"
        omitted = max(len(self.catalog) - 5, 0)
        note = f"<p>… {omitted} additional rows</p>" if omitted else ""
        return (
            "<div class='cubedynamics-event-result'><pre>"
            + escape(self.explain())
            + "</pre><details><summary>Catalog preview</summary>"
            + preview
            + note
            + "</details></div>"
        )
