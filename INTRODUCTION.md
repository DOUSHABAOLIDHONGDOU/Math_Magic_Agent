---
title: "Math Magic Agent 项目介绍"
author: "lwb（@DOUSHABAOLIDHONGDOU）"
date: "2026-06-10"
---

# Math Magic Agent · 项目介绍

> Codex + Claude Code 多 Agent 协作数学建模工作流。
> 项目主页：<https://github.com/DOUSHABAOLIDHONGDOU/Math_Magic_Agent>

---

## 一、为什么做这个项目

前不久在论坛上刷到一篇帖子（"启翔湖畔 · 西北工"频道，2026-05-16），作者分享了
自己用 AI 工具写美赛论文的全流程：

- 在 Overleaf 上找一个 LaTeX 模板，复制进 VS Code
- 比赛拿到题目后，让 ChatGPT 做问题分析、Claude Code 写代码、GPT 做优化
- 配合若干图像生成插件和数学建模插件，让图自动插入 LaTeX
- 全程实时编译 + 让 AI 调格式 + 修订正文
- 前后**只花了不到 5 小时**，大部分时间在调版面
- 一直拖到比赛截止才提交，最后拿了 **美赛 H 奖**

作者的两个观点对我冲击很大：

1. **数模本质上是抽奖**，AI 工作流能稳定降低运气依赖
2. **现在 AI 迭代太快**，从今年的角度看大学课程作业 90% 都能 AI 完成；从大厂角度看
   "vibe coding"也成了主流方式

帖子下面其他人也评论说：**会用 AI 就是能力**、**人和人用 AI 出来的效果差很多**。

我当时正在准备国赛训练，本来就在用 Codex + Claude Code 各负责一块，但每次跑题
都靠手动复制粘贴、记不清上次到哪一步、方案没对比、论文图不统一……痛点很集中。
于是趁机把整套流程**沉淀成一个命令化的 agent**，既是我自己的训练工具，也方便
后面想用 AI 工作流但还不知道怎么搭的同学直接抄作业。

---

## 二、它解决了什么问题

| 痛点 | 这个 agent 怎么处理 |
|---|---|
| 跑题状态零散、记不清下一步 | 文件型状态机 + `readiness` 命令一键告诉你下一步该跑什么命令 |
| 方案口头讨论容易漏 | 强制 A/B/C 三套方案 + 用户审批简报直接列选项 |
| Claude 工单上下文不够 | `create-claude-prompt` 自动内联方案 + 数据字典 + 论文风格 + 历史 blocker |
| 跑完不知道哪个方案最好 | `compare-schemes` 自动读 metrics CSV + 评分 + 推荐 |
| 数据特性看不清 | `auto-eda` 一键 6 张诊断图 + summary，自动注入方案生成提示 |
| 想参考优秀论文但没系统化 | BM25 RAG 索引，方案生成时按题型自动检索 |
| 论文图风格不一致 | `figure-lint` 自动检测红虚线 / 四宫格 / 超宽图 |
| 三段人工审批太繁琐 | `trust profile` 三档（strict / normal / fast）一键切赛时快速通道 |

更多细节见 [README.md](README.md) 和 [INSTALL.md](INSTALL.md)。

---

## 三、战绩（真实情况，不夸大）

这套工作流的雏形支撑了我自己的几次比赛：

- **美赛**：H 奖（Honorable Mention）
- **国赛（CUMCM）**：省一
- **校赛**：一二等奖各拿过一次

**这就是当前的真实战绩，没拿过更高级别的奖**。如果你看到这里期待"用了就能拿
M 奖 / 国一"，请理性看待——见下面的免责声明。

---

## 四、免责声明

> **请认真阅读，比拿什么奖更重要。**

1. **本项目不保证任何比赛成绩**。建模本身存在客观抽奖成分（题型契合度、评委
   偏好、参考答案漂移等），AI 工作流只是降低执行环节的方差，不能消除运气
   因素。
2. **AI 输出必须由人复核**。无论是 Codex 给的建模方案、Claude Code 写的代码，
   还是 RAG 检索回来的优秀论文片段，最终都要队员自己验证数学正确性、数据
   适配性和论文严谨性。盲信 AI 出错的责任在使用者。
3. **不替代任何学习**。这个工具的设计目标是让懂建模的人**更快**地做建模，而不
   是让不懂的人也能拿奖。如果连方差/置信区间/灵敏度分析是什么都不清楚，
   建议先补基础再用 agent。
4. **遵守竞赛规则**。CUMCM、美赛、各校赛对 AI 使用的态度在 2025-2026 年仍在
   变化，请在赛前主动确认当年规则；如果竞赛明令禁止 AI 协作，请勿使用本
   工作流参赛。论文 AI 使用说明（项目自动生成的 `AI_USAGE_LOG.md` 草稿）建
   议如实填写。
5. **版权与数据**。本仓库**不内置任何赛题题面、附件数据、优秀论文 PDF**。
   导入的题目、数据、参考论文版权均归原作者所有，使用者自行承担合规
   责任。
6. **个人项目，非商业产品**。代码 MIT 协议开源（见 `LICENSE`），但作者**不
   提供任何形式的保证**——能否在你的机器、你的题型、你的赛季稳定工作，
   需要自己实测。

---

## 五、欢迎贡献

这是一个**持续迭代**的项目，期望它越用越好。希望大家：

- **GitHub 上点个 star**：<https://github.com/DOUSHABAOLIDHONGDOU/Math_Magic_Agent>
  ——让更多需要 AI 建模工作流的同学看到。
- **持续提意见**：在 GitHub Issues 里留言。无论是发现 bug、流程不顺、对
  RAG 检索质量不满、对方案模板有建议……都欢迎。
- **欢迎 PR**：见 `CONTRIBUTING.md`，里面写清楚了模块布局和开发约定。
  特别欢迎：
  - 更好的题型分类器 / 优秀论文 RAG 检索质量
  - 更细的图表 lint 规则（图例位置、字体大小、横纵比）
  - 把 Codex 和 Claude Code 改成互相 critique 的双向流
  - 多人队伍并发跑题的状态机支持
- **分享你的实战截图**：如果在比赛中用了这套 agent，赛后欢迎在 Issues
  开个"我的实战记录"贴，让别人借鉴。
- **加群交流**：QQ 群 **836892770**——可以发实时问题、贴报错截图、聊建模
  思路、约队友，比 Issues 反馈更快。

---

## 六、快速开始

```bash
git clone https://github.com/DOUSHABAOLIDHONGDOU/Math_Magic_Agent.git
cd Math_Magic_Agent
conda env create -f environment.yml
conda activate math-magic
python 05_code/tools/agentctl.py doctor
python -m pytest 05_code/tools/tests/ -q   # 应该 43 passed
python 05_code/tools/agentctl.py readiness  # 看自愈建议
```

详细步骤：[INSTALL.md](INSTALL.md) → [README.md](README.md) → [CONTRIBUTING.md](CONTRIBUTING.md)。

---

## 七、致谢

- 感谢启翔湖畔频道 `.r` 同学 2026-05-16 的那篇分享帖（截图见 GitHub Issues），
  没有那篇贴子里"AI 大赛实锤了"的总结，我可能不会真的动手把流程沉淀下来。
- 感谢 Anthropic（Claude Code）和 OpenAI（Codex）让多 agent 工作流在 2026 年
  成为可能。
- 感谢历年 CUMCM 优秀论文作者——你们的论文是这个项目 RAG 检索的精神原料。

---

**祝大家 AI 用得顺、建模拿好奖、论文不熬夜。**

— lwb · 2026-06-10
