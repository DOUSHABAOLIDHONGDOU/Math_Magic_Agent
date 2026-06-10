"""Phase 4: RAG over the excellent-papers corpus.

The OCR step is driven by ``pdf_style_extractor.py --full-ocr``; this module
takes the resulting ``02_references/ocr_texts/*.md`` files and builds a BM25
index, then provides per-question retrieval of the most relevant passages.
"""

from __future__ import annotations

import json
import pickle
import re
from pathlib import Path

from ._paths import PROJECT_ROOT
from ._state import ensure_question, load_state
from ._util import now_iso, rel, write_text


PASSAGE_TARGET_CHARS = 280
OVERLAP_CHARS = 60
OCR_TEXTS_DIR = PROJECT_ROOT / "02_references" / "ocr_texts"
INDEX_PATH = PROJECT_ROOT / "02_references" / "bm25_index.pkl"
RAG_OUTPUT_DIR = PROJECT_ROOT / "02_references" / "rag_context"

# Sources to scan for paper text when building the index. Files at any of these
# paths get pulled in, so users can mix OCR output and hand-collected text.
INDEX_SOURCE_DIRS: list[Path] = [
    OCR_TEXTS_DIR,  # Full OCR markdown from pdf_style_extractor.py --full-ocr
    PROJECT_ROOT / "02_references" / "paper_texts",  # Manually-collected paper text
]
INDEX_SOURCE_EXTS = (".md", ".txt")


# Rule-based topic classifier: maps keyword presence in the problem statement
# to a topic label. The label currently isn't used for filtering, but it's
# emitted into the brief so Codex/the user can sanity-check the retrieval.
TOPIC_KEYWORD_RULES = [
    ("时序", ["时间序列", "时序", "kalman", "卡尔曼", "arima", "lstm", "rnn", "prophet", "smoothing", "趋势"]),
    ("图网络", ["最短路", "图论", "graph", "网络流", "节点", "路径", "邻接", "tsp", "shortest path"]),
    ("物理建模", ["偏微分", "扩散", "热传导", "波动", "navier", "ode", "微分方程", "physics", "燃烧", "辐射"]),
    ("优化", ["规划", "minimi", "maximi", "milp", "ilp", "整数规划", "线性规划", "凸优化", "启发式", "遗传算法", "粒子群"]),
    ("机器学习", ["机器学习", "回归", "分类", "随机森林", "xgboost", "神经网络", "深度学习", "聚类", "svm"]),
    ("统计推断", ["假设检验", "置信区间", "p 值", "p-value", "anova", "回归分析", "贝叶斯", "似然", "logistic"]),
    ("半导体/光谱", ["碳化硅", "外延", "折射率", "光谱", "反射", "薄膜", "波长", "frequency"]),
]


def classify_topic(text: str) -> str:
    lowered = text.lower()
    scores: list[tuple[str, int]] = []
    for label, keywords in TOPIC_KEYWORD_RULES:
        score = sum(1 for kw in keywords if kw in lowered)
        if score:
            scores.append((label, score))
    if not scores:
        return "通用"
    scores.sort(key=lambda kv: kv[1], reverse=True)
    return scores[0][0]


def _split_passages(text: str) -> list[str]:
    """Split a long OCR text into ~PASSAGE_TARGET_CHARS-char chunks with a small overlap."""
    text = re.sub(r"\n{2,}", "\n", text)
    passages: list[str] = []
    pos = 0
    n = len(text)
    while pos < n:
        end = min(n, pos + PASSAGE_TARGET_CHARS)
        # Try to align to a sentence boundary.
        boundary = max(text.rfind("。", pos, end), text.rfind("\n", pos, end), text.rfind(".", pos, end))
        if boundary != -1 and boundary > pos + PASSAGE_TARGET_CHARS // 2:
            end = boundary + 1
        chunk = text[pos:end].strip()
        if len(chunk) >= 40:
            passages.append(chunk)
        pos = max(end - OVERLAP_CHARS, end if end == n else pos + 1)
    return passages


def _tokenize(text: str) -> list[str]:
    """Cheap CJK+ASCII tokenizer: keep CJK chars as bigrams, split ASCII on \\W."""
    tokens: list[str] = []
    # CJK bigrams
    cjk = re.findall(r"[一-鿿]+", text)
    for run in cjk:
        for i in range(len(run) - 1):
            tokens.append(run[i : i + 2])
    # ASCII words
    for word in re.findall(r"[A-Za-z0-9_]+", text):
        if len(word) >= 2:
            tokens.append(word.lower())
    return tokens


def _iter_source_files() -> list[Path]:
    """Find every .md / .txt under any configured source dir, in stable order.

    Skips README.md / readme.md — those are explanatory, not paper content.
    """
    found: list[Path] = []
    for source_dir in INDEX_SOURCE_DIRS:
        if not source_dir.exists():
            continue
        for ext in INDEX_SOURCE_EXTS:
            for path in sorted(source_dir.glob(f"*{ext}")):
                if path.name.lower() in {"readme.md", "readme.txt"}:
                    continue
                found.append(path)
    return found


def build_index(force: bool = False) -> Path:
    source_files = _iter_source_files()
    if not source_files:
        existing_dirs = [rel(d) for d in INDEX_SOURCE_DIRS if d.exists()]
        missing_dirs = [rel(d) for d in INDEX_SOURCE_DIRS if not d.exists()]
        msg = [
            "no source text found for the RAG index.",
            f"checked dirs: {INDEX_SOURCE_DIRS}",
            "Provide at least one of:",
            "  (a) Drop .md / .txt files into 02_references/paper_texts/  (fastest, no OCR needed)",
            "  (b) Run: python 05_code/tools/pdf_style_extractor.py \\",
            "             --input-dir 02_references/excellent_papers \\",
            "             --full-ocr --ocr-texts-dir 02_references/ocr_texts --ocr-dpi 300",
            f"existing source dirs:  {existing_dirs or 'none'}",
            f"missing source dirs:   {missing_dirs or 'none'}",
        ]
        raise SystemExit("\n".join(msg))
    if INDEX_PATH.exists() and not force:
        return INDEX_PATH
    try:
        from rank_bm25 import BM25Okapi
    except ImportError as exc:
        raise SystemExit(
            "rank_bm25 not installed. Add to requirements.txt and `pip install rank-bm25`."
        ) from exc

    corpus_passages: list[tuple[str, str]] = []  # (source_file, text)
    for path in source_files:
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        for passage in _split_passages(text):
            corpus_passages.append((rel(path), passage))
    if not corpus_passages:
        raise SystemExit(
            f"found {len(source_files)} source file(s) but no passages survived splitting; "
            "files may be empty or contain only whitespace."
        )
    tokenized = [_tokenize(passage) for _, passage in corpus_passages]
    bm25 = BM25Okapi(tokenized)
    INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    with INDEX_PATH.open("wb") as f:
        pickle.dump(
            {
                "version": 2,
                "created_at": now_iso(),
                "source_files": [rel(p) for p in source_files],
                "passages": corpus_passages,
                "bm25": bm25,
            },
            f,
        )
    return INDEX_PATH


def _load_index() -> dict:
    if not INDEX_PATH.exists():
        raise SystemExit(
            f"BM25 index not built. Run: python 05_code/tools/agentctl.py index-papers"
        )
    with INDEX_PATH.open("rb") as f:
        return pickle.load(f)


def retrieve(query: str, top_k: int = 5) -> list[dict]:
    payload = _load_index()
    bm25 = payload["bm25"]
    passages = payload["passages"]
    tokens = _tokenize(query)
    if not tokens:
        return []
    scores = list(bm25.get_scores(tokens))
    # BM25 IDF degenerates for tiny corpora (N <= 2): IDF can be zero or even
    # negative, leaving the entire score vector flat. Fall back to per-passage
    # token-overlap counts so the ranking stays sensible regardless of size.
    if not any(s > 0 for s in scores):
        query_set = set(tokens)
        scores = []
        for _src, text in passages:
            passage_tokens = set(_tokenize(text))
            scores.append(len(query_set & passage_tokens))
    ranked = sorted(enumerate(scores), key=lambda kv: kv[1], reverse=True)[:top_k]
    return [
        {
            "rank": rank + 1,
            "score": float(score),
            "source": passages[index][0],
            "text": passages[index][1],
        }
        for rank, (index, score) in enumerate(ranked)
        if score > 0
    ]


def _problem_query_for_question(state: dict, question: str) -> str:
    """Concatenate the problem statement and any per-question sketch into a query."""
    parts: list[str] = []
    title = state.get("problem", {}).get("title")
    if title:
        parts.append(title)
    statement_path = PROJECT_ROOT / (state.get("problem", {}).get("statement_file") or "01_problem/problem_statement.md")
    if statement_path.exists():
        try:
            parts.append(statement_path.read_text(encoding="utf-8")[:4000])
        except OSError:
            pass
    scheme_dir = PROJECT_ROOT / "03_methods" / question
    if scheme_dir.exists():
        for path in sorted(scheme_dir.glob("scheme_*.md")):
            try:
                parts.append(path.read_text(encoding="utf-8")[:1500])
            except OSError:
                continue
    return "\n".join(parts)


def command_index_papers(args):
    if args.show_sources:
        sources = _iter_source_files()
        print(f"== RAG sources ({len(sources)} file(s)) ==")
        for path in sources:
            print(rel(path))
        if not sources:
            print("(no files found; see `index-papers --help` for setup options)")
        return
    path = build_index(force=args.force)
    payload = _load_index()
    print(path)
    print(f"passages: {len(payload['passages'])}")
    if payload.get("source_files"):
        print(f"sources:  {len(payload['source_files'])} file(s)")


def command_rag_status(args):
    """Diagnose what's missing for the RAG pipeline."""
    print("== RAG Status ==")
    try:
        from rank_bm25 import BM25Okapi  # noqa: F401

        print("rank-bm25:    installed")
    except ImportError:
        print("rank-bm25:    MISSING  (pip install rank-bm25)")
    sources = _iter_source_files()
    print(f"source files: {len(sources)}")
    for source_dir in INDEX_SOURCE_DIRS:
        exists = source_dir.exists()
        if not exists:
            print(f"  {rel(source_dir)}: missing (0 indexed)")
            continue
        indexed = [p for p in source_dir.glob("*") if p in sources]
        skipped = [
            p
            for p in source_dir.glob("*")
            if p.is_file() and p.suffix.lower() in INDEX_SOURCE_EXTS and p not in sources
        ]
        skip_note = f", {len(skipped)} skipped (README)" if skipped else ""
        print(f"  {rel(source_dir)}: exists ({len(indexed)} indexed{skip_note})")
    print(f"index:        {'built ' + rel(INDEX_PATH) if INDEX_PATH.exists() else 'not built'}")
    if INDEX_PATH.exists():
        try:
            payload = _load_index()
            print(f"  passages:   {len(payload['passages'])}")
            if payload.get("created_at"):
                print(f"  created_at: {payload['created_at']}")
        except (OSError, EOFError, pickle.UnpicklingError) as exc:
            print(f"  index is corrupt: {exc}")
    if not sources:
        print()
        print("Next step: drop hand-collected paper text into 02_references/paper_texts/ "
              "(any .md or .txt), OR run pdf_style_extractor.py --full-ocr.")


def command_retrieve_context(args):
    state = load_state()
    question = ensure_question(args.question)
    if args.query:
        # Free-form override; lets the user retrieve without importing a problem.
        query = args.query
    else:
        query = _problem_query_for_question(state, question)
    if not query.strip():
        raise SystemExit(
            "no problem statement available to use as query.\n"
            "  Either: 1) run `import-problem` first, or\n"
            "          2) pass --query \"your free-form search text\""
        )
    if not INDEX_PATH.exists():
        raise SystemExit(
            "BM25 index not built. Run `python 05_code/tools/agentctl.py index-papers` first "
            "(or `rag-status` to see what's missing)."
        )
    topic = classify_topic(query)
    hits = retrieve(query, top_k=args.top_k)
    RAG_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = RAG_OUTPUT_DIR / f"{question}_top_passages.md"
    lines = [
        f"# {question} 参考优秀论文片段（BM25 Top-{args.top_k}）",
        "",
        f"- 生成时间：{now_iso()}",
        f"- 推断题型：`{topic}`",
        "",
    ]
    if not hits:
        lines.append("_未命中任何段落；请先运行 `index-papers` 并确认 OCR 文本已生成_")
    else:
        for hit in hits:
            lines.extend(
                [
                    f"## #{hit['rank']}  score={hit['score']:.3f}  source: `{hit['source']}`",
                    "",
                    "> " + hit["text"].replace("\n", "\n> "),
                    "",
                ]
            )
    write_text(out_path, "\n".join(lines))
    print(out_path)
    # Print top-1 to terminal for quick sanity check.
    if hits:
        print(f"top1: {hits[0]['source']} (score={hits[0]['score']:.3f})")
