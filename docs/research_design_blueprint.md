# 研究设计蓝图

## 项目定位

本项目是一个心理学 + 哲学 + AI 交叉方向的研究原型，用 LLM-simulated respondents 预演一个关于 AI Agent 决策过程、agency 知觉与自由意志归因的实验设计。

它用于作品集展示、研究想法证明和模拟预实验，不是正式人类被试研究。

## 理论来源

项目整合了三类理论线索：

- 心智知觉：观察者会从 agency 和 experience 等维度判断一个对象是否“像有心智”。
- 自由意志与责任归因：观察者对自由选择、替代可能性和责任的判断，可能受到理由响应性和行动控制感影响。
- AI Agent 解释设计：AI 如何呈现决策过程，可能影响用户对其能力、控制性和问责性的理解。

## 理论模型

主模型：

```text
process_condition → agency → free_will_attribution
```

竞争解释：

```text
process_condition → perceived_intelligence → free_will_attribution
process_condition → char_len → free_will_attribution
```

核心判断不是“AI 是否真的有自由意志”，而是“观察者在什么条件下更容易做出类自由意志归因”。

## 变量定义

- `process_condition`：决策过程呈现方式。
- `identity_label`：决策者身份标签，AI 或人类。
- `agency`：观察者认为决策者能否行动、控制、根据理由调整行为。
- `free_will_attribution`：观察者对该决策者是否像是在自主选择的情境化归因。
- `perceived_intelligence`：观察者认为决策者是否理解情境、逻辑清楚、判断质量高。
- `experience`：观察者对感受性、体验性的归因。
- `responsibility`：责任归因，拆分为结果责任、道德赞责/责备和过程责任。
- `char_len`：材料文本长度，用于检查长度混淆。

## 6 × 2 设计

6 个决策过程条件：

1. `direct_choice`：只呈现直接选择。
2. `direct_choice_long`：长文本直接选择，不加入真正理由结构。
3. `alternatives`：呈现多个候选行动。
4. `reasons_concise`：短文本中的理由权衡。
5. `reasons`：较完整的理由比较。
6. `reflection_feedback`：理由、反思、反馈或后续修正。

2 个身份标签：

1. AI 决策者
2. 人类决策者

## 决策过程条件解释

`direct_choice` 是最低结构条件，用于提供基线。

`direct_choice_long` 控制文本长度。如果它和高结构条件差异不大，说明可能只是长度效应；如果它仍低于理由条件，说明结构本身有作用。

`alternatives` 检查“只列出选项”是否足够触发 agency。

`reasons_concise` 检查理由权衡是否在较短文本中仍然有效。

`reasons` 呈现更完整的理由比较。

`reflection_feedback` 呈现反思、反馈和修正，是最高结构条件。

## 测量构念

当前使用的是情境化归因题项池，不是完整成熟量表。

主要构念：

- factual manipulation check
- subjective process completeness
- agency
- experience
- free will attribution
- autonomy
- perceived intelligence
- outcome accountability
- moral praise/blame
- process accountability
- responsibility total

责任归因当前只作为探索性结果，因为它容易受到 choice valence、结果好坏和道德评价的影响。

## 模拟被试流程

```text
1. 生成 6 × 2 条件材料
2. 调用 DeepSeek API 作为 LLM-simulated respondents
3. 要求模型按题项输出结构化 JSON
4. 保存 raw_simulated_responses.jsonl
5. 清洗解析并计算量表均分
6. 输出 CSV、图表和分析报告
```

## 统计分析

当前分析包括：

- 数据质量检查
- 每个 cell 样本量检查
- factual check 范围检查
- 其他题项 1-7 范围检查
- 按 process_condition 的均值趋势
- 控制 perceived_intelligence 的回归
- 控制 char_len 的回归
- 同时控制 perceived_intelligence 和 char_len 的回归
- process_condition dummy coding
- 计划对比
- AI / 人类标签分组中介
- agency 与 perceived_intelligence 并行中介
- 按 scenario/domain 的稳健性检查

## 当前结果

基于 n-per-cell = 30 的稳定性复核：

- 总记录数 360。
- JSON/API 失败数 0。
- 每个 6 × 2 cell 均为 30 条记录。
- factual manipulation check 稳定。
- agency 是最稳定的结果。
- 控制 perceived_intelligence 和 char_len 后，process_condition 对 agency 仍显著。
- free_will_attribution 的直接 process 效应不稳定。
- agency 的间接中介路径稳定。
- perceived_intelligence 并未解释主要间接效应。
- `alternatives` 相比 `direct_choice` 不足以提高 agency 或 free_will_attribution。
- `reasons_concise` 高于 `direct_choice_long`，支持理由结构不是单纯长度效应。
- responsibility 结果不稳定，只作为探索性结果。

## 真实被试升级方案

下一阶段建议：

1. 专家评估材料和题项内容效度。
2. 小样本真实被试预测试。
3. 检查题项理解、作答时间和注意力质量。
4. 进行 Cronbach alpha / McDonald omega。
5. 进行 EFA / CFA。
6. 检验 agency、perceived intelligence 和 free will attribution 的区分效度。
7. 检查 AI / 人类标签下测量等价性。
8. 开展正式 6 × 2 人类被试实验。

## 不可夸大的结论

本项目不能证明 AI 有自由意志，不能替代真实人类被试，也不能作为正式心理学信效度证据。

更准确的表述是：当前模拟预实验支持该研究原型继续进入真实被试预测试阶段。
