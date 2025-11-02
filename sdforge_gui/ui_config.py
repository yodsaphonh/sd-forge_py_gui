"""Utilities for loading and applying UI configuration overrides."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from PyQt6 import QtCore, QtWidgets


class UIConfig:
    """Loads optional overrides from ``ui-config.json``."""

    def __init__(self, path: Path | str = "ui-config.json") -> None:
        self.path = Path(path)
        self._entries: Dict[str, Any] = {}
        self.error: str | None = None
        self._load()

    # ------------------------------------------------------------------
    def _load(self) -> None:
        if not self.path.exists():
            return
        try:
            with self.path.open("r", encoding="utf-8") as handle:
                data = json.load(handle)
        except Exception as exc:  # pragma: no cover - runtime feedback
            self.error = str(exc)
            self._entries = {}
            return
        if not isinstance(data, dict):
            self.error = "Top-level JSON structure must be an object"
            return
        self._entries = data

    # ------------------------------------------------------------------
    def section(self, name: str) -> Dict[str, Dict[str, Any]]:
        """Return configuration entries grouped by control for the section."""

        grouped: Dict[str, Dict[str, Any]] = {}
        normalized = name.lower()
        for key, value in self._entries.items():
            head, _, tail = key.partition("/")
            if not tail or head.lower() != normalized:
                continue
            control, _, prop = tail.partition("/")
            if not prop:
                continue
            grouped.setdefault(control, {})[prop] = value
        return grouped

    # ------------------------------------------------------------------
    @staticmethod
    def apply_properties(
        widget: QtWidgets.QWidget,
        properties: Dict[str, Any],
        form_layout: QtWidgets.QFormLayout | None = None,
    ) -> None:
        """Apply supported properties to a widget."""

        for prop, raw_value in properties.items():
            prop_lower = prop.lower()
            if prop_lower == "visible":
                visible = bool(raw_value)
                widget.setVisible(visible)
                if form_layout is not None:
                    label = form_layout.labelForField(widget)
                    if label is not None:
                        label.setVisible(visible)
            elif prop_lower == "enabled":
                widget.setEnabled(bool(raw_value))
            elif prop_lower == "value":
                UIConfig._apply_value(widget, raw_value)
            elif prop_lower in {"minimum", "maximum", "min", "max"}:
                UIConfig._apply_range(widget, prop_lower, raw_value)
            elif prop_lower in {"step", "singlestep"}:
                UIConfig._apply_step(widget, raw_value)

    # ------------------------------------------------------------------
    @staticmethod
    def _apply_value(widget: QtWidgets.QWidget, value: Any) -> None:
        if isinstance(widget, QtWidgets.QComboBox):
            if isinstance(value, list):
                if not value:
                    return
                UIConfig._set_combo_value(widget, value[0])
            else:
                UIConfig._set_combo_value(widget, value)
        elif isinstance(widget, QtWidgets.QSpinBox):
            try:
                widget.setValue(int(value))
            except (TypeError, ValueError):
                pass
        elif isinstance(widget, QtWidgets.QDoubleSpinBox):
            try:
                widget.setValue(float(value))
            except (TypeError, ValueError):
                pass
        elif isinstance(widget, QtWidgets.QAbstractButton):
            widget.setChecked(bool(value))
        elif isinstance(widget, QtWidgets.QLineEdit):
            widget.setText(str(value))
        elif isinstance(widget, QtWidgets.QPlainTextEdit):
            widget.setPlainText(str(value))
        elif isinstance(widget, QtWidgets.QTextEdit):
            widget.setPlainText(str(value))
        elif hasattr(widget, "setText"):
            try:
                widget.setText(str(value))
            except Exception:  # pragma: no cover - safety
                pass

    # ------------------------------------------------------------------
    @staticmethod
    def _apply_range(
        widget: QtWidgets.QWidget, prop: str, value: Any
    ) -> None:
        try:
            number = float(value)
        except (TypeError, ValueError):
            return

        if isinstance(widget, QtWidgets.QSpinBox):
            number = int(number)
            if prop in {"minimum", "min"}:
                widget.setMinimum(int(number))
            elif prop in {"maximum", "max"}:
                widget.setMaximum(int(number))
        elif isinstance(widget, QtWidgets.QDoubleSpinBox):
            if prop in {"minimum", "min"}:
                widget.setMinimum(number)
            elif prop in {"maximum", "max"}:
                widget.setMaximum(number)

    # ------------------------------------------------------------------
    @staticmethod
    def _apply_step(widget: QtWidgets.QWidget, value: Any) -> None:
        try:
            number = float(value)
        except (TypeError, ValueError):
            return
        if isinstance(widget, QtWidgets.QSpinBox):
            widget.setSingleStep(int(number))
        elif isinstance(widget, QtWidgets.QDoubleSpinBox):
            widget.setSingleStep(number)

    # ------------------------------------------------------------------
    @staticmethod
    def _set_combo_value(combo: QtWidgets.QComboBox, value: Any) -> None:
        if value in (None, ""):
            return
        text = str(value)
        index = combo.findData(text)
        if index < 0:
            index = combo.findText(text, QtCore.Qt.MatchFlag.MatchFixedString)
        if index < 0:
            for row in range(combo.count()):
                if combo.itemText(row).lower() == text.lower():
                    index = row
                    break
        if index < 0:
            combo.addItem(text, userData=text)
            index = combo.count() - 1
        combo.setCurrentIndex(index)
