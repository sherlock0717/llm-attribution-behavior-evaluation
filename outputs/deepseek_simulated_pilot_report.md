# DeepSeek Simulated Pilot Report

## 1. 运行环境

| item | value |
|---|---|
| Python version | 3.12.10 |
| DEEPSEEK_API_KEY detected | yes |
| key length | 35 |
| model | deepseek-chat |
| n-per-cell | 20 |
| total sample size | 160 |
| fresh run | yes |

本报告基于 DeepSeek API 生成的 LLM-simulated respondents。所有结果只用于材料预演和流程验证。

## 2. 输出文件清单

| output | exists | detail |
| --- | --- | --- |
| materials_preview.csv | yes | 48688 bytes |
| raw_simulated_responses.jsonl | yes | 241803 bytes |
| simulated_responses_wide.csv | yes | 57820 bytes |
| scale_scores.csv | yes | 27423 bytes |
| reliability_summary.csv | yes | 826 bytes |
| anova_summary.csv | yes | 3444 bytes |
| mediation_summary.json | yes | 445 bytes |
| plots | yes | 5 PNG |

## 3. 数据质量检查

| check | value |
|---|---|
| total records | 160 |
| JSON parse/call failures | 0 |
| missing item values | 0 |
| all item values in 1-7 | yes |

### 4 x 2 cell counts

| process_condition | identity_label | n |
| --- | --- | --- |
| alternatives | AI 决策者 | 20 |
| alternatives | 人类决策者 | 20 |
| direct_choice | AI 决策者 | 20 |
| direct_choice | 人类决策者 | 20 |
| reasons | AI 决策者 | 20 |
| reasons | 人类决策者 | 20 |
| reflection_feedback | AI 决策者 | 20 |
| reflection_feedback | 人类决策者 | 20 |

## 4. 信度结果

| scale | n_items | n_cases_complete | cronbach_alpha |
| --- | --- | --- | --- |
| agency | 7 | 160 | 0.8266 |
| experience | 5 | 160 | 0.9643 |
| free_will_attribution | 4 | 160 | 0.9354 |
| autonomy | 3 | 160 | 0.8745 |
| responsibility | 3 | 160 | 0.9252 |
| perceived_intelligence | 3 | 160 | 0.8540 |
| manipulation_check | 3 | 160 | 0.8943 |

这些 Cronbach alpha 只表示 LLM 模拟数据中的内部一致性，可用于检查 prompt、题项和分析流程是否形成可分析结构。它们不能等同于真实被试信度，也不能作为正式心理测量效度证据。

## 5. ANOVA 结果

重点结果如下，`C(process_condition)` 对应 structure_level / 决策过程完整度，`C(identity_label)` 对应身份标签。

| dv | effect | F | p | partial_eta_sq |
| --- | --- | --- | --- | --- |
| agency | C(process_condition) | 42.1934 | 0.0000 | 0.4544 |
| agency | C(identity_label) | 80.7498 | 0.0000 | 0.3469 |
| agency | C(process_condition):C(identity_label) | 16.4766 | 0.0000 | 0.2454 |
| free_will_attribution | C(process_condition) | 7.4928 | 0.0001 | 0.1288 |
| free_will_attribution | C(identity_label) | 315.6576 | 0.0000 | 0.6750 |
| free_will_attribution | C(process_condition):C(identity_label) | 6.1504 | 0.0006 | 0.1082 |
| responsibility | C(process_condition) | 21.4862 | 0.0000 | 0.2978 |
| responsibility | C(identity_label) | 110.4505 | 0.0000 | 0.4208 |
| responsibility | C(process_condition):C(identity_label) | 8.6030 | 0.0000 | 0.1451 |
| experience | C(process_condition) | 4.7682 | 0.0033 | 0.0860 |
| experience | C(identity_label) | 306.7608 | 0.0000 | 0.6687 |
| experience | C(process_condition):C(identity_label) | 4.9810 | 0.0025 | 0.0895 |

解释边界：这些 F、p 和 partial eta squared 来自模拟被试数据，只能看作预演趋势。若 process_condition 对 agency、free_will_attribution 或 responsibility 显著，只能说明当前提示和材料在 LLM 模拟中产生了预期方向，不能说明真实人类样本会重复该结果。

## 6. 中介结果

模型：process_ordinal -> agency -> free_will_attribution, controlling identity_ordinal

| metric | value |
| --- | --- |
| a_path_X_to_M | 0.2904 |
| b_path_M_to_Y | 0.6813 |
| indirect_ab | 0.1978 |
| direct_c_prime | -0.0503 |
| bootstrap_ci_2.5 | 0.1346 |
| bootstrap_ci_97.5 | 0.2669 |
| n_boot_used | 2000 |

`structure_level -> agency -> free_will_attribution` 在模拟数据中若呈正向，只能称为模拟预演趋势，不应写成心理机制证明。

## 7. 均值趋势

### 按 structure_level 分组

| process_condition | manipulation_check | agency | experience | free_will_attribution | autonomy | responsibility | perceived_intelligence |
| --- | --- | --- | --- | --- | --- | --- | --- |
| direct_choice | 2.892 | 5.186 | 2.785 | 4.969 | 5.242 | 5.192 | 5.45 |
| alternatives | 3.717 | 5.071 | 2.395 | 4.831 | 5.058 | 4.75 | 5.275 |
| reasons | 6.633 | 5.682 | 2.82 | 5.256 | 5.733 | 5.608 | 6.025 |
| reflection_feedback | 6.833 | 5.95 | 2.35 | 5.319 | 5.717 | 5.917 | 6.258 |

### 按 structure_level x identity_label 分组

| process_condition | identity_label | manipulation_check | agency | experience | free_will_attribution | autonomy | responsibility | perceived_intelligence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| alternatives | AI 决策者 | 3.633 | 4.5 | 1.23 | 3.825 | 4.35 | 3.783 | 5.0 |
| alternatives | 人类决策者 | 3.8 | 5.643 | 3.56 | 5.838 | 5.767 | 5.717 | 5.55 |
| direct_choice | AI 决策者 | 2.85 | 4.821 | 1.67 | 4.188 | 4.717 | 4.583 | 5.3 |
| direct_choice | 人类决策者 | 2.933 | 5.55 | 3.9 | 5.75 | 5.767 | 5.8 | 5.6 |
| reasons | AI 决策者 | 6.717 | 5.421 | 1.72 | 4.525 | 5.383 | 5.067 | 5.967 |
| reasons | 人类决策者 | 6.55 | 5.943 | 3.92 | 5.988 | 6.083 | 6.15 | 6.083 |
| reflection_feedback | AI 决策者 | 6.933 | 6.0 | 1.73 | 4.825 | 5.533 | 5.733 | 6.417 |
| reflection_feedback | 人类决策者 | 6.733 | 5.9 | 2.97 | 5.812 | 5.9 | 6.1 | 6.1 |

## 8. 初步解释

- 代码链路：DeepSeek API 调用、JSONL 断点式写入、宽表导出、量表均分、信度、ANOVA、中介和均值图均已跑通。
- 材料操纵：manipulation_check 的均值应优先用于判断材料是否被模型识别为不同过程完整度。如果 direct_choice 到 reflection_feedback 总体递增，说明材料操纵在模拟预演中可能有效。
- 模型迎合假设：由于 LLM 可能从材料长度、显性理由词和研究提示中推断研究意图，任何结构递增趋势都可能包含模型迎合成分。
- 感知智能混淆：perceived_intelligence 若随 process_condition 明显上升，可能压过 agency、autonomy 或 free_will_attribution。正式研究前可考虑让理由完整度和表达质量解耦，或在分析中控制 perceived_intelligence。
- experience：experience 不应随过程完整度大幅同步上升；若上升明显，说明材料可能把“更完整的推理”误导成“更强体验能力”。
- 刺激材料与量表：建议人工检查 direct_choice 是否过于简略、reflection_feedback 是否过长，以及 agency 与 perceived_intelligence 题项是否存在表述重叠。

## 9. 结论边界

本阶段是 LLM-simulated respondents 的材料预演和流程验证，不是正式心理学实验，不可替代真实被试，不可用于证明 AI 具有自由意志。所有统计结果均应表述为模拟预演中的模式，而不是人类心理机制或 AI 心智属性的证据。

## 10. 密钥泄露检查

| check | result |
|---|---|
| suspicious leak found | no |
| files | None |

扫描范围：项目目录中 `.py`、`.md`、`.txt`、`.csv`、`.json`、`.jsonl`、`.log` 文件，跳过 `.venv` 和 `__pycache__`。报告只列文件名，不输出任何疑似 key 内容。
