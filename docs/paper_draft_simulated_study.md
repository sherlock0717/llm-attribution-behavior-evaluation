# 决策过程结构对自由意志归因的影响：基于 LLM 模拟被试的材料预演研究

## 摘要

本研究使用 LLM-simulated respondents 对一项心理学、哲学与 AI 交叉实验进行模拟预演。研究操纵决策过程结构和决策者身份标签，考察观察者对 agency、自由意志归因、感知智能和责任归因的评分模式。当前设计为 6 × 2：direct choice、direct choice long、alternatives、reasons concise、reasons、reflection feedback × AI / 人类决策者。n-per-cell=30 的稳定性复核显示，事实性操纵检验稳定，agency 是最稳健的主结果。控制 perceived intelligence 与文本长度后，process condition 对 agency 仍显著；free will attribution 的直接效应不稳定，但 agency 的间接中介路径稳定。perceived intelligence 未解释主要间接效应。责任归因结果不稳定，仅作为探索性结果。本研究不是真实人类被试研究，不能证明 AI 具有自由意志，也不能替代正式心理测量信效度检验。

## 关键词

agency；自由意志归因；理由响应性；LLM-simulated respondents；mind perception；感知智能

## 引言

当观察者评价一个决策者时，最终选择并不是唯一信息。决策者是否生成候选方案、是否权衡理由、是否根据反馈调整行动，可能影响观察者对其 agency 和自由意志的归因。随着 AI Agent 被越来越多地描述为“会决策”的系统，理解人们如何根据 AI 的决策过程赋予心智属性，成为心理学、哲学和 AI 研究的交叉问题。

本研究不试图回答 AI 是否真的拥有自由意志。相反，它关注观察者如何进行自由意志归因，以及材料中的决策过程结构是否会改变这种归因。

## 理论基础

本研究参考 mind perception 中 agency 与 experience 的区分。Agency 指行动控制、计划、理由响应和行为修正等能力；experience 指痛苦、恐惧、愉悦等体验能力。自由意志归因参考 FWI / FAD-Plus 中自由意志、替代可能性和决定论相关构念，但题项均被改写为对材料中决策者的情境化归因。

理由响应性理论认为，一个行为者是否能够根据理由改变行动，是责任和自由意志归因的重要线索。本研究因此预测，理由权衡与反思反馈比单纯候选生成更能提升 agency 知觉，并通过 agency 影响自由意志归因。

## 研究假设

H1：决策过程结构越完整，factual manipulation check 与 subjective process completeness 越高。

H2：理由权衡与反思反馈比直接选择和单纯候选生成更能提高 agency。

H3：process condition 对 free will attribution 的影响主要通过 agency 间接发生。

H4：perceived intelligence 是竞争中介；若其路径强于 agency，则理论解释应转向“感知智能”路径。

H5：责任归因受结果价向和道德评价影响，当前阶段仅作探索性分析。

## 方法

### 设计

实验为 6 × 2 设计。过程条件包括 `direct_choice`、`direct_choice_long`、`alternatives`、`reasons_concise`、`reasons`、`reflection_feedback`。身份标签包括 `AI 决策者` 和 `人类决策者`。

### 材料

材料覆盖多个决策情境，并控制最终选择不总是更道德或更负责。`direct_choice_long` 用于诊断文本长度效应，`reasons_concise` 用于诊断理由结构是否能独立于长度发挥作用。

### 测量

题项包括 agency、experience、free_will_attribution、autonomy、perceived_intelligence、factual_manipulation_check、subjective_process_completeness，以及拆分后的 responsibility 子维度。当前题项池不是正式成熟量表，不能继承原量表信效度。

### 模拟流程

使用 DeepSeek API 生成 LLM-simulated respondents。每个模拟参与者只阅读一个材料并完成评分。稳定性复核采用 n-per-cell=30，总记录数 360。

## 结果

### 数据质量

总记录数为 360，每个 6 × 2 cell 为 30。JSON/API 失败为 0，缺失值为 0。factual check 均在 0-2，其他题项均在 1-7。

### 操纵检验

factual manipulation check 从 `direct_choice=0.094` 与 `direct_choice_long=0.011` 上升到 `reflection_feedback=2.000`。这表明材料结构在模拟被试中可被稳定区分。

### 核心结果

agency 随决策过程结构增强而上升。控制 perceived_intelligence 和 char_len 后，process condition 对 agency 仍显著，F=12.189，p<.001。

free_will_attribution 的直接 process 效应不稳定，控制后 p=.616。但计划对比显示，`reasons_concise` 高于 `direct_choice_long`，`reflection_feedback` 高于 `direct_choice_long`。

### 并行中介

agency 的间接效应为 0.2699，95% CI [0.1985, 0.3507]。perceived_intelligence 的间接效应为 0.0184，95% CI [-0.0068, 0.0442]。perceived_intelligence 未解释主要间接效应。

### 责任归因

responsibility_total 和子维度结果不稳定。责任归因不作为当前主结论变量，仅作为探索性结果。

## 讨论

本模拟预实验支持这样一种趋势：单纯候选生成不足以提高自由意志归因；理由权衡与反思反馈更可能通过提升 agency 知觉影响自由意志归因。文本长度本身不能充分解释结果，因为 `reasons_concise` 高于 `direct_choice_long`。

与此同时，free_will_attribution 的直接 process 效应并不稳定，说明自由意志归因可能不是直接由结构线索触发，而是经由 agency 等中介构念间接变化。

## 局限与展望

本研究是 LLM-simulated respondents 的模拟预实验，不是真实人类被试研究。LLM 可能受提示结构、语言模式和实验意图推断影响。当前题项池也不是正式心理测量量表，仍需真实被试检验信效度。

后续研究应开展真实被试预测试，检验量表结构、测量等价性、区分效度和操纵检验稳定性。

## 结论

本模拟预实验显示，决策过程结构可稳定影响 agency 知觉，并通过 agency 间接影响自由意志归因。perceived_intelligence 未解释主要间接效应。责任归因结果不稳定，应作为探索性结果处理。所有结论均限于模拟预实验趋势，不能被解释为正式心理学结论或 AI 具有自由意志的证据。
