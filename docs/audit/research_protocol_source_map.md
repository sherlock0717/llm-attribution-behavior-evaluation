# Research Protocol Source Map

> RES-001 + BMK-001 前置产物。本文件在编写 v1/v2 协议与 Benchmark 契约**之前**完成。
> 所有事实直接来自源文件（代码 / 配置 / 产物 / provenance 文档），条件 key、身份标签、字段名均从文件读取，**不依据展示页中文名或记忆填写**。
> 分支：`docs/research-and-benchmark-contract`，起始 HEAD `b375d5a421e6c7d46412dc262b14cc0e659bd251`。

## 1. 审计范围

实际检查的源：

- **研究设计与刺激代码**：`src/stimuli.py`、`src/scales.py`、`src/run_simulated_study.py`、`src/analyze_results.py`（存在性 + 关键结构）。
- **当前工程配置**：`configs/study.default.yaml`、`configs/prompt.v1.yaml`、`configs/model.mock.yaml`；`src/freewill_attribution/{schemas,config,runner,cli,paths}.py`。
- **历史产物**：`outputs/scale_scores.csv`（程序化核查）、`outputs/{reliability_summary,anova_summary,controlled_regression_summary,planned_contrasts,process_dummy_coefficients,char_len_summary,domain_robustness_summary,scenario_robustness_summary,grouped_mediation_summary}.csv`、`outputs/{parallel_mediation_summary,mediation_summary}.json`、`outputs/*.md` 报告、`outputs/plots/*.png`。
- **本地忽略文件**：`outputs/raw_simulated_responses.jsonl`、`outputs/simulated_responses_wide.csv`（程序化检查存在性——本地工作树中**均不存在**，且被 `.gitignore` 排除）。
- **Provenance**：`docs/audit/v1_provenance_statement.md`、`docs/audit/baseline_hashes.txt`、`docs/audit/current_state_v0.1.md`、`AGENT_WORKLOG.md`。

配套机器可读证据见审核包内 `review_evidence/`（Review-time evidence summaries were generated outside the versioned contract and are non-normative）。所有正式 claim 必须能回溯到版本化来源：`src/**`、`outputs/**`、`configs/**`、`docs/audit/**`；不得以不入 Git 的路径作为规范证据。

## 2. 证据等级

| evidence_type | 含义 |
|---|---|
| `direct_file_evidence` | 事实直接写在被审计文件中（代码常量、YAML key、CSV 列、JSON 字段） |
| `reconstructed_from_code` | 由代码逻辑推断（如 prompt 由 `build_prompt()` 构造，但无归档快照） |
| `reconstructed_from_outputs` | 由产物数据反推（如历史 n=30 由 360 条记录反推） |
| `historical_documentation` | 来自项目内历史文档/provenance 声明（含作者事实声明） |
| `unknown` | 当前无法从任何文件裁决（历史缺失元数据） |

confidence：`high` / `medium` / `low`。

## 3. 研究设计事实表

| claim_id | claim | source_file | source_location | evidence_type | confidence | notes |
|---|---|---|---|---|---|---|
| DS-01 | 6 个过程条件 | `src/stimuli.py` | 常量 `PROCESS_CONDITIONS` | direct_file_evidence | high | 与 `configs/study.default.yaml: design.process_conditions` 一致 |
| DS-02 | 2 个身份标签 | `src/stimuli.py` | 常量 `IDENTITY_LABELS` | direct_file_evidence | high | `["AI 决策者","人类决策者"]` |
| DS-03 | 历史每格 30、总计 360 | `outputs/scale_scores.csv` | 记录级 6×2 分组计数（每格 30） | reconstructed_from_outputs | high | 见 `local_evidence/cell_counts.csv` |
| DS-04 | 当前配置默认 n=20 | `configs/study.default.yaml` | key `design.n_per_cell: 20` | direct_file_evidence | high | **与历史 n=30 不同**：配置默认值 ≠ 历史运行值；非冲突，见 DS-12 |
| DS-05 | 8 个情境 scenario | `src/stimuli.py` | 常量 `SCENARIOS`（8 个 `Scenario`） | direct_file_evidence | high | scenario 通过 `n % len(SCENARIOS)` 轮转分配 |
| DS-06 | 每条记录固定选择 | `src/stimuli.py` | `Scenario.fixed_choice`、`build_decision_text()` | direct_file_evidence | high | 过程条件只改"过程叙述"，选择固定 |
| DS-07 | 结构等级映射 | `src/stimuli.py` | 常量 `PROCESS_ORDINAL` | direct_file_evidence | high | `direct_choice`/`direct_choice_long`=0；`alternatives`=1；`reasons_concise`/`reasons`=2；`reflection_feedback`=3 |
| DS-08 | 设计构造与洗牌 | `src/run_simulated_study.py` | `make_design(n_per_cell, seed)`（`rng.shuffle`） | direct_file_evidence | high | seed 默认 `20260425` |
| DS-09 | 34 个题项、10 个构念 | `src/scales.py` | `ITEMS`、`SCALE_ITEMS` | direct_file_evidence | high | 见 §8 |
| DS-10 | 记录含 22 个聚合列 | `outputs/scale_scores.csv` | CSV 表头 | direct_file_evidence | high | 见 `local_evidence/historical_record_schema.txt` |
| DS-11 | 数据为模型模拟（非人类被试） | `docs/audit/v1_provenance_statement.md` | §2 记录性质 | historical_documentation | high | `synthetic=True`（设计标记） |
| DS-12 | 历史运行 n=30（≠ 默认 20） | `outputs/scale_scores.csv` + `src/run_simulated_study.py` | 360 条 = 6×2×30；`--n-per-cell` 可覆盖默认 | reconstructed_from_outputs | high | 历史运行以 n=30 执行；配置默认 20 是当前默认值，二者不冲突 |

## 4. 六个过程条件

condition key 直接取自 `src/stimuli.py: PROCESS_CONDITIONS`；display_name 取自 `PROCESS_LABELS`。历史每条件记录数取自 `local_evidence/condition_counts.csv`。

| condition_key | display_name | historical_role | stimulus_source | historical_record_count | evidence_type | v2_status | notes |
|---|---|---|---|---|---|---|---|
| `direct_choice` | 直接选择 | 基线（低结构） | `build_decision_text()` 分支 | 60 | direct_file_evidence | retain（候选） | structure_level=0 |
| `direct_choice_long` | 直接选择-长文本诊断 | 长度诊断（只加长度不加结构） | `_long_direct_background()` | 60 | direct_file_evidence | diagnostic_only | structure_level=0；length-control |
| `alternatives` | 候选方案 | 列出可选方案 | `build_decision_text()` 分支 | 60 | direct_file_evidence | retain（候选） | structure_level=1 |
| `reasons_concise` | 简洁理由权衡 | 结构诊断（给结构不加长度） | `_compact_reason_block()` | 60 | direct_file_evidence | diagnostic_only | structure_level=2 |
| `reasons` | 理由权衡 | 完整理由结构 | `_reason_block()` | 60 | direct_file_evidence | retain（候选） | structure_level=2 |
| `reflection_feedback` | 反思反馈 | 最高结构（反思+修正） | `build_decision_text()` 分支 | 60 | direct_file_evidence | retain（候选） | structure_level=3 |

> v2_status 中标注的 retain/diagnostic_only 仅为**候选建议**，最终去留见 v2 协议 Open Questions，本映射不作定案。

## 5. 两个身份标签

取自 `src/stimuli.py: IDENTITY_LABELS` / `IDENTITY_ORDINAL`；历史记录数取自 `local_evidence/identity_counts.csv`。

| identity_value | display_name | historical_record_count | source | notes |
|---|---|---|---|---|
| `AI 决策者` | AI 决策者 | 180 | `IDENTITY_LABELS[0]`，`IDENTITY_ORDINAL=0` | `make_design` 中编码前缀 `AI_` |
| `人类决策者` | 人类决策者 | 180 | `IDENTITY_LABELS[1]`，`IDENTITY_ORDINAL=1` | `make_design` 中编码前缀 `HU_` |

## 6. 刺激材料

- **来源**：`src/stimuli.py`，无外部数据文件；全部由 `build_decision_text(scenario, process_condition, identity_label)` 程序化生成。
- **固定部分**：`Scenario.context`（情境）、`Scenario.fixed_choice`（固定选择）。
- **条件变化部分**：`【决策过程】` 段落随 `process_condition` 变化（`_long_direct_background` / `alternatives` 列表 / `_compact_reason_block` / `_reason_block` / reflection 追加段）。
- **身份变化部分**：`actor = identity_label` 插入到 `【决策者身份】` 及过程叙述主语。
- **刺激版本号**：`configs/study.default.yaml: stimuli_version: v1`（config 层版本标记）。
- **历史刺激精确快照**：源代码即刺激生成器；`outputs/materials_preview.csv` 为材料预览。历史运行时逐条刺激文本随原始响应（`raw_simulated_responses.jsonl`，已 gitignore 且本地不存在）保存，公开仓库中无逐条刺激快照；但刺激可由代码 + seed 确定性重建（evidence：`reconstructed_from_code`）。

## 7. Prompt 证据

| 分类 | 内容 |
|---|---|
| **Confirmed** | prompt 由 `src/run_simulated_study.py: build_prompt(persona, material)` 构造：system message（"模拟一名普通中文问卷参与者…只输出 JSON"）+ user message（JSON：task/factual_check_rule/persona/material/items/output_schema/strict_rules）。`items_for_prompt` 逐题包含 `item_id`、`scale`、`text`、`valid_range`、`coding` → **构念名（scale）在 prompt 中被暴露**。`configs/prompt.v1.yaml: expose_construct_names: true`、`items_batching: all` 与之一致。 |
| **Reconstructable** | 给定当前代码 + `--seed 20260425` + n=30，可重建 persona/material/prompt 文本；但这是**当前代码重建**，非历史运行的逐字节快照。 |
| **Unknown** | 历史运行的**精确 prompt snapshot 是否被归档**：否（公开仓库无）。历史 **prompt hash**：无。历史 system/user message 是否逐条完整保存：仅存在于未归档的原始响应旁（本地不存在）。**repair prompt**：当前代码**无** repair 流程（`call_deepseek` 只做整轮 retry，非题项级 repair）。题项 batching：当前代码为 `all`（一次请求含全部题项），历史是否相同——`prompt.v1.yaml` 标 `all`，confidence medium（config 与代码一致但无运行时快照佐证）。 |

> **不得**将当前 `configs/prompt.v1.yaml`（`prompt_id: legacy-inline-v1`，仅为引用标记，不含 prompt 正文）默认视为历史运行的精确 Prompt。真实 prompt 正文内联在 `build_prompt()` 中。

## 8. 量表和题项

逐构念取自 `src/scales.py: ITEMS` / `SCALE_ITEMS` / `ITEM_RESPONSE_RANGES`；历史列取自 `outputs/scale_scores.csv` 表头（见 `local_evidence/scale_column_mapping.csv`）。

| construct_id | n_items | response_range | reverse_items | aggregation | historical_column | evidence_type |
|---|---|---|---|---|---|---|
| `agency` | 6 | 1-7 | 无（代码中无反向计分标记） | 题项均值（`analyze_results.py`） | `agency` | direct_file_evidence |
| `experience` | 5 | 1-7 | 无 | 均值 | `experience` | direct_file_evidence |
| `free_will_attribution` | 5 | 1-7 | 无 | 均值 | `free_will_attribution` | direct_file_evidence |
| `autonomy` | 3 | 1-7 | 无 | 均值 | `autonomy` | direct_file_evidence |
| `outcome_accountability` | 2 | 1-7 | 无 | 均值 | `outcome_accountability` | direct_file_evidence |
| `moral_praise_blame` | 2 | 1-7 | 无 | 均值 | `moral_praise_blame` | direct_file_evidence |
| `process_accountability` | 2 | 1-7 | 无 | 均值 | `process_accountability` | direct_file_evidence |
| `perceived_intelligence` | 3 | 1-7 | 无 | 均值 | `perceived_intelligence` | direct_file_evidence |
| `factual_manipulation_check` | 3 | **0-2** | 无 | 事实编码均值/汇总 | `factual_manipulation_check` | direct_file_evidence |
| `subjective_process_completeness` | 3 | 1-7 | 无 | 均值 | `subjective_process_completeness` | direct_file_evidence |

- item_text_source：`src/scales.py: Item.text`（逐题原文）。
- 派生列 `responsibility_total`：出现在 `scale_scores.csv` 但不属 `SCALE_ITEMS`，为责任相关构念（outcome/moral/process accountability）的**派生合成列**（由 `analyze_results.py` 计算），evidence_type：reconstructed_from_code。
- 反向计分：`src/scales.py` 中题项无反向标记；若历史分析有反向处理，需在 `analyze_results.py` 核对（当前未见反向标记）。confidence high（无反向）。

## 9. 响应解析与质量控制

- **历史输出格式**：JSON（`response_format=json_object`；`extract_json()` 兼容 ```code fence``` 包裹）。
- **解析函数**：`src/run_simulated_study.py: extract_json()`、`normalize_record()`。
- **失败处理**：`call_deepseek()` 整轮 `max_retries=3`（sleep 退避）；失败写 `parse_or_call_error` 字段，评分置 None。
- **缺失/范围处理**：`normalize_record()` 对每题 `int()` 转换并校验 `response_min<=val<=response_max`，越界或缺失置 `None`。
- **repair**：当前代码**无题项级 repair**（只有整轮 retry）。
- **首次响应保留**：历史原始响应写 `raw_simulated_responses.jsonl`（append，`existing_ids` 支持续跑），该文件已 gitignore 且本地不存在。
- **历史 JSON/API failure 的证据**：`outputs/scale_scores.csv` 中 360 条各**聚合构念列**无缺失，仅能说明聚合结果存在；**不能**证明 34 个题项逐题都存在（无逐题数据）。因此 item-level missing rate 对 v1 = **unknown**；历史逐条 API failure/retry 计数**无归档**（unknown）。

## 10. 历史分析

来源：`src/analyze_results.py` + 报告脚本；产物见 `outputs/`。

| 分析 | 产物 | 性质 |
|---|---|---|
| 描述性（条件均值） | `outputs/plots/mean_*.png`、`scale_scores.csv` | descriptive |
| 事实操纵检验 | `factual_manipulation_check` 列、`mean_factual_manipulation_check.png` | planned_diagnostic |
| ANOVA | `outputs/anova_summary.csv` | descriptive/planned（historical_label_unclear：未见预注册） |
| 控制回归 | `outputs/controlled_regression_summary.csv`、`process_dummy_coefficients.csv` | planned |
| 计划对比 | `outputs/planned_contrasts.csv` | planned |
| 中介（并行/分组） | `outputs/parallel_mediation_summary.json`、`mediation_summary.json`、`grouped_mediation_summary.csv` | exploratory（探索性路径诊断，非机制证明） |
| 责任维度探索 | `responsibility_total`、`mean_responsibility*.png` | exploratory |
| 稳定性复核 | `outputs/n30_stability_replication_report.md` | planned_diagnostic |
| 稳健性（域/情境/长度） | `domain_robustness_summary.csv`、`scenario_robustness_summary.csv`、`char_len_summary.csv` | exploratory |

> 中介与责任分析为**探索性**，不得升级为确认性；provenance 声明 §6 明确中介是探索性路径诊断。

## 11. Provenance 缺口

逐项核查（见 `local_evidence/provenance_gap_summary.md` 与 `docs/audit/v1_provenance_statement.md §5`）：

| 项 | 状态 |
|---|---|
| exact model server snapshot | unknown / 未归档 |
| exact prompt snapshot | unknown / 未归档（prompt 由代码重建） |
| prompt hash | unknown |
| stimulus hash | unknown（刺激可代码重建，但无归档 hash） |
| request timestamp | unknown |
| provider request ID | unknown |
| token usage | unknown |
| cost | unknown |
| dependency snapshot | 部分（`uv.lock` 为当前锁，非历史运行时锁）|
| exact git commit at run time | 基线 `00c4725`（historical_documentation，作者声明） |
| retry information | unknown |
| raw response public availability | 不在公开仓库（gitignore；本地亦不存在） |

## 12. 现有工程能力边界

**已经实现**（`src/freewill_attribution/`）：
- `schemas.py`：数据 schema（需与 §12 核对是否含 RunManifest 契约字段）。
- `config.py`：config loader。
- `cli.py`：mock-only CLI（`python -m freewill_attribution.cli`）。
- `runner.py`：当前 runner（mock 流程；**非**多模型正式 runner）。
- `paths.py` / `src/path_safety.py`：安全输出路径（禁写 outputs/）。
- 现有 tests：`tests/{unit,integration,characterization,site}`。

**尚未实现**：
- 正式 TaskSpec / BenchmarkSpec 注册表；
- 正式 provider interface（真实多 provider 抽象）；
- 正式 RunManifest 落盘（含 hash/token/cost/artifacts）；
- 新 artifacts 生命周期（`artifacts/runs/**`）；
- Benchmark registry；
- 多模型比较。

> 本轮**只定义契约文档与 YAML 草案**，不实现上述任何运行时能力。

## 13. 阻断问题

无阻断级冲突。已澄清的潜在歧义（均非阻断）：

- config 默认 `n_per_cell=20` vs 历史 `n=30`：已由 DS-12 解释（默认值 vs 运行值）。
- `synthetic=True` 不能区分 API/mock：区分依据为作者声明 + outputs 冻结基线 + mock 只写显式 `--out`（`path_safety` 禁写 outputs/）。
- `mediation_summary.json` 与 `parallel_mediation_summary.json` 并存：前者为早期/分组版本，展示页与主结论采用 parallel 版本；非冲突。

## 14. Source Gate

门禁条件核验：

- 历史正式结果可验证为 360 条 ✓（`scale_scores.csv`）
- 真实条件数量 = 6 ✓
- 真实身份数量 = 2 ✓
- 每单元 = 30 ✓（12 格 min=max=30）
- 量表字段能与代码/文档对应 ✓（`scales.py` ↔ CSV 列）
- 历史数据与 mock 可区分 ✓（作者声明 + 冻结基线 + mock 路径隔离）
- 关键 provenance 缺口已明确写为 unknown ✓
- 不存在被跟踪的真实密钥 ✓（仅环境变量名 `DEEPSEEK_API_KEY`；见 §15 契约验证扫描）
- 协议核心事实无不可裁决冲突 ✓

```
PROTOCOL_SOURCE_GATE=PASS
gate_scope: historical_protocol_reconstruction_only
```

> **gate_scope 说明**：该 PASS 只表示证据足以编写**历史重建协议**，**不代表**：
> - 历史运行完全可复现；
> - API 来源可被仓库内容独立验证（依赖作者事实声明）；
> - 原始逐题响应可审计；
> - 历史 Prompt、seed、模型快照或 retry 可恢复。
>
> **表述纪律修正（RBC-001.1）**：
> 1. 默认 seed `20260425` 只是**代码默认值**（`make_design`/CLI default），**不得**写成已确认的历史运行 seed（无直接运行证据）。
> 2. `deepseek-chat` 只是 **current-code default / reconstruction candidate**，**不得**写成已确认的历史精确模型 ID。
> 3. raw JSONL / wide CSV 不存在：**不阻断** 360/6×2×30 的设计重建；但**阻断**逐题缺失、首答、retry、request ID、精确 Prompt 与原始 API 响应审计。
> 4. `outputs/scale_scores.csv` 聚合构念列无缺失，**不等于**题项无缺失（无逐题数据，无法证明 34 个题项都存在）。
