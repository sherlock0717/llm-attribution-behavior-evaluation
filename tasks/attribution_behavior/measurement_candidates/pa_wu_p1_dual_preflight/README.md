# PA-Wu R1 P1 双模型执行前置门禁包 (pa_wu_p1_dual_preflight)

本包是原单模型 preflight（`pa_wu_p1_preflight/`）的**后继结构**，实施 PA-Wu 测量候选
路线 **R1（English source-faithful, machine-only）** 从单模型迁移到**双模型
（co-primary）** 的合同与 validator **结构**。

**本轮只实施结构迁移，不填充最终采样、预算或授权决定。迁移完成后的真实包必须继续
保持 `blocked`。** 本包不调用真实模型、不请求外部 API、不写 API key、不产生模型输出、
不执行 P1。

## 与原单模型 preflight 的关系

- 原包 `pa_wu_p1_preflight/` **不删除、不废弃、不修改**，作为已合并的历史基线保留；
- 本包为其后继结构，采用**复数**模型合同表达两个 co-primary 模型；
- 迁移来源 hash（本轮实际输出）记录在 `preflight_manifest.yaml.source_packages`：
  - single_model_preflight：contract_hash `2b9548cb6bac6fd3`，package_hash `d73b5bf6ecee5830`；
  - dual_model_decision：package_hash `97a9a625bba76636`。

## 双模型选择

- 选择来源为已合并的决策包 `pa_wu_r1_p1_decision_fill/dual_model_selection/`；
- selected_models：**deepseek-v4-pro、gpt-5.6-terra**，均为 `co_primary`；
- **模型选择完成不等于模型合同已冻结**：本轮每模型 `freeze_status: unresolved`；
- **不存在** primary / secondary / fallback 关系。

## 核心不变量

- `all_or_nothing_execution: true`：任一模型子门禁不满足时，双模型整体保持 `blocked`；
- 单一共享 Prompt（六段，item_block 绑定完整固定顺序 P0 束，identity 恒 machine），
  provider 差异只能进入 `provider_adapter_contract.yaml`，不改变研究材料语义；
- 每模型独立：模型合同、采样、预算、请求数、retry 分类、合同 hash；
- aggregate 请求数 = 两模型之和；aggregate 预算 = 两模型之和；
- `authorization` 只有单一人工来源；validator 绝不自动授权、绝不改写合同；
- `p1_execution_status` **不持久化**，只由 `build_report()` 派生。

## 迁移状态

`migration_status: schema_implemented_not_frozen`（结构已实现，尚未冻结）。

## 当前状态（本轮结束时）

`preflight_status: blocked`、`authorization_status: blocked`、
`real_model_execution_authorized: false`、`p1_execution_status: blocked`；
所有模型合同/采样/预算/adapter/prompt/retry/logging/stop 未冻结，
privacy 与 environment review 未完成。

## 文件

| 文件 | 作用 |
|---|---|
| `preflight_manifest.yaml` | 包清单、迁移来源 hash、受管文件与合同列表 |
| `route_freeze.yaml` | 冻结 R1 路线边界，绑定 mock hash |
| `model_selection_decision.yaml` | 双模型选择（复数 decisions，每模型独立 freeze_status） |
| `provider_adapter_contract.yaml` | provider 适配层（只转换结构，语义不变量） |
| `prompt_freeze_contract.yaml` | 单一共享 Prompt 分段冻结 |
| `sampling_and_repeat_contract.yaml` | 共享设计 + 每模型采样参数 + aggregate |
| `budget_and_rate_limit_contract.yaml` | 每模型预算 + aggregate 汇总 |
| `retry_and_recovery_contract.yaml` | 共享退避 + 每模型错误分类 |
| `provenance_and_logging_contract.yaml` | 日志字段 + 双模型 provenance 字段 |
| `stop_conditions.yaml` | 原停止条件 + 双模型专属停止条件 |
| `authorization_gate.yaml` | 双模型语义授权门禁（单一人工来源，初始 blocked） |
| `environment_acceptance.yaml` | 新包环境验收（继承基线仅参考，初始 false） |
| `validate_dual_preflight.py` | 纯本地静态 validator（无网络/无 SDK/无模型执行） |

## 研究结论

**C — 仍需补证。** 结构迁移完成不代表可以执行真实 P1；P1 执行状态为 `blocked`。
