"""Application bootstrap utilities."""
from __future__ import annotations

import argparse
from typing import Optional

from PyQt6 import QtCore, QtWidgets

from ..api_client import StableDiffusionClient
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
    app = QtWidgets.QApplication([])
    client = StableDiffusionClient(base_url=args.api_url)

    window = MainWindow(client)
    window.show()

    return app.exec()
