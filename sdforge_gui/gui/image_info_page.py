"""Placeholder for image metadata inspection."""
from __future__ import annotations

from typing import Optional

from PyQt6 import QtWidgets, QtCore


class ImageInfoWidget(QtWidgets.QWidget):
    def __init__(self, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent=parent)
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)

        label = QtWidgets.QLabel(
            "Drop an image here to inspect its metadata (coming soon)."
        )
        label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        label.setWordWrap(True)
        layout.addStretch(1)
        layout.addWidget(label)
        layout.addStretch(1)
