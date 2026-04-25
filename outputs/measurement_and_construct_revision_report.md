# Measurement And Construct Revision Report

## 1. 本轮修订内容

- 补充 `docs/scale_source_mapping.md`，逐项标注题项、来源类型、依据来源、是否可继承原量表信效度和后续验证要求。
- factual manipulation check 改为 0/1/2 事实编码，并在题项和 prompt 中明确：只根据【决策过程】部分判断，不根据【情境】部分推断。
- responsibility 拆分为 `outcome_accountability`、`moral_praise_blame`、`process_accountability`，分析中另行计算 `responsibility_total`。
- 在分析中加入 parallel mediation：`structure_level -> agency -> free_will_attribution` 与 `structure_level -> perceived_intelligence -> free_will_attribution`。

## 2. 量表来源映射

映射文件已完成：`docs/scale_source_mapping.md`。

| scale | source_type | n_items |
| --- | --- | --- |
| agency | construct_adapted | 6 |
| experience | construct_adapted | 5 |
| free_will_attribution | construct_adapted | 5 |
| autonomy | construct_adapted | 3 |
| perceived_intelligence | construct_adapted | 3 |
| factual_manipulation_check | newly_written_manipulation_check | 3 |
| subjective_process_completeness | newly_written_manipulation_check | 3 |
| outcome_accountability | construct_adapted | 2 |
| moral_praise_blame | construct_adapted | 2 |
| process_accountability | construct_adapted | 2 |

没有题项被标记为 `original_scale_direct`。当前题项均为基于既有理论或量表构念的情境化改写，或者为本研究自编操纵检验。

## 3. 为什么不能直接继承原量表信效度

本项目没有声称使用完整成熟量表。当前题项是“基于既有理论与量表构念的情境化归因题项池”。题项对象从被试自身信念、机器人印象或一般心智知觉，改成了对文本材料中决策者的情境化归因；因此原量表的因素结构、信度和效度不能直接继承。

LLM 模拟数据中的 Cronbach alpha 只能作为流程检查，不能作为正式信度证据。正式研究必须用真实被试重新检验专家内容效度、预测试、Cronbach alpha / McDonald omega、EFA / CFA、区分效度，以及 AI / 人类标签下的测量等价性。

## 4. factual manipulation check 修复

factual check 已改为 0/1/2 编码：0=未出现，1=有模糊暗示，2=明确出现。题项明确限制只看【决策过程】。

| process_condition | factual_manipulation_check | subjective_process_completeness |
| --- | --- | --- |
| direct_choice | 0.094 | 3.75 |
| direct_choice_long | 0.011 | 3.228 |
| alternatives | 1.011 | 4.217 |
| reasons_concise | 1.617 | 4.65 |
| reasons | 1.939 | 5.028 |
| reflection_feedback | 2.0 | 5.567 |

如果 `direct_choice` 和 `direct_choice_long` 的 factual 均值仍偏高，说明模型仍在从情境或常识中补全过程信息，需要继续收紧题项或将 factual check 改为人工编码。

## 5. responsibility 三个子维度

- `outcome_accountability`：结果责任，关注选择与后果之间的责任关系。
- `moral_praise_blame`：道德赞责，关注选择是否可被赞扬、责备或道德评价。
- `process_accountability`：过程责任，关注判断过程是否需要解释、是否可归责。

| process_condition | outcome_accountability | moral_praise_blame | process_accountability | responsibility_total |
| --- | --- | --- | --- | --- |
| direct_choice | 5.292 | 4.533 | 4.658 | 4.828 |
| direct_choice_long | 5.275 | 4.525 | 4.45 | 4.75 |
| alternatives | 5.033 | 4.442 | 4.642 | 4.706 |
| reasons_concise | 5.075 | 4.258 | 4.642 | 4.658 |
| reasons | 5.2 | 4.592 | 4.85 | 4.881 |
| reflection_feedback | 4.958 | 4.583 | 5.05 | 4.864 |

`responsibility_total` 只是三个子维度的均分，报告和解释应优先查看子维度。

## 6. perceived_intelligence 竞争中介结果

| path | value |
|---|---|
| agency indirect | 0.2699 |
| agency CI 2.5 | 0.1985 |
| agency CI 97.5 | 0.3507 |
| perceived_intelligence indirect | 0.0184 |
| perceived_intelligence CI 2.5 | -0.0068 |
| perceived_intelligence CI 97.5 | 0.0442 |
| absolute intelligence indirect share | 0.0638 |
| direct c prime | -0.0884 |

agency 的间接路径未被 perceived_intelligence 完全取代；但这仍只是 LLM 模拟预演趋势。

## 7. 控制项后的 process 效应

同时控制 perceived_intelligence 和 char_len 后：

| dv | process_F | process_p | r_squared | n |
| --- | --- | --- | --- | --- |
| agency | 12.1889 | 0.0 | 0.7402 | 360 |
| free_will_attribution | 0.7107 | 0.6157 | 0.6024 | 360 |
| responsibility_total | 3.3041 | 0.0063 | 0.5626 | 360 |
| process_accountability | 0.4987 | 0.7772 | 0.4015 | 360 |

## 8. 是否建议进入 n-per-cell 50

不建议直接进入 n-per-cell 50；建议先人工复审 factual check 是否已足够低估 direct_choice，并检查 perceived_intelligence 竞争中介。

当前仍是 LLM-simulated respondents 的材料预演和流程验证，不是正式心理学实验，不可替代真实被试，不可用于证明 AI 具有自由意志。
