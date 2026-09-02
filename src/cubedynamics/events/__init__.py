"""Event construction and matching utilities."""

from .detection import detect_events
from .consolidation import consolidate_events
from .metrics import event_metrics
from .schemas import EventResult

__all__ = ["EventResult", "consolidate_events", "detect_events", "event_metrics"]
