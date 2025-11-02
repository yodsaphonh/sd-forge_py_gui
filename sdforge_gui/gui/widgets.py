"""Shared custom Qt widgets."""
from __future__ import annotations

from typing import Iterable, Sequence

from PyQt6 import QtCore, QtGui, QtWidgets


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
