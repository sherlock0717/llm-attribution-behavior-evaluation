# PA-Wu R1 P1 执行前置决策与授权门禁包 (pa_wu_p1_preflight)

本包建立 PA-Wu 测量候选路线 **R1（English source-faithful, machine-only）** 在进入
真实 P1 执行**之前**必须冻结的工程合同、决策记录与授权门禁。

**本包不调用真实模型、不请求任何外部 API、不写入 API key、不产生任何模型输出、
不执行 P1。** 它只是一组静态合同 + 一个纯本地静态校验器（`validate_preflight.py`）。

## 边界（严格）

- 不将 R1 Mock 结果解释为模型表现；
- 不将研究结论从 `C — 仍需补证` 改为可执行或已验证；
- 不引入 R2 中文路线、R3 AI/human 平行路线、human 身份版本、中文正式量表；
- 不产生 D/U 效应、身份效应或测量不变性结论。

## 核心不变量

在**所有** `required_gates` 为 `true` 且 `real_model_execution_authorized: true`
之前，`authorization_gate.yaml` 的 `authorization_status` 恒为 `blocked`，
`preflight_status` 恒为 `blocked`。`validate_preflight.py` **绝不**自动将授权改为
`true`——授权只能由人工在合同文件中显式写入并经全部门禁核验。

## 文件

| 文件 | 作用 |
|---|---|
| `preflight_manifest.yaml` | 包清单：文件列表、路线、复用来源、contract hash 引用 |
| `route_freeze.yaml` | 冻结 R1 路线边界（en / machine / mock_only），绑定 mock hash |
| `model_selection_decision.yaml` | 模型选择决策（初始 `unresolved`，不虚构已选模型） |
| `prompt_freeze_contract.yaml` | Prompt 分段冻结（system/task/scenario/identity/schema/item） |
| `sampling_and_repeat_contract.yaml` | 采样与重复参数（temperature/seed/repeats 等） |
| `budget_and_rate_limit_contract.yaml` | 预算与限流（初始 `budget_approved: false`） |
| `retry_and_recovery_contract.yaml` | 重试与恢复（区分可重试 / 不可自动重试） |
| `provenance_and_logging_contract.yaml` | 来源与日志字段要求（不记录 secret） |
| `stop_conditions.yaml` | 立即停止 + 阈值停止条件（阈值可 `unresolved`） |
| `authorization_gate.yaml` | 授权门禁（本阶段核心，初始 `blocked`） |
| `environment_acceptance.yaml` | 环境验收事实记录（Linux CI + Windows 例外） |
| `validate_preflight.py` | 纯本地静态校验器（无网络 / 无 SDK / 无模型执行） |

## 环境验收（如实记录，见 `environment_acceptance.yaml`）

- GitHub Actions CI #71：**Linux 环境 success**；
- Windows 本地：R1 目标测试通过、ruff 通过、compileall 通过；
- Windows 本地全量 pytest 存在 **5 个 bash wrapper 集成测试失败**
  （`tests/integration/test_cross_platform_scripts.py`）；
- 这 5 个失败**不在 PR #10 diff 范围内**，**不是** R1 Mock 回归，也**未被修复**；
- **不得**将此描述为"Windows 全量测试通过"。

## 研究结论

**C — 仍需补证。** Mock 执行包可用不代表可以执行真实 P1；P1 执行状态为 `blocked`。
