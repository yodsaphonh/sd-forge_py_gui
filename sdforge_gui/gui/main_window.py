"""Main window composed of multiple tabs."""
from __future__ import annotations

from typing import Optional

from PyQt6 import QtCore, QtGui, QtWidgets

from ..api_client import StableDiffusionClient
from .image2image_page import ImageToImageWidget
from .image_info_page import ImageInfoWidget
from .text2image_page import TextToImageWidget


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, client: StableDiffusionClient, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent=parent)
        self.client = client
        self.setWindowTitle("Stable Diffusion Forge GUI")
        self.resize(1200, 720)
        self._apply_theme()

        self.tab_widget = QtWidgets.QTabWidget()
        self.setCentralWidget(self.tab_widget)

        self.tab_widget.addTab(TextToImageWidget(client, self), "Text to Image")
        self.tab_widget.addTab(ImageToImageWidget(self), "Image to Image")
        self.tab_widget.addTab(ImageInfoWidget(self), "Image Info")

        self.statusBar().showMessage("Ready")

    def _apply_theme(self) -> None:
        palette = QtGui.QPalette()
        palette.setColor(QtGui.QPalette.ColorRole.Window, QtGui.QColor(26, 26, 30))
        palette.setColor(QtGui.QPalette.ColorRole.Base, QtGui.QColor(34, 34, 38))
        palette.setColor(QtGui.QPalette.ColorRole.AlternateBase, QtGui.QColor(44, 44, 50))
        palette.setColor(QtGui.QPalette.ColorRole.Text, QtGui.QColor(230, 230, 230))
        palette.setColor(QtGui.QPalette.ColorRole.Button, QtGui.QColor(44, 44, 50))
        palette.setColor(QtGui.QPalette.ColorRole.ButtonText, QtGui.QColor(240, 240, 240))
        palette.setColor(QtGui.QPalette.ColorRole.Highlight, QtGui.QColor(114, 137, 218))
        palette.setColor(QtGui.QPalette.ColorRole.HighlightedText, QtGui.QColor(0, 0, 0))
        palette.setColor(QtGui.QPalette.ColorRole.WindowText, QtGui.QColor(240, 240, 240))
        self.setPalette(palette)

        self.setStyleSheet(
            """
            QWidget {
                font-family: 'Segoe UI', 'Noto Sans', sans-serif;
                font-size: 12pt;
                color: #f0f0f0;
            }
            QPlainTextEdit, QTextEdit {
                background-color: #1e1e22;
                border: 1px solid #3f3f46;
                border-radius: 6px;
                padding: 8px;
            }
            QComboBox, QSpinBox, QDoubleSpinBox {
                background-color: #2a2a30;
                border-radius: 6px;
                padding: 4px 8px;
                border: 1px solid #3f3f46;
            }
            QPushButton#generateButton {
                background-color: #4c6ef5;
                border-radius: 8px;
                padding: 10px 16px;
                color: white;
                font-weight: bold;
            }
            QPushButton#generateButton:disabled {
                background-color: #3a3a3e;
            }
            QLabel#statusLabel {
                color: #c9c9d1;
            }
            QTabBar::tab {
                padding: 8px 16px;
                background-color: #202024;
                border: 1px solid #2e2e34;
                border-bottom: none;
            }
            QTabBar::tab:selected {
                background-color: #363642;
            }
            """
        )

        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_StyledBackground, True)
