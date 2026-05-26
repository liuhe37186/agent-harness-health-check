# Harness HTML 评测报告 Schema

## 目标

这份 schema 用于给 `agent-harness-health-check` 生成独立 HTML 评测报告。

它不只是展示“总分”，而是把评测结果拆成：

- `evals`：具体测试场景
- `runs`：技能启用版 / 基线版 / 其他配置的输出
- `formal_grades`：量化断言与证据
- `findings`：本次输出识别出的关键问题
- `audit_result`：成熟度、可信度、一级审计域判断
- `benchmark`：汇总对比与自动观察

最终报告会带 3 个标签页：

1. `结果详情`
2. `审计对比`
3. `评测集概览`

## 推荐结构

```json
{
  "meta": {
    "skill_name": "agent-harness-health-check",
    "version": "1.5.0",
    "evaluator": "Claude",
    "evaluation_date": "2026-05-25",
    "scope": "评估 Agent Harness 体检技能在典型场景下的诊断质量、证据纪律与整改建议质量",
    "summary": "本轮覆盖 2 个典型场景",
    "audit_target": "某 Agent 系统或技能本体"
  },
  "configs": [
    {
      "key": "with_skill",
      "label": "技能启用版",
      "description": "启用目标技能后的输出"
    },
    {
      "key": "without_skill",
      "label": "基线版",
      "description": "不启用技能的普通输出"
    }
  ],
  "evals": [
    {
      "id": "eval-001",
      "title": "文档型 Harness 体检",
      "prompt": "用户实际测试提示词",
      "expected_output": "期望输出或目标行为",
      "summary": "这个用例主要在测什么",
      "assertions": [
        { "text": "不会把规划中的能力误判成已实现" },
        { "text": "能明确给出待确认项" }
      ],
      "runs": [
        {
          "config_key": "with_skill",
          "summary": "本配置在该用例下的实际表现",
          "outputs": [
            { "label": "REPORT", "content": "输出摘录" }
          ],
          "formal_grades": [
            {
              "text": "不会把规划中的能力误判成已实现",
              "passed": true,
              "evidence": "明确指出 resume 尚无实现证据"
            }
          ],
          "findings": [
            {
              "severity": "P0",
              "title": "主恢复面缺失",
              "detail": "没有正式 continuation surface",
              "remediation": "统一 checkpoint + state 作为恢复面"
            }
          ],
          "audit_result": {
            "maturity_stage": "概念验证",
            "confidence": "中",
            "domain_verdicts": [
              {
                "domain": "状态与恢复",
                "verdict": "不符合",
                "risk": "P0"
              }
            ]
          },
          "metrics": {
            "duration_ms": 18000,
            "tokens": 12000
          }
        }
      ]
    }
  ],
  "benchmark": {
    "observations": [
      "技能启用版在证据纪律上明显更稳定"
    ]
  }
}
```

## 字段说明

- `meta`
  报告头信息。
- `meta.audit_target`
  这轮评测针对的对象，例如某个 Agent 系统、某个 runtime 方案，或技能本体。
- `configs`
  对比配置。通常至少有 `with_skill` 与 `without_skill`。
- `evals`
  评测用例列表，每个用例对应一个场景。
- `evals[].assertions`
  当前用例要验证的断言列表。
- `evals[].runs`
  每个配置在该用例下的一次运行结果。
- `runs[].outputs`
  结果摘录，可放报告摘要或关键输出片段。
- `runs[].formal_grades`
  必填量化评分项，必须带：
  - `text`
  - `passed`
  - `evidence`
- `runs[].findings`
  这次输出识别到的关键问题。推荐带：
  - `severity`
  - `title`
  - `detail`
  - `remediation`
- `runs[].audit_result`
  体检结果摘要，推荐带：
  - `maturity_stage`：`概念验证 / 可内测 / 可受控上线 / 可规模化运行`
  - `confidence`：`高 / 中 / 低`
  - `domain_verdicts`
- `runs[].audit_result.domain_verdicts`
  一级审计域判断，推荐带：
  - `domain`
  - `verdict`
  - `risk`
- `runs[].metrics`
  记录 `duration_ms` 与 `tokens`。
- `benchmark.observations`
  可选人工分析结论；为空时脚本会自动补基本观察。

## 报告结构

生成后的 HTML 报告包含：

### 1. 结果详情

- 左侧为 eval 列表
- 右侧展示：
  - 当前场景的 prompt / expected_output / assertions
  - 各配置的输出摘录
  - formal grades
  - findings
  - maturity / confidence / domain verdicts
  - 本地 feedback 输入框与 `feedback.json` 下载

### 2. 审计对比

- 配置级摘要卡片
- 通过率、平均分、耗时、token
- P0 / P1 finding 数量
- 成熟度分布
- assertion breakdown
- 自动观察结论

### 3. 评测集概览

- 全量 eval 的 prompt
- assertions 覆盖
- 适合人工检查样本覆盖面是否足够

## 使用建议

- 最少准备 2 个场景，避免只测单一类型问题
- 每个场景至少有 2-5 条 assertions
- `formal_grades` 优先写可验证结论，不写主观感受
- `findings` 用于体现这次输出识别到了哪些真实缺口
- `audit_result.domain_verdicts` 尽量只填关键一级域，不必机械覆盖全部 7 个一级域
- 如果某次输出没有识别出任何 findings，也应该明确写原因，而不是留空装作无问题

## 资源

- 默认模板：`assets/harness-evaluation-template.json`
- 生成脚本：`scripts/build_harness_eval_report.py`
