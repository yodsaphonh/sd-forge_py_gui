"""Shared custom Qt widgets."""
from __future__ import annotations

from PyQt6 import QtGui, QtWidgets


class _NoWheelMixin:
    """Mixin that blocks mouse wheel events to prevent accidental changes."""

    def wheelEvent(self, event: QtGui.QWheelEvent) -> None:  # type: ignore[override]
        event.ignore()


class NoWheelComboBox(_NoWheelMixin, QtWidgets.QComboBox):
    """Combo box that ignores mouse wheel scrolling."""


class NoWheelSpinBox(_NoWheelMixin, QtWidgets.QSpinBox):
    """Integer spin box that ignores mouse wheel scrolling."""


class NoWheelDoubleSpinBox(_NoWheelMixin, QtWidgets.QDoubleSpinBox):
    """Floating point spin box that ignores mouse wheel scrolling."""
