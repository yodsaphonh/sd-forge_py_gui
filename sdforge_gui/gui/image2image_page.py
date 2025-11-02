"""Placeholder Image-to-Image tab."""
from __future__ import annotations

from typing import Optional

from PyQt6 import QtWidgets, QtCore


class ImageToImageWidget(QtWidgets.QWidget):
    def __init__(self, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent=parent)
        layout = QtWidgets.QVBoxLayout(self)
        layout.addStretch(1)
        notice = QtWidgets.QLabel(
            "Image to Image features will be added in a future iteration."
        )
        notice.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(notice)
        layout.addStretch(1)
