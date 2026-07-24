# PA-Wu R1 P1 双模型选择决策包 (dual_model_selection)

本包固化用户已作出的**双模型选择**，并整理两个模型的官方公开证据、参数可比性边界，
以及现有单模型 preflight 合同迁移为双模型合同的**提案**。本包**不比较两模型的回答
效果**，**不对两模型进行优劣排序**。

## 用户已作出的选择

用户已选择以下两个模型，采用 **co-primary（双主模型）** 设计，二者地位对等：

1. **DeepSeek-V4-Pro**（provider: deepseek）— role: co_primary
2. **GPT-5.6 Terra**（provider: openai）— role: co_primary

本阶段**不再**进行候选模型筛选或四模型排名。用户的选择**不会**因为缺少实际效果
测试而被撤销。

## 本包记录的是什么

- 用户的模型**选择已经完成**（human_selected）；
- 官方规格证据已**按字段整理**（每个字段挂 `field_evidence`，documented 状态只由
  `field_evidence[field].status == confirmed_official_documentation` 计算，
  绝不因字段值非空就自动算作已确认）；
- **来源与字段语义绑定**：每个 source 声明 `supports_fields`，`field_evidence` 引用某来源时
  该字段（或风险 claim `known_risks.<risk_id>`）必须在该来源的 `supports_fields` 内，
  provider 一致不足以证明来源正确；
- **provider-specific 字段纳入证据追踪**：DeepSeek 的 `concurrency_limit`、GPT-5.6 Terra 的
  `long_context_pricing_rules` 必须有 confirmed 来源；每个 known risk 有稳定 `risk_id` 与独立
  confirmed 来源（不再靠字符串包含证明风险）；
- **compatibility 双侧来源**：涉及两提供商的参数需同时有 DeepSeek 与 OpenAI 来源，且来源须
  支持该侧对应字段；`context_window` 已纳入必需参数集；
- 严格区分三层状态：
  - **已选择**（human_selected）：用户已明确选定两个模型；
  - **文档能力已确认**（confirmed_official_documentation）：官方公开页面已读取记载；
  - **实际效果未评估**（not_evaluated）：本任务未测试任何回答效果 / 准确率 / 稳定性。
- 仍有部分**账户权限、不可变快照、具体条款与接口行为**未解决
  （`requires_account_check` / `requires_interface_check` / `unresolved`），
  已逐字段记录在各模型的 `unresolved_fields` 与 `field_evidence` 中。

## 明确的边界

- 没有实际比较模型效果（`empirical_evaluation.status == not_evaluated`）；
- 不对两模型排序，不设 winner / primary / secondary / fallback 关系；
- 文档规格（上下文、价格、结构化输出支持）**不构成**质量评分依据；
- 官方未明确说明的字段一律进入 `unresolved_fields`，**不用常识或其他模型经验补齐**，
  exact snapshot 无法确认时**不虚构**日期版本。

## 与现有 preflight 的关系

当前的单模型 preflight 合同（`pa_wu_p1_preflight/`，使用单数 `selected_model`）
**尚不能直接表达双模型决策**。本包**不修改**该 preflight 资产、**不修改**其授权状态；
后续需要**单独实施** preflight schema 迁移（见
`preflight_schema_migration_plan.md`，当前 `migration_status: proposed_not_implemented`）。

## 文件

| 文件 | 作用 |
|---|---|
| `dual_model_decision.yaml` | 双模型选择决策合同（唯一记录用户选择，co-primary） |
| `official_evidence.yaml` | 提供商官方来源登记 + 每模型字段（未确认字段进 unresolved） |
| `parameter_compatibility.yaml` | 研究参数到两提供商的映射与可比性状态 |
| `comparability_boundaries.yaml` | 可控/不可控一致性与当前不可得出的结论 |
| `preflight_schema_migration_plan.md` | 单模型→双模型 preflight 迁移提案（不执行） |
| `validate_dual_model_decision.py` | 纯本地静态 validator（不联网、不改授权状态） |

## 研究结论

**C — 仍需补证。** 用户已完成模型选择，但正式 Prompt、采样映射、预算、日志、
停止条件、隐私审查与双模型 preflight 结构尚未全部冻结；
`operational_readiness: incomplete`。
