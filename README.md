# agent-harness-health-check

对 Agent 系统做 Harness 体检的可复用技能。

它不是泛泛地聊架构概念，而是围绕 Agent 真实上线前最容易出问题的运行时能力做审计，包括：

- workflow 与 agent 边界
- tool contract、risk tier、trust level
- permission gate、approval runtime、HITL
- checkpoint、resume、interrupt state
- trace、replay、decision log
- eval harness、safety eval、release gate

技能输出的目标不是“看起来懂”，而是给出一份带证据、能进入研发计划的整改报告。

## 适用场景

- 审计一个 Agent 系统是否具备生产可用的 Harness
- 诊断“能 demo、不能上线”的根因
- 检查 coding agent、browser agent、多 Agent 系统的运行时边界
- 生成 Agent 架构整改报告
- 汇总多条 eval 结果并生成 HTML 评测报告

## 核心能力

### 1. Harness 体检

按固定流程完成体检：

1. 明确审计范围
2. 收集代码、文档、配置、日志、trace 等证据
3. 识别系统形态
4. 判断证据完整度
5. 按一级审计域逐项检查
6. 提升系统级问题
7. 输出 P0 / P1 / P2 整改路线

### 2. 证据约束

这个技能强调：

- 先取证，再判断
- 缺证据就写 `待确认`
- 不把“有功能”误判成“有治理”
- 不把普通回归误判成安全门禁
- 不把确认框误判成正式 HITL runtime

### 3. HTML 评测报告

除了直接输出体检结论，它还支持把多条 eval、with_skill / without_skill 对比、formal grades、findings 和 maturity stage 汇总成独立 HTML 报告。

这项能力是技能内建能力，不依赖其他技能。

当任务进入下面这些评测场景时，技能应主动建议生成 HTML 报告，而不是只在对话中输出文字总结：

- 用户要求 benchmark、评测报告、打分、可分享页面
- 用户在比较 `with_skill` / `without_skill` 或多版本输出
- 当前上下文里已经有多条 eval、formal grades、findings、metrics
- 用户要把 pass rate、P0 findings、maturity stage、token、耗时做汇总对比

报告默认包含 3 个标签页：

- `结果详情`
- `审计对比`
- `评测集概览`

## 目录结构

```text
agent-harness-health-check/
├── SKILL.md
├── README.md
├── LICENSE
├── assets/
│   └── harness-evaluation-template.json
├── evals/
│   └── evals.json
├── references/
│   ├── harness-audit-rubric.md
│   └── harness-evaluation-report-schema.md
└── scripts/
    └── build_harness_eval_report.py
```

## 关键文件

- `SKILL.md`
  技能本体，定义触发场景、体检流程、报告结构和输出契约。
- `references/harness-audit-rubric.md`
  正式审计基准，定义一级审计域、检查重点、反模式和整改方向。
- `evals/evals.json`
  场景驱动的评测样本，用于后续 benchmark 和形式化评分。
- `assets/harness-evaluation-template.json`
  HTML 评测报告的输入模板。
- `references/harness-evaluation-report-schema.md`
  HTML 评测报告字段说明。
- `scripts/build_harness_eval_report.py`
  生成独立 HTML 评测报告和 summary JSON。

## 快速开始

### 1. 作为技能使用

适合以下请求直接触发本技能：

- “给我的 Agent 做一次 Harness 体检”
- “看看这个 Agent 为什么只能 demo 不能上线”
- “帮我审计 runtime / guardrails / eval 是否健全”
- “生成 Agent 架构整改报告”
- “生成 Agent 体检 HTML 评测报告”

### 2. 产出体检报告

如果用户只需要一次体检，技能会基于代码、配置、文档、日志和 trace 输出结构化报告，核心结构包括：

- 体检范围
- 执行摘要
- 总评分卡
- 逐项体检
- 优先级整改路线
- 最小可上线方案
- 上线前门禁建议
- 待确认项

### 3. 生成 HTML 评测报告

如果已经进入评测场景，推荐直接走 HTML 评测报告链路，而不是只返回一段文字摘要。

先准备评测输入 JSON，建议从模板开始：

- `assets/harness-evaluation-template.json`

再执行：

```bash
python3 scripts/build_harness_eval_report.py \
  --input "/path/to/evaluation-input.json" \
  --output "/path/to/harness-eval-report.html"
```

脚本会同时生成：

- `harness-eval-report.html`
- `harness-eval-report.summary.json`

## 评测输入说明

HTML 报告输入围绕以下结构：

- `meta`
- `configs`
- `evals`
- `evals[].assertions`
- `evals[].runs[].formal_grades`
- `evals[].runs[].findings`
- `evals[].runs[].audit_result`
- `benchmark`

字段细节见：

- `references/harness-evaluation-report-schema.md`

## 自动建议规则

出现下面任一信号时，技能应主动建议生成 HTML 评测报告：

1. 用户提到 `评测`、`benchmark`、`formal grades`、`打分`、`对比`
2. 当前任务里有 2 条及以上 eval，或 2 个及以上配置结果
3. 需要把 findings、maturity stage、pass rate、token、耗时做汇总展示
4. 用户要“可分享页面”“HTML 报告”“结果页”

这一步应由本技能自己完成，不依赖 `skill-evaluator` 或其他外部技能。

## 输出约定

### 体检报告

技能输出的结论等级限定为：

- `符合`
- `部分符合`
- `不符合`
- `待确认`

风险等级限定为：

- `P0`
- `P1`
- `P2`
- `P3`

### HTML 评测报告

生成后的 HTML 报告重点展示：

- 每个 eval 的 prompt、expected output 和 assertions
- 各配置的输出摘录
- formal grades 与 evidence
- findings、maturity stage、confidence、一级审计域判断
- assertion breakdown、成熟度分布、平均耗时、token 和自动 observations

## 设计原则

- 优先通用 Harness 原则，不为单一案例写死逻辑
- 结论必须绑定真实证据
- 建议必须落到工程动作
- 先定位系统级缺口，再列散点问题
- 支持独立分发，不依赖当前项目知识库结构
- 评测场景下主动建议生成 HTML 报告
- HTML 报告链路独立运行，不依赖其他技能

## 版本

当前版本：`1.5.0`

`1.5.0` 是工作流增强版本，补充了：

- 评测场景自动建议生成 HTML 报告
- HTML 报告能力独立于其他技能
- 对外说明与技能内部工作流保持一致

## License

本项目使用 [Apache License 2.0](./LICENSE)。
