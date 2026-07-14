# Failure Taxonomy

> 每项字段：`failure_code` / `stage` / `failure_scope` / `terminal_scope` / `description` / `retryable` / `record_required` / `repair_allowed` / `default_severity` / `example` / `notes`。
> `stage`：configuration / provider / transport / content / parse / schema_validation / scoring / run_lifecycle / artifact_integrity。
> `failure_scope` ∈ {run, request, record, artifact}；`terminal_scope` ∈ {none, attempt, record, run}。
> **不得把所有失败都标为 retryable**；provider/API、content、parse、validation、scoring、lifecycle、artifact 严格区分。

| failure_code | stage | failure_scope | terminal_scope | retryable | record_required | repair_allowed | default_severity | description / example / notes |
|---|---|---|---|---|---|---|---|---|
| CONFIG_INVALID | configuration | run | run | no | no | no | fatal | 配置非法（如 n<1）；运行前门禁拦截 |
| TASK_SPEC_INVALID | configuration | run | run | no | no | no | fatal | TaskSpec 不合法（缺 protocol_ref） |
| MODEL_SPEC_INVALID | configuration | run | run | no | no | no | fatal | ModelSpec 不合法；key 不属于 spec |
| BUDGET_EXCEEDED | run_lifecycle | run | run | no | yes | no | fatal | 超预算，主动停止 |
| AUTH_FAILURE | provider | run | run | no | yes | no | fatal | 认证失败（401/密钥无效）；**不记录 key 值** |
| RATE_LIMITED | provider | request | none | yes | yes | no | warning | 429；退避重试 |
| PROVIDER_TIMEOUT | provider | request | attempt | yes | yes | no | error | 超时；退避重试 |
| PROVIDER_UNAVAILABLE | provider | request | attempt | yes | yes | no | error | 503；退避重试 |
| TRANSPORT_ERROR | transport | request | attempt | yes | yes | no | error | 连接重置；退避重试 |
| PROMPT_RENDER_FAILURE | configuration | record | record | no | yes | no | error | prompt 模板渲染失败（缺变量/模板错误） |
| STIMULUS_INVALID | configuration | record | record | no | yes | no | error | 刺激缺失/非法/hash 不符 |
| EMPTY_RESPONSE | content | record | attempt | yes | yes | no | error | 空响应；重试 |
| TRUNCATED_RESPONSE | content | record | attempt | yes | yes | yes | error | 截断；增 token 重试/repair |
| MALFORMED_JSON | parse | record | none | no | yes | yes | error | JSON 无法解析；允许 repair |
| PARSE_FAILURE | parse | record | none | no | yes | yes | error | 解析其他失败；允许 repair |
| SCHEMA_FAILURE | schema_validation | record | none | no | yes | yes | error | 缺必填键；允许 repair |
| MISSING_ITEM | schema_validation | record | none | no | yes | yes | warning | 缺题项；repair 补全 |
| OUT_OF_RANGE | schema_validation | record | none | no | yes | yes | warning | 评分越界；置 null 或 repair |
| DUPLICATE_RESPONSE_SUSPECTED | content | record | none | no | yes | no | warning | **疑似**重复：不因两个 JSON 完全相同就自动判失败；仅当跨不同 stimulus 出现异常高比例完全相同输出时触发；属质量诊断，**不直接删除记录** |
| SCORING_FAILURE | scoring | record | record | no | yes | no | error | 计分阶段失败（聚合/映射异常） |
| REPAIR_EXHAUSTED | run_lifecycle | record | record | no | yes | no | error | repair 次数耗尽仍失败；记为失败，不计有效评分 |
| RUN_INTERRUPTED | run_lifecycle | run | none | yes | yes | no | error | 运行中断；resume 续跑 |
| RESUME_CONFLICT | run_lifecycle | run | run | no | yes | no | error | manifest 与 artifact 不一致；需人工介入 |
| ARTIFACT_WRITE_FAILURE | artifact_integrity | artifact | attempt | yes | yes | no | error | artifact 写入失败（磁盘/权限）；重试写 |
| ARTIFACT_HASH_MISMATCH | artifact_integrity | artifact | run | no | yes | no | fatal | artifact 哈希不匹配；完整性破坏，停止运行 |
| UNKNOWN_RUNTIME_ERROR | run_lifecycle | run | none | no | yes | no | error | 未分类运行时错误；记录并归类后处理 |

分类校验：
- configuration：CONFIG_INVALID、TASK_SPEC_INVALID、MODEL_SPEC_INVALID、PROMPT_RENDER_FAILURE、STIMULUS_INVALID。
- provider/API：AUTH_FAILURE、RATE_LIMITED、PROVIDER_TIMEOUT、PROVIDER_UNAVAILABLE。
- transport：TRANSPORT_ERROR。
- content：EMPTY_RESPONSE、TRUNCATED_RESPONSE、DUPLICATE_RESPONSE_SUSPECTED。
- parse：MALFORMED_JSON、PARSE_FAILURE。
- schema_validation：SCHEMA_FAILURE、MISSING_ITEM、OUT_OF_RANGE。
- scoring：SCORING_FAILURE。
- run_lifecycle：BUDGET_EXCEEDED、REPAIR_EXHAUSTED、RUN_INTERRUPTED、RESUME_CONFLICT、UNKNOWN_RUNTIME_ERROR。
- artifact_integrity：ARTIFACT_WRITE_FAILURE、ARTIFACT_HASH_MISMATCH。

terminal_scope 关键项：AUTH_FAILURE=run；REPAIR_EXHAUSTED=record；BUDGET_EXCEEDED=run；ARTIFACT_HASH_MISMATCH=run。

> AUTH_FAILURE 等涉及凭证的失败**只记录 failure_code 与非敏感上下文，绝不记录 API key / token 值**。
