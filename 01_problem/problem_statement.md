# Problem Statement

## 题目信息

- 竞赛类型：待导入
- 题目编号：待导入
- 题目名称：待导入
- 附件列表：待数据扫描后补充

## 使用方式

将题面 PDF、Markdown 或 OCR 后的题面文本放入 `01_problem/source/`，然后运行：

```bash
python 05_code/tools/agentctl.py import-problem --statement 01_problem/source/problem.md --title 训练题目 --data-dir 01_problem/source/data
```

导入后，agent 会重写本文件，并更新 `01_problem/data_dictionary.md` 与 `00_shared/workflow_state.json`。
