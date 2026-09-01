#!/usr/bin/env python3
"""Compatibility shim for the canonical read-pdf split backend."""

from __future__ import annotations

import runpy
from pathlib import Path


CANONICAL_SPLITTER = (
    Path(__file__).resolve().parents[2] / "read-pdf" / "scripts" / "split.py"
)


if __name__ == "__main__":
    runpy.run_path(str(CANONICAL_SPLITTER), run_name="__main__")
