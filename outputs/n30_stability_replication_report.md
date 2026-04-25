# n=30 Stability Replication Report

## 1. 数据质量

| check | value |
| --- | --- |
| total records | 360 |
| JSON/API failures | 0 |
| missing factual values | 0 |
| missing other values | 0 |
| factual check all in 0-2 | True |
| other items all in 1-7 | True |

### 6 x 2 每格样本量

| process_condition | identity_label | n |
| --- | --- | --- |
| alternatives | AI 决策者 | 30 |
| alternatives | 人类决策者 | 30 |
| direct_choice | AI 决策者 | 30 |
| direct_choice | 人类决策者 | 30 |
| direct_choice_long | AI 决策者 | 30 |
| direct_choice_long | 人类决策者 | 30 |
| reasons | AI 决策者 | 30 |
| reasons | 人类决策者 | 30 |
| reasons_concise | AI 决策者 | 30 |
| reasons_concise | 人类决策者 | 30 |
| reflection_feedback | AI 决策者 | 30 |
| reflection_feedback | 人类决策者 | 30 |

## 2. factual check 复核

| process_condition | factual_manipulation_check | subjective_process_completeness |
| --- | --- | --- |
| direct_choice | 0.094 | 3.75 |
| direct_choice_long | 0.011 | 3.228 |
| alternatives | 1.011 | 4.217 |
| reasons_concise | 1.617 | 4.65 |
| reasons | 1.939 | 5.028 |
| reflection_feedback | 2.0 | 5.567 |

判断：`direct_choice` / `direct_choice_long` 是否接近 0：是。后续条件是否总体递增：是。

## 3. 核心均值趋势

| process_condition | agency | free_will_attribution | perceived_intelligence | subjective_process_completeness | outcome_accountability | moral_praise_blame | process_accountability | responsibility_total |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| direct_choice | 4.308 | 4.44 | 5.0 | 3.75 | 5.292 | 4.533 | 4.658 | 4.828 |
| direct_choice_long | 3.942 | 4.087 | 4.628 | 3.228 | 5.275 | 4.525 | 4.45 | 4.75 |
| alternatives | 4.25 | 4.413 | 5.056 | 4.217 | 5.033 | 4.442 | 4.642 | 4.706 |
| reasons_concise | 4.433 | 4.503 | 5.144 | 4.65 | 5.075 | 4.258 | 4.642 | 4.658 |
| reasons | 4.583 | 4.69 | 5.267 | 5.028 | 5.2 | 4.592 | 4.85 | 4.881 |
| reflection_feedback | 5.2 | 4.87 | 5.533 | 5.567 | 4.958 | 4.583 | 5.05 | 4.864 |

## 4. 控制分析

同时控制 perceived_intelligence 和 char_len 后：

| dv | process_F | process_p | r_squared | n |
| --- | --- | --- | --- | --- |
| agency | 12.1889 | 0.0 | 0.7402 | 360 |
| free_will_attribution | 0.7107 | 0.6157 | 0.6024 | 360 |
| responsibility_total | 3.3041 | 0.0063 | 0.5626 | 360 |
| process_accountability | 0.4987 | 0.7772 | 0.4015 | 360 |

## 5. 并行中介

| path | estimate | ci_low | ci_high |
|---|---|---|---|
| agency indirect | 0.2699 | 0.1985 | 0.3507 |
| perceived_intelligence indirect | 0.0184 | -0.0068 | 0.0442 |

absolute intelligence indirect share: 0.0638

判断：agency 间接效应是否仍稳定：是。perceived_intelligence 是否仍没有解释大部分效应：是。

## 6. 计划对比

| dv | contrast | mean_a | mean_b | diff_a_minus_b | t | p | n_a | n_b |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| agency | alternatives_vs_direct_choice | 4.25 | 4.3083 | -0.0583 | -0.4012 | 0.689 | 60 | 60 |
| agency | reasons_concise_vs_direct_choice_long | 4.4333 | 3.9417 | 0.4917 | 3.3397 | 0.0011 | 60 | 60 |
| agency | reflection_feedback_vs_reasons | 5.2 | 4.5833 | 0.6167 | 5.3414 | 0.0 | 60 | 60 |
| agency | reflection_feedback_vs_direct_choice_long | 5.2 | 3.9417 | 1.2583 | 9.401 | 0.0 | 60 | 60 |
| free_will_attribution | alternatives_vs_direct_choice | 4.4133 | 4.44 | -0.0267 | -0.1407 | 0.8883 | 60 | 60 |
| free_will_attribution | reasons_concise_vs_direct_choice_long | 4.5033 | 4.0867 | 0.4167 | 2.2916 | 0.0238 | 60 | 60 |
| free_will_attribution | reflection_feedback_vs_reasons | 4.87 | 4.69 | 0.18 | 1.3086 | 0.1932 | 60 | 60 |
| free_will_attribution | reflection_feedback_vs_direct_choice_long | 4.87 | 4.0867 | 0.7833 | 4.5928 | 0.0 | 60 | 60 |
| process_accountability | alternatives_vs_direct_choice | 4.6417 | 4.6583 | -0.0167 | -0.1196 | 0.905 | 60 | 60 |
| process_accountability | reasons_concise_vs_direct_choice_long | 4.6417 | 4.45 | 0.1917 | 1.4437 | 0.1516 | 60 | 60 |
| process_accountability | reflection_feedback_vs_reasons | 5.05 | 4.85 | 0.2 | 1.7739 | 0.0787 | 60 | 60 |
| process_accountability | reflection_feedback_vs_direct_choice_long | 5.05 | 4.45 | 0.6 | 4.5084 | 0.0 | 60 | 60 |
| responsibility_total | alternatives_vs_direct_choice | 4.7056 | 4.8278 | -0.1222 | -0.746 | 0.4571 | 60 | 60 |
| responsibility_total | reasons_concise_vs_direct_choice_long | 4.6583 | 4.75 | -0.0917 | -0.5735 | 0.5674 | 60 | 60 |
| responsibility_total | reflection_feedback_vs_reasons | 4.8639 | 4.8806 | -0.0167 | -0.1122 | 0.9109 | 60 | 60 |
| responsibility_total | reflection_feedback_vs_direct_choice_long | 4.8639 | 4.75 | 0.1139 | 0.7127 | 0.4774 | 60 | 60 |
| subjective_process_completeness | alternatives_vs_direct_choice | 4.2167 | 3.75 | 0.4667 | 3.6924 | 0.0003 | 60 | 60 |
| subjective_process_completeness | reasons_concise_vs_direct_choice_long | 4.65 | 3.2278 | 1.4222 | 12.7595 | 0.0 | 60 | 60 |
| subjective_process_completeness | reflection_feedback_vs_reasons | 5.5667 | 5.0278 | 0.5389 | 5.5425 | 0.0 | 60 | 60 |
| subjective_process_completeness | reflection_feedback_vs_direct_choice_long | 5.5667 | 3.2278 | 2.3389 | 21.5417 | 0.0 | 60 | 60 |

判断：仍支持 “单纯候选生成不足以提高自由意志归因；理由权衡与反思反馈才是关键线索。”

## 7. 责任归因处理

| process_condition | outcome_accountability | moral_praise_blame | process_accountability | responsibility_total |
| --- | --- | --- | --- | --- |
| direct_choice | 5.292 | 4.533 | 4.658 | 4.828 |
| direct_choice_long | 5.275 | 4.525 | 4.45 | 4.75 |
| alternatives | 5.033 | 4.442 | 4.642 | 4.706 |
| reasons_concise | 5.075 | 4.258 | 4.642 | 4.658 |
| reasons | 5.2 | 4.592 | 4.85 | 4.881 |
| reflection_feedback | 4.958 | 4.583 | 5.05 | 4.864 |

责任归因不作为当前主结论变量，仅作为探索性结果。

## 8. 结论建议

- 是否可以冻结当前实验设计：暂不建议完全冻结当前实验设计，应先人工复审计划对比和责任归因稳定性。
- 是否可以开始整理项目论文/报告：可以开始整理项目论文/报告的设计、测量边界、模拟流程和诊断结果。
- 是否需要继续 n-per-cell 50：如需进一步确认，可继续 n-per-cell 50；不建议跳到 n-per-cell 100/500。
- 是否仍不建议 n-per-cell 100/500：仍不建议。当前阶段没有必要直接扩大到 100/500。

## 9. 安全检查

疑似 API key 泄露：no

涉及文件：None

本报告基于 LLM-simulated respondents，仅用于材料预演和流程验证，不是正式心理学实验结果。
