# Environment Setup

本项目默认使用 conda 环境运行代码、PDF OCR、绘图和 LaTeX 编译。交付目标优先适配 Windows + VS Code，同时保留 macOS/Linux 运行能力。

如果是新机器或给他人复现，优先使用项目根目录的 `environment.yml` 创建独立环境：

```bash
conda env create -f environment.yml
conda activate math-magic
python 05_code/tools/agentctl.py env-check
```

Windows 新用户完成环境创建后，应先运行：

```powershell
python 05_code/tools/agentctl.py doctor --target-os windows --write-vscode-smoke-task
```

随后在 VS Code 中运行 `Math Magic: Claude smoke test`，确认 VS Code 集成终端可以调用 `claude`、`python` 和项目环境。

## 已验证能力

- Python：不固定小版本，优先使用项目 `environment.yml` 或已有 conda/base 环境。
- PDF 解析：`pypdf`, `PyMuPDF`
- OCR：`tesseract`, `pytesseract`
- OCR 语言：`chi_sim`, `eng`
- 数据处理：`numpy`, `pandas`
- 绘图：`matplotlib`, `seaborn`
- 科学计算：`scipy`, `statsmodels`
- 机器学习：`scikit-learn`
- Excel：`openpyxl`, `xlrd`
- 网络和图算法：`networkx`
- LaTeX：`xelatex`

## 运行约定

所有脚本优先从项目根目录运行：

```bash
conda run -n base python 05_code/tools/pdf_style_extractor.py --help
```

绘图脚本需要将 Matplotlib 缓存写入项目目录，避免访问用户主目录：

```bash
MPLCONFIGDIR=.cache/matplotlib conda run -n base python <script.py>
```

Windows PowerShell 中不需要使用 `MPLCONFIGDIR=...` 前缀；绘图脚本应在代码内设置项目内 Matplotlib 缓存目录。

Claude Code 生成的 Python 绘图脚本也应在代码开头设置：

```python
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
os.environ.setdefault("MPLCONFIGDIR", str(PROJECT_ROOT / ".cache" / "matplotlib"))
```

## PDF 风格索引

优秀论文多为扫描图像版 PDF，直接文本抽取为空。因此使用 OCR：

```bash
conda run -n base python 05_code/tools/pdf_style_extractor.py \
  --input-dir 02_references/excellent_papers \
  --out-csv 02_references/excellent_papers_style_signals.csv \
  --out-md 02_references/excellent_papers_style_signals.md \
  --ocr
```

默认 OCR 策略为每篇前 3 页和后 2 页。深度分析某篇论文时，可提高页数或单独全篇 OCR。

## LaTeX 编译

工作论文入口：

```bash
cd 07_paper
xelatex -interaction=nonstopmode -halt-on-error main.tex
```

当前 `07_paper/main.tex` 已验证可生成 `07_paper/main.pdf`。
