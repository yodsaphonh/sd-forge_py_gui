"""Entry point for launching the Stable Diffusion Forge GUI."""
from __future__ import annotations

import sys

from sdforge_gui.gui.application import run_app


if __name__ == "__main__":  # pragma: no cover
    sys.exit(run_app())
