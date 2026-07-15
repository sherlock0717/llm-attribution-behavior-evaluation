# 测量与信效度计划

当前测量采用基于既有理论与量表构念进行情境化改写的归因题项池，主要用于任务材料、计分流程和构念关系的预演。

## 当前模拟阶段主模型

当前模拟阶段的主模型是：

`process_condition -> agency -> free_will_attribution`

其中 `process_condition` 使用 6 个条件，并通过 dummy coding、材料长度诊断条件和控制回归检查结构效应是否独立于文本长度。

`perceived_intelligence` 不是普通控制变量，而是竞争中介。分析中需要同时检查：

- `process_condition -> agency -> free_will_attribution`
- `process_condition -> perceived_intelligence -> free_will_attribution`

如果 perceived_intelligence 路径更强，结论应改为：“决策结构可能通过提升感知智能，从而提高自由意志归因。”

## 构念来源

各构念来源如下，完整参考文献与逐题映射见 `docs/research_and_measurement_sources.md` 与 `docs/scale_source_mapping.md`。

- 心智知觉（Gray, Gray, & Wegner, 2007）：对应 agency / experience，参考其心智知觉二维框架，改写为对情境中决策者的能动性与体验性评分。
- 自由意志归因（Nadelhoffer 等, 2014，FWI；Paulhus & Carey, 2011，FAD-Plus）：对应 free_will_attribution，参考自由意志、替代可能性与决定论构念，将一般信念题项改写为对具体决策者的情境化归因。
- 自主性与行动控制（自主性 / 行动控制相关理论背景）：对应 autonomy，作为一般理论背景情境化编写，暂无直接采用的完整量表。
- 理由响应性与责任（Fischer & Ravizza, 1998）：对应 responsibility，作为道德责任理论背景，拆分为 outcome_accountability、moral_praise_blame、process_accountability。
- 感知智能（Bartneck 等, 2009，Godspeed）：对应 perceived_intelligence，参考 perceived intelligence 维度，改写为对文本决策者的评价。
- 自编操纵检验（本研究自编）：对应 factual_manipulation_check / subjective_process_completeness，根据六种过程条件自行编写。

## 责任归因边界

责任归因当前只作为探索性结果，不作为主结论变量。责任归因容易受 `choice_valence`、结果好坏、道德赞责、后果严重性和归责对象差异影响。因此报告中必须分别查看：

- `outcome_accountability`
- `moral_praise_blame`
- `process_accountability`
- `responsibility_total`

如果这些子维度方向不一致，应明确写明：责任归因不作为当前主结论变量，仅作为探索性结果。

## 后续测量验证

由于题项对象、语境和计分方式经过改写，当前内部一致性只用于检查题项响应是否稳定。正式使用前仍需通过内容效度、因素结构、区分效度和测量等价性检验。

## 正式研究所需步骤

1. 专家内容效度评估。
2. 真实被试预测试。
3. Cronbach alpha / McDonald omega。
4. EFA / CFA。
5. 区分效度检验，尤其区分 agency、perceived_intelligence、autonomy 和 responsibility。
6. AI / 人类标签下的测量等价性。
7. 操纵检验，区分事实性检查和主观过程完整度。

本阶段用于材料与流程预演，正式结论仍需真实被试研究支持。
