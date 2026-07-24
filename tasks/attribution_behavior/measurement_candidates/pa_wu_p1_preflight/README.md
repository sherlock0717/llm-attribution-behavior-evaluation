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

## P1 执行状态只在报告中派生

`p1_execution_status` **不持久化**于任何合同或 manifest，只由
`build_preflight_report()` 依据授权状态机派生（authorized 时为 `authorized`，
否则 `blocked`）。授权状态的**唯一来源**是 `authorization_gate.yaml`
（`authorization_status` / `real_model_execution_authorized` / `authorized_by` /
`authorized_at` / `required_gates`）；`route_freeze.yaml` 只冻结研究路线。

## template_reference 如何解析与校验

Prompt 各段可用 `template_reference` 指向本地资产。受控解析器只允许白名单根内的
真实本地文件（`pa_wu_p0/*` 与 `pa_wu_p1_preflight/templates/*`），**不联网**，
且拒绝路径逃逸；冻结时 `sha256` 必须等于该文件规范化内容的哈希。

- **item_block 必须绑定 P0**：只允许 `template_reference` 指向 `pa_wu_p0/`
  下的 item wording 资产，**不允许 inline content 替代**；其 `sha256` 必须等于该
  P0 文件实际内容哈希，**P0 wording 变化后 prompt 门禁必失败**。
- **scenario_block** 若使用 `template_reference` 也必须解析真实本地文件与 hash；
  在正式 scenario 资产尚不存在前保持未冻结与 blocked，不构造虚假正式引用。

## synthetic authorized 已通过完整 build_preflight_report 链

测试 `test_end_to_end_synthetic_authorized` 将整个包复制到临时目录，写入一套完整、
合法、静态的冻结合同（含由真实 P0 文件计算的 item_block hash 与受控本地模板 hash），
将 `authorization_gate` 置为 authorized，并直接调用 `build_preflight_report()`，
断言 `preflight_status == authorized`、`p1_execution_status == authorized`、
`blocking_gates == []`。此测试只验证状态机，**不调用模型、不执行 P1**。

## 安全自扫描

`validate_preflight.py` 通过 AST 扫描自身与包内 `.py`：拒绝 banned 模块的
`import`/`from`、`importlib.import_module`/`__import__` 动态导入、对
requests/httpx/urllib/socket 的调用、subprocess 调用网络 CLI、以及对 R2/R3 路径的
`open`/`Path`/import 操作。secret 扫描在去除行尾注释后判定，**不能通过追加注释标记绕过**。

## 当前真实合同状态

当前磁盘上的真实合同仍为 **blocked**（模型未选定、prompt/sampling/budget/retry/logging/
stop 未冻结、privacy review 处于 pending）。

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
