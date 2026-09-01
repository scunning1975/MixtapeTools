#!/usr/bin/env python3
"""
read-pdf installer — sets up the local PDF→markdown converter (marker backend).

Idempotent. First run creates a venv at ~/.cache/claude-pdf-converter/venv-marker/,
installs marker-pdf, and warms up model downloads. Subsequent runs short-circuit
if marker imports cleanly under the venv.

The venv lives outside any git repo so that backend models (~hundreds of MB)
do not pollute the skills checkout.

OS-agnostic: searches for a Python ≥ 3.10 across macOS, Linux, and Windows
common install locations. If none is found, prints a platform-aware install hint.
"""

import platform
import shutil
import subprocess
import sys
from pathlib import Path

BACKEND = "marker"
PINS = ["marker-pdf"]  # latest; pin a version after a regression is observed

PY_MIN = (3, 10)

# Names to try on PATH. Cross-platform: same on macOS/Linux/Windows because
# python.org and most package managers install with these names.
PY_NAMES = ["python3.13", "python3.12", "python3.11", "python3.10", "python3", "python"]

# Absolute fallback paths by OS, only consulted if PATH search fails.
def _fallback_paths() -> list[list[str]]:
    sysname = platform.system()
    if sysname == "Darwin":
        return [[path] for path in (
            f"/Library/Frameworks/Python.framework/Versions/{v}/bin/python{v}"
            for v in ("3.13", "3.12", "3.11", "3.10")
        )] + [[path] for path in (
            f"/opt/homebrew/bin/python{v}" for v in ("3.13", "3.12", "3.11", "3.10")
        )] + [[path] for path in (
            f"/usr/local/bin/python{v}" for v in ("3.13", "3.12", "3.11", "3.10")
        )]
    if sysname == "Linux":
        return [[f"/usr/bin/python{v}"] for v in ("3.13", "3.12", "3.11", "3.10")]
    if sysname == "Windows":
        # py launcher handles version selection on Windows
        return [["py", f"-{v}"] for v in ("3.13", "3.12", "3.11", "3.10")]
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


def _check_version(cmd: list[str]) -> bool:
    try:
        out = subprocess.check_output(
            [*cmd, "-c", "import sys; print('%d.%d' % sys.version_info[:2])"],
            text=True, stderr=subprocess.DEVNULL,
        ).strip()
        major, minor = (int(x) for x in out.split("."))
        return (major, minor) >= PY_MIN
    except Exception:
        return False


def find_python() -> list[str]:
    """Return command for a Python ≥3.10. Prefers the running interpreter if it qualifies."""
    if sys.version_info >= PY_MIN:
        return [sys.executable]
    for name in PY_NAMES:
        path = shutil.which(name)
        if path and _check_version([path]):
            return [path]
    for cand in _fallback_paths():
        executable = cand[0]
        path = executable if Path(executable).exists() else shutil.which(executable)
        if path:
            cmd = [path, *cand[1:]]
            if _check_version(cmd):
                return cmd
    print(
        f"error: need Python ≥{PY_MIN[0]}.{PY_MIN[1]} but found only "
        f"{sys.version_info.major}.{sys.version_info.minor}.\n"
        f"{_install_hint()}",
        file=sys.stderr,
    )
    sys.exit(2)


CACHE_ROOT = Path.home() / ".cache" / "claude-pdf-converter"
VENV_DIR = CACHE_ROOT / f"venv-{BACKEND}"


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


def create_venv() -> None:
    CACHE_ROOT.mkdir(parents=True, exist_ok=True)
    print(
        f"First run: creating venv at {VENV_DIR} and installing "
        f"{BACKEND} (~500MB, 1–3 min, one-time).",
        flush=True,
    )
    base_python = find_python()
    subprocess.run([*base_python, "-m", "venv", str(VENV_DIR)], check=True)
    subprocess.run(
        [str(venv_python()), "-m", "pip", "install", "--upgrade", "pip"],
        check=True,
    )
    subprocess.run(
        [str(venv_python()), "-m", "pip", "install", *PINS],
        check=True,
    )


def warmup_models() -> None:
    """Trigger first-run model download so the first conversion is fast."""
    print("Downloading layout/OCR models (one-time)...", flush=True)
    subprocess.run(
        [str(venv_python()), "-c",
         "from marker.models import create_model_dict; create_model_dict()"],
        check=True,
    )


def main() -> int:
    if backend_imports():
        return 0
    if not venv_exists():
        create_venv()
    warmup_models()
    print(f"read-pdf setup complete. Backend: {BACKEND}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
