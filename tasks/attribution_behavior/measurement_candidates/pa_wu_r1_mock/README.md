# PA—Wu R1 英文机器条件 Mock 执行包（research only, mock-only）

本目录是 **R1（English source-faithful, machine-only）** 路线的 **Mock 执行包**。
它只在已合并的 P0（`../pa_wu_p0/`）契约之上，用**静态预制 fixture** 演示"工程执行包如何组织、如何被校验"，
**不调用真实模型、不进行网络请求、不执行真实 P1、不产生任何研究结论**。

所有评分与响应校验**复用 P0 引擎**（`freewill_attribution.measurement.pa_wu_p0`），
本包**不存在第二套评分逻辑**。

## 固定的 R1 路线边界

| 字段 | 值 |
|--|--|
| `route_id` | R1 |
| `language` | en |
| `target_identity` | machine |
| `human_parallel_version` | false |
| `translation_used` | false |
| `is_construct_adaptation` | false |
| `real_model_execution` | false |
| `package_status` | mock_only |

本轮**不引入**：R2 中文路线、R3 AI/human 平行改写、D/U 效应检验、身份效应检验、
测量不变性检验、正式效度结论。

## 文件

| 文件 | 作用 |
|--|--|
| `mock_run_contract.yaml` | 固定 R1 路线边界与允许的阳性对照级别 |
| `mock_input_cases.jsonl` | Mock 输入合同（7 个 case，含 3 个坏例） |
| `mock_model_outputs.jsonl` | **静态预制**模型输出 fixture（11 条，覆盖 10 类输出问题），**非模型生成** |
| `expected_scored_outputs.jsonl` | 每条 output 的预期 outcome / failure_code / 分量表分 |
| `mock_manifest.yaml` | 包清单、case 数、坏例类型、确定性 hash 参考 |
| `run_mock.py` | 确定性 Mock 运行器（复用 P0 引擎；无网络/无模型） |
| `validate_mock_package.py` | 包结构校验器 |

## Mock 运行输出（`run_mock.build_run_report`）

- `package_manifest`
- `case_validation_results`
- `item_level_scores`
- `subscale_level_scores`（PA13/PA8/PA5 与 Wu IN4/GO4/MSI6/IC5，**无任何总分**）
- `expected_vs_actual_comparison`
- `failure_codes`
- `deterministic_run_hash`

## 坏例与失败码

输入坏例：缺失必填字段、请求非法总分（WU19_TOTAL）、错误身份+错误语言（human/zh）。
输出问题（11 条 fixture / 10 类）：完整合法、缺少条目、量尺越界（IN 与 MSI 各一）、非法 item ID、
生成禁止总分、错误语言、错误身份、非法自由文本（非数值）、重复条目、不可解析 JSON。

失败码（闭集）：`missing_items` / `out_of_range` / `unknown_item` / `duplicate_item` /
`non_numeric_rating` / `forbidden_total` / `wrong_language` / `wrong_identity` /
`unparseable_json` / `missing_required_field`。

## 阳性对照边界（严格）

`positive_control_level` 仅允许三种枚举：

- `body_fragment` — Wu 正文中**已公开出现的逐字短片段**（如低独立性片段
  `"I instruct you to generate the message now"`，CC BY 4.0，来源 OUP minimal HTML 正文）；
- `source_adapted_prototype` — 依据来源描述逻辑构造的**原型**，**必须显式标记为 prototype**
  （`is_prototype: true`、`is_full_script: false`、`status: prototype_unvalidated`）；
- `none`。

**禁止**使用 `formal_calibrated_positive_control`。

本包**不声称**：已取得完整 Supplementary Table 9、已完成正式阳性对照校准、
prototype 等同来源完整刺激。

## 边界声明（不越界）

- 不运行真实模型、不执行 P1、不修改默认 benchmark、不修改 P0/P1-prep 来源条目；
- 不创建中文正式量表、不进入 D/U 或 AI/human 效应分析；
- 不生成 Wu19 / machine-agency / PA+Wu 总分；
- Mock 输出仅为**工程验证信号**，绝非研究发现。

## 研究结论

**C — 仍需补证。** Mock 执行包的存在只证明"工程契约可承载合规评分与坏例拒绝"，
**不代表可运行真实 P1**，也不构成任何效度、身份或翻译等价性结论。
