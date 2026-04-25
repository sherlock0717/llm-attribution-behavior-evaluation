# Method Revision Report

## 1. 修订内容

- 刺激材料从 4 个 process_condition 扩展为 6 个：保留 `direct_choice`、`alternatives`、`reasons`、`reflection_feedback`，新增 `direct_choice_long` 和 `reasons_concise`。
- `direct_choice_long` 用较长背景复述接近长材料长度，但不加入候选比较、理由比较、反事实、记忆或后果修正。
- `reasons_concise` 保持较短文本，但包含简洁理由比较，用于和 `direct_choice_long` 区分结构效应与长度效应。
- 删除材料中的元描述句，避免直接告诉被试“展示了理由权衡”或“展示了反思反馈”。
- 情境加入 `choice_valence`：`positive_choice`、`mixed_choice`、`negative_choice`，避免所有最终选择都显得更道德或更负责。
- agency 题项改为行动控制、理由响应、行动修正；移除 `agency_communication`，将原 `agency_thought` 改为更行为化的理由响应题项。
- manipulation_check 拆成 `factual_manipulation_check` 和 `subjective_process_completeness`。
- 自由意志归因增加间接题项，减少直接使用“自由”表述的比例。

## 2. 每个条件的材料长度

| process_condition | mean | min | max |
| --- | --- | --- | --- |
| direct_choice | 114.7 | 102 | 132 |
| direct_choice_long | 572.2 | 559 | 590 |
| alternatives | 178.37 | 161 | 204 |
| reasons_concise | 223.87 | 207 | 249 |
| reasons | 356.87 | 339 | 383 |
| reflection_feedback | 516.37 | 497 | 544 |

## 3. 均值趋势

### 按 process_condition

| process_condition | agency | experience | free_will_attribution | autonomy | outcome_accountability | moral_praise_blame | process_accountability | responsibility_total | perceived_intelligence | factual_manipulation_check | subjective_process_completeness |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| direct_choice | 4.308 | 2.807 | 4.44 | 4.578 | 5.292 | 4.533 | 4.658 | 4.828 | 5.0 | 0.094 | 3.75 |
| direct_choice_long | 3.942 | 2.763 | 4.087 | 4.206 | 5.275 | 4.525 | 4.45 | 4.75 | 4.628 | 0.011 | 3.228 |
| alternatives | 4.25 | 3.073 | 4.413 | 4.5 | 5.033 | 4.442 | 4.642 | 4.706 | 5.056 | 1.011 | 4.217 |
| reasons_concise | 4.433 | 2.76 | 4.503 | 4.544 | 5.075 | 4.258 | 4.642 | 4.658 | 5.144 | 1.617 | 4.65 |
| reasons | 4.583 | 2.937 | 4.69 | 4.8 | 5.2 | 4.592 | 4.85 | 4.881 | 5.267 | 1.939 | 5.028 |
| reflection_feedback | 5.2 | 2.527 | 4.87 | 5.1 | 4.958 | 4.583 | 5.05 | 4.864 | 5.533 | 2.0 | 5.567 |

### 按 process_condition x identity_label

| process_condition | identity_label | agency | experience | free_will_attribution | autonomy | outcome_accountability | moral_praise_blame | process_accountability | responsibility_total | perceived_intelligence | factual_manipulation_check | subjective_process_completeness |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| alternatives | AI 决策者 | 4.117 | 1.747 | 4.093 | 4.3 | 4.3 | 3.85 | 4.35 | 4.167 | 5.178 | 1.022 | 4.078 |
| alternatives | 人类决策者 | 4.383 | 4.4 | 4.733 | 4.7 | 5.767 | 5.033 | 4.933 | 5.244 | 4.933 | 1.0 | 4.356 |
| direct_choice | AI 决策者 | 4.244 | 1.473 | 4.0 | 4.422 | 4.75 | 3.883 | 4.45 | 4.361 | 5.144 | 0.089 | 3.778 |
| direct_choice | 人类决策者 | 4.372 | 4.14 | 4.88 | 4.733 | 5.833 | 5.183 | 4.867 | 5.294 | 4.856 | 0.1 | 3.722 |
| direct_choice_long | AI 决策者 | 3.6 | 1.433 | 3.447 | 3.733 | 4.517 | 3.767 | 4.05 | 4.111 | 4.478 | 0.0 | 3.067 |
| direct_choice_long | 人类决策者 | 4.283 | 4.093 | 4.727 | 4.678 | 6.033 | 5.283 | 4.85 | 5.389 | 4.778 | 0.022 | 3.389 |
| reasons | AI 决策者 | 4.528 | 1.713 | 4.307 | 4.656 | 4.55 | 3.883 | 4.633 | 4.356 | 5.344 | 1.967 | 5.0 |
| reasons | 人类决策者 | 4.639 | 4.16 | 5.073 | 4.944 | 5.85 | 5.3 | 5.067 | 5.406 | 5.189 | 1.911 | 5.056 |
| reasons_concise | AI 决策者 | 4.333 | 1.513 | 4.273 | 4.478 | 4.333 | 3.55 | 4.333 | 4.072 | 5.233 | 1.633 | 4.511 |
| reasons_concise | 人类决策者 | 4.533 | 4.007 | 4.733 | 4.611 | 5.817 | 4.967 | 4.95 | 5.244 | 5.056 | 1.6 | 4.789 |
| reflection_feedback | AI 决策者 | 5.106 | 1.527 | 4.573 | 4.933 | 4.3 | 3.95 | 4.917 | 4.389 | 5.467 | 2.0 | 5.478 |
| reflection_feedback | 人类决策者 | 5.294 | 3.527 | 5.167 | 5.267 | 5.617 | 5.217 | 5.183 | 5.339 | 5.6 | 2.0 | 5.656 |

## 4. 控制 perceived_intelligence 后的结果

| dv | spec | process_F | process_p | r_squared | n |
| --- | --- | --- | --- | --- | --- |
| agency | control_perceived_intelligence | 14.6964 | 0.0 | 0.739 | 360 |
| free_will_attribution | control_perceived_intelligence | 0.48 | 0.7912 | 0.601 | 360 |
| responsibility_total | control_perceived_intelligence | 3.1073 | 0.0093 | 0.5603 | 360 |
| outcome_accountability | control_perceived_intelligence | 7.1851 | 0.0 | 0.5606 | 360 |
| moral_praise_blame | control_perceived_intelligence | 3.2427 | 0.0071 | 0.5473 | 360 |
| process_accountability | control_perceived_intelligence | 0.7422 | 0.5923 | 0.4011 | 360 |
| experience | control_perceived_intelligence | 4.6307 | 0.0004 | 0.7943 | 360 |
| autonomy | control_perceived_intelligence | 1.541 | 0.1764 | 0.6584 | 360 |

## 5. 控制 char_len 后的结果

| dv | spec | process_F | process_p | r_squared | n |
| --- | --- | --- | --- | --- | --- |
| agency | control_char_len | 34.616 | 0.0 | 0.5691 | 360 |
| free_will_attribution | control_char_len | 9.5195 | 0.0 | 0.4612 | 360 |
| responsibility_total | control_char_len | 2.2971 | 0.0449 | 0.4704 | 360 |
| outcome_accountability | control_char_len | 3.3732 | 0.0055 | 0.5073 | 360 |
| moral_praise_blame | control_char_len | 2.2673 | 0.0475 | 0.4961 | 360 |
| process_accountability | control_char_len | 6.6834 | 0.0 | 0.2381 | 360 |
| experience | control_char_len | 3.5081 | 0.0042 | 0.7948 | 360 |
| autonomy | control_char_len | 12.5846 | 0.0 | 0.4891 | 360 |

## 6. 同时控制 perceived_intelligence 和 char_len 后的结果

| dv | spec | process_F | process_p | r_squared | n |
| --- | --- | --- | --- | --- | --- |
| agency | control_both | 12.1889 | 0.0 | 0.7402 | 360 |
| free_will_attribution | control_both | 0.7107 | 0.6157 | 0.6024 | 360 |
| responsibility_total | control_both | 3.3041 | 0.0063 | 0.5626 | 360 |
| outcome_accountability | control_both | 7.6982 | 0.0 | 0.5636 | 360 |
| moral_praise_blame | control_both | 3.2361 | 0.0072 | 0.5498 | 360 |
| process_accountability | control_both | 0.4987 | 0.7772 | 0.4015 | 360 |
| experience | control_both | 3.289 | 0.0065 | 0.7948 | 360 |
| autonomy | control_both | 1.5112 | 0.1856 | 0.6595 | 360 |

## 7. 计划对比

| dv | contrast | mean_a | mean_b | diff_a_minus_b | t | p | n_a | n_b |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| agency | alternatives_vs_direct_choice | 4.25 | 4.3083 | -0.0583 | -0.4012 | 0.689 | 60 | 60 |
| agency | reasons_concise_vs_direct_choice_long | 4.4333 | 3.9417 | 0.4917 | 3.3397 | 0.0011 | 60 | 60 |
| free_will_attribution | alternatives_vs_direct_choice | 4.4133 | 4.44 | -0.0267 | -0.1407 | 0.8883 | 60 | 60 |
| free_will_attribution | reasons_concise_vs_direct_choice_long | 4.5033 | 4.0867 | 0.4167 | 2.2916 | 0.0238 | 60 | 60 |
| process_accountability | alternatives_vs_direct_choice | 4.6417 | 4.6583 | -0.0167 | -0.1196 | 0.905 | 60 | 60 |
| process_accountability | reasons_concise_vs_direct_choice_long | 4.6417 | 4.45 | 0.1917 | 1.4437 | 0.1516 | 60 | 60 |
| responsibility_total | alternatives_vs_direct_choice | 4.7056 | 4.8278 | -0.1222 | -0.746 | 0.4571 | 60 | 60 |
| responsibility_total | reasons_concise_vs_direct_choice_long | 4.6583 | 4.75 | -0.0917 | -0.5735 | 0.5674 | 60 | 60 |
| subjective_process_completeness | alternatives_vs_direct_choice | 4.2167 | 3.75 | 0.4667 | 3.6924 | 0.0003 | 60 | 60 |
| subjective_process_completeness | reasons_concise_vs_direct_choice_long | 4.65 | 3.2278 | 1.4222 | 12.7595 | 0.0 | 60 | 60 |

解释重点：

- `alternatives_vs_direct_choice` 用于检查单纯候选生成是否足以提升 agency / free_will_attribution。
- `reasons_concise_vs_direct_choice_long` 用于检查包含理由权衡的短文本是否能超过只有长背景复述的文本。

## 8. 分身份中介

| model | control_identity | a_path_X_to_M | b_path_M_to_Y | indirect_ab | direct_c_prime | bootstrap_ci_2.5 | bootstrap_ci_97.5 | n_boot_used | note | identity_label |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| structure_level -> agency -> free_will_attribution | False | 0.3525 | 0.8879 | 0.313 | -0.0336 | 0.2171 | 0.4198 | 1000 | Exploratory mediation on synthetic AI-simulated data only. | AI 决策者 |
| structure_level -> agency -> free_will_attribution | False | 0.2641 | 1.0011 | 0.2644 | -0.1605 | 0.1701 | 0.3592 | 1000 | Exploratory mediation on synthetic AI-simulated data only. | 人类决策者 |

该中介只用于 LLM-simulated respondents 预演，不构成心理机制证明。

## 9. 按 domain 的稳健性

| group_type | group | dv | structure_coef | p | n | note |
| --- | --- | --- | --- | --- | --- | --- |
| domain | 人际关系 | agency | 0.1558 | 0.0003 | 84 | Controls perceived_intelligence, char_len, identity_label. |
| domain | 人际关系 | free_will_attribution | 0.0016 | 0.9774 | 84 | Controls perceived_intelligence, char_len, identity_label. |
| domain | 人际关系 | responsibility_total | -0.2383 | 0.0006 | 84 | Controls perceived_intelligence, char_len, identity_label. |
| domain | 人际关系 | process_accountability | -0.0792 | 0.2676 | 84 | Controls perceived_intelligence, char_len, identity_label. |
| domain | 服从与自主 | agency | 0.2891 | 0.0004 | 48 | Controls perceived_intelligence, char_len, identity_label. |
| domain | 服从与自主 | free_will_attribution | 0.2094 | 0.0122 | 48 | Controls perceived_intelligence, char_len, identity_label. |
| domain | 服从与自主 | responsibility_total | -0.1183 | 0.2328 | 48 | Controls perceived_intelligence, char_len, identity_label. |
| domain | 服从与自主 | process_accountability | 0.0448 | 0.6679 | 48 | Controls perceived_intelligence, char_len, identity_label. |
| domain | 自我控制 | agency | 0.1754 | 0.0001 | 48 | Controls perceived_intelligence, char_len, identity_label. |
| domain | 自我控制 | free_will_attribution | 0.2021 | 0.005 | 48 | Controls perceived_intelligence, char_len, identity_label. |
| domain | 自我控制 | responsibility_total | 0.0768 | 0.1928 | 48 | Controls perceived_intelligence, char_len, identity_label. |
| domain | 自我控制 | process_accountability | 0.2675 | 0.0002 | 48 | Controls perceived_intelligence, char_len, identity_label. |
| domain | 责任困境 | agency | 0.0911 | 0.0845 | 84 | Controls perceived_intelligence, char_len, identity_label. |
| domain | 责任困境 | free_will_attribution | -0.0121 | 0.8397 | 84 | Controls perceived_intelligence, char_len, identity_label. |
| domain | 责任困境 | responsibility_total | -0.1586 | 0.0271 | 84 | Controls perceived_intelligence, char_len, identity_label. |
| domain | 责任困境 | process_accountability | -0.0434 | 0.504 | 84 | Controls perceived_intelligence, char_len, identity_label. |
| domain | 道德冲突 | agency | 0.14 | 0.0116 | 48 | Controls perceived_intelligence, char_len, identity_label. |
| domain | 道德冲突 | free_will_attribution | -0.0738 | 0.3189 | 48 | Controls perceived_intelligence, char_len, identity_label. |
| domain | 道德冲突 | responsibility_total | -0.14 | 0.0315 | 48 | Controls perceived_intelligence, char_len, identity_label. |
| domain | 道德冲突 | process_accountability | -0.0699 | 0.2385 | 48 | Controls perceived_intelligence, char_len, identity_label. |
| domain | 风险决策 | agency | 0.1825 | 0.0042 | 48 | Controls perceived_intelligence, char_len, identity_label. |
| domain | 风险决策 | free_will_attribution | -0.005 | 0.9392 | 48 | Controls perceived_intelligence, char_len, identity_label. |
| domain | 风险决策 | responsibility_total | -0.2254 | 0.0207 | 48 | Controls perceived_intelligence, char_len, identity_label. |
| domain | 风险决策 | process_accountability | -0.1037 | 0.2655 | 48 | Controls perceived_intelligence, char_len, identity_label. |

## 10. 初步方法学判断

- 若 process_condition 在控制 perceived_intelligence 后仍对 free_will_attribution、agency 或 responsibility 有明显影响，说明结果不完全由“看起来更聪明”解释。
- 若 process_condition 在控制 char_len 后仍成立，说明结果不完全由“文本更长”解释。
- 若 `direct_choice_long` 的均值接近或高于理由条件，说明长度混淆仍然严重；若 `reasons_concise` 高于 `direct_choice_long`，则更支持结构线索解释。
- 若 perceived_intelligence 的控制使 process_condition 效应大幅下降，需进一步拆分“理由响应性”和“推理能力/聪明程度”。
- 若 identity_label 仍强烈影响 experience 或 free_will_attribution，需要在正式研究中考虑身份标签前测、操纵强度和测量等价性。

## 11. 是否支持修正后的理论

修正理论是：“单纯候选生成不足以提高自由意志归因，理由权衡与反思反馈才是关键线索。”

本轮 `n-per-cell=5` 只能作为小样本流程验证。判断时应重点看：

1. `alternatives` 相对 `direct_choice` 在 free_will_attribution 上是否较弱或不稳定；
2. `reasons_concise` 相对 `direct_choice_long` 是否仍更高；
3. 控制 perceived_intelligence 与 char_len 后，process_condition 是否仍有方向一致的残余效应。

如果三点同时成立，才能说模拟预演方向支持修正理论；否则应继续修订材料，不应扩大样本量。

## 12. 结论边界

本阶段是 LLM-simulated respondents 的材料预演和流程验证，不是正式心理学实验，不可替代真实被试，不可用于证明 AI 具有自由意志。
