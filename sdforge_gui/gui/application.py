"""Application bootstrap utilities."""
from __future__ import annotations

import argparse
from typing import Optional

from PyQt6 import QtCore, QtWidgets

from ..api_client import StableDiffusionClient
from ..ui_config import UIConfig
from .main_window import MainWindow


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Stable Diffusion Forge desktop GUI")
    parser.add_argument(
        "--api-url",
        default="http://127.0.0.1:7860",
        help="Base URL for the running Stable Diffusion Forge API",
    )
    return parser


def run_app(argv: Optional[list[str]] = None) -> int:
    parser = build_argument_parser()
    args = parser.parse_args(argv)

    QtCore.QLocale.setDefault(
        QtCore.QLocale(QtCore.QLocale.Language.English, QtCore.QLocale.Country.UnitedStates)
    )
    QtCore.QCoreApplication.setOrganizationName("SDForge")
    QtCore.QCoreApplication.setOrganizationDomain("sdforge.app")
    QtCore.QCoreApplication.setApplicationName("StableDiffusionGUI")
    app = QtWidgets.QApplication([])
    client = StableDiffusionClient(base_url=args.api_url)
    ui_config = UIConfig()

    window = MainWindow(client, ui_config)
    window.show()

    if ui_config.error:
        QtWidgets.QMessageBox.warning(
            window,
            "UI configuration error",
            f"Failed to load ui-config.json: {ui_config.error}",
        )

    return app.exec()
