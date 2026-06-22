"""Import helper for running pipeline modules directly during development."""

from __future__ import annotations

import sys
from pathlib import Path


def ensure_project_root() -> None:
    root = Path(__file__).resolve().parents[2]
    root_text = str(root)
    if root_text not in sys.path:
        sys.path.insert(0, root_text)


__all__ = ["ensure_project_root"]
