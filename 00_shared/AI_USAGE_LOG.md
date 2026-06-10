# AI Usage Log

本文件用于记录 Codex 和 Claude Code 的关键使用情况，后续可整理为论文中的 AI 使用说明和支撑材料。

## 记录模板

```markdown
## AILOG-000

- 日期：
- 工具：Codex / Claude Code / 其他
- 用途：
- 输入摘要：
- 输出摘要：
- 采纳情况：全部采纳 / 部分采纳 / 未采纳
- 人工修改：
- 关联文件：
- 备注：
```

## AILOG-AUTO-2026-06-10T17:19:02 信任配置变更

- 日期：2026-06-10
- 工具：agentctl set-trust-profile
- 用途：切换信任配置为 `normal`。
- 含义：strict=训练严格；normal=演练；fast=赛时快速通道。

## AILOG-AUTO-2026-06-10T17:19:30 自动汇总

- 日期：2026-06-10
- 工具：agentctl gen-ai-log
- 题目：`题目名称待定`
- 当前阶段：`INIT`
- 信任配置：`normal`
- Q1：confirmed=—, model_confirmed=False, paper_written=False
- Q2：confirmed=—, model_confirmed=False, paper_written=False
- Q3：confirmed=—, model_confirmed=False, paper_written=False
- Q4：confirmed=—, model_confirmed=False, paper_written=False
- Q5：confirmed=—, model_confirmed=False, paper_written=False

## AILOG-AUTO-2026-06-10T18:28:10 题目导入

- 日期：2026-06-10
- 工具：agentctl import-problem
- 用途：导入训练题目 `2025 B题 碳化硅外延层厚度的确定`。
- 关联文件：`01_problem\problem_statement.md`

## AILOG-AUTO-2026-06-10T18:44:38 题目导入

- 日期：2026-06-10
- 工具：agentctl import-problem
- 用途：导入训练题目 `2025 B题 碳化硅外延层厚度的确定`。
- 关联文件：`01_problem/problem_statement.md`
