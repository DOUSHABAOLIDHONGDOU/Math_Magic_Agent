# Paper Texts (for RAG)

放置 **可读的 markdown / txt 优秀论文文本**，BM25 索引器会自动扫描本目录与
`02_references/ocr_texts/`。

两种来源都可以：

## 方式 A：手工准备文本

- 一篇论文 → 一个 `.md` 或 `.txt` 文件
- 文件名建议 `年份_题号_关键词.md`，例如 `2023_B_spectrum.md`
- 内容只需带摘要 / 模型建立 / 算法流程等关键段落，不必整篇

## 方式 B：从 PDF OCR

需要 tesseract + chi_sim 语言包。

```bash
python 05_code/tools/pdf_style_extractor.py \
    --input-dir 02_references/excellent_papers \
    --full-ocr --ocr-texts-dir 02_references/ocr_texts --ocr-dpi 300
```

会把每篇 PDF OCR 为 `02_references/ocr_texts/<原文件名>.md`。

## 建立索引

```bash
python 05_code/tools/agentctl.py rag-status        # 检查依赖与文件
python 05_code/tools/agentctl.py index-papers      # 构建 BM25 索引
python 05_code/tools/agentctl.py retrieve-context --question Q1 --top-k 5
```

索引建好后，`prepare-schemes` 会自动检索本题型相关片段，注入 Codex 提示。

## 公开仓库注意

本仓库 `.gitignore` 默认排除本目录下的 `.md` / `.txt` 文件（论文版权问题）。
如果你的样本论文有可分发许可，明确加 `!` 解除忽略再 commit。
