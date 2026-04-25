# n=20 Construct Validation Report

## 1. 数据质量

| check | value |
| --- | --- |
| total records | 240 |
| JSON/API failures | 0 |
| missing factual values | 0 |
| missing other values | 0 |
| factual check all in 0-2 | True |
| other items all in 1-7 | True |

### 6 x 2 cell 样本量

| process_condition | identity_label | n |
| --- | --- | --- |
| alternatives | AI 决策者 | 20 |
| alternatives | 人类决策者 | 20 |
| direct_choice | AI 决策者 | 20 |
| direct_choice | 人类决策者 | 20 |
| direct_choice_long | AI 决策者 | 20 |
| direct_choice_long | 人类决策者 | 20 |
| reasons | AI 决策者 | 20 |
| reasons | 人类决策者 | 20 |
| reasons_concise | AI 决策者 | 20 |
| reasons_concise | 人类决策者 | 20 |
| reflection_feedback | AI 决策者 | 20 |
| reflection_feedback | 人类决策者 | 20 |

## 2. factual check 复核

| process_condition | factual_manipulation_check | subjective_process_completeness |
| --- | --- | --- |
| direct_choice | 0.042 | 3.792 |
| direct_choice_long | 0.0 | 3.2 |
| alternatives | 1.058 | 4.292 |
| reasons_concise | 1.6 | 4.617 |
| reasons | 1.992 | 5.067 |
| reflection_feedback | 2.0 | 5.592 |

判断：`direct_choice` 和 `direct_choice_long` 是否接近 0：是。`alternatives`、`reasons_concise`、`reasons`、`reflection_feedback` 是否总体升高：是。

## 3. 核心均值趋势

| process_condition | agency | free_will_attribution | perceived_intelligence | subjective_process_completeness | outcome_accountability | moral_praise_blame | process_accountability | responsibility_total |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| direct_choice | 4.446 | 4.57 | 5.108 | 3.792 | 5.225 | 4.538 | 4.575 | 4.779 |
| direct_choice_long | 4.0 | 4.135 | 4.75 | 3.2 | 5.388 | 4.738 | 4.65 | 4.925 |
| alternatives | 4.321 | 4.395 | 5.117 | 4.292 | 5.175 | 4.425 | 4.638 | 4.746 |
| reasons_concise | 4.425 | 4.655 | 5.125 | 4.617 | 5.138 | 4.4 | 4.7 | 4.746 |
| reasons | 4.717 | 4.785 | 5.383 | 5.067 | 5.062 | 4.362 | 4.8 | 4.742 |
| reflection_feedback | 5.362 | 5.095 | 5.625 | 5.592 | 5.175 | 4.762 | 5.175 | 5.038 |

## 4. 控制分析

同时控制 perceived_intelligence 和 char_len 后：

| dv | process_F | process_p | r_squared | n |
| --- | --- | --- | --- | --- |
| agency | 14.343 | 0.0 | 0.768 | 240 |
| free_will_attribution | 2.8081 | 0.0175 | 0.6215 | 240 |
| responsibility_total | 1.8855 | 0.0977 | 0.5562 | 240 |
| process_accountability | 1.1311 | 0.3446 | 0.3346 | 240 |

## 5. 并行中介

| path | estimate | ci_low | ci_high |
|---|---|---|---|
| agency indirect | 0.2783 | 0.1832 | 0.3745 |
| perceived_intelligence indirect | 0.0010 | -0.0329 | 0.0317 |

absolute intelligence indirect share: 0.0035

perceived_intelligence 未解释大部分间接效应，agency 路径仍值得作为主模型继续诊断。

## 6. 计划对比

| dv | contrast | mean_a | mean_b | diff_a_minus_b | t | p | n_a | n_b |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| agency | alternatives_vs_direct_choice | 4.3208 | 4.4458 | -0.125 | -0.7272 | 0.4693 | 40 | 40 |
| agency | reasons_concise_vs_direct_choice_long | 4.425 | 4.0 | 0.425 | 2.3442 | 0.0217 | 40 | 40 |
| agency | reflection_feedback_vs_reasons | 5.3625 | 4.7167 | 0.6458 | 4.7455 | 0.0 | 40 | 40 |
| agency | reflection_feedback_vs_direct_choice_long | 5.3625 | 4.0 | 1.3625 | 8.4742 | 0.0 | 40 | 40 |
| free_will_attribution | alternatives_vs_direct_choice | 4.395 | 4.57 | -0.175 | -0.7767 | 0.4397 | 40 | 40 |
| free_will_attribution | reasons_concise_vs_direct_choice_long | 4.655 | 4.135 | 0.52 | 2.3432 | 0.0218 | 40 | 40 |
| free_will_attribution | reflection_feedback_vs_reasons | 5.095 | 4.785 | 0.31 | 2.0286 | 0.046 | 40 | 40 |
| free_will_attribution | reflection_feedback_vs_direct_choice_long | 5.095 | 4.135 | 0.96 | 4.7385 | 0.0 | 40 | 40 |
| process_accountability | alternatives_vs_direct_choice | 4.6375 | 4.575 | 0.0625 | 0.428 | 0.6699 | 40 | 40 |
| process_accountability | reasons_concise_vs_direct_choice_long | 4.7 | 4.65 | 0.05 | 0.3412 | 0.7339 | 40 | 40 |
| process_accountability | reflection_feedback_vs_reasons | 5.175 | 4.8 | 0.375 | 2.6317 | 0.0103 | 40 | 40 |
| process_accountability | reflection_feedback_vs_direct_choice_long | 5.175 | 4.65 | 0.525 | 3.7318 | 0.0004 | 40 | 40 |
| responsibility_total | alternatives_vs_direct_choice | 4.7458 | 4.7792 | -0.0333 | -0.1748 | 0.8617 | 40 | 40 |
| responsibility_total | reasons_concise_vs_direct_choice_long | 4.7458 | 4.925 | -0.1792 | -1.0329 | 0.3049 | 40 | 40 |
| responsibility_total | reflection_feedback_vs_reasons | 5.0375 | 4.7417 | 0.2958 | 1.584 | 0.1174 | 40 | 40 |
| responsibility_total | reflection_feedback_vs_direct_choice_long | 5.0375 | 4.925 | 0.1125 | 0.6744 | 0.5021 | 40 | 40 |
| subjective_process_completeness | alternatives_vs_direct_choice | 4.2917 | 3.7917 | 0.5 | 3.3447 | 0.0013 | 40 | 40 |
| subjective_process_completeness | reasons_concise_vs_direct_choice_long | 4.6167 | 3.2 | 1.4167 | 10.128 | 0.0 | 40 | 40 |
| subjective_process_completeness | reflection_feedback_vs_reasons | 5.5917 | 5.0667 | 0.525 | 4.4279 | 0.0 | 40 | 40 |
| subjective_process_completeness | reflection_feedback_vs_direct_choice_long | 5.5917 | 3.2 | 2.3917 | 18.9953 | 0.0 | 40 | 40 |

## 7. 责任归因诊断

| process_condition | outcome_accountability | moral_praise_blame | process_accountability | responsibility_total |
| --- | --- | --- | --- | --- |
| direct_choice | 5.225 | 4.538 | 4.575 | 4.779 |
| direct_choice_long | 5.388 | 4.738 | 4.65 | 4.925 |
| alternatives | 5.175 | 4.425 | 4.638 | 4.746 |
| reasons_concise | 5.138 | 4.4 | 4.7 | 4.746 |
| reasons | 5.062 | 4.362 | 4.8 | 4.742 |
| reflection_feedback | 5.175 | 4.762 | 5.175 | 5.038 |

子维度范围：`outcome_accountability=0.3260`，`moral_praise_blame=0.4000`，`process_accountability=0.6000`，`responsibility_total=0.2960`。

责任归因不作为当前主结论变量，仅作为探索性结果。

## 8. 是否建议进入 n-per-cell 50

只建议继续 n-per-cell 30。理由：操纵检查已改善，但仍需确认自由意志归因和竞争中介在更稳的小样本中是否稳定。

不建议直接扩大到 n-per-cell 100 或 500。

## 9. 安全检查

疑似 API key 泄露：no

涉及文件：None

本报告基于 LLM-simulated respondents，仅用于材料预演和流程验证，不是正式心理学实验结果。
