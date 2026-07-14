# Free-Will Attribution V1 Historical Protocol Reconstruction

```
protocol_id: freewill-attribution-v1-historical
protocol_version: "1.0"
status: historical_reconstructed
executable: false
evidence_basis: docs/audit/research_protocol_source_map.md (PROTOCOL_SOURCE_GATE=PASS)
gate_scope: historical_protocol_reconstruction_only
```

> `gate_scope: historical_protocol_reconstruction_only` —— PASS 仅表示证据足以编写历史重建协议，**不代表**历史运行完全可复现、API 来源可被仓库独立验证、原始逐题响应可审计、或历史 Prompt/seed/模型快照/retry 可恢复。

> 这是基于现有**代码、产物和文档**进行的历史协议重建，**不是**原始运行环境的完整复刻。
> 历史缺失元数据（服务端模型快照、prompt hash、时间戳、token、cost 等）不被补写，一律标为 unknown。

## 1. 协议状态

- `protocol_id`: `freewill-attribution-v1-historical`
- `protocol_version`: `"1.0"`
- `status`: `historical_reconstructed`
- `executable`: `false`（当前公开仓库不含历史精确 prompt/环境快照，无法逐字节重放历史模型响应；`executable` 仅在文件证据证明可完全复刻时才可设 true）
- `evidence basis`: `src/stimuli.py`、`src/scales.py`、`src/run_simulated_study.py`、`src/analyze_results.py`、`configs/*.yaml`、`outputs/**`、`docs/audit/v1_provenance_statement.md`；证据分级见 source map。

## 2. 研究目标

描述在给定材料下，**单一大语言模型作为观察者**对决策者的归因模式：当同一决定的"决策过程"叙述从低结构变为高结构、且决策者身份标注为 AI 或人类时，模型给出的行动者感（agency）、自由意志归因（free_will_attribution）及相关维度评分如何变化。

本协议测量的是**模型输出中的归因模式**，不涉及：
- 模型是否真的拥有自由意志；
- 人类会如何判断（非人类被试）；
- 正式心理测量结论或所有 LLM 的普遍规律。

## 3. 研究对象与解释边界

- 测量对象：模型输出的归因评分（模拟被试）。
- 单一模型、单一 prompt 模板、提示暴露（构念名/题项/判断规则对模型可见）、记录独立性有限。
- 不外推到人类心理机制，不外推到其他模型。

## 4. 设计

来自 source map §3–§5（`src/stimuli.py`、`configs/study.default.yaml`、`outputs/scale_scores.csv`）：

- **过程条件（6，真实 key）**：`direct_choice`、`direct_choice_long`、`alternatives`、`reasons_concise`、`reasons`、`reflection_feedback`。
- **身份标签（2，真实 value）**：`AI 决策者`、`人类决策者`。
- **每格**：30；**总计**：360（6 × 2 × 30，由 `scale_scores.csv` 记录级计数证实）。
- **诊断条件**：`direct_choice_long`（length-control，只加长度不加结构，structure_level=0）；`reasons_concise`（结构诊断，给结构不加长度，structure_level=2）。
- **结构等级**（`PROCESS_ORDINAL`）：direct_choice=0、direct_choice_long=0、alternatives=1、reasons_concise=2、reasons=2、reflection_feedback=3。
- **情境**：8 个 `Scenario`，按 `n % 8` 轮转；每格内 scenario、persona 由 `--seed 20260425` 确定。

> 注：`configs/study.default.yaml: n_per_cell` 当前默认为 20；历史运行为 n=30（由 360 条反推）。默认值 ≠ 历史运行值，非冲突。

## 5. 样本与运行单元

- 每格 30，总计 360 条模型生成记录。
- 每条记录 = 模型对一段决策材料的一次观察者评分（`participant_id` 为设计内编号，非独立信息源）。
- 历史 provider：DeepSeek API（`docs/audit/v1_provenance_statement.md`，作者事实声明；API 来源无法由仓库内容独立验证）。
- 模型 ID：`deepseek-chat` 仅为 **current-code default / reconstruction candidate**（`run_simulated_study.py` 环境变量 `DEEPSEEK_MODEL` 默认值），**不得**写成已确认的历史精确模型 ID。
- seed：`20260425` 仅为**代码默认值**，**不得**写成已确认的历史运行 seed（无直接运行证据）。
- 服务端精确模型快照、时间戳、token、cost、retry：**unknown**（未归档）。

## 6. 刺激材料

- 由 `src/stimuli.py: build_decision_text()` 程序化生成，无外部数据文件。
- 固定：`Scenario.context`、`Scenario.fixed_choice`；条件变化：`【决策过程】`段；身份变化：`actor`。
- 版本：`stimuli_version: v1`。历史逐条刺激文本随原始响应保存（gitignore，本地不存在）；刺激可由代码 + seed 确定性重建（reconstructed_from_code），但无归档 stimulus hash（unknown）。

## 7. Prompt 重建

- **Confirmed**：prompt 由 `run_simulated_study.py: build_prompt()` 构造；system=模拟中文问卷参与者、只输出 JSON；user=JSON（task/factual_check_rule/persona/material/items/output_schema/strict_rules）；逐题暴露 `item_id/scale/text/valid_range/coding` → 构念名暴露（`configs/prompt.v1.yaml: expose_construct_names: true`，`items_batching: all`）。
- **Reconstructed**：给定当前代码 + seed，可重建 prompt 文本（当前代码重建，非历史逐字节快照）。
- **Unknown**：历史精确 prompt snapshot / prompt hash / 逐条 system-user 完整存档 / repair prompt（当前代码无题项级 repair，仅整轮 retry）。

## 8. 响应格式与解析

- 输出 JSON（`response_format=json_object`）；`extract_json()` 兼容 code fence。
- `normalize_record()` 逐题 `int()` + 范围校验（越界/缺失置 None）；失败记 `parse_or_call_error`。
- 无题项级 repair；整轮 `max_retries=3`。
- 首次原始响应写 `raw_simulated_responses.jsonl`（gitignore，本地不存在）。

## 9. 量表与计分

10 个构念、34 个题项（`src/scales.py`）：agency(6)、experience(5)、free_will_attribution(5)、autonomy(3)、outcome_accountability(2)、moral_praise_blame(2)、process_accountability(2)、perceived_intelligence(3)、factual_manipulation_check(3，范围 0-2)、subjective_process_completeness(3)。其余为 1-7 同意量表。聚合为题项均值（`analyze_results.py`），派生 `responsibility_total` 合成列。无反向计分标记。

## 10. 数据质量

- 360 条标准化记录各**聚合构念列**无缺失；但**无逐题数据**，聚合列无缺失**不能证明** 34 个题项都存在，故 item-level missing rate 对 v1 = **unknown**。
- 历史逐条 API failure / retry / parse failure 计数：**unknown**（未归档）。
- 数据为模型模拟（`synthetic=True`），非人类被试。

## 11. 分析计划与历史分析性质

（详见 source map §10）

- descriptive：条件均值、图表。
- planned：控制回归、计划对比、事实操纵检验、n30 稳定性复核。
- exploratory：并行/分组中介（探索性路径诊断，非机制证明）、责任维度、稳健性（域/情境/长度）。
- historical_label_unclear：ANOVA（未见预注册标记）。

**不重新生成结果**；本协议不重算任何统计量。

## 12. 历史结果资产

仅列文件与作用（不复制结果数字）：

- `outputs/scale_scores.csv`：360×22 记录级量表分（记录数/单元格来源）。
- `outputs/{controlled_regression_summary,planned_contrasts,process_dummy_coefficients}.csv`：控制回归与计划对比。
- `outputs/{parallel_mediation_summary,mediation_summary}.json`、`grouped_mediation_summary.csv`：探索性中介。
- `outputs/{reliability_summary,anova_summary,domain_robustness_summary,scenario_robustness_summary,char_len_summary}.csv`：信度/方差/稳健性。
- `outputs/*.md`：pilot / n30 稳定性 / 测量修订 / 方法修订报告。
- `outputs/plots/*.png`：条件均值图（含 agency / free_will_attribution / subjective_process_completeness 等）。

## 13. Provenance

见 source map §11 与 `docs/audit/v1_provenance_statement.md`。可验证：360 条、baseline `00c4725`、代码与产物、SHA 清单。作者事实声明：360 条来自真实 DeepSeek API。历史缺失元数据：一律 unknown，不补写。

## 14. 可复现范围

- **currently verifiable**：从 `outputs/` 重新派生汇总/展示数据并校验一致；校验基线内容哈希；本地 mock 流程跑通（工程流程，非历史响应）。
- **partially reconstructable**：刺激/persona/prompt 文本可由代码 + seed 重建（当前代码，非历史快照）。
- **not recoverable**：逐字节重放历史 DeepSeek 响应；服务端模型版本、token、cost、时间戳、prompt/依赖 hash。

## 15. 与 Benchmark TaskSpec 的映射

本历史协议映射到 `docs/benchmark/BENCHMARK_SPEC.md` 的 TaskSpec：
- `task_id`: `freewill-attribution-v1-historical`（`configs/tasks/freewill_attribution.v1.yaml`）。
- `status`: `historical_reconstructed`，`executable: false`。
- `prompt_provenance.exact_snapshot_available: false`、`exact_hash_available: false`、`reconstruction_status: partial`。

> 映射仅用于把历史设计接入 Benchmark 对象模型；**不声称**该任务当前可执行。可执行目标见 v2 协议。
