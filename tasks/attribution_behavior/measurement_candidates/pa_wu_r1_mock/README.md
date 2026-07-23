# PA—Wu R1 英文机器条件 Mock 执行包（research only, mock-only）

本目录是 **R1（English source-faithful, machine-only）** 路线的 **Mock 执行包**。
它在已合并的 P0（`../pa_wu_p0/`）契约之上，用**静态预制 fixture** 演示"工程执行包如何组织、
输入与输出分别如何校验"，**不调用真实模型、不进行网络请求、不执行真实 P1、不产生任何研究结论**。

所有评分与响应校验**复用 P0 引擎**（`freewill_attribution.measurement.pa_wu_p0`），
本包**不存在第二套评分逻辑**；item-wording 的 `administration_hash` **由 P0 引擎计算**，未自行实现。

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
| `mock_input_cases.jsonl` | **输入合同**（8 个 case，4 合法 + 4 坏例） |
| `mock_model_outputs.jsonl` | **静态预制**模型输出 fixture（14 条），**不携带答案** |
| `expected_scored_outputs.jsonl` | **唯一静态 oracle**：outcome / failure_code / 分量表分 / 禁止总分标记 |
| `mock_manifest.yaml` | 包清单（实际被 validator 加载并逐项核对，含确定性 hash） |
| `run_mock.py` | 确定性 Mock 运行器（复用 P0 引擎；无网络/无模型） |
| `validate_mock_package.py` | 包结构 + manifest + oracle 校验器 |

## 输入 case 如何验证

`run_mock.validate_input_case(contract, case)` 让每个输入 case 进入**真实校验链**，产出
`case_id / accepted / failure_code(s) / validation_errors / form_id / item_order_id /
administration_hash / mock_only`。合法 case 必须满足：必填字段完整、`source_route==R1`、
`language==en`、`target_identity==machine`、`mock_only==true`、`item_set_version==p0.SCORING_VERSION`、
`form_id/order_id` 可由 P0 解析、`selected_item_ids` 与 `p0.build_form_item_ids(...)` 顺序完全一致、
`requested_scores` 不含禁止总分、positive-control 枚举与 provenance 合法。坏例经**真实拒绝**得到失败码，
不依赖 `_bad_case` 标签跳过。

**8 个输入 case**：2 中性（`r1_neutral_01` 用 combined、`r1_neutral_02` 用 wu19_only）+
2 Wu 线索（`body_fragment` 逐字片段 + `source_adapted_prototype` 原型）+ 4 原子坏例
（缺失字段、请求禁止总分、错误语言 zh、错误身份 human）。

## 输出 fixture 如何验证

每个输出 fixture **引用一个存在且合法的输入 case**；`response_language`/`response_identity` 为**必填**，
缺失返回 `missing_required_field`，且必须分别为 `en`/`machine`。输出层坏例（`wrong_language`/
`wrong_identity`/`forbidden_total` 等）都构建在**合法输入 case** 之上、仅在输出本身注入故障，
从而拒绝层次明确。硬性量尺/ID/重复/缺失规则委托 P0 `validate_response`；分数由 P0 `derive_scores` 派生。

**14 条输出 fixture**：完整合法 combined（覆盖 PA13/PA8/PA5 + Wu 四分量表，32 项）、完整合法 wu19_only、
缺条目、量尺越界（IN 与 MSI 各一）、非法 item ID、生成禁止总分、错误语言、错误身份、
缺失 response_language、缺失 response_identity、非法自由文本（非数值）、重复条目、不可解析 JSON。

## PA combined 合法 fixture

`out_complete_valid_combined`（引用 `r1_neutral_01`，`pa13_wu19_combined` / `pa_first`，32 项）
提供固定评分（PA 各项=3、Wu IN/GO/IC 各项=4、MSI 各项=3），预期：
`PA13=3.0, PA8=3.0, PA5=3.0, IN4=4.0, GO4=4.0, MSI6=3.0, IC5=4.0`。测试按 P0 成员关系实际派生，
不只校验成员数量。

## 唯一 oracle 与 administration_hash

- `expected_scored_outputs.jsonl` 是**唯一静态期望值来源**（`run_mock.load_expected_scored_outputs()`），
  运行器按 `output_id` 与实际结果**一一比对**（无缺失/无多余、outcome/failure_code/分量表分/禁止总分标记精确一致）。
  `mock_model_outputs.jsonl` **已移除** `expected_outcome` 与 `failure_code_expected`，避免输入 fixture 自带答案；
  测试**不再**硬编码第二套 failure-code 映射。
- `administration_hash` 通过 `p0.administration_hash(...)` 计算（form/order + scenario_id +
  target_identity→identity + 固定 condition_id + 固定 choice_direction + repeat_index=0），
  测试证明其确定性复现、且对 item wording/顺序/量尺变化敏感、包内无第二套 wording hash。

## 失败码（闭集）

`missing_items` / `out_of_range` / `unknown_item` / `duplicate_item` / `non_numeric_rating` /
`forbidden_total` / `wrong_language` / `wrong_identity` / `unparseable_json` / `missing_required_field` /
`wrong_route` / `item_set_version_mismatch` / `selected_items_mismatch` / `illegal_positive_control` /
`unknown_output_case` / `p0_contract_error`（未识别的 P0 错误**不再**默认误分类为 `unknown_item`）。

## 阳性对照边界（严格）

`positive_control_level` 仅允许 `body_fragment` / `source_adapted_prototype` / `none`；
`source_adapted_prototype` **必须**显式 `is_prototype: true`、`is_full_script: false`、
`status: prototype_unvalidated`。**禁止** `formal_calibrated_positive_control`。
不声称已取得完整 Supplementary Table 9、已完成正式阳性对照校准、prototype 等同来源完整刺激。

## 边界声明与研究结论

- 不运行真实模型、不执行 P1、不修改默认 benchmark、不修改 P0/P1-prep 来源条目；
- 不创建中文正式量表、不进入 D/U 或 AI/human 效应分析；不生成 Wu19 / machine-agency / PA+Wu 总分；
- Mock 输出仅为**工程验证信号**，绝非研究发现。

**研究结论：C — 仍需补证。** Mock 执行包只证明"工程契约可承载合规评分与坏例拒绝"，
**不代表可运行真实 P1**，也不构成任何效度、身份或翻译等价性结论。
