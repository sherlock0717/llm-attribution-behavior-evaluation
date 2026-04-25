# 一页看懂项目

## 项目一句话

这是一个心理学 + 哲学 + AI 交叉方向的研究原型：我用 LLM-simulated respondents 预演一个关于 AI Agent 决策过程、agency 知觉与自由意志归因的实验设计。

## 研究问题

- AI 展示更完整的决策过程时，人们是否更容易把它看成有 agency？
- 自由意志归因是否主要通过 agency 发生？
- 这种效果是否只是因为文本更长，或者 AI 看起来更聪明？

## 设计图文字版

```text
6 个决策过程条件 × 2 个身份标签

direct_choice
direct_choice_long
alternatives
reasons_concise
reasons
reflection_feedback

×

AI 决策者 / 人类决策者
```

`direct_choice_long` 用来检查长度混淆。  
`reasons_concise` 用来检查理由结构是否在短文本中仍然有效。

## 数据流程

```text
材料生成 → DeepSeek 模拟被试 → JSONL 原始回答
→ 量表得分 → 操纵检查 → 控制分析
→ 计划对比 → 并行中介 → 报告输出
```

## 主要发现

基于 n-per-cell = 30 的模拟预实验：

- 总样本量为 360。
- JSON/API 失败数为 0。
- factual manipulation check 稳定。
- agency 是最稳定的核心结果。
- 控制 perceived_intelligence 和 char_len 后，process_condition 对 agency 仍显著。
- free_will_attribution 的直接效应不稳定，但 agency 间接路径稳定。
- perceived_intelligence 没有解释主要间接效应。
- 单纯列出 alternatives 不足以提高 agency 或 free_will_attribution。
- `reasons_concise` 高于 `direct_choice_long`，说明结果不是单纯文本长度效应。
- responsibility 结果不稳定，当前只作为探索性结果。

## 研究边界

这是作品集展示、研究想法证明和 LLM 模拟预实验。

它不是正式人类被试研究，不能证明 AI 有自由意志，也不能替代正式心理学信效度检验。当前题项池需要在真实被试中重新验证。

## 作品集价值

这个项目展示了我如何把一个抽象问题转化为可执行研究原型：提出理论问题、设计实验材料、构建变量、调用 LLM API、搭建分析管线，并在结果解释中保留清晰的方法学边界。
