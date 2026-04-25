# Codex → ChatGPT 交接文档

## 当前项目目标

项目定位为：

一个心理学 + 哲学 + AI 交叉方向的研究原型，用 LLM-simulated respondents 预演一个关于 AI Agent 决策过程、agency 知觉与自由意志归因的实验设计。

当前目标不是写正式期刊论文，而是整理作品集、项目展示和研究想法证明材料。

## 已完成文件

核心结果与报告：

- `outputs/n30_stability_replication_report.md`
- `outputs/final_simulated_pilot_report.md`
- `docs/paper_draft_simulated_study.md`
- `docs/project_showcase_summary.md`

方法与测量边界：

- `docs/measurement_plan.md`
- `docs/scale_source_mapping.md`
- `outputs/measurement_and_construct_revision_report.md`
- `outputs/method_revision_report.md`

本轮作品集材料：

- `docs/portfolio_research_case.md`
- `docs/project_one_page_summary.md`
- `docs/interview_explanation_script.md`
- `docs/research_design_blueprint.md`
- `docs/codex_to_chatgpt_handoff.md`

## 当前最佳结果

基于 n-per-cell = 30 的 LLM-simulated respondents 稳定性复核：

- 总记录数 360。
- JSON/API 失败数 0。
- 每个 6 × 2 cell 均为 30 条记录。
- factual manipulation check 稳定。
- agency 是最稳定的主结果。
- 控制 perceived_intelligence 和 char_len 后，process_condition 对 agency 仍显著。
- free_will_attribution 的直接 process 效应不稳定。
- agency 的间接中介路径稳定。
- perceived_intelligence 没有解释主要间接效应。
- `alternatives` 不足以提高 agency 或 free_will_attribution。
- `reasons_concise` 高于 `direct_choice_long`，说明理由结构不是单纯长度效应。
- `reflection_feedback` 稳定提高 agency，但对 free_will_attribution 的直接提升不稳定。
- responsibility 不稳定，只作为探索性结果。

## 不能夸大的点

请不要写：

- “证明 AI 有自由意志”
- “AI 替代人类被试”
- “本研究获得正式心理学结论”
- “量表已验证有效”
- “中介机制已被证明”

推荐写法：

- “模拟预实验趋势”
- “材料与模型诊断”
- “LLM-simulated respondents”
- “研究原型”
- “后续仍需真实被试验证”
- “为真实人类被试研究提供前期依据”

## 需要 ChatGPT 后续润色的重点

1. 压缩 AI 味，让语言更像一个真实项目展示。
2. 改成作品集语言，减少论文腔。
3. 补充更自然的项目叙事，突出“我为什么做、怎么做、发现了什么”。
4. 把技术流程讲得 HR、导师和面试官都能看懂。
5. 保留研究边界，不把模拟结果写成正式心理学结论。
6. 产出最终可放进个人网站、GitHub README 或作品集 PDF 的版本。

## 推荐最终叙事主线

可以围绕这条线展开：

我把一个抽象的哲学问题转化为心理学实验原型，设计了 6 × 2 的 AI Agent 决策过程材料，用 LLM-simulated respondents 做模拟预实验，验证材料是否可区分、理论路径是否有初步趋势，并明确指出它不能替代真实被试。这个项目展示的是研究建模、实验设计、AI API 数据流程和边界意识。

## 后续人工修改建议

- 根据目标场景调整长度：个人网站可以更短，作品集 PDF 可以保留更多细节。
- 如果面向心理学导师，可以保留理论模型和测量边界。
- 如果面向 AI 产品岗位，可以强调 Agent 解释设计、人机信任和责任界面。
- 如果面向数据分析岗位，可以强调 API 管线、数据清洗、控制回归、计划对比和中介分析。
