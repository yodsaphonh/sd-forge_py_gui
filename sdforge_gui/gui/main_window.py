"""Main window composed of multiple tabs."""
from __future__ import annotations

from typing import Optional

from PyQt6 import QtCore, QtGui, QtWidgets

from ..api_client import StableDiffusionClient
from ..ui_config import UIConfig
from .image2image_page import ImageToImageWidget
from .image_info_page import ImageInfoWidget
from .text2image_page import TextToImageWidget


class MainWindow(QtWidgets.QMainWindow):
    def __init__(
        self,
        client: StableDiffusionClient,
        ui_config: UIConfig,
        parent: Optional[QtWidgets.QWidget] = None,
    ) -> None:
        super().__init__(parent=parent)
        self.client = client
        self.ui_config = ui_config
        self.settings = QtCore.QSettings(self)
        self.setWindowTitle("Stable Diffusion Forge GUI")
        self.resize(1200, 720)
        self._apply_theme()

        self.tab_widget = QtWidgets.QTabWidget()

        central = QtWidgets.QWidget()
        central_layout = QtWidgets.QVBoxLayout(central)
        central_layout.setContentsMargins(0, 0, 0, 0)
        central_layout.setSpacing(0)

        self.connection_bar = QtWidgets.QWidget()
        bar_layout = QtWidgets.QHBoxLayout(self.connection_bar)
        bar_layout.setContentsMargins(12, 12, 12, 6)
        bar_layout.setSpacing(8)

        bar_label = QtWidgets.QLabel("API base URL")
        bar_layout.addWidget(bar_label)

        self.api_url_edit = QtWidgets.QLineEdit()
        self.api_url_edit.setPlaceholderText("http://127.0.0.1:7860")
        self.api_url_edit.setClearButtonEnabled(True)
        bar_layout.addWidget(self.api_url_edit, stretch=1)

        self.api_url_button = QtWidgets.QPushButton("Apply")
        bar_layout.addWidget(self.api_url_button)

        central_layout.addWidget(self.connection_bar)
        central_layout.addWidget(self.tab_widget, stretch=1)
        self.setCentralWidget(central)

        stored_url = self.settings.value("api/base_url", type=str)
        initial_url = self._normalize_api_url(stored_url) if stored_url else None
        if initial_url:
            try:
                self.client.base_url = initial_url
            except ValueError:
                initial_url = None
        if not initial_url:
            initial_url = self.client.base_url
        self.api_url_edit.setText(initial_url)

        self.api_url_edit.editingFinished.connect(self._on_api_url_applied)
        self.api_url_button.clicked.connect(self._on_api_url_applied)

        self.text_to_image_tab = TextToImageWidget(client, ui_config, self)

        self.tab_widget.addTab(self.text_to_image_tab, "Text to Image")
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

    def _normalize_api_url(self, text: Optional[str]) -> Optional[str]:
        if not text:
            return None
        cleaned = text.strip()
        if not cleaned:
            return None
        if "://" not in cleaned:
            cleaned = f"http://{cleaned}"
        return cleaned.rstrip("/")

    def _on_api_url_applied(self) -> None:
        normalized = self._normalize_api_url(self.api_url_edit.text())
        if not normalized:
            QtWidgets.QMessageBox.warning(
                self,
                "Invalid URL",
                "Please enter a valid API base URL.",
            )
            self.api_url_edit.setText(self.client.base_url)
            return

        if self.text_to_image_tab.is_generation_active():
            QtWidgets.QMessageBox.information(
                self,
                "Generation in progress",
                "Please wait for the current generation to finish before changing the API URL.",
            )
            self.api_url_edit.setText(self.client.base_url)
            return

        if normalized == self.client.base_url:
            self.statusBar().showMessage("API base URL unchanged.", 3000)
            return

        try:
            self.client.base_url = normalized
        except ValueError:
            QtWidgets.QMessageBox.warning(
                self,
                "Invalid URL",
                "The API base URL cannot be empty.",
            )
            self.api_url_edit.setText(self.client.base_url)
            return

        self.settings.setValue("api/base_url", normalized)
        self.settings.sync()
        self.api_url_edit.setText(normalized)
        self.statusBar().showMessage(f"API base URL set to {normalized}", 5000)
        self.text_to_image_tab.reload_metadata()
