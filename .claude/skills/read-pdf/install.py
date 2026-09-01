#!/usr/bin/env python3
"""
read-pdf installer — sets up the local PDF→markdown converter (marker backend).

Idempotent. First run creates a venv at ~/.cache/claude-pdf-converter/venv-marker/,
installs marker-pdf, and warms up model downloads. Subsequent runs reuse the
existing install if marker imports cleanly. They do not check PyPI or
auto-upgrade marker, but they run a lazy monthly check for marker major-version
updates and surface an advisory when one is available.

The venv lives outside any git repo so that backend models (~hundreds of MB)
do not pollute the skills checkout.

OS-agnostic: searches for a Python ≥ 3.10 across macOS, Linux, and Windows
common install locations. If none is found, prints a platform-aware install hint.
"""

import argparse
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

BACKEND = "marker"
PACKAGE = "marker-pdf"
PINS = [PACKAGE]  # unpinned first install; no automatic upgrades after setup
CHECK_INTERVAL_SECONDS = 30 * 24 * 60 * 60

PY_MIN = (3, 10)

# Names to try on PATH. Cross-platform: same on macOS/Linux/Windows because
# python.org and most package managers install with these names.
PY_NAMES = ["python3.13", "python3.12", "python3.11", "python3.10", "python3", "python"]

# Absolute fallback paths by OS, only consulted if PATH search fails.
def _fallback_paths() -> list[str]:
    sysname = platform.system()
    if sysname == "Darwin":
        return [
            f"/Library/Frameworks/Python.framework/Versions/{v}/bin/python{v}"
            for v in ("3.13", "3.12", "3.11", "3.10")
        ] + [
            f"/opt/homebrew/bin/python{v}" for v in ("3.13", "3.12", "3.11", "3.10")
        ] + [
            f"/usr/local/bin/python{v}" for v in ("3.13", "3.12", "3.11", "3.10")
        ]
    if sysname == "Linux":
        return [f"/usr/bin/python{v}" for v in ("3.13", "3.12", "3.11", "3.10")]
    if sysname == "Windows":
        # py launcher handles version selection on Windows
        return ["py", "-3.13", "py", "-3.12", "py", "-3.11", "py", "-3.10"]
    return []


def _install_hint() -> str:
    sysname = platform.system()
    if sysname == "Darwin":
        return "Install Python 3.10+ via `brew install python@3.12` or python.org installer."
    if sysname == "Linux":
        return "Install Python 3.10+ via your package manager (e.g. `apt install python3.12` or `dnf install python3.12`)."
    if sysname == "Windows":
        return "Install Python 3.10+ via `winget install Python.Python.3.12` or python.org installer."
    return "Install Python 3.10 or newer."


def _check_version(path: str) -> bool:
    try:
        out = subprocess.check_output(
            [path, "-c", "import sys; print('%d.%d' % sys.version_info[:2])"],
            text=True, stderr=subprocess.DEVNULL,
        ).strip()
        major, minor = (int(x) for x in out.split("."))
        return (major, minor) >= PY_MIN
    except Exception:
        return False


def find_python() -> str:
    """Return path to a Python ≥3.10. Prefers the running interpreter if it qualifies."""
    if sys.version_info >= PY_MIN:
        return sys.executable
    for name in PY_NAMES:
        path = shutil.which(name)
        if path and _check_version(path):
            return path
    for cand in _fallback_paths():
        path = cand if Path(cand).exists() else shutil.which(cand)
        if path and _check_version(path):
            return path
    print(
        f"error: need Python ≥{PY_MIN[0]}.{PY_MIN[1]} but found only "
        f"{sys.version_info.major}.{sys.version_info.minor}.\n"
        f"{_install_hint()}",
        file=sys.stderr,
    )
    sys.exit(2)


CACHE_ROOT = Path.home() / ".cache" / "claude-pdf-converter"
VENV_DIR = CACHE_ROOT / f"venv-{BACKEND}"
CHECK_FILE = CACHE_ROOT / f"version-check-{BACKEND}.json"


def venv_python() -> Path:
    # Windows venvs put python in Scripts/, not bin/
    if platform.system() == "Windows":
        return VENV_DIR / "Scripts" / "python.exe"
    return VENV_DIR / "bin" / "python"


def venv_exists() -> bool:
    return venv_python().exists()


def backend_imports() -> bool:
    if not venv_exists():
        return False
    result = subprocess.run(
        [str(venv_python()), "-c", "import marker"],
        capture_output=True,
    )
    return result.returncode == 0


def installed_marker_version() -> str | None:
    """Return the installed marker-pdf version inside the backend venv."""
    if not venv_exists():
        return None
    result = subprocess.run(
        [
            str(venv_python()),
            "-c",
            (
                "import importlib.metadata; "
                f"print(importlib.metadata.version('{PACKAGE}'))"
            ),
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def version_major(version: str | None) -> int | None:
    """Extract a simple PEP 440-style leading major version."""
    if not version:
        return None
    match = re.match(r"^\s*(\d+)", version)
    return int(match.group(1)) if match else None


def latest_marker_version() -> str | None:
    """Fetch the latest marker-pdf release from PyPI. Network failures are nonfatal."""
    url = f"https://pypi.org/pypi/{PACKAGE}/json"
    try:
        with urllib.request.urlopen(url, timeout=5) as response:
            payload = json.load(response)
    except (OSError, urllib.error.URLError, TimeoutError, json.JSONDecodeError):
        return latest_marker_version_from_pip()
    return payload.get("info", {}).get("version")


def latest_marker_version_from_pip() -> str | None:
    """Use pip's index command as a fallback when Python TLS certs are unavailable."""
    if not venv_exists():
        return None
    try:
        result = subprocess.run(
            [str(venv_python()), "-m", "pip", "index", "versions", PACKAGE],
            capture_output=True,
            text=True,
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None
    match = re.search(r"^\s*LATEST:\s*(\S+)", result.stdout, re.MULTILINE)
    if match:
        return match.group(1)
    match = re.search(rf"^{re.escape(PACKAGE)}\s+\(([^)]+)\)", result.stdout)
    return match.group(1) if match else None


def monthly_check_due(force: bool = False) -> bool:
    """Return true when the lazy update check should hit PyPI."""
    if force:
        return True
    try:
        checked_at = json.loads(CHECK_FILE.read_text(encoding="utf-8")).get(
            "checked_at", 0
        )
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return True
    return (time.time() - float(checked_at)) >= CHECK_INTERVAL_SECONDS


def record_version_check(installed: str | None, latest: str | None) -> None:
    """Persist the last version check so normal invocations avoid network calls."""
    CACHE_ROOT.mkdir(parents=True, exist_ok=True)
    CHECK_FILE.write_text(
        json.dumps(
            {
                "checked_at": time.time(),
                "package": PACKAGE,
                "installed_version": installed,
                "latest_version": latest,
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def check_for_major_update(force: bool = False) -> None:
    """Warn when PyPI has crossed a marker-pdf major-version boundary."""
    if not monthly_check_due(force):
        return
    installed = installed_marker_version()
    latest = latest_marker_version()
    if latest is None:
        return
    record_version_check(installed, latest)
    installed_major = version_major(installed)
    latest_major = version_major(latest)
    if (
        installed
        and latest
        and installed_major is not None
        and latest_major is not None
        and latest_major > installed_major
    ):
        print(
            "\nread-pdf notice: marker-pdf has a major update available.\n"
            f"  installed: {installed}\n"
            f"  latest:    {latest}\n"
            "Major marker updates may change PDF conversion behavior. "
            "Upgrade only when you are ready to review conversion output.\n"
            f"To upgrade: {sys.executable} {Path(__file__).resolve()} --upgrade-marker\n"
            "Existing cached conversions will be left in place. To force "
            "re-conversion after upgrading, delete selected cache entries under "
            f"{CACHE_ROOT / 'cache' / BACKEND}, or delete that whole directory. "
            "Large caches may take a long time to rebuild.",
            flush=True,
        )


def create_venv() -> None:
    CACHE_ROOT.mkdir(parents=True, exist_ok=True)
    print(
        f"First run: creating venv at {VENV_DIR} and installing "
        f"{BACKEND} (~500MB, 1–3 min, one-time).",
        flush=True,
    )
    base_python = find_python()
    subprocess.run([base_python, "-m", "venv", str(VENV_DIR)], check=True)
    subprocess.run(
        [str(venv_python()), "-m", "pip", "install", "--upgrade", "pip"],
        check=True,
    )
    subprocess.run(
        [str(venv_python()), "-m", "pip", "install", *PINS],
        check=True,
    )


def upgrade_marker() -> None:
    """Explicit opt-in marker upgrade; never called during normal setup."""
    if not venv_exists():
        create_venv()
    before = installed_marker_version() or "not installed"
    subprocess.run(
        [str(venv_python()), "-m", "pip", "install", "--upgrade", PACKAGE],
        check=True,
    )
    after = installed_marker_version() or "unknown"
    print(f"marker-pdf upgraded: {before} -> {after}", flush=True)
    record_version_check(after, after)


def warmup_models() -> None:
    """Trigger first-run model download so the first conversion is fast."""
    print("Downloading layout/OCR models (one-time)...", flush=True)
    subprocess.run(
        [str(venv_python()), "-c",
         "from marker.models import create_model_dict; create_model_dict()"],
        check=True,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Install the read-pdf marker backend.")
    parser.add_argument(
        "--upgrade-marker",
        action="store_true",
        help="Explicitly upgrade marker-pdf in the read-pdf venv.",
    )
    parser.add_argument(
        "--force-version-check",
        action="store_true",
        help="Check PyPI for marker-pdf major-version updates even if checked recently.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.upgrade_marker:
        upgrade_marker()
        warmup_models()
        return 0
    if backend_imports():
        print(
            "read-pdf setup already present. Reusing existing marker install "
            "(no automatic update).",
            flush=True,
        )
        check_for_major_update(force=args.force_version_check)
        return 0
    if not venv_exists():
        create_venv()
    warmup_models()
    record_version_check(installed_marker_version(), installed_marker_version())
    print(f"read-pdf setup complete. Backend: {BACKEND}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
