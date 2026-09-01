#!/usr/bin/env python3
"""Split a PDF into fixed-size page chunks using the skill directory convention."""

from __future__ import annotations

import argparse
import math
from pathlib import Path

from pypdf import PdfReader, PdfWriter


def default_split_dir(pdf_path: Path) -> Path:
    folder_path = pdf_path.resolve().parent
    folder_name = folder_path.name
    return folder_path / f"{folder_name}_build" / f"split_{pdf_path.stem}"


def split_pdf(input_path: Path, output_dir: Path, pages_per_chunk: int) -> tuple[int, int]:
    output_dir.mkdir(parents=True, exist_ok=True)
    reader = PdfReader(str(input_path))
    total_pages = len(reader.pages)

    for start in range(0, total_pages, pages_per_chunk):
        end = min(start + pages_per_chunk, total_pages)
        writer = PdfWriter()

        for page_index in range(start, end):
            writer.add_page(reader.pages[page_index])

        output_path = output_dir / f"{input_path.stem}_pp{start + 1}-{end}.pdf"
        with output_path.open("wb") as handle:
            writer.write(handle)

    return total_pages, math.ceil(total_pages / pages_per_chunk)


def main() -> None:
    parser = argparse.ArgumentParser(description="Split a PDF into fixed-size page chunks.")
    parser.add_argument("pdf_path", type=Path, help="PDF to split")
    parser.add_argument("--output-dir", type=Path, default=None, help="Directory for split PDFs")
    parser.add_argument("--pages-per-chunk", type=int, default=4, help="Pages per split PDF")
    args = parser.parse_args()

    if args.pages_per_chunk < 1:
        raise SystemExit("--pages-per-chunk must be at least 1")

    pdf_path = args.pdf_path.expanduser().resolve()
    if not pdf_path.is_file():
        raise SystemExit(f"PDF not found: {pdf_path}")

    output_dir = args.output_dir.expanduser().resolve() if args.output_dir else default_split_dir(pdf_path)
    total_pages, chunk_count = split_pdf(pdf_path, output_dir, args.pages_per_chunk)
    print(f"Split {total_pages} pages into {chunk_count} chunks in {output_dir}")


if __name__ == "__main__":
    main()
