#!/usr/bin/env python3
"""Extract problem statements from PDF files into Markdown."""

from __future__ import annotations

import argparse
from pathlib import Path

import fitz
import pytesseract
from PIL import Image


def normalize_text(text: str) -> str:
    text = text.replace("\u3000", " ")
    lines = [line.rstrip() for line in text.splitlines()]
    return "\n".join(lines).strip()


def pdf_text(path: Path) -> str:
    doc = fitz.open(path)
    parts = [page.get_text("text") for page in doc]
    doc.close()
    return normalize_text("\n".join(parts))


def ocr_pdf(path: Path, dpi: int, lang: str) -> str:
    doc = fitz.open(path)
    parts = []
    for idx, page in enumerate(doc):
        pix = page.get_pixmap(dpi=dpi, alpha=False)
        image = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
        parts.append(f"\n\n--- OCR PAGE {idx + 1} ---\n")
        parts.append(pytesseract.image_to_string(image, lang=lang, config="--psm 6"))
    doc.close()
    return normalize_text("\n".join(parts))


def infer_title(text: str, fallback: str) -> str:
    for line in text.splitlines():
        clean = line.strip()
        if clean and "题" in clean:
            return clean
    return fallback


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pdf", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--title", default=None)
    parser.add_argument("--ocr", action="store_true")
    parser.add_argument("--ocr-dpi", type=int, default=180)
    parser.add_argument("--ocr-lang", default="chi_sim+eng")
    args = parser.parse_args()

    text = pdf_text(args.pdf)
    if args.ocr or len(text) < 100:
        text = ocr_pdf(args.pdf, dpi=args.ocr_dpi, lang=args.ocr_lang)
    title = args.title or infer_title(text, args.pdf.stem)
    body = [
        f"# {title}",
        "",
        f"- 来源文件：`{args.pdf}`",
        "",
        "## 题面文本",
        "",
        text,
        "",
    ]
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text("\n".join(body), encoding="utf-8")
    print(args.out)


if __name__ == "__main__":
    main()
