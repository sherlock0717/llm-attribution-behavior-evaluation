# LLM Attribution Behavior Benchmark Specification

```
benchmark_id: llm-attribution-behavior
benchmark_version: "0.1-draft"
current_maturity_level: pre-BMK-L1
target_maturity_level: BMK-L1
release_status: planned
```

> RBC-001.1：区分 `current_maturity_level`（当前 **pre-BMK-L1**，尚无可复现运行）与 `target_maturity_level`（**BMK-L1**）。不得写 `maturity_level: BMK-L1` 或声称 BMK-L1 已达成。

> 本文件**只定义契约**，不实现 runner / provider，不落盘真实 Manifest。
> 当前任务：`freewill-attribution-v1-historical`（historical_reconstructed，不可执行）、`freewill-attribution-v2`（draft_specification，不可执行）。
> **API key 不属于任何 Spec 或 Manifest**；token/cost 可 null；所有 artifact 必须带 path + sha256；Manifest 记录实际运行而非计划。

字段说明统一维度：`name` / `type` / `required` / `nullable` / `description` / `validation` / `versioning_notes`。

---

## 一、BenchmarkSpec

| name | type | required | nullable | description | validation | versioning_notes |
|---|---|---|---|---|---|---|
| benchmark_id | string | yes | no | 全局唯一 benchmark 标识 | slug，唯一 | 变更即新 benchmark |
| benchmark_version | string | yes | no | 语义版本（含 -draft） | semver-like | major/minor 见 §九 |
| title | string | yes | no | 名称 | 非空 | — |
| description | string | yes | no | 描述 | 非空 | — |
| task_ids | list[string] | yes | no | 包含的 task_id | 每项存在于 TaskSpec | 增删 task 递增 minor |
| metric_ids | list[string] | yes | no | 引用的 metric_id | 每项存在于 METRIC_SPEC | — |
| current_maturity_level | enum | yes | no | 当前成熟度（pre-BMK-L1/BMK-L1..L4） | 见 §十 | 达成后提升 |
| target_maturity_level | enum | yes | no | 目标成熟度 | 见 §十 | 目标调整递增 minor |
| release_status | enum | yes | no | planned/internal/public | 枚举 | public 需 REL 授权 |
| license_status | enum | yes | no | unset/... | 当前 unset（不自动选许可证） | — |
| created_at | string(date) | yes | no | 创建日期 | ISO date | — |
| source_commit | string | yes | no | 契约对应 commit | 40-hex 或 unknown | 记录契约来源 |

null policy：所有 required 字段非 null；列表不得为 null（可空列表需显式空）。

---

## 二、TaskSpec

| name | type | required | nullable | description | validation |
|---|---|---|---|---|---|
| task_id | string | yes | no | 唯一任务 id | 唯一 |
| task_version | string | yes | no | 任务版本 | semver-like |
| protocol_ref | path | yes | no | 协议文档路径 | 文件存在 |
| constructs | list[string] | yes | no | 测量构念 | 与 scales 一致 |
| condition_schema | object | yes | no | 过程条件定义 | 6 条件 key |
| identity_schema | object | yes | no | 身份定义 | 2 value |
| stimulus_set | object | yes | no | 刺激集引用/版本 | version + hash 要求 |
| prompt_config | object | yes | no | prompt 策略/provenance | 见 prompt_provenance |
| response_schema | object | yes | no | 响应契约 | JSON schema |
| scoring_config | object | yes | no | 计分配置 | 聚合方式 |
| aggregation_config | object | yes | no | 聚合配置 | — |
| evidence_boundary | string | yes | no | 证据边界声明 | 非空 |
| status | enum | yes | no | historical_reconstructed/draft_specification/executable | 枚举 |
| executable | bool | yes | no | 是否可执行（当前所有 task 均 false） | 与 status 一致 |

> RBC-001.1：v1/v2 YAML 顶层字段名与本表一致（`condition_schema`/`identity_schema`/`stimulus_set`/`prompt_config`/`response_schema`/`scoring_config`/`aggregation_config`）。历史兼容字段（如 `n_per_cell`、`historical_record_count`、`seed_code_default`）放入 `legacy_metadata`，不作正式 TaskSpec 顶层字段。
>
> **核心响应契约**：模型只生成 `response_schema.core.items[*] = {item_id, rating}`；`participant_id/response_version/stimulus_id/scenario_id/condition/identity/batch_id/attempt/run_id/task_id` 由 runner 写入 ResponseRecord，模型不复述。`attention_check` 已从核心响应移除；`short_reason` 不属于核心评分响应（仅未来独立 explanation variant）。

---

## 三、ModelSpec

| name | type | required | nullable | description |
|---|---|---|---|---|
| provider | string | yes | no | provider 名（如 deepseek/mock） |
| model_id | string | yes | no | 模型标识（如 deepseek-chat） |
| model_version_snapshot | string | no | yes | 服务端版本快照（历史多为 null） |
| sampling_parameters | object | yes | no | temperature/max_tokens/seed 等 |
| capabilities | object | no | yes | json_mode 等能力 |
| endpoint_type | enum | yes | no | chat/completion/mock |

> **API key 不属于 ModelSpec**（永不记录）。

---

## 四、RunSpec

| name | type | required | nullable | description |
|---|---|---|---|---|
| benchmark_id | string | yes | no | 关联 benchmark |
| task_id | string | yes | no | 关联 task |
| model_spec | ModelSpec | yes | no | 模型规格（不含 key） |
| seed | int | yes | no | 随机种子 |
| n_per_cell | int | yes | no | 每格样本 |
| budget | object | yes | no | max_calls/max_cost_usd（可 null） |
| concurrency | int | yes | no | 并发 |
| retry_policy | object | yes | no | 重试策略 |
| resume_policy | object | yes | no | 续跑策略 |
| artifact_root | path | yes | no | artifact 根目录（禁写 outputs/） |

> **API key 不属于 RunSpec**。

---

## 五、RunManifest（只定义契约，不实现）

| name | type | required | nullable | description |
|---|---|---|---|---|
| run_id | string | yes | no | 运行唯一 id |
| status | enum | yes | no | pending/running/completed/failed/interrupted |
| started_at | string | yes | yes | 开始时间（ISO） |
| finished_at | string | yes | yes | 结束时间 |
| git_commit | string | yes | no | 运行时 commit |
| benchmark_version | string | yes | no | — |
| task_version | string | yes | no | — |
| resolved_config_hash | string | yes | no | resolved config 的 sha256 |
| task_spec_hash | string | yes | no | TaskSpec sha256 |
| model_spec_hash | string | yes | no | ModelSpec（不含 key）sha256 |
| prompt_template_hash | string | yes | no | prompt 模板 sha256 |
| prompt_snapshot_set_hash | string | yes | no | 实际渲染 prompt 快照集 sha256 |
| stimulus_set_hash | string | yes | no | 刺激集 sha256 |
| scoring_spec_hash | string | yes | no | 计分规格 sha256 |
| provider | string | yes | no | — |
| model_id | string | yes | no | — |
| model_snapshot | string | yes | yes | 服务端快照（可 null） |
| planned_records | int | yes | no | 计划记录数 |
| completed_records | int | yes | no | 实际完成 |
| failed_records | int | yes | no | 失败数 |
| retry_count | int | yes | no | 重试次数 |
| parse_failure_count | int | yes | no | 解析失败 |
| schema_failure_count | int | yes | no | schema 失败 |
| token_usage | object | yes | yes | prompt/completion/total（可 null） |
| estimated_cost_usd | number | yes | yes | 估算费用美元（可 null） |
| artifacts | list[object] | yes | no | 每项 {path, sha256} |
| errors | list[object] | yes | no | 失败记录（failure_code 等） |

**Canonical serialization（用于所有 *_hash）**：UTF-8 编码；稳定 key 排序；规范化换行（LF）；对规范化字节做 sha256。
规则：token/estimated_cost_usd 可为 null（费用字段全仓库统一为 `estimated_cost_usd`，不混用 `cost`/`estimated_cost`）；**API key 永远不记录**；所有 artifact 必须有 sha256；Manifest 必须反映**实际发生**的运行，而非运行计划。**本阶段不落盘真实 Manifest**。

---

## 六、ResponseRecord

| name | type | required | nullable | description |
|---|---|---|---|---|
| record_id | string | yes | no | 记录 id |
| run_id | string | yes | no | 所属运行 |
| task_id | string | yes | no | 所属任务 |
| condition | string | yes | no | 过程条件 key |
| identity | string | yes | no | 身份 value |
| request_index | int | yes | no | 请求序号 |
| batch_id | string | yes | yes | 批次 id |
| attempt | int | yes | no | 第几次尝试（首答=1） |
| parent_attempt_id | string | yes | yes | repair 通过它关联首答（首答为 null） |
| stimulus_id | string | yes | no | 刺激 id |
| scenario_id | string | yes | no | 情境 id |
| persona_ref | path | yes | yes | persona 引用（artifact + sha256） |
| prompt_ref | path | yes | no | 渲染 prompt 引用（artifact + sha256） |
| request_ref | path | yes | no | 请求引用（artifact + sha256，不含 key） |
| raw_response_ref | path | yes | no | 原始响应引用（artifact + sha256） |
| parsed_response | object | yes | yes | 解析后结构（失败为 null） |
| parse_status | enum | yes | no | ok/malformed/... |
| validation_status | enum | yes | no | ok/missing_item/out_of_range/... |
| latency_ms | number | yes | yes | 延迟（可 null） |
| usage | object | yes | yes | token usage（可 null） |
| provider_metadata | object | yes | yes | provider 元数据（不含 key） |

> `prompt_ref`/`request_ref`/`raw_response_ref`/`persona_ref` 均作为 artifact 引用并带 sha256；模型**无需复述** condition/identity 等元数据（runner 写入）；`attempt=1` 为首答，repair 响应通过 `parent_attempt_id` 关联首答且单独记录，不覆盖首答。

---

## 七、ScoreRecord

| name | type | required | nullable | description |
|---|---|---|---|---|
| record_id | string | yes | no | 关联记录 |
| metric_id | string | yes | no | 指标 id |
| raw_value | number | yes | yes | 原始值 |
| normalized_value | number | yes | yes | 归一化值 |
| validity | enum | yes | no | valid/invalid/partial |
| evidence | object | yes | yes | 计算证据 |
| scoring_version | string | yes | no | 计分版本 |

---

## 八、AggregateReport

| name | type | required | nullable | description |
|---|---|---|---|---|
| run_id | string | yes | no | 关联运行 |
| execution_quality | object | yes | no | 完成率/重试/延迟等 |
| output_quality | object | yes | no | parse/schema/missing 等 |
| task_metrics | object | yes | no | agency/free_will 等构念指标 |
| reliability_metrics | object | yes | yes | 重复稳定性等 |
| comparative_metrics | object | yes | yes | v1/v2 或多模型比较 |
| limitations | list[string] | yes | no | 局限声明 |
| figure_refs | list[object] | yes | yes | 图引用 {path, sha256} |

---

## 九、版本规则

- **benchmark major**：不兼容的 task 集合/指标语义变更。
- **benchmark minor**：新增 task/metric、成熟度提升。
- **task version**：条件/刺激/协议实质变更递增。
- **prompt version**：prompt 结构/盲化策略变更递增（并记录 prompt_hash）。
- **scoring version**：聚合/计分口径变更递增。
- **metric version**：指标定义/公式变更递增。
- **breaking change**：改变已发布结果可比性者，必须 major。

---

## 十、成熟度

- **BMK-L1**：单任务、单模型、可复现运行与重复稳定性。
- **BMK-L2**：多模型比较。
- **BMK-L3**：相关任务套件。
- **BMK-L4**：公开版本化 Benchmark。

> 当前 `current_maturity_level = pre-BMK-L1`（尚无可复现运行），`target_maturity_level = BMK-L1`；L2–L4 为未来方向，未经人工批准不执行。**不得声称 BMK-L1 已达成。**
