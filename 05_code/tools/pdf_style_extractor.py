#!/usr/bin/env python3
"""Extract high-level style signals from CUMCM excellent-paper PDFs."""

from __future__ import annotations

import argparse
import csv
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

import fitz
import pytesseract
from PIL import Image


KEYWORDS = [
    "摘要",
    "关键词",
    "问题重述",
    "问题分析",
    "模型假设",
    "符号说明",
    "模型建立",
    "模型求解",
    "模型检验",
    "灵敏度",
    "敏感性",
    "误差分析",
    "鲁棒性",
    "稳定性",
    "优缺点",
    "模型评价",
    "推广",
    "参考文献",
    "附录",
    "MATLAB",
    "Python",
]


SECTION_PATTERNS = [
    "摘要",
    "问题重述",
    "问题分析",
    "模型假设",
    "符号说明",
    "模型的建立",
    "模型建立",
    "模型的求解",
    "模型求解",
    "模型检验",
    "结果分析",
    "敏感性分析",
    "灵敏度分析",
    "误差分析",
    "模型评价",
    "优缺点",
    "参考文献",
    "附录",
]


@dataclass
class PaperSignals:
    path: Path
    pages: int
    chars: int
    ocr_pages: str
    keyword_counts: Counter[str]
    detected_sections: list[str]
    abstract_preview: str


def normalize_text(text: str) -> str:
    text = text.replace("\u3000", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    spaced_terms = [
        "摘要",
        "关键词",
        "关键字",
        "问题重述",
        "问题分析",
        "模型假设",
        "符号说明",
        "模型建立",
        "模型求解",
        "模型检验",
        "敏感性分析",
        "灵敏度分析",
        "误差分析",
        "参考文献",
        "附录",
    ]
    for term in spaced_terms:
        pattern = r"\s*".join(map(re.escape, term))
        text = re.sub(pattern, term, text)
    return text.strip()


def extract_text(pdf_path: Path, max_pages: int | None = None) -> tuple[str, int]:
    doc = fitz.open(pdf_path)
    page_count = len(doc)
    limit = page_count if max_pages is None else min(page_count, max_pages)
    parts = []
    for idx in range(limit):
        parts.append(doc[idx].get_text("text"))
    doc.close()
    return normalize_text("\n".join(parts)), page_count


def ocr_page(doc: fitz.Document, page_idx: int, dpi: int, lang: str) -> str:
    page = doc[page_idx]
    pix = page.get_pixmap(dpi=dpi, alpha=False)
    image = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
    return pytesseract.image_to_string(image, lang=lang, config="--psm 6")


def ocr_selected_pages(
    pdf_path: Path,
    first_pages: int,
    last_pages: int,
    dpi: int,
    lang: str,
) -> tuple[str, str, int]:
    doc = fitz.open(pdf_path)
    page_count = len(doc)
    selected = set(range(min(first_pages, page_count)))
    if last_pages > 0:
        selected.update(range(max(0, page_count - last_pages), page_count))
    ordered = sorted(selected)
    parts = []
    for page_idx in ordered:
        parts.append(f"\n\n--- OCR PAGE {page_idx + 1} ---\n")
        parts.append(ocr_page(doc, page_idx, dpi=dpi, lang=lang))
    doc.close()
    pages_used = ",".join(str(i + 1) for i in ordered)
    return normalize_text("\n".join(parts)), pages_used, page_count


def abstract_preview(text: str, max_len: int = 360) -> str:
    match = re.search(r"摘要[:：]?\s*(.+?)(关键词|关键字|一、|1\s)", text, flags=re.S)
    if not match:
        return normalize_text(text[:max_len])
    return normalize_text(match.group(1))[:max_len]


def detect_sections(text: str) -> list[str]:
    found = []
    for pattern in SECTION_PATTERNS:
        if pattern in text and pattern not in found:
            found.append(pattern)
    return found


def analyze_paper(
    pdf_path: Path,
    max_pages: int | None = None,
    use_ocr: bool = False,
    ocr_first_pages: int = 3,
    ocr_last_pages: int = 2,
    ocr_dpi: int = 150,
    ocr_lang: str = "chi_sim+eng",
) -> PaperSignals:
    text, pages = extract_text(pdf_path, max_pages=max_pages)
    ocr_pages = ""
    if use_ocr and len(text) < 100:
        text, ocr_pages, pages = ocr_selected_pages(
            pdf_path,
            first_pages=ocr_first_pages,
            last_pages=ocr_last_pages,
            dpi=ocr_dpi,
            lang=ocr_lang,
        )
    counts = Counter({keyword: text.count(keyword) for keyword in KEYWORDS})
    return PaperSignals(
        path=pdf_path,
        pages=pages,
        chars=len(text),
        ocr_pages=ocr_pages,
        keyword_counts=counts,
        detected_sections=detect_sections(text),
        abstract_preview=abstract_preview(text),
    )


def write_csv(signals: list[PaperSignals], out_csv: Path) -> None:
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["file", "year", "problem", "pages", "chars", "ocr_pages", "sections"] + KEYWORDS
    with out_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for item in signals:
            name = item.path.stem
            row = {
                "file": str(item.path),
                "year": infer_year(item.path),
                "problem": name[0] if name else "",
                "pages": item.pages,
                "chars": item.chars,
                "ocr_pages": item.ocr_pages,
                "sections": "；".join(item.detected_sections),
            }
            row.update({k: item.keyword_counts[k] for k in KEYWORDS})
            writer.writerow(row)


def write_markdown(signals: list[PaperSignals], out_md: Path) -> None:
    out_md.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Excellent Paper Style Signals",
        "",
        "本文件由 `05_code/tools/pdf_style_extractor.py` 自动抽取，用于辅助 Codex 对照优秀论文结构。内容仅记录高层结构信号和短摘要预览，不作为论文正文来源。",
        "",
        "## 总览",
        "",
        "| 年份 | 题号 | 文件 | 页数 | 字符数 | OCR 页 | 关键结构 |",
        "|---|---|---|---:|---:|---|---|",
    ]
    for item in signals:
        name = item.path.stem
        sections = "、".join(item.detected_sections[:8])
        lines.append(
            f"| {infer_year(item.path)} | {name[:1]} | {name} | {item.pages} | {item.chars} | {item.ocr_pages or '-'} | {sections} |"
        )

    lines.extend(["", "## 逐篇摘要预览", ""])
    for item in signals:
        name = item.path.stem
        lines.extend(
            [
                f"### {infer_year(item.path)} {name}",
                "",
                f"- 页数：{item.pages}",
                f"- OCR 页：{item.ocr_pages or '未使用'}",
                f"- 检测结构：{'、'.join(item.detected_sections) or '未检测到'}",
                f"- 摘要预览：{item.abstract_preview or '未抽取到'}",
                "",
            ]
        )

    out_md.write_text("\n".join(lines), encoding="utf-8")


def infer_year(path: Path) -> str:
    match = re.search(r"20\d{2}", str(path))
    return match.group(0) if match else ""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--out-csv", type=Path, required=True)
    parser.add_argument("--out-md", type=Path, required=True)
    parser.add_argument("--max-pages", type=int, default=None)
    parser.add_argument("--ocr", action="store_true")
    parser.add_argument("--ocr-first-pages", type=int, default=3)
    parser.add_argument("--ocr-last-pages", type=int, default=2)
    parser.add_argument("--ocr-dpi", type=int, default=150)
    parser.add_argument("--ocr-lang", default="chi_sim+eng")
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()

    pdfs = sorted(args.input_dir.rglob("*.pdf"))
    if args.limit is not None:
        pdfs = pdfs[: args.limit]
    signals = [
        analyze_paper(
            pdf,
            max_pages=args.max_pages,
            use_ocr=args.ocr,
            ocr_first_pages=args.ocr_first_pages,
            ocr_last_pages=args.ocr_last_pages,
            ocr_dpi=args.ocr_dpi,
            ocr_lang=args.ocr_lang,
        )
        for pdf in pdfs
    ]
    write_csv(signals, args.out_csv)
    write_markdown(signals, args.out_md)
    print(f"analyzed {len(signals)} PDFs")
    print(args.out_csv)
    print(args.out_md)


if __name__ == "__main__":
    main()
