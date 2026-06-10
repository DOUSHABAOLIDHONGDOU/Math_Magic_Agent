# Agent Spec: Math Modeling Multi-Agent

## Agent 目标

开发一个用于中国大学生数学建模赛前训练的多 Agent 协作系统，跑通题目解析、方案生成、代码实现、结果验收、图表生成、论文写入和代码附录整理。

## Agent 角色

### Codex Agent

职责：

- 读取题目、数据说明、优秀论文和 LaTeX 模板。
- 按题目顺序逐问推进；当前问题入文、编译和版面检查通过后再解锁下一问。
- 对当前问题生成 A/B/C 三套建模方案。
- 生成用户审批简报。
- 用户选择方案后，生成 Claude Code 执行提示词和工单。
- 审查 Claude Code 的代码、结果和日志。
- 汇总三套方案结果，给出推荐。
- 小问模型确认后，立即写入对应 LaTeX 小节并编译 PDF。
- 生成最终图表，审批后补入 LaTeX 并重新编译。
- 对流程图、机制图、结构示意图按 imagegen skill 规则生成项目位图资产。
- 撰写中文 CUMCM 风格论文。
- 整理代码附录。
- 维护共享状态和 AI 使用记录。
- 摘要、全局问题分析、模型评价和论文 AI 使用说明等总结性内容最后统一整理。

限制：

- 不在未经用户审批时确定最终模型。
- 不使用生图伪造真实数据图。
- 不把项目引用的生图资产只留在默认生成目录。

### Claude Code Agent

职责：

- 按 Codex 工单实现代码。
- 调试和运行代码。
- 输出表格、基础图、日志和完成报告。
- 报告 blocker 与不确定边界问题。

限制：

- 不修改已批准建模路线。
- 不直接写最终论文结论。
- 不负责最终图表审美和 LaTeX 插入。

### Human Controller

职责：

- 审批方案。
- 确认最终模型。
- 审批最终图表。
- 仲裁 Codex 与 Claude Code 冲突。
- 对论文最终提交负责。

## 状态机

```text
INIT
  -> PROBLEM_LOADED
  -> SCHEMES_GENERATED
  -> SCHEMES_APPROVED
  -> CLAUDE_WORKORDERS_CREATED
  -> CODE_COMPLETED
  -> CODE_REVIEWED
  -> MODEL_CONFIRMED
  -> PAPER_WRITTEN
  -> FIGURES_GENERATED / FIGURES_APPROVED
  -> APPENDIX_READY
  -> FINAL_REVIEW
```

## 文件接口

Codex 与 Claude Code 通过文件通信：

- 输入状态：`00_shared/PROJECT_STATE.md`
- 决策记录：`00_shared/DECISION_LOG.md`
- 边界问题：`00_shared/QUESTION_BOUNDARIES.md`
- 冲突记录：`00_shared/CONFLICT_LOG.md`
- 工单：`04_claude_workorders/`
- 代码：`05_code/`
- 结果：`06_results/`
- 论文：`07_paper/`

## 控制脚本

当前提供轻量控制脚本 `05_code/tools/agentctl.py`：

- `env-check`：检查 Python、OCR、LaTeX 和建模依赖。
- `status`：读取共享状态和待确认边界。
- `tools`：读取并打印工具注册表。
- `init-state`：初始化机器可读状态。
- `import-problem`：导入题目。
- `archive-stale-artifacts`：归档旧题/旧主题生成物，防止新题流程读取旧脚本、旧工单、旧图或旧论文段落。
- `scan-data`：扫描数据字段。
- `approve-language`：记录语言审批。
- `set-active-question`：设置当前逐问推进的问题。
- `prepare-schemes`：准备 A/B/C 方案文件和 Codex 提示。
- `create-approval-brief`：生成当前问题的用户审批简报。
- `approve-schemes`：记录方案审批。
- `create-workorder` / `create-workorders`：从模板生成 Claude Code 工单。
- `create-claude-prompt`：生成可直接发给 Claude Code 的执行提示词。
- `ingest-claude-report`：摄取 Claude Code 完成报告。
- `create-review` / `mark-reviewed`：生成和记录 Codex 审查。
- `compare-schemes`：生成方案对比模板。
- `confirm-model`：记录最终模型确认。
- `approve-figures`：记录图表审批。
- `write-question-paper`：模型确认后写入单题 LaTeX 小节并编译 PDF。
- `mark-paper-written`：记录论文写入状态。
- `paper-check`：检查论文关键文件。
- `latex-check`：编译当前论文。
- `readiness`：输出当前流程就绪状态。

该脚本是 V0.2 agent 编排器的命令层。换题时 `import-problem` 默认归档上一题生成物；如在真实运行中发现旧题污染，Codex 应先运行 `archive-stale-artifacts --dry-run` 审查清单，再用 `--force` 归档。真实题目测试后，应继续扩展自动拆题、深度 OCR 选择、输出文件审查和代码附录自动整理。

## 工具注册表

工具注册表由两部分组成：

- 机器可读：`05_code/tools/tool_registry.json`
- 人类可读：`08_agent_design/TOOL_REGISTRY.md`

新增工具或新增依赖时，必须同步更新工具注册表、安装文件和环境检查逻辑。

## 一次完整运行的成功标准

1. 至少一个问题完成 A/B/C 三套方案和用户审批简报。
2. 用户选择至少一个方案并生成 Claude Code 提示词。
3. Claude Code 跑出用户选定方案的结果。
4. Codex 完成代码和结果审查。
5. 用户确认最终模型。
6. Codex 生成至少一张最终论文图并插入 LaTeX。
7. Codex 写入论文对应章节。
8. 代码附录完成初版。
