"""Shared custom Qt widgets."""
from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from PyQt6 import QtCore, QtGui, QtWidgets

from ..models import LoraInfo


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


_TAG_WEIGHT_PATTERN = re.compile(
    r"^\(\s*(?P<tag>.+?)\s*:\s*(?P<weight>-?\d+(?:\.\d+)?)\s*\)$"
)

_SIMPLE_TAG_WEIGHT_PATTERN = re.compile(
    r"^(?P<tag>.+?)\s*:\s*(?P<weight>-?\d+(?:\.\d+)?)$"
)


class PromptTextEdit(QtWidgets.QPlainTextEdit):
    """Prompt editor with popup tag completion."""

    def __init__(self, tags: Sequence[str] | None = None, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self._model = QtCore.QStringListModel([], self)
        self._completer = QtWidgets.QCompleter(self._model, self)
        self._completer.setWidget(self)
        self._completer.setCaseSensitivity(QtCore.Qt.CaseSensitivity.CaseInsensitive)
        self._completer.setFilterMode(QtCore.Qt.MatchFlag.MatchContains)
        self._completer.setCompletionMode(QtWidgets.QCompleter.CompletionMode.PopupCompletion)
        self._completer.activated.connect(self._insert_completion)
        self._completion_context: tuple[int, str] | None = None
        self._inserting_completion = False
        self.minimum_completion_length = 2
        if tags:
            self.set_tags(tags)

    # ------------------------------------------------------------------
    def set_tags(self, tags: Iterable[str]) -> None:
        unique: list[str] = []
        seen: set[str] = set()
        for tag in tags:
            normalized = tag.strip()
            if not normalized:
                continue
            key = normalized.lower()
            if key in seen:
                continue
            seen.add(key)
            unique.append(normalized)
        unique.sort(key=str.lower)
        self._model.setStringList(unique)

    # ------------------------------------------------------------------
    def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:  # type: ignore[override]
        if (
            event.modifiers() == QtCore.Qt.KeyboardModifier.NoModifier
            and event.key() in {QtCore.Qt.Key.Key_Up, QtCore.Qt.Key.Key_Down}
        ):
            delta = Decimal("0.5") if event.key() == QtCore.Qt.Key.Key_Up else Decimal("-0.5")
            if self._adjust_selected_tag_weight(delta):
                event.accept()
                return

        if self._completer.popup().isVisible():
            if event.key() in {
                QtCore.Qt.Key.Key_Tab,
                QtCore.Qt.Key.Key_Backtab,
                QtCore.Qt.Key.Key_Enter,
                QtCore.Qt.Key.Key_Return,
                QtCore.Qt.Key.Key_Escape,
            }:
                event.ignore()
                return

        force_popup = (
            event.modifiers() == QtCore.Qt.KeyboardModifier.ControlModifier
            and event.key() == QtCore.Qt.Key.Key_Space
        )

        super().keyPressEvent(event)

        if self._inserting_completion:
            return

        self._show_completions(force_popup)

    # ------------------------------------------------------------------
    def focusInEvent(self, event: QtGui.QFocusEvent) -> None:  # type: ignore[override]
        super().focusInEvent(event)
        self._completer.setWidget(self)

    # ------------------------------------------------------------------
    def _current_completion_context(self) -> tuple[int, str] | None:
        cursor = self.textCursor()
        cursor_pos = cursor.position()
        text = self.toPlainText()
        if not text or cursor_pos == 0:
            return None

        start = cursor_pos
        while start > 0 and text[start - 1] not in {",", "\n", "\r"}:
            start -= 1
        fragment = text[start:cursor_pos]
        stripped_fragment = fragment.lstrip()
        if not stripped_fragment:
            return None

        replace_start = start + (len(fragment) - len(stripped_fragment))
        return replace_start, stripped_fragment

    # ------------------------------------------------------------------
    def _show_completions(self, force: bool = False) -> None:
        if self._model.rowCount() == 0:
            return

        context = self._current_completion_context()
        if context is None:
            if not force:
                self._completer.popup().hide()
                return
            cursor_pos = self.textCursor().position()
            context = (cursor_pos, "")

        start, prefix = context
        if not force and len(prefix) < self.minimum_completion_length:
            self._completer.popup().hide()
            return

        if prefix != self._completer.completionPrefix():
            self._completer.setCompletionPrefix(prefix)
            self._completer.popup().setCurrentIndex(
                self._completer.completionModel().index(0, 0)
            )

        self._completion_context = (start, prefix)
        popup = self._completer.popup()
        rect = self.cursorRect()
        rect.setWidth(popup.sizeHintForColumn(0) + popup.verticalScrollBar().sizeHint().width())
        self._completer.complete(rect)

    # ------------------------------------------------------------------
    def _insert_completion(self, completion: str) -> None:
        if not self._completion_context:
            return
        start, prefix = self._completion_context
        cursor = self.textCursor()
        self._inserting_completion = True
        cursor.beginEditBlock()
        try:
            cursor.setPosition(start)
            cursor.movePosition(
                QtGui.QTextCursor.MoveOperation.Right,
                QtGui.QTextCursor.MoveMode.KeepAnchor,
                len(prefix),
            )
            cursor.insertText(completion)
            self.setTextCursor(cursor)
        finally:
            cursor.endEditBlock()
            self._inserting_completion = False
        self._completion_context = None
        self._completer.popup().hide()

    # ------------------------------------------------------------------
    def insertFromMimeData(self, source: QtCore.QMimeData) -> None:  # type: ignore[override]
        super().insertFromMimeData(source)
        self._show_completions(False)

    # ------------------------------------------------------------------
    def _adjust_selected_tag_weight(self, delta: Decimal) -> bool:
        cursor = self.textCursor()
        if not cursor.hasSelection():
            return False

        text = self.toPlainText()
        start = cursor.selectionStart()
        end = cursor.selectionEnd()
        if start == end:
            return False

        raw_selection = cursor.selectedText().replace("\u2029", "\n")
        if not raw_selection or "\n" in raw_selection or "\r" in raw_selection:
            return False

        leading_ws = len(raw_selection) - len(raw_selection.lstrip())
        trailing_ws = len(raw_selection) - len(raw_selection.rstrip())
        core_start = start + leading_ws
        core_end = end - trailing_ws
        if core_start >= core_end:
            return False

        core_text = text[core_start:core_end]
        trimmed = core_text.strip()
        if not trimmed:
            return False

        match = _TAG_WEIGHT_PATTERN.match(trimmed)
        if match:
            tag = match.group("tag").strip()
            try:
                weight = Decimal(match.group("weight"))
            except InvalidOperation:
                return False
            token_relative_start = core_text.find(match.group(0))
            if token_relative_start == -1:
                return False
            core_start += token_relative_start
            core_end = core_start + len(match.group(0))
        else:
            simple_match = _SIMPLE_TAG_WEIGHT_PATTERN.match(trimmed)
            if simple_match:
                tag = simple_match.group("tag").strip()
                try:
                    weight = Decimal(simple_match.group("weight"))
                except InvalidOperation:
                    return False
                token_relative_start = core_text.find(simple_match.group(0))
                if token_relative_start == -1:
                    return False
                core_start += token_relative_start
                core_end = core_start + len(simple_match.group(0))
            else:
                # Check if the selection sits inside an existing weighted tag.
                expanded_start = core_start
                expanded_end = core_end
                if expanded_start > 0 and text[expanded_start - 1] == "(":
                    closing_index = text.find(")", expanded_end)
                    if closing_index != -1:
                        candidate = text[expanded_start - 1 : closing_index + 1]
                        candidate_match = _TAG_WEIGHT_PATTERN.match(candidate.strip())
                        if candidate_match:
                            try:
                                weight = Decimal(candidate_match.group("weight"))
                            except InvalidOperation:
                                return False
                            tag = candidate_match.group("tag").strip()
                            core_start = expanded_start - 1
                            core_end = closing_index + 1
                        else:
                            inner = candidate.strip()[1:-1].strip()
                            if not inner:
                                return False
                            if "," in inner:
                                return False
                            tag = inner
                            weight = Decimal("1.0")
                            core_start = expanded_start - 1
                            core_end = closing_index + 1
                    else:
                        return False
                else:
                    if "," in trimmed:
                        return False
                    tag = trimmed
                    weight = Decimal("1.0")

        new_weight = weight + delta
        if new_weight < Decimal("0"):
            new_weight = Decimal("0")

        normalized = new_weight.normalize()
        if normalized == normalized.to_integral():
            formatted_weight = f"{normalized:.1f}"
        else:
            formatted_weight = format(normalized.normalize(), "f").rstrip("0").rstrip(".")
            if not formatted_weight:
                formatted_weight = "0"

        replacement = f"({tag}:{formatted_weight})"

        cursor.beginEditBlock()
        try:
            cursor.setPosition(core_start)
            cursor.setPosition(core_end, QtGui.QTextCursor.MoveMode.KeepAnchor)
            cursor.insertText(replacement)
            cursor.setPosition(core_start)
            cursor.setPosition(core_start + len(replacement), QtGui.QTextCursor.MoveMode.KeepAnchor)
        finally:
            cursor.endEditBlock()
        self.setTextCursor(cursor)
        return True


class LoraListItemWidget(QtWidgets.QWidget):
    """Widget shown inside a list that displays a single LoRA selection."""

    weightChanged = QtCore.pyqtSignal(str, float)
    removeRequested = QtCore.pyqtSignal(str)

    def __init__(self, info: LoraInfo, weight: float = 1.0, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        self.info = info

        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(6)

        self.label = QtWidgets.QLabel(info.display_name)
        self.label.setObjectName("loraLabel")
        layout.addWidget(self.label)

        self.weight_spin = NoWheelDoubleSpinBox(self)
        self.weight_spin.setRange(0.0, 2.0)
        self.weight_spin.setSingleStep(0.05)
        self.weight_spin.setDecimals(2)
        self.weight_spin.setValue(weight)
        self.weight_spin.setSuffix("x")
        self.weight_spin.valueChanged.connect(self._emit_weight_change)
        layout.addWidget(self.weight_spin)

        remove_button = QtWidgets.QToolButton(self)
        remove_button.setText("✕")
        remove_button.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
        remove_button.setToolTip("Remove this LoRA")
        remove_button.clicked.connect(lambda: self.removeRequested.emit(self.info.name))
        layout.addWidget(remove_button)

        layout.addStretch(1)

    def weight(self) -> float:
        return float(self.weight_spin.value())

    def set_weight(self, weight: float) -> None:
        with QtCore.QSignalBlocker(self.weight_spin):
            self.weight_spin.setValue(weight)

    def _emit_weight_change(self, value: float) -> None:
        self.weightChanged.emit(self.info.name, float(value))


class LoraSelectionList(QtWidgets.QListWidget):
    """Displays selected LoRAs with weights and removal controls."""

    selectionsChanged = QtCore.pyqtSignal()

    def __init__(self, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        self._items: Dict[str, QtWidgets.QListWidgetItem] = {}
        self._loading = False
        self.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
        self.setAlternatingRowColors(True)
        self.setMinimumHeight(110)

    def add_or_update(self, info: LoraInfo, weight: float = 1.0) -> None:
        item = self._items.get(info.name)
        if item is not None:
            widget = self.itemWidget(item)
            if isinstance(widget, LoraListItemWidget):
                widget.set_weight(weight)
            if not self._loading:
                self.selectionsChanged.emit()
            return

        widget_item = QtWidgets.QListWidgetItem()
        widget_item.setData(QtCore.Qt.ItemDataRole.UserRole, info.name)
        widget = LoraListItemWidget(info, weight, self)
        widget.weightChanged.connect(self._on_weight_changed)
        widget.removeRequested.connect(self._on_remove_requested)
        widget_item.setSizeHint(widget.sizeHint())
        self._items[info.name] = widget_item
        super().addItem(widget_item)
        self.setItemWidget(widget_item, widget)
        if not self._loading:
            self.selectionsChanged.emit()

    def selections(self) -> List[Tuple[LoraInfo, float]]:
        result: List[Tuple[LoraInfo, float]] = []
        for row in range(self.count()):
            item = self.item(row)
            if item is None:
                continue
            widget = self.itemWidget(item)
            if isinstance(widget, LoraListItemWidget):
                result.append((widget.info, widget.weight()))
        return result

    def remove_selected(self) -> None:
        item = self.currentItem()
        if item is None:
            return
        name = item.data(QtCore.Qt.ItemDataRole.UserRole)
        if isinstance(name, str):
            self._remove_by_name(name)

    def clear(self) -> None:  # type: ignore[override]
        self._loading = True
        try:
            self._items.clear()
            super().clear()
        finally:
            self._loading = False
        self.selectionsChanged.emit()

    def set_selections(self, selections: Iterable[Tuple[LoraInfo, float]]) -> None:
        self._loading = True
        try:
            self._items.clear()
            super().clear()
            for info, weight in selections:
                self.add_or_update(info, weight)
        finally:
            self._loading = False
        self.selectionsChanged.emit()

    def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:  # type: ignore[override]
        if event.key() in {QtCore.Qt.Key.Key_Delete, QtCore.Qt.Key.Key_Backspace}:
            current = self.currentItem()
            if current is not None:
                name = current.data(QtCore.Qt.ItemDataRole.UserRole)
                if isinstance(name, str):
                    self._remove_by_name(name)
                    event.accept()
                    return
        super().keyPressEvent(event)

    def _on_weight_changed(self, name: str, _weight: float) -> None:
        if not self._loading:
            self.selectionsChanged.emit()

    def _on_remove_requested(self, name: str) -> None:
        self._remove_by_name(name)

    def _remove_by_name(self, name: str) -> None:
        item = self._items.pop(name, None)
        if item is None:
            return
        row = self.row(item)
        if row >= 0:
            super().takeItem(row)
        if not self._loading:
            self.selectionsChanged.emit()
