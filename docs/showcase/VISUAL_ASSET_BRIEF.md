# Visual Asset Brief

> 展示页新增插图的规范占位说明（SITE-005）。用于后续交给生图工具或用 SVG 手工实现。
> 纪律：页面中占位块 ≤ 3；不显示破损图片；每个占位用唯一 ID 并与页面 `data-visual-id` 对应；
> 能用 HTML/CSS/原生 SVG 表达的优先不生图；不要求生图模型渲染大量细小中文文字。
> 生成后需回填 `PUBLIC_ASSET_INVENTORY.md`；`public_release_status` 保持 `pending_user_approval`。

SITE-005.1 更新：VIS-002、VIS-003 已用原生网页可视化替换，页面**不再有任何 "Visual asset pending" 占位**。
SITE-005.2 更新：VIS-001 已由用户提供的研究问题概念图接入 Research Question 栏目（本地预览）；页面已无任何占位。

---

## VIS-001 · 研究问题概念图（用户提供，已接入本地预览）

- 状态：`provided_and_integrated_for_local_preview`。
- 用户提供文件名：`fcdb0f90-6a14-4e45-9412-9b6325cf17a3.png`（仓库根目录临时副本，导入并校验后已删除）。
- 规范站点路径：`site/assets/figures/attribution-research-concept.png`。
- 实际尺寸：1586 × 992（宽高比 1.5988 ≈ 8:5）。
- SHA-256：`FFCC3139FD2FBE71CC9049F06CF718BBBFBB6C56E2BF37210C8268FF702BC7F7`。
- 页面位置：Research Question 栏目（研究缘起/比较内容 之后，三个核心问题 之前），桌面左文右图。
- alt：`AI 决策系统与人类决策者经过不同决策过程后，被模型评估其能动性、自由意志归因和责任归因的概念示意`。
- caption：概念图展示本研究的比较结构：同一类决策过程分别与 AI 和人类身份标签组合，再观察模型如何作出能动性、自由意志和责任归因。该图只用于解释研究结构，不承载统计结果。
- 图下三项图例（HTML/CSS，不写入图片像素）：决策主体（AI / 人类）、过程描述（六种结构）、归因输出（模型评分）。
- 集成日期：2026-07-14。
- local preview：已批准（approved）。
- public release：仍待用户批准（pending_user_approval）。
- 边界：该图片不承担统计证据，不计入三张历史结果图；未修改任何像素（源/目标 SHA-256 一致）。

## VIS-002 · 决策过程结构梯度示意（页面已放置）

- 页面位置：Research Question 栏目，三个核心问题卡之后（`data-visual-id="VIS-002"`）。
- 建议图名：`process_structure_gradient`。
- 主要用途：直观呈现六类过程从“只报结论”到“理由 + 反思 + 修正”的结构递增。
- 为什么现有资产不能满足：`outputs/plots/` 全是结果均值图，没有“材料结构梯度”这类方法示意图。
- 类型：结构图 / 概念插图。
- 建议尺寸：1600×640；宽高比 5:2。
- 建议配色：单色蓝阶（浅到深表示结构增强），中性灰底。
- 必须包含的信息：六个从左到右逐级“变厚/变复杂”的结构块；表达“结构递增”而非“更长”。
- 禁止包含的信息：任何统计结论、均值数字、AI 拥有意识的暗示。
- alt 文案：决策过程结构梯度概念插图（占位，尚未生成）。
- caption 草稿：从直接选择到反思反馈——决策过程结构逐级增强的示意。
- 生图提示词：`Clean instructional diagram, six blocks left to right increasing in internal structure and layering, monochrome blue gradient from light to dark, neutral gray background, thin outlines, no dense text, at most short single-word labels rendered as placeholders, flat vector, 5:2.`
- 是否可由 Mermaid/SVG 代替：可（推荐最终用 SVG，文字由 HTML 叠加）。
- 当前状态：`resolved_with_native_web_visual`——已由 `site_summary.design.process_conditions` 驱动的原生 Process Structure Gradient 替换，`direct_choice_long` 标为 length-control diagnostic；不再需要生图。

## VIS-003 · 中介路径结构图（页面已放置）

- 页面位置：Historical Results 栏目，图表区之后（`data-visual-id="VIS-003"`）。
- 建议图名：`mediation_path_structure`。
- 主要用途：呈现“过程 → 行动者感 → 自由意志归因”的路径关系，并标注为探索性。
- 为什么现有资产不能满足：仓库无路径图；`parallel_mediation_summary.json` 只有数值，无结构图。
- 类型：结构图。
- 建议尺寸：1400×760；宽高比 ~16:9。
- 建议配色：站点强调蓝为主，间接路径用较浅描边；探索性标签用琥珀色。
- 必须包含的信息：三个节点（过程 / 行动者感 / 自由意志）与有向连线；明显的“Exploratory”标注。
- 禁止包含的信息：因果断言措辞、具体系数数字、机制证明暗示。
- alt 文案：过程到行动者感到自由意志的中介路径结构图（占位，尚未生成）。
- caption 草稿：探索性路径：过程 → 行动者感 → 自由意志归因（非机制证明）。
- 生图提示词：`Simple path diagram, three labeled nodes left to center to right with directional arrows, an explicit "exploratory" tag, site blue accent with light secondary strokes, lots of whitespace, no coefficients, no numbers, flat vector, 16:9.`
- 是否可由 Mermaid/SVG 代替：可（强烈建议用原生 SVG 实现，避免生图的文字问题）。
- 当前状态：`resolved_with_native_svg_or_html`——已由原生 HTML/CSS Exploratory Path Diagram 替换，展示主/次路径的间接效应估计、置信区间与是否跨 0，并标注 Exploratory、非机制证明；不再需要生图。
