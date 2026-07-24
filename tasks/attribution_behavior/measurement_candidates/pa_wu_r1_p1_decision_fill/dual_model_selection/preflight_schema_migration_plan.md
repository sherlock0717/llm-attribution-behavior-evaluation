# Preflight 合同双模型迁移计划（仅提案，不执行）

本文件仅**提出**将现有**单模型** preflight 合同（`pa_wu_p1_preflight/`）迁移为
**双模型（co-primary）** 结构的方案，**不执行任何迁移**，不修改现有 preflight 资产、
不修改授权状态。

## 一、现有单模型结构的问题

1. `model_selection_decision.yaml` 使用**单数** `selected_model` 与单个 `decision`；
   无法表达两个 co-primary 模型。
2. validator 的 `_model_frozen` / `model_frozen` 门禁只接受**一个** `decision`，
   无法对两个模型分别判定"已冻结"。
3. `sampling_and_repeat_contract.yaml`、`budget_and_rate_limit_contract.yaml`、
   `provenance_and_logging_contract.yaml` **没有 `model_id` 维度**，无法按模型
   分别记录采样映射、预算与日志。
4. 当前 `contract_hash` / `package_hash` **未按模型分别计算**，无法体现某一模型
   合同变化。
5. 当前 `authorization_gate.yaml` 的 `required_gates` **没有双模型完整性要求**
   （未要求"两个模型均冻结"才放行）。

## 二、迁移方案（proposed）

1. **字段复数化**：`selected_model` → `selected_models`（列表）；对应 `decision`
   → `decisions`（按 `model_id` 键控的映射或有序列表）。
2. **与决策包精确对齐**：`selected_models` 必须精确匹配本双模型决策包的两个模型
   （`deepseek-v4-pro`、`gpt-5.6-terra`），数量、provider、role 全一致，
   role 均为 `co_primary`。
3. **每模型独立子合同**：每个模型拥有独立的
   - model decision（provider / model_id / endpoint 等冻结字段）；
   - exact snapshot 字段（无确认快照不得冻结）；
   - provider 参数映射（引用 `parameter_compatibility.yaml`）；
   - pricing（币种、快照日期、单价）；
   - rate limit（RPM / TPM / 并发）；
   - planned request count；
   - budget estimate。
4. **Prompt 语义统一 + provider 适配层**：Prompt 分段语义保持**单一冻结来源**，
   仅允许一层 provider 适配层做请求/响应结构转换。
5. **适配层不变量**：provider 适配层**不得改变**
   - 场景语义（scenario semantics）；
   - 身份语义（identity semantics）；
   - item wording（PA-Wu 题项措辞，仍绑定 P0 来源束）；
   - 响应字段含义（response field meaning）。
6. **每模型独立 hash 与计量**：每个模型独立计算
   - prompt/request hash；
   - model contract hash；
   - planned request count；
   - maximum cost。
7. **总预算**：双模型总预算 = 两个模型预算之和；硬上限对总额与单模型分别约束。
8. **整体门禁**：**任一模型**的任一门禁失败 → 双模型 P1 **整体保持 blocked**。
9. **单一授权来源**：authorization 仍只有**单一人工授权来源**
   （`authorization_gate.yaml`），validator 绝不自动授权。
10. **禁止 fallback**：**不得**把一个模型设为另一个模型的 fallback / 替代；
    两者恒为 co-primary。

## 三、迁移不改变的既有不变量

- 研究路线仍为 R1（en / machine / mock_only 边界不变）；
- P0 来源束绑定不变（item_block 仍绑定完整固定顺序 P0 束）；
- `p1_execution_status` 仍只在报告中派生，不持久化；
- 授权状态机语义不变（blocked/authorized 二态、全门禁 + 人工授权）；
- 安全自扫描（AST / secret / R2·R3 路径）不变。

## 四、迁移状态

migration_status: proposed_not_implemented
