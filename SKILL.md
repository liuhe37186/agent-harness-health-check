---
name: agent-harness-health-check
version: 1.5.0
description: 对用户的 Agent 系统做 Harness 体检，检查 workflow 与 agent 边界、执行回路、工具契约、权限审批、状态恢复、上下文治理、trace/replay、HITL、eval 与发布门禁是否达到可生产落地水平，并输出带证据的整改报告。只要用户提到“给我的 Agent 做体检”“审计 Agent 系统”“检查 harness / runtime / guardrails / eval 是否健全”“帮我找出为什么 Agent 只能 demo 不能上线”“生成 Agent 架构整改报告”“生成 Agent 体检 HTML 评测报告”“汇总多条 eval / formal grades / benchmark 生成评测页面”，都应优先使用本技能。
---

# Agent Harness 体检技能

## 这个技能解决什么问题

很多 Agent 系统的问题，不是“模型不够强”，而是 Harness 没接稳：

- 会调工具，但没有权限边界
- 能跑 demo，但没有状态恢复
- 有日志，但没有 trace / replay
- 有人工确认，但没有暂停 / 恢复语义
- 改一次 prompt 或模型后，没有 regression 门禁

这个技能的目标不是泛泛地讲架构，而是对用户当前 Agent 系统做一次可落地的 Harness 体检，产出：

- 当前系统的范围与证据清单
- 按维度拆分的符合项 / 不符合项
- 每个问题的风险等级与影响面
- 对应的改造建议、优先级和落地路径
- 一份能进入真实研发计划的整改报告

## 适用场景

- 用户想检查自己的 Agent 系统是否具备生产可用的 Harness
- 用户想知道为什么系统“能演示，但不稳”
- 用户要审计 coding agent、browser agent、research agent、多 Agent 系统
- 用户要在上线前做 runtime / eval / guardrails / approval 体检
- 用户要生成一份真实可执行的 Agent 架构整改报告

## 开始前必须确认

如果用户没有明确给出，优先补齐这些信息：

1. 审计对象是什么：代码仓库、设计文档、接口文档、运行日志、trace 还是它们的组合
2. 系统类型是什么：single-agent、multi-agent、coding、browser、research、workflow + agent 混合
3. 当前目标是什么：上线前体检、问题排查、架构升级、专项整改
4. 是否允许你读取仓库、配置、测试、日志、设计文档
5. 报告需要只在对话中给出，还是同时落成 Markdown 文件

如果用户没有说明，默认策略是：

- 优先基于可读到的代码、文档、配置和运行证据做判断
- 没有证据的内容标记为“待确认”，不要脑补
- 输出一份面向工程落地的体检报告，而不是纯概念点评

## 技能资源

本技能的审计基准在：

- `references/harness-audit-rubric.md`
- `references/harness-evaluation-report-schema.md`
- `assets/harness-evaluation-template.json`
- `scripts/build_harness_eval_report.py`

当你准备正式体检时，先读这份参考文件，再开始判断。

当用户要求“生成 HTML 评测报告”“输出评测页面”“把多条 eval 结果汇总成可分享报告”时，优先读取：

- `references/harness-evaluation-report-schema.md`
- `assets/harness-evaluation-template.json`
- `scripts/build_harness_eval_report.py`

这条能力是本技能内建工作流的一部分，不依赖其他技能，不需要调用外部 skill evaluator。只要当前任务已经进入“评测 / benchmark / with_skill 对比 / formal grades / findings 汇总”场景，就应主动切换到 HTML 评测报告分支。

如果用户提供了代码仓库、架构文档目录、知识库目录或一组 Markdown / 设计文档，不要假设存在某个固定项目结构。你应该先在用户给定材料里主动搜索下面这些主题，再决定补读哪些文件：

- agent harness / runtime / orchestration
- resume / continuation / checkpoint / state schema
- approval / HITL / interrupt / reject / override
- trace / transcript / replay / observability
- tool registry / tool contract / risk tier / trust level
- safety eval / regression / release gate / failure taxonomy

优先读取最可能承载这些主题的材料，例如：

- 架构总览、运行时设计、状态机设计
- 安全策略、审批策略、权限模型
- 评测框架、回归门禁、失败复盘
- 工具层设计、执行边界、沙箱与副作用控制

如果用户没有提供外部知识材料，就只基于技能自带的 `references/harness-audit-rubric.md` 和用户提供的代码、配置、日志、trace、设计文档做判断，不要假设宿主环境一定存在某个固定知识库目录。

## 固定流程

按下面顺序执行，不要跳步：

1. 先明确审计范围
   - 这是代码实现体检，还是架构方案体检
   - 目标是“找问题”，还是“给整改路线”

2. 收集证据
   - 代码入口、agent loop、工具层、权限层、状态层、trace、eval、审批流
   - 配置文件、README、设计文档、测试、日志、运行样例

3. 先识别系统形态，再决定重点体检域
   - single-agent：重点看 loop、工具面、状态恢复、trace、eval
   - multi-agent：额外重点看 ownership、handoff artifact、resume decision
   - coding / browser / computer use：额外重点看执行隔离、roots、approval、幂等与副作用控制
   - 长运行任务：额外重点看 main resume surface、checkpoint、interrupt schema、pending writes

4. 判断证据够不够
   - 如果某个关键维度完全没有证据，不能直接下定论
   - 要标记“待确认”，并说明还缺什么材料

5. 按审计维度逐项检查
   - 以 `references/harness-audit-rubric.md` 为准
   - 每个维度都要给出结论、证据、风险、建议

6. 识别系统级问题，而不是只列散点缺陷
   - 比如“状态恢复缺失”往往会同时影响 approval、长任务、replay 和回归
   - 比如“没有 main resume surface”往往会同时影响中断恢复、ownership、pending_action 和审计裁决
   - 比如“只有 risk tier 没有 trust level”往往会同时影响工具放权、审批路由和结果裁剪
   - 要指出根因，不要只写表层现象

7. 给出整改路径
   - 先给 P0 / P1 / P2 优先级
   - 再给 quick wins、下一阶段、上线前门禁
   - 如果合适，补一条“最小可上线方案”，帮助用户从 demo 过渡到受控上线

8. 输出体检报告
   - 结构必须统一，方便用户直接进入改造计划

9. 识别是否进入评测场景
   - 如果用户在比较 `with_skill` / `without_skill`
   - 如果用户要求 benchmark、formal grades、断言通过率、评测页面、评测报告
   - 如果当前上下文已经有多条 eval、runs、findings、metrics
   - 不要只给对话摘要，应主动建议生成 HTML 评测报告

10. 如果进入评测场景，自动切换到 HTML 报告分支
   - 先告诉用户：当前更适合生成独立 HTML 评测报告，而不是只在对话中汇总
   - 再准备 `evaluation-input.json`
   - 然后运行 `scripts/build_harness_eval_report.py`
   - 最后返回 HTML 报告与 summary JSON 路径
   - 这一步必须使用本技能自带脚本、模板和 schema 完成，不依赖其他技能

## 一级审计域

正式体检时，优先把问题归入下面 7 个一级审计域，再展开细项：

1. `边界与架构`
   - workflow / agent 边界
   - single-agent / multi-agent 拆分理由
   - ownership 与 handoff 设计

2. `工具与放权治理`
   - tool registry / tool contract
   - risk tier 与 trust level
   - permission gate / approval routing / allowed roots

3. `状态与恢复`
   - main resume surface
   - checkpoint / state / pending writes
   - interrupt state schema / state_version / migration

4. `上下文与交接`
   - compaction / reset
   - handoff artifact
   - tool profile、ownership 与 pending_action 的连续性

5. `观测与审计`
   - trace / transcript / replay
   - decision record / audit log
   - retention / access / redaction

6. `安全与人工接管`
   - guardrails
   - HITL / pause / reject / resume
   - safe fallback / takeover / blast radius

7. `评测与发布门禁`
   - eval harness / regression
   - safety eval / stress testing
   - release gate / bad case 回流

## 证据优先级

判断时优先使用下面顺序的证据，不要把低质量材料当成强证据：

1. 运行时代码、状态结构、策略配置、测试代码
2. 真实 trace、transcript、日志样本、审批记录
3. 设计文档、架构图、README
4. 用户口头描述

如果高优先级证据和低优先级证据冲突，优先相信高优先级证据，并在报告中明确指出冲突。

## 审计原则

### 1. 先取证，再判断

不要只因为看到了 “agent”“workflow”“langgraph”“tools”“guardrails” 这些词，就默认系统做对了。

你必须优先寻找真实证据，例如：

- 是否真的存在工具注册与调用边界
- 是否真的有 checkpoint / session / state
- 是否真的支持 pause / resume
- 是否真的保留 trace / transcript / replay
- 是否真的有 eval 与 regression 门禁

### 2. 不把“有功能”误判成“有治理”

例如：

- 有确认框，不等于有 HITL
- 有日志，不等于有 trace / replay
- 有函数调用，不等于有 tool contract
- 有多 Agent，不等于 ownership 清晰
- 有测试，不等于有 eval harness

### 3. 缺证据就写缺证据

如果某一项无法从代码、文档、配置或运行材料中确认：

- 结论写“待确认”
- 补充需要用户提供什么材料
- 不要为了完整报告而编造系统能力

### 4. 结论必须能落到工程动作

每个不符合项都要说明：

- 为什么它违反 Harness 原则
- 当前会带来什么风险
- 具体应该改哪里
- 改造优先级是什么
- 最小落地方案是什么

### 5. 优先识别“主恢复面”和“决策记录”缺口

很多 Agent 系统最危险的不是“没有某个小功能”，而是下面两个主骨架缺位：

- 没有主恢复面：history、session、checkpoint、临时 state 混用，恢复时无法判定从哪里继续
- 没有决策记录：allow / reject / fallback / human takeover 发生了，但没有 reason code、evidence refs 和 policy version

遇到这类缺口时，要直接提升为系统级问题，而不是埋在某个细项里。

### 6. 不把 risk tier 当成 trust governance

如果系统只给动作分风险等级，却没有给工具本体分 trust level，也没有定义 data / action / namespace / result / autonomy boundary，不能判为工具治理成熟。

### 7. 不把普通回归当成安全门禁

如果系统只有通用 regression，没有 safety eval、policy stress testing、approval edge cases 和 recovery safety 样本，不能判为“发布门禁完整”。

## 报告结构

ALWAYS 使用下面这个结构输出结果；如果用户要求落盘，也按同样结构写入 Markdown：

```md
# Agent Harness 体检报告

## 一、体检范围
- 审计对象：
- 系统类型：
- 证据来源：
- 结论可信度：

## 二、执行摘要
- 总体结论：
- 当前阶段判断：概念验证 / 可内测 / 可受控上线 / 可规模化运行
- 最关键的 3 个问题：

## 三、总评分卡
| 维度 | 结论 | 风险等级 | 证据完整度 | 说明 |
|------|------|----------|------------|------|

## 四、逐项体检
### 1. [维度名称]
- 结论：
- 发现：
- 证据：
- 为什么不符合 Harness 原则：
- 当前风险：
- 建议改动：
- 最小落地方案：

## 五、优先级整改路线
- P0：
- P1：
- P2：

## 六、最小可上线方案
- 先补哪 3 项：
- 补完后能达到什么阶段：
- 仍然不能自动放开的边界：

## 七、上线前门禁建议
- 必须补齐：
- 可以延期：
- 建议监控：

## 八、待确认项
- 缺失证据：
- 建议补充材料：
```

## 评分口径

每个维度只能使用下面四种结论之一：

- `符合`：有明确实现和证据，且设计方向正确
- `部分符合`：有实现雏形，但边界、恢复、治理或可观测性不足
- `不符合`：关键能力缺失，已影响系统稳定性或可上线性
- `待确认`：证据不足，不能做强判断

风险等级使用：

- `P0`：不上线前必须修
- `P1`：短期必须进入研发计划
- `P2`：建议优化，不影响当前受控试运行
- `P3`：增强项

## 如何给出建议

建议不能停留在“建议增强”“建议完善”这种空话，至少要落到下面一种形式：

- 新增某个状态结构，例如 `session state`、`checkpoint schema`
- 抽离某层边界，例如 `tool registry`、`permission gate`
- 增加某类运行时语义，例如 `interrupt / resume`
- 新增某种观测资产，例如 `trace id`、`transcript store`、`replay`
- 建立某个治理动作，例如 `regression eval`、`approval policy`
- 明确主恢复面，例如统一到 `checkpoint + state`
- 增加决策记录，例如 `decision / reasons / evidence_refs / policy_version / next_action`
- 区分工具长期信任和单次动作风险，例如同时定义 `trust_level` 与 `risk_tier`
- 增加专项安全样本，例如 `approval edge cases`、`scope escalation`、`recovery safety`

如果能定位到代码目录、模块、配置或链路，优先明确指出应该改哪里。

## 常见误判提醒

- 不要把普通工作流误判成 agent harness 成熟
- 不要把单次成功运行误判成具备恢复能力
- 不要把日志打印误判成 observability
- 不要把人工按钮误判成 HITL runtime
- 不要把 demo 数据集误判成 regression eval

## 汇报格式

完成后默认用中文按下面结构对用户汇报：

- `审计对象`：这次看了哪些代码、文档、配置和运行材料
- `总体判断`：当前系统处于什么成熟度阶段
- `关键问题`：最影响上线和稳定性的缺口
- `整改建议`：P0 / P1 / P2 的落地动作
- `最小可上线方案`：如果用户只想先过受控上线，最少要补哪几项
- `结论可信度`：哪些结论证据充分，哪些仍待确认
- `交付物`：报告文件路径或对话内报告

## HTML 评测报告

如果用户不是只要一次体检结论，而是要把多条 eval、with_skill / baseline 对比、formal grades、findings 和 benchmark 汇总成可分享页面，就不要只在对话里总结；应改用 HTML 评测报告链路。

这不是一个“用户明确要求时才可用”的附加能力，而是本技能在评测场景下的默认工作流分支。

### 适用场景

- 用户要“给技能做评测报告”
- 用户要“输出 HTML 页面 / 可分享报告”
- 用户要把多条 eval 的输出、formal grades、findings、maturity stage 汇总展示
- 用户要把 `with_skill`、`without_skill` 或多版本输出做可视化对比
- 用户已经在当前上下文里给出多条 eval、formal grades、runs、metrics 或 benchmark 材料

### 自动建议规则

出现下面任一信号时，应主动建议生成 HTML 评测报告，而不是只输出一段文字总结：

1. 用户提到 `评测`、`benchmark`、`打分`、`formal grades`、`with_skill / without_skill`
2. 当前任务已经有 2 条及以上 eval 或 2 个及以上配置结果
3. 当前任务需要把 findings、maturity stage、pass rate、耗时或 token 汇总对比
4. 用户需要“可分享页面”“HTML 报告”“评测结果页”

建议用户时要明确说明：

- 生成 HTML 报告是本技能内建能力
- 使用本技能目录里的模板、schema 和脚本即可完成
- 不依赖 `skill-evaluator` 或其他外部技能

### 输入结构

优先使用：

- `assets/harness-evaluation-template.json`

字段说明见：

- `references/harness-evaluation-report-schema.md`

最小输入至少包含：

- `meta`
- `configs`
- `evals`
- `evals[].assertions`
- `evals[].runs[].formal_grades`

建议同时补齐：

- `runs[].findings`
- `runs[].audit_result`
- `runs[].metrics`
- `benchmark.observations`

### 生成命令

执行：

```bash
python3 path/to/agent-harness-health-check/scripts/build_harness_eval_report.py \
  --input "path/to/evaluation-input.json" \
  --output "path/to/harness-eval-report.html"
```

脚本会同时生成：

- `harness-eval-report.html`
- `harness-eval-report.summary.json`

### 独立性要求

HTML 评测报告链路必须视为本技能自带能力，执行时遵守下面约束：

- 不依赖其他技能来决定是否生成报告
- 不依赖其他技能来构造报告 schema
- 不依赖其他技能来生成 HTML 页面
- 仅使用本技能目录中的：
  - `assets/harness-evaluation-template.json`
  - `references/harness-evaluation-report-schema.md`
  - `scripts/build_harness_eval_report.py`

### 报告内容

生成后的 HTML 默认包含 3 个标签页：

1. `结果详情`
   - 按 eval 展示 prompt、expected output、assertions、各配置输出、formal grades、findings、audit result
2. `审计对比`
   - 汇总 pass rate、avg score、P0 findings、平均耗时、token、成熟度分布、自动观察结论
3. `评测集概览`
   - 展示本轮评测集的 prompt 与 assertions 覆盖

### 输出契约

如果生成 HTML 评测报告，最终至少交付：

- 评测输入 JSON
- HTML 报告文件
- summary JSON
- 对用户的简要总结：总体分数、关键差异、主要风险、文件路径

## 自测要求

完成技能编写或修改后，至少检查：

1. `SKILL.md` frontmatter 完整，包含 `name`、`version`、`description`
2. `references/harness-audit-rubric.md` 可正常读取
3. 技能说明中已经明确“先取证、再判断、再整改”
4. 报告结构中包含范围、评分卡、逐项体检、整改路线、待确认项
5. 技能不会鼓励在证据不足时编造结论
6. 如果提供 `evals/evals.json`，评测样本应优先使用场景驱动描述，而不是绑定某个固定项目路径
7. 如果提供 HTML 评测报告能力，脚本、模板和 schema 必须彼此一致
8. HTML 报告至少能展示 eval、formal grades、findings 和汇总对比
9. 技能在评测场景下会主动建议生成 HTML 报告，而不是被动等待用户点名
10. 评测报告链路必须能独立运行，不依赖其他技能

## 当前版本边界

`1.5.0` 版本覆盖的是 Agent Harness 体检与整改建议，重点是：

- 基于现有代码和文档做架构与运行时审计
- 生成可落地的体检报告
- 给出整改优先级与上线前门禁
- 提供可独立分发的场景驱动评测样本
- 提供更难被关键词投机满足的二阶 expectations 设计
- 提供独立 HTML 评测报告生成能力
- 提供 GitHub 风格 README 与 `Apache-2.0` 协议文件
- 在评测场景下自动建议走 HTML 评测报告工作流
- 明确 HTML 报告能力独立于其他技能

当前版本不负责：

- 自动修改整个 Agent 系统实现
- 自动生成完整生产代码补丁
- 自动收集线上真实 trace 平台数据

如果后续要升级，优先考虑：

1. 增加专项审计模式，例如 coding agent / browser agent / multi-agent
2. 增加基于样例仓库的 benchmark 与判分准则
3. 增加更细粒度的图表、趋势与历史对比视图
