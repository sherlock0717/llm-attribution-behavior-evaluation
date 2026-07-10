# v1 Historical DeepSeek API Baseline · Provenance Statement

> 本文件记录 v1 基线的来源事实、可验证证据与历史元数据缺失边界。遵循分层原则：**作者事实声明 / 机器可验证证据 / 历史缺失元数据** 三者严格区分，历史缺失元数据不得通过推测补写。

---

## 1. 基线身份

- v1 对应 Git commit：`00c4725dc7b891de3a7bfa11b4856be177d9d2a6`（message：`Initial public portfolio version`）。
- 当前公开分析基于 **360 条模型生成记录**。
- 这些记录由**项目作者确认来自真实 DeepSeek API 调用**。
- 它们**不是** `mock_response()`（`src/run_simulated_study.py`）生成的数据。
- 它们保留为 **DeepSeek 历史真实 API 基线（historical DeepSeek API baseline）**。

---

## 2. 记录性质

严格区分：

```text
360 条模型生成记录
≠
360 名人类被试
≠
360 个独立模型系统
```

说明：

- 这些记录用于**大模型模拟研究**（可复现的大模型模拟研究原型）。
- 它们来自**单一主要模型配置下的重复生成**（同一基础模型、同一 prompt 模板；persona 与 `participant_id` 为设计内标签/记录编号，不代表独立信息源）。
- 记录层面可用于**描述性、探索性和当前配置下的稳定性分析**。
- **不应**直接外推为人类心理规律，也不应外推为所有模型的一般规律。

---

## 3. 已确认信息（仅事实）

当前确实已知：

- 使用 **DeepSeek API**（作者确认为真实 API 调用）。
- 总记录数为 **360**（6 process_condition × 2 identity_label × 30 per-cell）。
- 当前基线 commit：`00c4725dc7b891de3a7bfa11b4856be177d9d2a6`。
- 当前公开输出文件位于 `outputs/**`（CSV / JSON / Markdown / 图表）。
- 当前项目代码中的实验设计与分析流程（`src/stimuli.py`、`src/scales.py`、`src/run_simulated_study.py`、`src/analyze_results.py` 等）。
- 作者对上述来源事实的确认。

> 不添加没有证据的精确日期、服务端模型快照或费用。

---

## 4. 当前公开仓库可验证的信息

第三方基于**当前公开仓库**可以验证：

- 基线 Git commit（`00c4725…`）。
- 刺激材料与题项代码（`src/stimuli.py`、`src/scales.py`）。
- 分析代码（`src/analyze_results.py` 及报告生成脚本）。
- 当前公开的 CSV、JSON、Markdown 与图表（`outputs/**`）。
- 本次生成的 SHA-256 清单（`docs/audit/baseline_hashes.txt`）。该清单直接基于指定 Git commit 中的原始 blob bytes 计算，不受 Windows/Linux 换行转换或本地 checkout 配置影响。
- 当前仓库中可运行的 mock 与分析流程（用于流程/可复现性检查，非重放历史 API 响应）。

> 使用“当前公开仓库”作为限定；本文件**不**声称本地或其他位置一定不存在原始文件。

---

## 5. 历史运行中缺失或不完整的信息

以下信息当前未被完整归档或未包含在公开仓库中：

- 完整历史 run manifest；
- DeepSeek 服务端精确模型快照；
- 完整调用时间戳；
- token 使用量；
- 费用；
- prompt hash；
- dependency lock hash；
- 完整环境快照；
- 完整调用日志；
- 当前公开仓库未包含的原始响应（`raw_simulated_responses.jsonl`）与宽表（`simulated_responses_wide.csv`，二者被 `.gitignore` 排除）。

统一口径：

```text
这些信息当前未被完整归档或未包含在公开仓库中。
```

**不得**写成“这些信息从未存在”。

---

## 6. 证据边界

- v1 是**历史真实 API 基线**。
- v1 **不是**能够完整重复生成同一模型响应的封闭式复现实验包。
- 后续版本**不会伪造或补写**不存在的历史元数据。
- v1 的统计结果需结合以下限制解释：**单模型、单 prompt、提示暴露（构念名/题项/判断规则可见）、记录独立性有限**。
- 中介分析属于**探索性路径诊断**，**不是**心理机制证明；不构成关于 AI 自主性或决策过程因果作用的任何断言。

---

## 7. 后续改进（新运行的可追溯要求）

后续新运行（Phase 3A 起）将记录：

- run ID；
- Git SHA；
- provider；
- 模型名称与可得版本；
- prompt 版本与 hash；
- 刺激材料版本与 hash；
- 配置（resolved config）；
- 依赖（dependency lock hash）；
- 开始与结束时间；
- token / cost（provider 可返回时）；
- 重试与错误分类；
- 原始响应；
- 标准化响应；
- checksum。

> 这些记录仅适用于**新运行**；不会回溯性地补写 v1 缺失的历史元数据。

---

## 8. 作者声明与机器证据分层

```text
作者事实声明：
v1 的 360 条记录来自真实 DeepSeek API。

机器可验证证据：
当前 commit、公开输出、代码与 SHA-256 清单（docs/audit/baseline_hashes.txt）。

历史缺失元数据：
不得通过推测补写。
```

---

_关联：`docs/audit/current_state_v0.1.md`（H-00）、`docs/planning/RISK_REGISTER.md`（R-15）、`docs/planning/DECISION_LOG.md`（DEC-008）。_
