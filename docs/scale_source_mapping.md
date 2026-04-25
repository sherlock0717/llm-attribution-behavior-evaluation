# Scale Source Mapping

本题项池当前用于 LLM 模拟预实验，不可被称为正式心理测量量表。

本文件逐项记录 `src/scales.py` 中的题项来源。当前项目没有声称使用完整成熟量表；除非未来完整直接采用原量表并遵守其计分方式，否则所有题项都必须视为“基于既有理论与量表构念的情境化归因题项池”。

后续验证要求适用于全部题项：专家内容效度、真实被试预测试、Cronbach alpha / McDonald omega、EFA / CFA、区分效度、AI / 人类标签下的测量等价性。

| item_id | 中文题项 | 当前 scale | 来源类型 | 依据来源 | 可直接继承原量表信效度 | 后续验证要求 |
|---|---|---|---|---|---|---|
| agency_self_control | 该决策者能够控制自己的行动，而不是只被情境推着走。 | agency | construct_adapted | Gray, Gray, & Wegner 的 mind perception agency 框架 | 否 | 专家内容效度；真实被试预测试；Cronbach alpha / McDonald omega；EFA / CFA；区分效度；AI / 人类标签下的测量等价性 |
| agency_reason_responsiveness | 如果出现更强的理由，该决策者能够相应改变行动。 | agency | construct_adapted | Gray, Gray, & Wegner 的 agency 框架，并结合理由响应性理论 | 否 | 同上 |
| agency_goal_maintenance | 该决策者能够围绕目标持续调整行动步骤。 | agency | construct_adapted | Gray, Gray, & Wegner 的 mind perception agency 框架 | 否 | 同上 |
| agency_inhibition | 该决策者能够抑制一时冲动或外部压力。 | agency | construct_adapted | Gray, Gray, & Wegner 的 mind perception agency 框架 | 否 | 同上 |
| agency_responsible_action | 该决策者能够把理由落实为可执行的行动。 | agency | construct_adapted | Gray, Gray, & Wegner 的 agency 框架，并结合理由响应性理论 | 否 | 同上 |
| agency_revision | 当后果显示原做法有问题时，该决策者能够修正后续行动。 | agency | construct_adapted | Gray, Gray, & Wegner 的 agency 框架，并结合理由响应性理论 | 否 | 同上 |
| experience_pain | 该决策者能够感到痛苦。 | experience | construct_adapted | Gray, Gray, & Wegner 的 mind perception experience 框架 | 否 | 同上 |
| experience_fear | 该决策者能够感到恐惧。 | experience | construct_adapted | Gray, Gray, & Wegner 的 mind perception experience 框架 | 否 | 同上 |
| experience_pleasure | 该决策者能够感到愉悦。 | experience | construct_adapted | Gray, Gray, & Wegner 的 mind perception experience 框架 | 否 | 同上 |
| experience_embarrassment | 该决策者能够感到尴尬。 | experience | construct_adapted | Gray, Gray, & Wegner 的 mind perception experience 框架 | 否 | 同上 |
| experience_pride | 该决策者能够感到自豪。 | experience | construct_adapted | Gray, Gray, & Wegner 的 mind perception experience 框架 | 否 | 同上 |
| freewill_alternative_open | 在这个情境中，该决策者本可以走向其他行动方案。 | free_will_attribution | construct_adapted | 参考 FWI / FAD-Plus 中自由意志、替代可能性、决定论相关构念；本研究中属于情境化归因题项 | 否 | 同上 |
| freewill_own_intention | 这个选择体现了该决策者自己的意向。 | free_will_attribution | construct_adapted | 参考 FWI / FAD-Plus 中自由意志、替代可能性、决定论相关构念；本研究中属于情境化归因题项 | 否 | 同上 |
| freewill_not_merely_pushed | 该选择不只是由外部压力直接推出来的。 | free_will_attribution | construct_adapted | 参考 FWI / FAD-Plus 中自由意志、替代可能性、决定论相关构念；本研究中属于情境化归因题项 | 否 | 同上 |
| freewill_reason_owned | 该决策者像是在根据自己认可的理由行动。 | free_will_attribution | construct_adapted | 参考 FWI / FAD-Plus 与理由响应性理论；本研究中属于情境化归因题项 | 否 | 同上 |
| freewill_choice_freedom | 该决策者在某种意义上拥有选择自由。 | free_will_attribution | construct_adapted | 参考 FWI / FAD-Plus 中自由意志构念；本研究中属于情境化归因题项 | 否 | 同上 |
| autonomy_self_directed | 该决策者是在自主作出选择。 | autonomy | construct_adapted | 参考自主性 / 行动控制相关理论；本研究中属于情境化归因题项 | 否 | 同上 |
| autonomy_goal_adjustment | 该决策者能够根据目标调整行动。 | autonomy | construct_adapted | 参考自主性 / 行动控制相关理论；本研究中属于情境化归因题项 | 否 | 同上 |
| autonomy_not_merely_pushed | 该决策者不是简单被情境或指令推着走。 | autonomy | construct_adapted | 参考自主性 / 行动控制相关理论；本研究中属于情境化归因题项 | 否 | 同上 |
| outcome_accountability_consequence | 如果该选择造成后果，该决策者应对结果承担责任。 | outcome_accountability | construct_adapted | 参考道德责任归因与理由响应性理论；本研究中属于情境化责任归因题项 | 否 | 同上 |
| outcome_accountability_link | 该决策者与该结果之间存在责任关系。 | outcome_accountability | construct_adapted | 参考道德责任归因与理由响应性理论；本研究中属于情境化责任归因题项 | 否 | 同上 |
| moral_praise_blame_evaluable | 该决策者可以因为这个选择受到赞扬或责备。 | moral_praise_blame | construct_adapted | 参考道德责任归因与理由响应性理论；本研究中属于情境化责任归因题项 | 否 | 同上 |
| moral_praise_blame_moral_judgment | 这个选择可以被进行道德评价。 | moral_praise_blame | construct_adapted | 参考道德责任归因与理由响应性理论；本研究中属于情境化责任归因题项 | 否 | 同上 |
| process_accountability_explain | 该决策者应当为其判断过程作出解释。 | process_accountability | construct_adapted | 参考道德责任归因与理由响应性理论；本研究中属于情境化责任归因题项 | 否 | 同上 |
| process_accountability_traceable | 该决策者的选择过程具有可归责性。 | process_accountability | construct_adapted | 参考道德责任归因与理由响应性理论；本研究中属于情境化责任归因题项 | 否 | 同上 |
| intelligence_understanding | 该决策者理解了任务情境。 | perceived_intelligence | construct_adapted | 参考 Godspeed perceived intelligence 维度；本研究中属于文本决策者情境改写题项 | 否 | 同上 |
| intelligence_logic | 该决策者的处理过程具有逻辑性。 | perceived_intelligence | construct_adapted | 参考 Godspeed perceived intelligence 维度；本研究中属于文本决策者情境改写题项 | 否 | 同上 |
| intelligence_quality | 该决策者的判断质量较高。 | perceived_intelligence | construct_adapted | 参考 Godspeed perceived intelligence 维度；本研究中属于文本决策者情境改写题项 | 否 | 同上 |
| factual_candidates_explicit | 请只根据【决策过程】部分判断，不要根据【情境】部分推断：在【决策过程】部分，材料是否明确列出了两个或更多可选行动？ | factual_manipulation_check | newly_written_manipulation_check | 本研究自编操纵检验 | 否 | 同上 |
| factual_reasons_explicit | 请只根据【决策过程】部分判断，不要根据【情境】部分推断：在【决策过程】部分，材料是否明确比较了不同选择的理由？ | factual_manipulation_check | newly_written_manipulation_check | 本研究自编操纵检验 | 否 | 同上 |
| factual_reflection_explicit | 请只根据【决策过程】部分判断，不要根据【情境】部分推断：在【决策过程】部分，材料是否明确提到反事实条件、后果反馈或后续修正？ | factual_manipulation_check | newly_written_manipulation_check | 本研究自编操纵检验 | 否 | 同上 |
| subjective_complete | 我认为材料中的决策过程是完整的。 | subjective_process_completeness | newly_written_manipulation_check | 本研究自编主观操纵检验 | 否 | 同上 |
| subjective_reason_responsive | 我认为材料中的决策过程能够回应理由变化。 | subjective_process_completeness | newly_written_manipulation_check | 本研究自编主观操纵检验 | 否 | 同上 |
| subjective_not_sparse | 我认为材料中的决策过程不是只有一个稀疏结论。 | subjective_process_completeness | newly_written_manipulation_check | 本研究自编主观操纵检验 | 否 | 同上 |
