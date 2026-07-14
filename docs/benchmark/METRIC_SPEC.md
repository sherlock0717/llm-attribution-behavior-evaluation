# Metric Specification

> 统一模板字段：`metric_id` / `name` / `category` / `status` / `definition` / `inputs` / `calculation` / `range` / `direction` / `aggregation` / `missingness_policy` / `evidence_level` / `applicable_tasks` / `source_mapping` / `limitations`。
> **指标数量由 `configs/metrics/attribution_metrics.v1.yaml` 动态计算，不在任何摘要中手写死**（当前实现拆分后 registry 条目数以 YAML 为准）。
> `status`：`planned`（无实现）/`planned_without_formula`（已登记但公式待定）/`derived`/`direct`/`historical_available`/`alias`。
> `direction`：`higher_better` / `lower_better` / `context`（不得把全部指标写成"越高越好"）。
> `applicable_tasks`：`v1`=freewill-attribution-v1-historical，`v2`=freewill-attribution-v2。
> 统计效应类指标必须说明估计量、置信区间与比较单位。

## A. Execution Integrity

| metric_id | status | definition | calculation | range | direction | aggregation | missingness_policy | evidence_level | applicable_tasks | source_mapping | limitations |
|---|---|---|---|---|---|---|---|---|---|---|---|
| planned_record_count | planned | 计划记录数 | n_per_cell×conditions×identities | int≥0 | context | per-run | n/a | reconstructed_from_code | v2 | RunManifest.planned_records | v1 未归档 |
| completed_record_count | planned | 完成记录数 | 计数 | int≥0 | higher_better | per-run | 缺失记失败 | direct(run) | v2 | RunManifest.completed_records | v1=360 反推 |
| failed_record_count | planned | 失败记录数 | 计数 | int≥0 | lower_better | per-run | n/a | direct(run) | v2 | RunManifest.failed_records | v1 unknown |
| completion_rate | planned | 完成率 | completed/planned | 0-1 | higher_better | per-run | 分母 planned | derived | v2 | RunManifest | v1 unknown |
| retry_rate | planned | 重试率 | retry_count/planned | ≥0 | lower_better | per-run | n/a | direct(run) | v2 | RunManifest.retry_count | v1 unknown |
| resume_count | planned | 续跑次数 | 计数 | int≥0 | context | per-run | n/a | direct(run) | v2 | RunManifest | v1 unknown |
| latency_ms | planned | 单请求延迟 | 记录 latency | ≥0 | lower_better | mean/median | null 排除 | direct(run) | v2 | ResponseRecord.latency_ms | v1 unknown |
| prompt_tokens | planned | 提示 token | provider usage | int≥0 | context | sum | 可 null | direct(run) | v2 | RunManifest.token_usage | v1 unknown |
| completion_tokens | planned | 生成 token | provider usage | int≥0 | context | sum | 可 null | direct(run) | v2 | RunManifest.token_usage | v1 unknown |
| total_tokens | planned | 总 token | prompt+completion | int≥0 | context | sum | 可 null | derived | v2 | RunManifest.token_usage | v1 unknown |
| estimated_cost_usd | planned | 估算费用（美元） | tokens×单价 | ≥0 | lower_better | sum | 可 null | derived | v2 | RunManifest.estimated_cost_usd | v1 unknown；依赖单价 |

## B. Output Quality

首答（first_attempt）与最终（final，含 repair 后）分开；解析成功率与 schema 合规率各分两级。

| metric_id | status | definition | calculation | range | direction | aggregation | missingness_policy | evidence_level | applicable_tasks | source_mapping | limitations |
|---|---|---|---|---|---|---|---|---|---|---|---|
| first_attempt_parse_success_rate | planned | 首答 JSON 解析成功率 | first_ok/total_first | 0-1 | higher_better | per-run | 分母=首答数 | direct(run) | v2 | ResponseRecord.parse_status(attempt=1) | v1 unknown |
| final_parse_success_rate | planned | 最终解析成功率 | final_ok/total | 0-1 | higher_better | per-run | — | direct(run) | v2 | ResponseRecord.parse_status(final) | v1 unknown |
| first_attempt_schema_compliance_rate | planned | 首答 schema 合规率 | first_valid/total_first | 0-1 | higher_better | per-run | — | direct(run) | v2 | ResponseRecord.validation_status(attempt=1) | v1 unknown |
| final_schema_compliance_rate | planned | 最终 schema 合规率 | final_valid/total | 0-1 | higher_better | per-run | — | direct(run) | v2 | ResponseRecord.validation_status(final) | v1 unknown |
| missing_item_rate | derived | 缺题率 | 缺失题项/应答题项 | 0-1 | lower_better | per-run | 空值计缺失 | direct(run) | v2 | ResponseRecord items | **v1 historical status = unknown**：scale_scores.csv 只有聚合构念列，聚合列无缺失**不能证明** 34 个题项都存在 |
| range_validity_rate | planned | 范围合法率 | 落区间/应答 | 0-1 | higher_better | per-run | — | direct(run) | v2 | normalize 范围校验 | v1 unknown |
| repair_trigger_rate | planned | repair 触发率 | repaired/total | 0-1 | **context** | per-run | — | direct(run) | v2 | ResponseRecord.attempt | 触发率高低本身非好坏（context）；需结合 repair_success_rate |
| repair_success_rate | planned | repair 成功率 | repair_fixed/repair_triggered | 0-1 | higher_better | per-run | — | direct(run) | v2 | ResponseRecord(parent_attempt_id) | v1 无 repair |
| empty_response_rate | planned | 空响应率 | empty/total | 0-1 | lower_better | per-run | — | direct(run) | v2 | Failure EMPTY_RESPONSE | v1 unknown |
| duplicate_response_suspected_rate | planned | 疑似重复响应率 | suspected_dup/total | 0-1 | context | per-run | — | direct(run) | v2 | Failure DUPLICATE_RESPONSE_SUSPECTED | 质量诊断，不自动删记录 |
| response_length_chars | planned | 响应字符长度 | len(chars) | ≥0 | context | mean/median | — | direct(run) | v2 | raw_response_ref | — |
| response_length_tokens | planned | 响应 token 长度 | completion tokens | ≥0 | context | mean/median | 可 null | direct(run) | v2 | RunManifest.token_usage | 依赖 provider |
| parse_success_rate | alias | 兼容别名 → final_parse_success_rate | 见 final_parse_success_rate | 0-1 | higher_better | per-run | — | — | v2 | alias | 仅兼容旧引用 |
| schema_compliance_rate | alias | 兼容别名 → final_schema_compliance_rate | 见 final_schema_compliance_rate | 0-1 | higher_better | per-run | — | — | v2 | alias | 仅兼容旧引用 |
| repair_rate | alias | 兼容别名 → repair_trigger_rate | 见 repair_trigger_rate | 0-1 | context | per-run | — | — | v2 | alias | 仅兼容旧引用 |

## C. Task Metrics

量表口径见 `src/scales.py`；聚合为题项均值（`analyze_results.py`）。1-7 除 factual（0-2）。

| metric_id | status | definition | calculation | range | direction | aggregation | evidence_level | applicable_tasks | source_mapping | limitations |
|---|---|---|---|---|---|---|---|---|---|---|
| factual_process_check | historical_available | 事实操纵检验 | 3 题(0-2)均值 | 0-2 | context | cell mean | direct_file_evidence | v1,v2 | scales factual_manipulation_check | 操纵检验非结果 |
| subjective_process_completeness | historical_available | 主观过程完整性 | 3 题均值 | 1-7 | context | cell mean | direct_file_evidence | v1,v2 | scale_scores 同名列 | 主观 |
| agency | historical_available | 行动者感 | 6 题均值 | 1-7 | context | cell mean | direct_file_evidence | v1,v2 | scale_scores.agency | 主结果 |
| free_will_attribution | historical_available | 自由意志归因 | 5 题均值 | 1-7 | context | cell mean | direct_file_evidence | v1,v2 | scale_scores.free_will_attribution | 与 agency 分开 |
| responsibility | historical_available | 责任相关合成 | 责任子构念 | 1-7 | context | cell mean | reconstructed_from_code | v1,v2 | scale_scores.responsibility_total | 探索性 |
| perceived_intelligence | historical_available | 感知智能 | 3 题均值 | 1-7 | context | cell mean | direct_file_evidence | v1,v2 | scale_scores.perceived_intelligence | 见下：不作默认确认性协变量 |
| condition_sensitivity | planned_without_formula | 条件区分度（预定义对比 + 次级趋势） | 见下方预定义对比，估计量+95%CI，比较单位=指定条件对 | 依估计量 | context | per-metric | reconstructed_from_outputs | v1,v2 | controlled_regression/planned_contrasts | 公式待定 |
| identity_effect | planned_without_formula | 身份主效应 | AI vs 人类 均值差 + 95%CI，单位=身份对比 | 依估计量 | context | per-metric | reconstructed_from_outputs | v1,v2 | planned_contrasts | 探索性；公式待定 |

**condition_sensitivity 预定义对比（primary contrasts）**：
- `reasons_concise` vs `direct_choice_long`（结构 vs 纯长度）
- `reasons` vs `direct_choice`
- `reflection_feedback` vs `direct_choice`

ordinal trend（按 structure_level）**只作次级估计**；诊断条件如何进入趋势必须显式说明：`direct_choice_long`（structure_level=0，length-control）不作为结构递增节点计入趋势；`reasons_concise`（structure_level=2，结构诊断）在趋势中按其结构级处理但标注为诊断。

**perceived_intelligence 使用约束**：不作为默认确认性普通协变量；放入探索性中介或敏感性分析；说明它可能是被操纵后的下游变量（过程结构可能同时抬高感知智能）。

## D. Reliability

| metric_id | status | definition | calculation | range | direction | aggregation | evidence_level | applicable_tasks | source_mapping | limitations |
|---|---|---|---|---|---|---|---|---|---|---|
| repeat_run_stability | planned_without_formula | 重复运行稳定性 | 跨重复 run 的均值差/相关 + CI（公式待定） | context | higher_better(稳定) | across-runs | planned | v2 | 重复 run/seed | v1 仅单次；**重复 run/seed 才是评估模型稳定性的主复现层** |
| seed_sensitivity | planned | 种子敏感性 | 跨 seed 方差 | ≥0 | lower_better | across-seeds | planned | v2 | — | 未实现 |
| prompt_version_sensitivity | planned | prompt 版本敏感性 | 跨 prompt 版本差异 | context | context | across-versions | planned | v2 | prompt_template_hash | 未实现 |
| model_version_sensitivity | planned | 模型版本敏感性 | 跨模型快照差异 | context | context | across-snapshots | planned | v2 | model_snapshot | v1 快照 unknown |
| cell_variance | planned | 单元内方差 | 每格评分方差 | ≥0 | context | per-cell | reconstructed_from_outputs | v1,v2 | scale_scores | — |
| rank_stability | planned | 排序稳定性 | 条件排序跨运行一致性 | context | higher_better | across-runs | planned | v2 | — | 未实现 |

## E. Benchmark Quality Audit

| metric_id | status | definition | calculation | range | direction | aggregation | evidence_level | applicable_tasks | source_mapping | limitations |
|---|---|---|---|---|---|---|---|---|---|---|
| construct_coverage | planned_without_formula | 构念覆盖 | 覆盖构念数/目标构念数（公式待定） | 0-1 | higher_better | per-task | direct_file_evidence | v1,v2 | scales SCALE_ITEMS | 需定义"目标集" |
| condition_balance | planned_without_formula | 条件平衡 | 各格计数一致性度量（公式待定，如 max/min 或熵） | 0-1 | higher_better | per-task | reconstructed_from_outputs | v1,v2 | cell_counts（v1 全 30） | 公式待定 |
| item_leakage | planned | 题项泄漏 | 题项在 prompt 中被复述/暗示 | 0-1 | lower_better | per-run | planned | v2 | prompt 审计 | 未实现 |
| construct_label_exposure | direct | 构念标签暴露 | prompt 是否暴露构念**标签**（如 scale: agency） | bool | lower_better | per-task | direct_file_evidence | v1,v2 | prompt_config.expose_construct_labels（v1=true） | 仅标签层；题项语义仍表达构念 |
| missingness_bias | planned | 缺失偏倚 | 缺失与条件的关联 | context | lower_better | per-run | planned | v2 | — | 未实现 |
| metric_dependency | planned | 指标依赖 | 指标间相关/冗余 | context | context | per-benchmark | planned | v2 | — | 未实现 |
| provenance_completeness | planned_without_formula | provenance 完整度 | 已归档 provenance 项/应归档项（公式待定） | 0-1 | higher_better | per-run | historical_documentation | v1,v2 | provenance_gap（v1 多项 unknown） | v1 低 |
