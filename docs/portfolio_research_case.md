# 大语言模型 Agent 决策结构对自由意志归因的影响：一个心理学 × 哲学 × AI 的模拟研究原型

## 1. 项目一句话

我把“AI 是否像是在自主选择”这个抽象哲学问题，转化成一个可操作的心理学实验原型，并用 DeepSeek 作为 LLM-simulated respondents 完成材料预演、流程验证和理论模型诊断。

## 2. 为什么做这个项目

AI Agent 越来越常以“决策者”“助手”“执行者”的身份出现。它们不只是回答问题，还会比较方案、解释理由、修正计划，甚至承担某些行动后果。

这带来一个很具体的问题：当一个 AI 展示出理由权衡、反思和后果修正时，观察者会不会更容易把它看成一个有 agency 的决策者？进一步说，人们会不会因此更容易对它产生“它像是在自由选择”的归因？

这个问题同时涉及三个方向：

- 心理学：人如何知觉他者的心智、控制感和责任。
- 哲学：自由意志、替代可能性、理由响应性和道德责任。
- AI：Agent 的决策过程如何被呈现，如何影响信任、责任和解释设计。

## 3. 核心研究问题

1. 决策过程越完整，观察者是否越容易归因 agency？
2. 自由意志归因是否主要通过 agency 发生？
3. 这种效果是否只是因为 AI 看起来更聪明，或者材料文本更长？

## 4. 我的设计

项目采用 6 × 2 的模拟实验设计。

6 个决策过程条件：

- `direct_choice`：只给出直接选择。
- `direct_choice_long`：文本长度接近复杂条件，但不增加真正的理由权衡。
- `alternatives`：列出多个可选行动。
- `reasons_concise`：用较短文本呈现清楚的理由权衡。
- `reasons`：呈现较完整的理由比较。
- `reflection_feedback`：加入反思、反馈或后续修正。

2 个身份标签：

- AI 决策者
- 人类决策者

其中两个条件是专门加入的诊断条件：

- `direct_choice_long` 用来排除“只是文本更长”的解释。
- `reasons_concise` 用来检验“短文本中的理由结构”是否仍然有效。

## 5. 我做了哪些工作

- 将自由意志这个抽象问题拆解为可测量的心理学变量。
- 构建 6 × 2 实验材料，并加入长度控制和理由结构诊断条件。
- 设计情境化归因题项池，区分 agency、experience、free will attribution、perceived intelligence 和 responsibility。
- 将 responsibility 进一步拆成 outcome accountability、moral praise/blame 和 process accountability。
- 使用 DeepSeek API 模拟被试作答，生成 JSONL、CSV、图表和 Markdown 报告。
- 编写 Python 分析流程，完成数据清洗、量表均分、操纵检查、控制回归、计划对比和并行中介分析。
- 明确区分 LLM-simulated respondents 与真实人类被试，避免把模拟结果写成正式心理学结论。

## 6. 模拟流程

```text
生成材料
→ DeepSeek 模拟被试
→ 题项评分
→ 数据清洗
→ 量表均分
→ 操纵检查
→ 控制 perceived_intelligence 与 char_len
→ 计划对比
→ 并行中介分析
→ 自动生成报告
```

## 7. 关键结果

基于 n-per-cell = 30 的 LLM-simulated respondents 稳定性复核：

- 总记录数为 360。
- JSON/API 失败数为 0。
- 每个 6 × 2 cell 均为 30 条记录。
- factual manipulation check 稳定，说明 6 类决策过程材料可被模型区分。
- agency 是最稳定的主结果。
- 在同时控制 perceived_intelligence 和 char_len 后，process_condition 对 agency 仍显著。
- free_will_attribution 的直接 process 效应不稳定。
- agency 的间接中介路径稳定。
- perceived_intelligence 没有解释主要间接效应，绝对间接效应占比约为 6.4%。
- `alternatives` 相比 `direct_choice` 不足以提高 agency 或 free_will_attribution。
- `reasons_concise` 高于 `direct_choice_long`，说明理由结构不是单纯长度效应。
- responsibility 结果不稳定，只作为探索性结果。

## 8. 这个结果说明什么

这个模拟预实验提示：AI 决策过程中的“理由响应”和“反思反馈”，可能比单纯列出选项更能触发观察者的类主体感。

观察者对 AI 是否“像在自由选择”的判断，可能并不只是来自最终答案，也不只是来自文本长度或显得聪明，而是来自它是否表现出能根据理由调整行动的 agency。

这对 AI Agent 的解释设计、人机信任和责任界面设计有启发意义：如果一个系统需要被用户理解为“可问责的行动者”，过程呈现方式可能和最终结果同样重要。

## 9. 方法学边界

本项目是作品集展示、研究想法证明和 LLM 模拟预实验，不是正式人类被试研究。

需要明确：

- LLM 模拟被试不能替代真实被试。
- 当前结果只能作为材料预演和理论诊断。
- 当前题项是基于既有理论与量表构念的情境化题项池，不是已验证成熟量表。
- 模拟数据中的信度和中介结果不能作为正式心理学证据。
- 本项目不能证明 AI 具有自由意志。
- 后续仍需真实被试验证材料、信效度和心理机制。

## 10. 后续怎么升级

- 邀请专家进行内容效度评估。
- 进行小样本真实被试预测试。
- 使用 EFA / CFA 检查题项结构。
- 检验 agency、perceived intelligence 和 free will attribution 的区分效度。
- 开展正式 6 × 2 人类被试实验。
- 检查 AI / 人类标签下的测量等价性。
- 根据真实被试结果重新修订材料和题项。

## 11. 可展示的能力

这个项目可以展示以下能力：

- 心理学实验设计
- AI Agent 研究问题建模
- 哲学问题的变量操作化
- 大语言模型 API 调用与数据管线搭建
- Python 数据分析与自动报告生成
- 控制变量、计划对比和中介分析
- 研究边界意识
- 跨学科问题转译能力
