# Harness 审计基准

这份文件是 `agent-harness-health-check` 的正式审计基准。体检时不要脱离这份基准随意发挥。

## 目录

1. 使用方式
2. 证据优先级
3. 一级审计域
4. 审计维度
5. 体检结论判断建议
6. 输出提醒

## 使用方式

逐个维度检查：

1. 看有没有实现
2. 看实现是不是正式能力，而不是 demo 拼接
3. 看有没有证据支撑
4. 看缺口会带来什么真实风险
5. 看建议是否能落到明确改造动作

## 证据优先级

优先使用下面顺序的证据：

1. 运行时代码、状态结构、策略配置、测试代码
2. 真实 trace、transcript、审批记录、运行样本
3. 设计文档、架构图、README
4. 用户口头描述

如果高优先级证据与低优先级证据冲突，优先信任高优先级证据，并在报告中单独指出冲突。

## 一级审计域

建议先把发现的问题归到下面 7 个一级域，再展开到具体维度：

- 边界与架构
- 工具与放权治理
- 状态与恢复
- 上下文与交接
- 观测与审计
- 安全与人工接管
- 评测与发布门禁

## 维度 1：Workflow 与 Agent 边界

### 检查重点

- 系统是否先区分固定流程和开放式 agent 决策
- 是否为了“像 Agent”而把本该确定性的流程也交给模型
- 多 Agent 是否有明确拆分理由，而不是先复杂化

### 符合信号

- 能清楚说明哪些链路是 workflow，哪些链路是 agent
- 单 Agent 已经覆盖主要价值场景后，才开始拆多 Agent
- 多 Agent 拆分基于职责、上下文边界或工具面复杂度

### 常见不符合

- 所有流程都交给模型自由决定
- 一开始就上多 Agent，但 ownership 不清楚
- manager、handoff、agents as tools 混用，没有边界定义

### 证据来源

- 架构图
- 编排代码
- agent 注册与路由逻辑
- 设计文档

### 整改方向

- 先把固定流程收回 workflow
- 先做 single-agent 最小闭环
- 只在确有必要时拆 specialist

## 维度 2：Agent Loop 与步数控制

### 检查重点

- 是否存在正式的“决策 -> 执行 -> 观察 -> 更新状态 -> 继续/结束”回路
- 是否有限步数、终止条件、超时与失败退出策略

### 符合信号

- 有明确 loop
- 有 `max_steps`、timeout、终止条件
- 失败时不是无限重试

### 常见不符合

- 只是单次 prompt + tool call
- 没有迭代上限
- 没有退出条件，容易卡死

### 证据来源

- 主执行器
- runner / orchestrator 代码
- 配置项

### 整改方向

- 补最小 loop
- 加步数上限、超时、失败退出
- 把成功 / 失败 / 中断状态显式化

## 维度 3：Tool Registry 与 Tool Contract

### 检查重点

- 工具是否显式注册
- 工具输入输出是否结构化
- 工具错误是否有可处理语义

### 符合信号

- 有统一工具注册层
- 参数、返回值、错误结构清晰
- 有工具说明，便于模型正确选择

### 常见不符合

- 直接暴露一堆函数给模型
- 返回值混乱，错误只能靠字符串猜
- 工具很多，但没有工具发现和裁剪机制

### 证据来源

- tool registry
- tool schema
- function definitions
- MCP server / client 配置

### 整改方向

- 建立统一工具契约
- 把错误码、重试策略、降级策略结构化
- 对大工具面增加 `allowed_tools` 或按需发现

## 维度 4：Tool Trust Levels 与 Execution Boundaries

### 检查重点

- 是否同时定义 `risk_tier` 和 `trust_level`
- 是否定义 data / action / namespace / result / autonomy boundary
- 是否存在 trust 升级、降级、复证和回退机制

### 符合信号

- 低信任工具默认只读或窄 scope
- 高信任工具具备审计、回放、脱敏和回滚控制
- risk tier 与 trust level 不混用，各自负责不同判断

### 常见不符合

- 只给动作分风险等级，不给工具本体分信任层
- 工具能调通就默认给高放权
- tool result 边界和 tool execution 边界脱钩

### 证据来源

- tool registry
- policy 配置
- trust / risk 映射表
- 结果裁剪与审批逻辑

### 整改方向

- 为每个工具同时补 `risk_tier` 与 `trust_level`
- 明确 data、action、namespace、result、autonomy 五类边界
- 为高 trust 工具补复证、回退和异常降级策略

## 维度 5：Permission Gate 与 Approval Policy

### 检查重点

- 是否把“能调用”和“允许执行”分开
- 高风险动作是否需要审批
- 是否有正式的 approval policy

### 符合信号

- 工具按只读、低风险、高风险分层
- 高风险动作要过审批
- 审批结果能影响后续运行状态

### 常见不符合

- 工具可见即默认可执行
- 只有前端确认框，没有运行时审批语义
- 删除、发布、支付、外发等动作无门禁

### 证据来源

- permission middleware
- policy 配置
- approval 节点
- 中断与恢复代码

### 整改方向

- 建立风险分级
- 抽离 permission gate
- 为高风险动作引入审批和拒绝分支

## 维度 6：State、Session 与 Checkpoint

### 检查重点

- 是否有正式状态层
- 是否支持 session / checkpoint / resume
- 是否避免中断后整轮重来

### 符合信号

- 有 `state`、`session` 或 `checkpoint` 结构
- 中断后可从稳定点恢复
- 中间产物可复用

### 常见不符合

- 只靠聊天历史续跑
- 一旦失败就从头再来
- 审批前后状态不一致

### 证据来源

- session store
- checkpointer
- 持久化层
- resume 逻辑

### 整改方向

- 引入状态模型
- 为关键步骤加 checkpoint
- 把恢复点、审批状态、中间产物显式存储

## 维度 7：Runtime Continuation 与 Main Resume Surface

### 检查重点

- 是否定义主恢复面，而不是 history / session / checkpoint / 临时 state 混用
- 是否保存 `pending_action`、`current_step`、`ownership`、`checkpoint_ref`
- 是否把“重新发一次请求”和“resume”严格区分

### 符合信号

- 能明确说出主 continuation surface
- 恢复时优先从 checkpoint / state 继续，而不是整段 history 回灌
- 多 Agent handoff 会把 ownership 和 artifact 一起进入 continuation record

### 常见不符合

- 同时依赖 history、session 和临时 state，但没有主恢复面
- 审批中断后靠重新请求凑恢复
- specialist handoff 后 ownership 错位

### 证据来源

- resume 逻辑
- continuation record
- checkpoint / state schema
- handoff artifact

### 整改方向

- 统一主恢复面
- 恢复时强制核对 `run_id`、`thread_id`、`current_step`、`pending_action`
- 把 ownership、tool_profile、resume_reason 纳入 continuation record

## 维度 8：Context Compaction、Reset 与 Handoff Artifact

### 检查重点

- 长任务是否只堆上下文
- 是否区分 compaction 和 reset
- 是否有交接物而不是纯靠记忆

### 符合信号

- 有摘要压缩策略
- 超长任务支持 clean slate reset
- 有结构化 handoff artifact

### 常见不符合

- 上下文无限膨胀
- 历史尝试和当前决策混在一起
- 多 Agent 交接只靠 prompt 文本

### 证据来源

- memory 管理逻辑
- summarization / trim 逻辑
- handoff 文件或状态对象

### 整改方向

- 对中长任务加 compaction
- 对超长任务加 reset 机制
- 把计划、完成项、待办、验证标准文件化

## 维度 9：Runtime Interrupt State Schema 与 State Version

### 检查重点

- 中断状态是否是正式 schema，而不是临时对象
- 是否包含 `pending_action`、`approval_state`、`ownership`、`tool_profile`
- 是否有 `state_version` 和 migration / reject 策略

### 符合信号

- interrupt state 可校验、可持久化、可恢复
- schema 区分业务状态和运行时控制状态
- 校验失败时会拒绝恢复或进入修复路径

### 常见不符合

- 把整段 history 当 interrupt state
- 不记录 `pending_action`、`ownership`
- 没有 state version，升级后历史状态全失效

### 证据来源

- interrupt schema
- validation 逻辑
- migration 逻辑
- recovery eval

### 整改方向

- 建立版本化 interrupt state schema
- 拆分业务状态与控制状态
- 为 schema validation failure 建安全拒绝和修复路径

## 维度 10：Trace、Replay 与 Observability

### 检查重点

- 是否能看到过程，而不只是最终答案
- 是否能 replay / fork / time travel
- trace 是否能进入调试、评测和线上监控

### 符合信号

- 每次 run 有 trace id 或同等标识
- 保留 tool call、状态变化、中断、恢复等关键事件
- 能回放 bad case

### 常见不符合

- 只有 print 日志
- 只有最终结果，没有过程记录
- 不能复现线上错误

### 证据来源

- trace store
- transcript
- observability 平台
- replay 逻辑

### 整改方向

- 建立 trace / transcript 存储
- 为关键事件打点
- 补 replay 与 checkpoint 分叉能力

## 维度 11：Trace Retention、Access 与 Redaction

### 检查重点

- trace 是否定义保留层级
- 是否有角色化访问控制
- 是否有 redaction 或引用化策略

### 符合信号

- 定义 hot / warm / archive / purged 或等价分层
- operator、reviewer、auditor、developer 视图不同
- 敏感字段默认受控，purge 后仍保留删除证明

### 常见不符合

- 永久全量保留所有 trace
- 所有人看到同一份高保真敏感数据
- 删除后完全断链，无法审计

### 证据来源

- retention policy
- access policy
- redaction 配置
- deletion / retention 证明

### 整改方向

- 建立 trace 保留与访问分层
- 把敏感内容改成引用化或裁剪展示
- 为 purge 和 retention 决策保留审计证明

## 维度 12：Failure Taxonomy、Durable Execution 与 Recovery

### 检查重点

- 是否区分失败类型
- 是否有按失败类型的恢复策略
- 是否能避免重复副作用

### 符合信号

- 至少区分 tool、state、retrieval、approval、context 等失败
- 不同失败有不同处理方式
- 已成功步骤不会因重跑重复执行

### 常见不符合

- 所有错误都统一重试
- 一失败就重开整轮
- 失败原因无法归类

### 证据来源

- 错误处理逻辑
- 重试策略
- 失败报告
- 运行记录

### 整改方向

- 建立失败分类
- 把 retry、abort、fallback、resume 分开
- 避免重复执行已成功副作用步骤

## 维度 13：Human-in-the-Loop

### 检查重点

- 人工介入是否是运行时能力
- 是否支持 pause / approve / reject / resume
- 是否有审计痕迹

### 符合信号

- 高风险动作前可中断
- 批准和拒绝都会进入正式状态转移
- 有恢复语义和审计记录

### 常见不符合

- 只有“确认一下”的 UI
- 审批后是重新发请求，不是恢复原 run
- 人工决定没有进入 trace

### 证据来源

- interrupt 代码
- approval 状态
- UI / API 审批流
- trace

### 整改方向

- 把 HITL 做成 runtime 原语
- 建立批准 / 拒绝 / 恢复分支
- 补审批轨迹和状态机

## 维度 14：Resume Decision Explainability 与 Audit Logs

### 检查重点

- 每次 allow / reject / fallback / human takeover 是否都有结构化 decision record
- 是否记录 reasons、evidence_refs、policy_version、next_action
- override 是否记录 actor、时效、退出条件

### 符合信号

- resume 尝试会生成 decision record
- reject 和 human takeover 会进入 audit log
- 高频拒绝原因可检索、可聚合、可进 bad case

### 常见不符合

- 只记录 `resume=false`，不记录原因
- 人工 override 生效了，但日志里看不出是谁批准的
- 决策理由写成长文本，无法检索聚合

### 证据来源

- decision logs
- audit logs
- approval / override 记录
- incident review 或 recovery eval

### 整改方向

- 建立 `decision / reasons / evidence_refs / policy_version / next_action` 结构
- 对 override 追加批准人、有效期和退出条件
- 把 reject / takeover 样本回流到专项 eval

## 维度 15：Eval Harness 与 Release Gate

### 检查重点

- 是否有固定任务集、失败分类和回归门禁
- 是否能把 bad case 回流成 regression 样本
- 是否在上线前有 release gate

### 符合信号

- 有 dataset、grader、failure taxonomy、regression runner
- 能比较新旧版本差异
- 关键能力进发布门禁

### 常见不符合

- 只做人工试几个问题
- 只看最终答案是否通过
- 没有 regression，只做 demo benchmark

### 证据来源

- eval 目录
- benchmark
- CI / release gate
- 失败样本库

### 整改方向

- 先从高频 bad case 建最小回归集
- 建 pass/fail + failure taxonomy
- 把关键指标进发布门禁

## 维度 16：Safety Evals 与 Policy Stress Testing

### 检查重点

- 是否有独立 safety eval，而不是只做通用 regression
- 是否覆盖 approval edge cases、scope escalation、recovery safety、policy bypass
- 失败样本是否关联 policy version 和 trace

### 符合信号

- 有高风险动作专项样本集
- 安全失败样本带 `policy_version`、`severity`、`trace_ref`
- 高严重问题可阻断发布

### 常见不符合

- 把安全评测混在通用 benchmark 里，只看总分
- 只测单步 prompt injection，不测多步组合风险
- 审批拒绝、超时、重复批准、部分批准没有单独样本

### 证据来源

- safety eval suite
- stress test 样本
- release gate
- bad case 库

### 整改方向

- 建独立 safety suite
- 把 approval edge cases、scope escalation、recovery safety 加入回归
- 为高严重失败配置阻断门禁

## 维度 17：执行隔离与副作用控制

### 检查重点

- coding / browser / computer use 是否隔离执行环境
- 是否限制文件系统、环境变量、账号和外部站点
- 是否控制副作用半径

### 符合信号

- 有容器、VM、浏览器隔离或等价边界
- 访问范围和根目录明确
- 对高风险站点和高影响动作有限制

### 常见不符合

- 直接在宿主环境高权限执行
- 根目录无边界
- 外部操作没有沙箱和限制

### 证据来源

- sandbox 配置
- roots / workspace 配置
- browser / vm 配置
- 执行策略

### 整改方向

- 补执行隔离层
- 明确 workspace boundary
- 对外部副作用动作做白名单与审批

## 体检结论判断建议

### 可以判断为“概念验证”

- 能完成任务，但状态、权限、eval、恢复都不稳定

### 可以判断为“可内测”

- 最小 loop、工具边界、基础状态已具备
- 但 replay、审批、回归门禁仍不足

### 可以判断为“可受控上线”

- 高风险动作可拦截
- 长任务可恢复
- 关键 bad case 可回放
- 有最小 regression 门禁
- 有主恢复面、decision log 和基本 safety eval

### 可以判断为“可规模化运行”

- 上述能力都具备
- 并且 trace、retention、eval、release gate、multi-agent ownership、隔离与成本治理也比较成熟

## 输出提醒

- 结论一定要引用真实证据
- 找不到证据就写“待确认”
- 不符合项一定要给工程化改造动作
- 不要只说“建议增强”“建议优化”
- 遇到“没有 main resume surface”“没有 decision record”“只有 risk tier 没有 trust level”“没有独立 safety eval”时，优先提升为系统级问题
