# Showcase Deferred Refinements

> 本文件只做**登记**，不在本轮继续修改展示页。
> 目的：把展示页已知的文案自然度、内部流程外露、数字图表化等问题，作为**延后任务**记录下来，
> 统一放到 Phase 5（结构化报告层）与 Phase 7（发布阶段）处理，避免现在反复大改页面。
> 纪律：这些改进依赖后续真实结果与结构化报告，**不得现在手工伪造图表或数字**。

## 1. 文案自然度

后续统一处理，使全站作者口吻一致、减少“AI 助手/审核说明”式表达：

- “不研究什么”一节的措辞；
- “能说的 / 不能说的”式对照标题；
- “按你想做的事挑入口”一类导航文案；
- 类似 AI 助手总结或审核说明的表达；
- 边界/限制信息在多个栏目重复；
- 作者口吻不统一（部分第一人称、部分说明书语气）。

## 2. 内部流程不面向公众

明确以下内容属于**内部项目管理结构**，不应作为最终公开页面的正式内容：

- Phase 1～7；
- Track S；
- SITE / FND / RES / RUN 等任务编号。

最终公开页应替换为**简化演进叙事**：

- Historical research baseline；
- Current engineering foundation；
- Reproducible execution；
- Multi-model evaluation；
- Public benchmark maturity。

当前暂不大修，待 Phase 5 报告层和 Phase 7 发布阶段统一处理。

## 3. 数字图表化

后续将文本和数字替换或补充为结构化图形：

- 效应值和置信区间图；
- 身份标签差异图；
- 条件均值图；
- 重复运行稳定性图；
- 模型对比图；
- parse / schema 质量图；
- token / cost / latency 图；
- provenance completeness 图。

这些图必须由 Phase 5 的结构化报告生成，**不得现在手工伪造**。

## 4. 最终页面清理时机

统一放在：

- Phase 5 报告层完成后；
- BMK-L1 有正式结果后；
- Phase 7 发布前。

## 5. 浏览器运行时与移动端自动验证（deferred validation）

**Browser runtime and 390px automated layout validation deferred to Phase 7 release validation.**

说明：

- 展示页运行时修复目前依赖**静态 DOM slot 契约测试**（slot 存在性、`requireSlot` 使用、渲染链路完整）与本地 HTTP smoke 验证；
- 浏览器级 JavaScript 渲染验证（`data-render-complete`、load-error 隐藏、figure/path/version 计数）与 390px `document.scrollWidth <= clientWidth` 的**自动读取**本轮未执行；
- 该验证统一登记为 deferred validation，留到 **Phase 7 发布验证**处理，届时随 GitHub Pages 发布验证一并完成。

明确**不声称**：

- 浏览器视觉验证已通过；
- 移动端自动布局验证已通过；
- GitHub Pages 页面已验证。

该项**不作为**当前展示页本地里程碑人工提交的阻断条件。
