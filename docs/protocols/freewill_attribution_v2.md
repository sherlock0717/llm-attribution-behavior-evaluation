# Free-Will Attribution V2 Protocol

```
protocol_id: freewill-attribution-v2
protocol_version: "2.0-mock"
status: implemented_mock
executable: true
supported_providers: [mock]
```

> **FAST-001 状态更新**：v2 现已针对**确定性 mock provider** 实现（`executable: true` 仅表示"可用 mock 运行"）。
> 这**不代表**存在真实模型运行，也**不代表** BMK-L1 已达成（benchmark `current_maturity_level` 仍为 `pre-BMK-L1`）。
> 真实 provider 运行属 RUN-003（需单独授权）。§19 的八个 Open Questions 已冻结为实现决定（见 §19）。

## 1. 修订目标

针对 v1 已确认问题（`docs/audit/research_protocol_source_map.md`）：

- **prompt snapshot 不完整**：v1 无历史精确 prompt 快照/hash → v2 要求运行时归档 prompt 全文 + hash。
- **构念标签暴露**：v1 `expose_construct_names: true`（prompt 逐题带 `scale` 标签）→ v2 默认**构念标签盲化**（construct-label blinding）：不显示 `scale: agency` 等标签，但题项语义仍表达相应构念。
- **输出结构稳定性**：v1 靠 `extract_json` 容错 → v2 定义严格 response schema + validation。
- **首次响应与 repair 区分**：v1 无题项级 repair、无首答/修复分离 → v2 定义 repair 策略并强制保留首答。
- **运行元数据**：v1 缺 run manifest/token/cost/timestamp/hash → v2 要求完整 RunManifest（见 BENCHMARK_SPEC）。
- **失败分类**：v1 无失败分类 → v2 引用 Failure Taxonomy。
- **可审计性**：v2 要求 artifact 级 hash 与 provenance 完整。

## 2. 研究问题

（在 v1 三问基础上收紧）
- RQ1：盲化构念名后，过程结构对 agency 的效应是否仍稳定？
- RQ2：free_will_attribution 是直接随过程变化，还是经由 agency 的间接路径？
- RQ3：效应能否与文本长度（length-control）、感知智能（perceived_intelligence）区分？
- RQ4（工程）：v2 相对 v1 的输出质量与运行可审计性是否提升？

## 3. 假设分层

> **H-C01/H-C02 前置声明**：These are prospective replication hypotheses informed by v1 and become confirmatory only after the v2 protocol is frozen before any v2 result is inspected.（在 v2 协议冻结且未查看任何 v2 结果前，它们只是前瞻性复制假设。）

| id | 类型 | 假设 |
|---|---|---|
| H-C01 | Prospective replication → confirmatory（冻结后） | 过程结构等级越高，agency 评分越高（在主要模型中控制 `char_len`、`scenario` 或预定义设计变量后仍成立；`perceived_intelligence` 不作默认协变量）。 |
| H-C02 | Prospective replication → confirmatory（冻结后） | `reasons_concise` > `direct_choice_long`（结构诊断条件的 agency 高于同等长度的 length-control 诊断条件）。 |
| H-E01 | Exploratory | 过程 → agency → free_will_attribution 的 associational indirect-path 区间不跨 0。 |
| H-E02 | Exploratory | 身份标签（AI vs 人类）对 free_will_attribution 有主效应。 |
| H-E03 | Exploratory | 责任相关维度方向不如 agency 稳定。 |

> 不得把探索性假设写成确认性假设。工程质量项不作为研究"假设"，改列为 §16.1 Engineering Acceptance Criteria（AC-Q01~AC-Q03）。

## 4. 条件设计

| v1 condition | v2 决定 | 说明 |
|---|---|---|
| `direct_choice` | retain | 基线 |
| `direct_choice_long` | diagnostic_only | length-control，保留但单列 |
| `alternatives` | retain（候选） | 见 Open Questions Q-COND-1 |
| `reasons_concise` | diagnostic_only | 结构诊断 |
| `reasons` | retain | 完整理由结构 |
| `reflection_feedback` | retain | 最高结构 |

未定案项（是否合并 alternatives / 是否新增更高结构层）→ §19。

## 5. 身份设计

保留 `AI 决策者` / `人类决策者` 两标签。是否新增中性/无标签对照 → §19（Q-ID-1）。

## 6. 刺激版本

```
stimulus_set_id: freewill-attribution-stimuli
stimulus_version: v2-draft
snapshot_requirement: 运行时归档逐条刺激文本
hash_requirement: 记录 stimulus_hash（sha256 over canonical stimulus set）
```

## 7. 构念标签盲化（construct-label blinding）

v2 prompt 中**默认不显示构念标签**（如 `scale: agency`、`free_will`、`responsibility`）。但需明确：

- 题项**语义仍表达** agency / free will / responsibility；
- 因此**不能声称模型不知道自己正在评价这些概念**——这是构念**标签**盲化，不是"构念盲化"；
- `by_construct` 分组可能**反向暴露**构念结构（同组题项聚在一起）；
- 若需暴露标签版本，必须作为**单独对照协议**（`construct-label-exposed` variant），不得默认混入核心运行。

## 8. Prompt 结构

- `system_instruction`：中性评分者角色，只输出结构化 JSON。
- `task_instruction`：评分规则（一般题 1-7；factual 0-2）。
- `stimulus_block`：单条决策材料。
- `rating_items`：题项（盲化，无构念名）。
- `output_contract`：见 §9。
- `repair_instruction`：见 §12（仅在触发 repair 时附加）。

## 9. JSON 响应契约（定义，未实现）

模型实际需要生成的**核心 JSON 只包含 items**：

```json
{
  "items": [
    { "item_id": "string", "rating": 1 }
  ]
}
```

- 每个 item 至少：`item_id`、`rating`（整数，落在该题 valid_range）。事实操纵检验题仍属于 `items`，按其 `item_id` 与 0-2 范围验证。
- 以下字段由 **runner 写入 ResponseRecord，不得要求模型复述**：`participant_id`、`response_version`、`stimulus_id`、`scenario_id`、`condition`、`identity`、`batch_id`、`attempt`、`run_id`、`task_id`。
- **删除**独立自由文本 `attention_check`。
- `short_reason` **不属于核心评分响应**：core protocol 默认不生成理由；理由仅作为未来独立的 **optional explanation variant**（单独 prompt 变体），**不得与核心评分结果混在同一主运行中**。
- 此处为草案，不声称已实现。

## 10. Batching

```
batching:
  decision_status: unresolved
  candidates:
    - all_items
    - by_construct
    - single_item
  recommended_core_default: all_items
  methodological_constraint: >-
    Core mediation-compatible runs must collect agency and free_will_attribution in the
    same model response record. By-construct and single-item modes are separate prompt
    robustness variants and cannot replace the core run.
```

协议明确：

- 主要 v2 运行若保留**记录内中介分析**，必须在**同一次模型响应**中获得所有核心构念（agency 与 free_will_attribution）；
- `by_construct` / `single_item` 只能作为**单独的 prompt 稳健性试验**，不能替代核心运行；
- **不得把不同 API 调用自动拼成同一"模拟参与者"**；
- `by_construct` 不得写成主协议 provisional default；最终选择 → §19（Q-BATCH-1）。
- 记录 `batch_id`、题项呈现顺序、随机种子。

## 11. Parser 与 validation

- 严格 JSON 解析（拒绝非 JSON）。
- schema 校验：必填字段、item 覆盖全部题项、rating 落在 valid_range。
- 校验失败按 §12 处理并按 Failure Taxonomy 归类。

## 12. Repair

- 允许 repair 的错误：`MALFORMED_JSON`、`MISSING_ITEM`、`OUT_OF_RANGE`、`SCHEMA_FAILURE`（内容可修复类）。
- 最多次数：暂定 1 次（→ §19 Q-REPAIR-1）。
- **首次响应必须保留**；repair 响应**单独记录**（`attempt` 递增），repair 不得覆盖原始响应。
- repair 耗尽后仍失败：标 `REPAIR_EXHAUSTED`，记录为失败，不计入有效评分。

## 13. Failure handling

引用 [../benchmark/FAILURE_TAXONOMY.md](../benchmark/FAILURE_TAXONOMY.md)。provider/transport/content/parse/schema/lifecycle/artifact 各类分别处理，不统一标 retryable。

## 14. Scoring

题项 → 构念聚合（均值），factual 0-2 单列；盲化不改变计分口径。scoring_version 独立版本化。

## 15. Quality metrics

引用 `docs/benchmark/METRIC_SPEC.md`：first_attempt_parse_success_rate、final_parse_success_rate、first_attempt_schema_compliance_rate、final_schema_compliance_rate、missing_item_rate、range_validity_rate、repair_trigger_rate、repair_success_rate、empty_response_rate、duplicate_response_suspected_rate、response_length_chars、response_length_tokens。

## 16. 分析计划

- confirmatory（冻结后）：H-C01/H-C02（控制回归 + 预定义计划对比；主要模型可控制 `char_len`、`scenario` 或预定义设计变量）。
- exploratory：H-E01（**associational indirect-path diagnostic**，非因果中介机制）、H-E02/H-E03；`perceived_intelligence` 放入探索性中介或敏感性分析，不作默认确认性普通协变量（它可能是被操纵后的下游变量）。
- 预注册区分 confirmatory / exploratory；探索性不升级为确认性；中介统一写为 associational indirect-path diagnostic，不得写成因果中介机制。

### 16.1 Engineering Acceptance Criteria（非研究假设）

| id | 验收标准 |
|---|---|
| AC-Q01 | v2 的 final_parse_success_rate / final_schema_compliance_rate ≥ 预设阈值，且 first_attempt 与 final 分别记录。 |
| AC-Q02 | repair_trigger_rate 与 repair_success_rate、首答/修复分离可被完整记录（parent_attempt_id）。 |
| AC-Q03 | v2 运行产出完整 RunManifest（含各 *_hash；token/estimated_cost_usd 可 null）。 |

### 16.2 分析单位与依赖结构

- `participant_id` 是**模型生成记录 ID**，不是独立人类被试；
- 研究目标是**固定模型/Prompt 配置下的输出分布**；
- `scenario` 是**重复设计因素**；核心分析至少纳入 **scenario fixed effects 或预定义分层**；
- 需报告 **condition-by-scenario 稳健性**；
- **重复 run/seed 才是评估模型稳定性的主要复现层**（不是把同一 run 内记录当独立样本）。

## 17. v1/v2 比较

区分两类比较：

**A. historical-v1 comparison**（对历史 v1）：v1 缺 parse/schema/repair/token/cost/latency，**只能比较已有研究结果与聚合字段**（agency/free_will/条件均值/身份效应等），不得声称能比较 v1 的 parse/schema/token/cost/latency。

**B. v1-compatible rerun**（未来新运行）：使用新 runner、相同 provider/model 条件与 v1-compatible prompt，用于比较 parse/schema/token/cost/latency/repair。**该 rerun 是未来新运行，不是历史 v1 的重放**，当前**未实现、无结果**，不得注册为已实现。

可比较指标（B 类，未来）：first/final parse & schema、missing_item_rate、repair_trigger/success、response_length_chars/tokens、condition_sensitivity、identity_effect、repeat_run_stability、token_usage、estimated_cost_usd、latency_ms。

## 18. 运行前门禁

- TaskSpec / ModelSpec / RunSpec 校验通过；
- prompt/stimulus hash 可计算；
- 预算与并发上限设定；
- Failure Taxonomy 就绪；
- 构念盲化确认（默认盲化，暴露版本单列）。

## 19. Open Questions → 冻结实现决定（FAST-001）

以下八个问题在 FAST-001 已**冻结为首个 mock 垂直切片的实现决定**（保留设计空间用于未来稳健性变体）：

- **Q-COND-1**：保留现有 6 个条件，不新增；`alternatives` 保留；`direct_choice_long` / `reasons_concise` 继续作为诊断条件。
- **Q-ID-1**：只保留 `AI 决策者` / `人类决策者`，首个 v2 不加中性身份。
- **Q-OUT-1**：核心响应不生成 `short_reason`；explanation variant 延后。
- **Q-BATCH-1**：核心 batching = `all_items`；`by_construct` / `single_item` 仅为未来稳健性变体，不进入核心运行。
- **Q-REPAIR-1**：`max_repair_attempts = 1`。
- **Q-EXPOSE-1**：首个核心运行不含 construct-label-exposed 对照（属 BMK-002）。
- **Q-MODEL-1**：mock 垂直切片不绑定真实模型；真实 provider/model 属 RUN-003 运行配置。
- **Q-N-1**：mock smoke `n_per_cell=1`；mock acceptance `n_per_cell=2`；real smoke `n_per_cell=1`；real pilot `n_per_cell=5`；正式 BMK-L1 样本量在 pilot 后冻结。

> 仍需人工裁决的**真实运行**事项（provider/model 选择、预算、正式样本量）留待 RUN-003。
- Q-N-1：v2 每格 n 与总量？

> 以上均为**未决**，不得在本轮写成决定。
