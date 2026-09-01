#!/usr/bin/env python3
"""
read-pdf converter — PDF → markdown + figures (marker backend).

Caches by SHA-256 of the PDF bytes. Re-running on the same content is free.

Usage:
    python3 convert.py <pdf-path>

Prints the absolute path to the cached markdown.md on success (exit 0).
On backend failure, exits non-zero with the error on stderr — no fallback.

Cache layout:
    ~/.cache/claude-pdf-converter/cache/marker/<sha256>/
        markdown.md       # verbatim conversion with inline ![](figures/...)
        figures/*.png     # extracted figures
        meta.json         # backend, version, page/figure counts, source path
"""

import hashlib
import json
import os
import platform
import re
import subprocess
import sys
import time
from pathlib import Path

BACKEND = "marker"
CACHE_ROOT = Path.home() / ".cache" / "claude-pdf-converter"
CACHE_DIR = CACHE_ROOT / "cache" / BACKEND
VENV_DIR = CACHE_ROOT / f"venv-{BACKEND}"
VENV_PYTHON = (
    VENV_DIR / "Scripts" / "python.exe"
    if platform.system() == "Windows"
    else VENV_DIR / "bin" / "python"
)
SKILL_DIR = Path(__file__).resolve().parent


def detect_torch_device() -> str:
    """Pick best available torch device: cuda > cpu. MPS excluded — surya's layout
    model crashes on Apple Silicon MPS with an index-bounds error at runtime."""
    try:
        import torch
    except ImportError:
        return "cpu"
    if torch.cuda.is_available():
        return "cuda"
    return "cpu"


def normalize_footnotes(text: str) -> str:
    """
    Rewrite marker's bare-number footnote encoding as Pandoc-style markdown footnotes.

    Marker places footnote superscripts as bare digits attached to the preceding
    word/punctuation, then dumps the footnote body as a standalone paragraph
    starting with the matching number at the next page-break boundary. This
    function detects matched anchor/definition pairs and rewrites them:

        ...coefficient.12 We then...      →  ...coefficient.[^12] We then...
        12The county-level cluster...      →  (removed from body)

    A definitions block is appended at the end of the document:

        [^12]: The county-level cluster...

    Guards: code fences, table rows, display-math paragraphs, and numbered list
    items (digit followed by ". " or ") ") are left untouched.
    Only numbers that appear as BOTH an anchor and a definition are rewritten —
    this is the primary false-positive guard.
    """
    paragraphs = re.split(r'\n\n+', text)

    # --- Pass 1: find definition paragraphs ---
    # Matches: bare 1–3 digit number at paragraph start, NOT followed by ". "
    # or ") " (numbered list items), then optional whitespace, then the body.
    # No mandatory space between number and body (handles OCR gaps in old scans).
    fn_def_re = re.compile(r'^(\d{1,3})(?!\.\s|\)\s)\s*(\S.+)', re.DOTALL)

    footnote_defs: dict[str, str] = {}
    def_para_indices: set[int] = set()
    in_fence = False

    for i, para in enumerate(paragraphs):
        stripped = para.strip()
        # Track code-fence state across paragraphs
        if stripped.count('```') % 2 != 0:
            in_fence = not in_fence
        if in_fence:
            continue
        # Skip tables, display math, and code fences
        if re.match(r'\s*(\||```|\$\$)', stripped):
            continue
        m = fn_def_re.match(stripped)
        if m:
            num, body = m.group(1), m.group(2).strip()
            if body and not body.isdigit():
                footnote_defs[num] = body
                def_para_indices.add(i)

    if not footnote_defs:
        return text

    # --- Pass 2: replace anchors in body paragraphs ---
    # Anchor: one of the known footnote numbers immediately following a word
    # character or sentence-ending punctuation, not preceded by '[' (citation).
    # Lookahead: whitespace, sentence punctuation, closing bracket, or EOL.
    nums_alt = '|'.join(re.escape(n) for n in sorted(footnote_defs, key=lambda x: -len(x)))
    anchor_re = re.compile(
        r'(?<=[a-zA-Z.,;:!?\'")\]])(?<!\[)(' + nums_alt + r')(?=[\s,.:;!?\n\)\]]|$)'
    )

    result_paras: list[str] = []
    in_fence = False
    for i, para in enumerate(paragraphs):
        stripped = para.strip()
        if stripped.count('```') % 2 != 0:
            in_fence = not in_fence

        if i in def_para_indices:
            continue  # will be collected at end

        # Skip anchor replacement inside protected blocks
        if in_fence or re.match(r'\s*(\||```|\$\$)', stripped):
            result_paras.append(para)
        else:
            result_paras.append(anchor_re.sub(lambda m: f'[^{m.group(1)}]', para))

    # Append all definitions in numerical order
    defs_block = '\n\n'.join(
        f'[^{n}]: {footnote_defs[n]}'
        for n in sorted(footnote_defs, key=int)
    )
    result_paras.append(defs_block)

    return '\n\n'.join(result_paras)


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def text_layer_chars(path: Path, pages: int = 3) -> int:
    """Return non-whitespace chars extracted from the PDF text layer sample."""
    try:
        result = subprocess.run(
            ["pdftotext", "-l", str(pages), str(path), "-"],
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return 0
    if result.returncode != 0:
        return 0
    return sum(1 for ch in result.stdout if not ch.isspace())


def in_venv() -> bool:
    return Path(sys.prefix).resolve() == VENV_DIR.resolve()


def reexec_in_venv(args: list[str]) -> None:
    """Re-run this script under the backend venv's Python."""
    if not VENV_PYTHON.exists():
        installer = SKILL_DIR / "install.py"
        subprocess.run([sys.executable, str(installer)], check=True)
    os.execv(str(VENV_PYTHON), [str(VENV_PYTHON), str(Path(__file__).resolve()), *args])


def convert_with_marker(pdf_path: Path, out_dir: Path) -> dict:
    from marker.converters.pdf import PdfConverter
    from marker.models import create_model_dict
    from marker.output import text_from_rendered

    text_chars = text_layer_chars(pdf_path)
    use_text_layer = text_chars >= 500
    config = {"disable_ocr": True} if use_text_layer else {}
    converter = PdfConverter(artifact_dict=create_model_dict(), config=config)
    rendered = converter(str(pdf_path))
    text, _, images = text_from_rendered(rendered)

    figures_dir = out_dir / "figures"
    figures_dir.mkdir(exist_ok=True)

    fig_count = 0
    for name, img in (images or {}).items():
        out_name = figures_dir / Path(name).name
        try:
            img.save(out_name)
            fig_count += 1
        except Exception as exc:  # pragma: no cover
            print(f"warn: figure {name} save failed: {exc}", file=sys.stderr)

    text = normalize_footnotes(text)
    (out_dir / "markdown.md").write_text(text, encoding="utf-8")

    return {
        "backend": "marker",
        "page_count": None,
        "figure_count": fig_count,
        "text_layer_chars_sample": text_chars,
        "ocr_disabled": use_text_layer,
        "equation_extraction_mode": "native",  # marker emits LaTeX directly
    }


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: convert.py <pdf-path>", file=sys.stderr)
        return 2

    pdf_path = Path(sys.argv[1]).expanduser().resolve()
    if not pdf_path.is_file():
        print(f"error: not a file: {pdf_path}", file=sys.stderr)
        return 2

    if not in_venv():
        reexec_in_venv([str(pdf_path)])

    # Marker reads TORCH_DEVICE at import time. Set before importing the
    # backend, after we're inside the venv (so torch is the venv's torch).
    if "TORCH_DEVICE" not in os.environ:
        os.environ["TORCH_DEVICE"] = detect_torch_device()

    digest = sha256_of(pdf_path)
    out_dir = CACHE_DIR / digest
    md_path = out_dir / "markdown.md"
    if md_path.is_file():
        print(str(md_path))
        return 0

    out_dir.mkdir(parents=True, exist_ok=True)
    started = time.time()
    info = convert_with_marker(pdf_path, out_dir)
    info.update(
        {
            "source_path": str(pdf_path),
            "sha256": digest,
            "elapsed_seconds": round(time.time() - started, 2),
            "torch_device": os.environ.get("TORCH_DEVICE", "cpu"),
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
    )
    (out_dir / "meta.json").write_text(
        json.dumps(info, indent=2), encoding="utf-8"
    )
    print(str(md_path))
    return 0


if __name__ == "__main__":
    sys.exit(main())
