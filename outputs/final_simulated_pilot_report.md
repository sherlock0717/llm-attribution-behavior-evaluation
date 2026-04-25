# LLM 模拟预实验最终报告

## 1. 研究背景

人们如何根据一个决策者的“决策过程”来归因其 agency、自由意志和责任，是心理学、哲学与 AI 交叉研究中的重要问题。对于 AI Agent 而言，观察者可能不仅关注最终选择，也会关注它是否展示了候选方案、理由权衡、反思反馈和后续修正。

## 2. 研究问题

本模拟预实验关注：不同决策过程结构是否会影响观察者对 AI / 人类决策者的 agency 知觉与自由意志归因。核心问题是：单纯列出候选方案是否足够，还是理由权衡与反思反馈才是更关键的线索。

## 3. 理论框架

本项目参考 mind perception 中 agency / experience 的区分、FWI / FAD-Plus 中自由意志相关构念、理由响应性理论、责任归因理论和 Godspeed perceived intelligence 维度。当前主模型是：

`process_condition -> agency -> free_will_attribution`

同时把 `perceived_intelligence` 作为竞争中介，而不只是普通控制变量。

## 4. 当前研究定位

本研究是 LLM-simulated respondents 的模拟预实验。目的为材料预演、理论模型诊断和分析流程验证。它不是真实人类被试研究，不能证明 AI 具有自由意志，不能替代正式心理学信效度检验。

## 5. 实验设计：6 × 2

过程条件：

- `direct_choice`
- `direct_choice_long`
- `alternatives`
- `reasons_concise`
- `reasons`
- `reflection_feedback`

身份标签：

- `AI 决策者`
- `人类决策者`

`direct_choice_long` 和 `reasons_concise` 是诊断条件，用于区分文本长度效应与决策结构效应。

## 6. 材料与条件

材料覆盖道德冲突、自我控制、人际关系、风险决策、责任困境、服从与自主等情境，并加入 positive / mixed / negative choice valence，避免所有最终选择都显得更道德或更负责。

事实性操纵检验显示模型能区分 6 类材料：`direct_choice=0.094`，`direct_choice_long=0.011`，`alternatives=1.011`，`reasons_concise=1.617`，`reasons=1.939`，`reflection_feedback=2.000`。

## 7. 测量与题项来源边界

当前题项是基于既有理论与量表构念的情境化归因题项池，不是正式成熟量表。LLM 模拟数据中的 alpha 只能作为流程检查，不能作为正式信度证据。正式研究必须使用真实被试重新检验内容效度、预测试、omega / alpha、EFA / CFA、区分效度和测量等价性。

## 8. LLM 模拟被试流程

使用 DeepSeek API 模拟问卷参与者。每个模拟参与者只阅读一个材料并完成题项评分。最终稳定性复核采用 `n-per-cell=30`，总样本量为 360。

## 9. 数据质量

- 总记录数：360
- 每个 6 × 2 cell：30
- JSON/API 失败：0
- 缺失值：0
- factual check 全部在 0-2
- 其他题项全部在 1-7

## 10. 操纵检查

factual manipulation check 稳定。`direct_choice` 与 `direct_choice_long` 接近 0，后续条件总体递增，说明 6 类决策过程材料可被模型区分。

subjective process completeness 同样随结构增强而上升：从 `direct_choice_long=3.228` 到 `reflection_feedback=5.567`。

## 11. 核心结果

agency 是最稳定的主结果。按条件均值：

- `direct_choice`: 4.308
- `direct_choice_long`: 3.942
- `alternatives`: 4.250
- `reasons_concise`: 4.433
- `reasons`: 4.583
- `reflection_feedback`: 5.200

同时控制 `perceived_intelligence` 和 `char_len` 后，`process_condition -> agency` 仍显著，F=12.189，p<.001。

free_will_attribution 的直接 process 效应不稳定：控制 `perceived_intelligence` 和 `char_len` 后，F=0.711，p=.616。但计划对比显示 `reasons_concise` 高于 `direct_choice_long`，`reflection_feedback` 高于 `direct_choice_long`。

单纯 `alternatives` 不足以提高 agency 或 free_will_attribution；`alternatives` 与 `direct_choice` 的差异接近 0。

## 12. 并行中介结果

并行中介显示：

- agency indirect = 0.2699，95% CI [0.1985, 0.3507]
- perceived_intelligence indirect = 0.0184，95% CI [-0.0068, 0.0442]
- absolute intelligence indirect share = 0.0638

agency 的间接中介路径稳定。perceived_intelligence 并未解释主要间接效应。

## 13. 责任归因探索性结果

责任归因拆分为 outcome_accountability、moral_praise_blame、process_accountability 与 responsibility_total。结果方向不如 agency 稳定。

同时控制 perceived_intelligence 和 char_len 后，responsibility_total 显著，但 process_accountability 不显著。因此责任归因不作为当前主结论变量，仅作为探索性结果。

## 14. 讨论

模拟预实验趋势支持：观察者对决策者 agency 的判断主要受理由结构和反思反馈影响，而不是单纯文本长度。`reasons_concise` 高于 `direct_choice_long`，说明理由结构不是单纯长度效应。`reflection_feedback` 稳定提高 agency，但对 free_will_attribution 的直接提升不稳定。

## 15. 方法学限制

本研究使用 LLM-simulated respondents，不能替代真实人类被试。模型可能迎合提示、利用语言模式推断实验意图，并且不能提供正式心理测量证据。所有结论都只能称为模拟预实验趋势。

## 16. 后续真实人类被试研究方案

后续可使用当前冻结材料开展真实被试预试。建议步骤：

1. 专家内容效度评估。
2. 小样本真实被试预测试。
3. 检查 factual / subjective 操纵检验。
4. 检验 agency、free_will_attribution、perceived_intelligence 的区分效度。
5. 进行正式 6 × 2 实验。
6. 检查 AI / 人类标签下的测量等价性。

## 17. 可引用的核心结论

在 LLM-simulated respondents 的模拟预实验中，6 类决策过程材料可被稳定区分。agency 是最稳定的主结果；控制文本长度和感知智能后，决策过程条件对 agency 仍有显著影响。自由意志归因的直接效应不稳定，但 `process_condition -> agency -> free_will_attribution` 的间接路径稳定。perceived_intelligence 未解释主要间接效应。责任归因结果不稳定，应仅作为探索性结果。
