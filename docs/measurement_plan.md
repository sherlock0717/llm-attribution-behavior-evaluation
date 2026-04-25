# 测量与信效度计划

本项目没有声称使用完整成熟量表。当前题项是“基于既有理论与量表构念的情境化归因题项池”，用于 LLM-simulated respondents 的材料预演和流程验证。

## 当前模拟阶段主模型

当前模拟阶段的主模型是：

`process_condition -> agency -> free_will_attribution`

其中 `process_condition` 使用 6 个条件，并通过 dummy coding、材料长度诊断条件和控制回归检查结构效应是否独立于文本长度。

`perceived_intelligence` 不是普通控制变量，而是竞争中介。分析中需要同时检查：

- `process_condition -> agency -> free_will_attribution`
- `process_condition -> perceived_intelligence -> free_will_attribution`

如果 perceived_intelligence 路径更强，结论应改为：“决策结构可能通过提升感知智能，从而提高自由意志归因。”

## 构念来源

- agency / experience：参考 Gray, Gray, & Wegner 的 mind perception agency / experience 框架。
- free_will_attribution：参考 FWI / FAD-Plus 中自由意志、替代可能性、决定论相关构念，但本研究中属于情境化归因题项。
- autonomy：参考自主性 / 行动控制相关理论，但本研究中属于情境化归因题项。
- responsibility：参考道德责任归因与理由响应性理论，并拆分为 outcome_accountability、moral_praise_blame、process_accountability。
- perceived_intelligence：参考 Godspeed perceived intelligence 维度，但本研究中属于文本决策者情境改写题项。
- factual_manipulation_check / subjective_process_completeness：本研究自编操纵检验。

## 责任归因边界

责任归因当前只作为探索性结果，不作为主结论变量。责任归因容易受 `choice_valence`、结果好坏、道德赞责、后果严重性和归责对象差异影响。因此报告中必须分别查看：

- `outcome_accountability`
- `moral_praise_blame`
- `process_accountability`
- `responsibility_total`

如果这些子维度方向不一致，应明确写明：责任归因不作为当前主结论变量，仅作为探索性结果。

## 信效度边界

LLM 模拟数据中的 Cronbach alpha 只能作为流程检查，不能作为正式信度证据。由于题项对象、语境、计分和研究目的均经过情境化改写，原量表的信度、效度、因素结构和测量等价性不能直接继承。

## 正式研究所需步骤

1. 专家内容效度评估。
2. 真实被试预测试。
3. Cronbach alpha / McDonald omega。
4. EFA / CFA。
5. 区分效度检验，尤其区分 agency、perceived_intelligence、autonomy 和 responsibility。
6. AI / 人类标签下的测量等价性。
7. 操纵检验，区分事实性检查和主观过程完整度。

本阶段不能替代真实被试，不可用于证明 AI 具有自由意志。
