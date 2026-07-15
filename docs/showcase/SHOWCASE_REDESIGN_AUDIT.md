# Showcase Redesign Audit

> SITE-005 修改前审查。分支 `feat/showcase-v1`，起始 HEAD `8fc1d6a7f9678b3bbb707fbb2e70731214163e5d`。
> 本报告完成前不得修改 `site/index.html`、`site/assets/css/site.css`、`site/assets/js/site.js`、`site/data/**`、`docs/showcase/site_manifest.yaml`。
> 审查以本地实际文件为准，截图倾向仅作复核线索。

## 1. 当前页面结构

十个主栏目（`site/index.html`）：

| # | id | 栏目 | 数据来源 | 硬编码在 HTML | 来自 JSON |
|---|---|---|---|---|---|
| 1 | `hero` | Hero | `site_summary.json` | 标题/副标题/状态徽章文字 | version、record-count、design-grid、n-per-cell、provider、metrics |
| 2 | `research-question` | 研究问题 | 无（纯静态文字） | 全部 4 段 | 无 |
| 3 | `experimental-design` | 实验设计 | `site_summary.json` | 6 条件列表、身份标签、诊断说明 | record-count、design-grid、n-per-cell、provider |
| 4 | `pipeline` | 流程 | 无（纯静态） | 8 步有序列表 + Completed/Partial/Planned 三列 | 无 |
| 5 | `historical-results` | 历史结果 | `historical_results.json` | 只有一句来源说明 | claims（7）+ figures（3） |
| 6 | `evidence-limitations` | 证据与局限 | 无（纯静态） | 8 条 `<li>` | 无 |
| 7 | `reproducibility` | 可复现性 | 无（纯静态） | 8 条 `<li>` + CI 说明 | 无 |
| 8 | `version-history` | 版本历史 | `version_history.json` | 无 | versions（3） |
| 9 | `roadmap` | 路线图 | `roadmap.json` | 无 | phases（8）+ track_s（5） |
| 10 | `repository-links` | 仓库链接 | 无（纯静态） | 5 条链接 | 无 |

关键观察：栏目 2/4/6/7/10 完全是静态文字，没有任何结构化/可视化组件；栏目 5 的三张图挤在 `repeat(auto-fit, minmax(280px, 1fr))` 网格里，桌面端被压成小缩略图。

## 2. 当前页面的主要优点

- 数据与文案分离的骨架已经存在：动态数字都走 `data-slot` + `site/data/*.json`，HTML 不含硬编码统计值（`test_no_hardcoded_statistics_in_html` 已约束）。
- 证据边界口径严谨：Historical vs mock、provenance 不完整、单一模型、非人类被试、探索性路径诊断都已写明。
- agency 与 free_will_attribution 的结果已明确分开，计划对比明确标注"数值对应 agency"。
- 无第三方依赖、无 CDN、无 inline onclick，可访问性基础（skip-link、focus-visible、prefers-reduced-motion、alt）已具备。
- 状态系统（Historical/Completed/Current/Planned/Pending verification）已贯通 JSON 与徽章。

这些必须在重构中保留，不能因为改版而破坏。

## 3. 文案问题

逐项引用当前页面表达并说明问题类型。

### 模板化
- `hero` tagline（L41）与 `<meta name="description">`（L7）、manifest `tagline_zh` 三处重复同一句"一个面向可复现研究的大语言模型自由意志归因实验与模型行为评测原型"。这是典型的定位口号，读起来像产品简介而不是作者说明。
- `subtitle`（L42）"通过系统改变"决策过程"的呈现方式，观察……做出行动者感、自由意志与责任归因"——"通过……的方式，观察……"是模板句式，信息密度低。
- 研究问题段（L59）"项目系统改变这种"决策过程"结构，观察它是否……"——"系统改变……观察是否"重复 subtitle 的结构。

### 抽象
- `subtitle` 把三件事（改变过程呈现、观察者角色、三种归因）压进一句长定语，读者 30 秒内抓不到"到底比较什么"。
- Research Question 三个加粗小问句都停留在概念定义，没有落到"具体拿什么材料、比出什么差别"。

### 重复
- 边界声明"AI 模拟数据；非人类被试；单一模型"在页脚（L215）、每张 figure caption（JSON）、每条 claim 的 boundary_note（JSON）反复出现，主页面读起来像免责声明堆叠。
- "mock 仅用于工程/CI，不进入研究结果"在 Experimental Design（L85）、Evidence（L148）、footer 语义上重复三次，但没有一次把 Historical 与 Mock 做**视觉对照**。

### 过度概括
- Research Question"重要说明"（L60）用"测量的是模型输出的归因行为，而不是……"表述正确，但和 Evidence 栏目的"不构成任何断言"重复，且没有和"实际比较了什么"绑定。

### 证据不足
- Pipeline（L93-102）8 步只有 badge + 一句名词，没有说明"每一步当前实现落在哪个文件/模块、下一步是什么"。
- Reproducibility（L164-173）是 8 条能力名词清单，没有指向 `pyproject.toml`/`uv.lock`/`configs`/`tests` 等具体文件级证据。
- Evidence（L146-155）是 8 条平铺 `<li>`，没有区分"已支持 / 部分支持 / 未声称"，读者无法快速判断边界。

### 状态不准确
- Pipeline 首步 badge 写 `Historical/Partial`（L94），把"历史已跑过"与"工程组件部分完成"混在同一个徽章里，语义含糊。
- 当前 roadmap.json 中 `site-002/003/004` 仍为 `current`，但这些里程碑在上一轮已本地完成——页面状态与实际进度不一致（本轮可在数据层校正为 completed，属状态更正非结果更改）。

### 不像真实作者表达
- 整个页面没有一处第一人称或"我为什么这么做"的说明，读起来像"AI 助手替项目写的说明书"，正是本轮要消除的 AI 感来源。

### 阅读负担过大
- Evidence 8 条、Reproducibility 8 条、Pipeline 8 步全部是等长 `<li>`，没有分层、没有折叠，长屏滚动疲劳。

## 4. 视觉与排版问题

- **字号**：正文继承 body 无显式 `font-size`（≈16px），但 `.note`/`.subtitle`/caption 大量 `.82~.92rem`，导航 `.9rem`，实际阅读偏小。
- **行宽**：`.subtitle` 限 `60ch`，但正文段落无 `reading-width` 限制，在宽屏铺满 `--maxw: 960px`，长段落行宽过大。
- **页面宽度**：`--maxw: 960px` 偏窄，Hero 无左右双栏，信息拥挤。
- **留白**：`.section { padding: 48px 0 }` 偏小，栏目间节奏平。
- **色块重复**：`.section.alt { background: var(--bg-alt) }` 与主背景 `--bg` 交替，但两者都是浅灰（`#f7f8fa` / `#eef1f5`），对比极弱，视觉上"整页一片灰"。
- **卡片数量**：Pipeline 每步、Reproducibility、Roadmap 都用卡片，卡片泛滥，反而没有重点。
- **图表尺寸**：`.figures` 三列网格把 1760×800 的图压到 ≥280px 宽的小卡，承担不了结果解释功能（P0/P1 重点问题）。
- **图文比例**：除了 Historical Results 三张小图，全页几乎无图，图文比例失衡。
- **视觉重心**：Hero 无右侧概览面板、无记忆点，首屏是纯文字。
- **移动端**：仅有 `max-width: 640px` 一个断点，只调了 h1 和 nav 间距；矩阵/双栏/图表在窄屏行为未定义。

## 5. 信息缺口

- **缺少背景**：没有"这个问题为什么值得研究"的作者动机（README 有"AI 从回答工具变成参与判断的系统"，页面没有）。
- **缺少研究解释**：Experimental Design 没有 6×2 设计矩阵，读者看不到条件 × 身份的交叉结构和每格样本。
- **缺少工程细节**：Pipeline/Reproducibility 没有 current implementation vs future architecture 的对照，也没有文件级路径。
- **缺少结果解释**：每张图缺"读图结论"，统计量与图混排，没有 `<details>` 分层。
- **缺少证据边界结构**：Evidence 没有 Directly supported / Partially supported / Not claimed 三层结构，也没把 Data authenticity / Run auditability / Full reproducibility 区分开。
- **缺少版本演进信息**：Version History 三节点没有"已有/证据/限制/与下一版差异"的结构，Roadmap 无时间线视觉。

## 6. 可复用资产

来自 `docs/showcase/PUBLIC_ASSET_INVENTORY.md` 与 `outputs/plots/`（均 1760×800，AI 模拟数据、非人类被试、需标题+来源+边界）。

已在页面使用（首版选用，保留、放大）：

| 文件 | 尺寸 | SHA-256 | 指标 | 当前显示 | 适合放大 | 首版展示 |
|---|---|---|---|---|---|---|
| `mean_agency.png` | 1760×800 | `8611DBD905130582FC49A1AF44724854EAFE5EA62D756379CDA5F1A851B6CE04` | agency 条件均值 | 三列小卡 | 是 | 是（核心） |
| `mean_free_will_attribution.png` | 1760×800 | `0814EE77E3B09815F1CF1545F8DA4DE50433E528F3183B627D4C92EAB3DC10C7` | 自由意志归因均值 | 三列小卡 | 是 | 是 |
| `mean_subjective_process_completeness.png` | 1760×800 | `66810828D1B9816D7F41EA624BE82B4C2BE958FB2A7A0D91E0A30C058736FE54` | 主观过程完整性均值 | 三列小卡 | 是 | 是（操纵检验） |

仓库其他可选图（本轮**不加入**，理由：责任维度为探索性，加入会让探索性结果看起来像确认性结论；且不满足"与现有结论直接相关"的必要性）：`mean_experience.png`、`mean_factual_manipulation_check.png`、`mean_moral_praise_blame.png`、`mean_outcome_accountability.png`、`mean_process_accountability.png`、`mean_responsibility_total.png`。旧命名 `mean_manipulation_check.png`(1440×800)、`mean_responsibility.png` 保持排除。

结论：本轮**不新增图片资产**，只放大和重新组织现有 3 张；`local_preview_status = approved`，`public_release_status` 保持 `pending_user_approval`。

## 7. 需要新增的网页原生可视化

均由 JSON / manifest 驱动，无 JavaScript 时保留文字兜底：

1. **6×2 实验设计矩阵**（CSS Grid）：6 行过程条件 × 2 列身份，每格 `n=<n_per_cell>`，底部合计；条件名从数据读取。
2. **Pipeline 状态流程图**（Flex + CSS 连接符）：节点含状态、当前实现、对应文件、下一步；current implementation vs future architecture 两条对照。
3. **Historical / Mock 对照组件**：左右分栏，视觉明确区分历史真实 API 数据与确定性合成数据用途。
4. **Evidence Boundaries 三栏**：Directly supported / Partially supported / Not claimed，每栏 3–5 项；下方 Data authenticity / Run auditability / Full reproducibility 三态区分。
5. **Phase 1–7 + Track S 路线图**（时间线 + 当前高亮 + `<details>` 展开交付）：Phase 1 双状态（local completed / release pending）。
6. **结果比较条**（CSS bar，从 claim metrics value 派生）：agency 条件均值与 factual check 的横向条形。
7. **复现组件关系图**（CSS，静态结构 + 状态徽章）：baseline → frozen outputs → lock → CLI → safe paths → schema → CI → wrappers → future runner。
8. **版本时间线**（增强 version_history 渲染）。

## 8. 需要保留图片占位的位置

仅在 HTML/CSS/SVG 无法自然表达、且现有资产不足、且确实改善理解时使用，且不超过 3 个（详见 `docs/showcase/VISUAL_ASSET_BRIEF.md`）：

- **VIS-001**：Hero 右侧项目概览封面视觉（研究线 + 工程线并列的抽象结构底图）。
- **VIS-002**：Research Question 的"过程结构梯度"概念插图（从直接选择到反思反馈的结构递增示意）。
- **VIS-003**：中介路径 process → agency → free_will_attribution 的结构图（可由 SVG 代替，标注为探索性）。

占位块显示"Visual asset pending"，不显示破损图片，带 `data-visual-id`，不影响主内容阅读。

## 9. 重构后的页面结构

保留十个主栏目与全部 `id`，内部重组：

1. **Hero**：左右双栏（左：标签+主标题+90–140 字介绍+按钮+一行边界；右：概览面板 + Research/Engineering 双状态线）。
2. **Research Question**：研究缘起 / 实际比较内容 / 不研究什么 / 三个核心问题卡。
3. **Experimental Design**：6×2 矩阵 + 数据来源卡 + Historical/Mock 对照 + 测量维度 + 实验单元。
4. **Pipeline**：原生流程图 + current implementation / future architecture 对照。
5. **Historical Results**：结果导读 + Manipulation/Process check + Agency + Free-will + Exploratory path + Responsibility；大图 + 读图结论 + `<details>` 统计详情 + 比较条。
6. **Evidence And Limitations**：三层证据边界 + 360 条建立了什么 / provenance 限制了什么 / 未来需补什么 + 三态区分。
7. **Reproducibility**：组件关系图 + 能复现什么 / 还不能复现什么 + 文件级路径。
8. **Version History**：v0.1 / v0.2 / Next / Future 时间线。
9. **Roadmap**：Phase 1–7 + Track S 可视化时间线，当前高亮，未来弱化。
10. **Repository Links**：按读者任务组织的入口 + 一句用途。

## 10. 停止条件与风险

- 停止条件：本轮完成后停在未提交状态；不 commit / merge / push / 部署 / 建新分支 / 调用 API / 改 outputs / 跑完整 pytest。
- 风险 R1：扩展 `site_summary.json` 的 `design` 块可能影响 `build_site_data.py` 的 `--check` 与 site 测试——通过重新生成 JSON 并跑 `tests/site` 缓解，不触碰研究结果字段。
- 风险 R2：HTML 大改可能误引入被禁子串（"360"、"F = " 等）触发 `test_no_hardcoded_statistics_in_html`——重写后针对性 grep 复核。
- 风险 R3：JS 重写可能引入 `import ... from` 或 `http(s)://` 触发 `test_js_has_no_third_party_imports`——避免 ES module import 语法与远程串。
- 风险 R4：状态更正（site-002/003/004 → completed）需与 backlog/worklog 一致，避免口径漂移。

## 11. SITE-005.1 精修附录（accuracy and release-safe data）

在 SITE-005 结构与视觉方向之上，本轮修正以下准确性问题（不改研究结果数值）：

- **Pipeline 状态更正**：原"配置与基础组件"节点同时引用 `configs/` 与 `src/freewill_attribution/` 却标 Historical，属误标。改为三层：Historical research path（条件与刺激 / Prompt 构造〔exact prompt snapshot/hash unavailable〕/ DeepSeek API 响应 / 解析与量表记录 / 分析与报告）、Current engineering layer（Package·safe paths·wrapper=Completed locally / Schema·config=Partial / 站点导出·展示页=Current）、Planned（formal runner·RunManifest·provider abstraction）。明确 `prompt.v1.yaml` 是当前配置组件，不替代历史精确 prompt。
- **source_commit 自引用**：改用 `RESEARCH_SOURCE_PATHS` 的最近提交，避免页面提交后 `--check` 失效；页脚文案改"研究数据源提交"。
- **失效链接**：移除 `../` 本地相对链接，改锚点 + GitHub 根链接 + `<code>` 路径。
- **跨平台表述**：Windows 本地 + Git Bash compatibility validation；真实 Linux/远程 CI 待发布阶段；不把 Git Bash 当 Linux。
- **占位替换**：VIS-002 → 原生 Process Structure Gradient（direct_choice_long 标 length-control diagnostic）；VIS-003 → 原生 Exploratory Path Diagram（间接效应估计/CI/是否跨 0/Exploratory）。页面不再有 "Visual asset pending"。
- **结果表述收紧**：操纵检验改"低/高结构整体差异"；中介改"区间是否跨 0"，不用因果措辞。
- **读图文案数据化**：移除 JS `FIGURE_READS`，改由 manifest `read_note_zh` → `figures[*].read_note`。
- **比较条**：条件主标签改中文 label，key 作次级 `<code>`。

REDESIGN_AUDIT=PASS

## SITE-005.2 Runtime, Mobile And Concept Visual

- **缺失 figures slot**：SITE-005.1 替换 VIS-003 块时误删了 `<div class="figures" data-slot="figures">`，导致 `renderFigures` 中 `slotEl("figures")` 返回 null。
- **JS 中断位置**：`renderFigures` 内 `figWrap.textContent = ""` 抛 `Cannot set properties of null`；`renderResults` 在调用 `renderFigures` 后抛错，`renderPathDiagram` 未执行；且 `main` 中 `renderVersions`、两次 `renderRoadmapGroup` 均未执行。
- **受影响栏目**：三张历史结果图、探索性路径图、Version History、Roadmap、Track S 全部空白。
- **修复**：在 Historical Results 的 results 之后补回 `data-slot="figures"` 容器（含 `<noscript>` 兜底 + 图表导读）；结果区顺序＝导读→claim→三张图→比较条→路径图。
- **DOM slot 契约**：新增 `requireSlot(name)`，核心容器（hero-metrics/design-stats/design-matrix/process-gradient/results/result-bars/figures/path-diagram/version-timeline/roadmap-phases/roadmap-track）改用它，缺失即抛清晰错误而非 null 崩溃；`catch` 区分 `file:`（提示用本地服务器）与其他（提示检查结构/slot/数据）；成功写 `data-render-complete="true"`，失败写 `"false"`；`?diagnostics=1` 下用双 rAF 写入 doc/matrix/figures 的 client/scroll 宽度。
- **移动端溢出来源**：`.results`/`.figures` 用 `1fr 1fr`、`.meta-cards` 用 `repeat(3,1fr)`（未用 `minmax(0,·)`），加上 figure/caption/长英文/文件路径缺 `min-width:0` 与断词，导致 390px 页面级横向溢出（约 61px）。
- **修复后布局**：网格改 `repeat(n, minmax(0,1fr))`；卡片（claim/figure/meta-card/q-card/impl-card/evidence-col/rmcard/research-concept-figure/frame）加 `min-width:0`；caption/fig-read/code/flow-ref 加 `overflow-wrap:anywhere; word-break:break-word`；1024px 结果/图表单列；未使用 `body{overflow-x:hidden}` 掩盖。过程梯度改 6 列网格 + 独立 scale header，移动端单列。**注：390px 的最终 document overflow 数值本应由浏览器 dump-dom 读取，但浏览器命令被拒绝（见下），未取得实测数值。**
- **概念图输入文件**：`fcdb0f90-6a14-4e45-9412-9b6325cf17a3.png`（根目录暂存，导入校验后删除）。
- **概念图尺寸和 Hash**：1586 × 992，比例 1.5988（≈8:5），SHA-256 `FFCC3139FD2FBE71CC9049F06CF718BBBFBB6C56E2BF37210C8268FF702BC7F7`；源/目标字节一致；站点路径 `site/assets/figures/attribution-research-concept.png`。
- **概念图边界**：仅解释研究结构，不承载统计结果，不计入三张历史结果图；置于 Research Question（桌面左文右图），图下三项图例（决策主体/过程描述/归因输出）。
- **浏览器运行结果**：本机存在 Edge；本轮按要求以 `127.0.0.1` + `--headless=new --dump-dom` + 截图设计运行时校验命令，但**该命令被用户拒绝执行**，故 dump-dom 运行时断言与截图**未执行、不声称通过**。运行时修复改为通过静态 DOM slot 契约测试（slot 存在性、requireSlot 使用、render 链路完整）验证。
- **截图结果**：未生成（浏览器命令被拒绝）；无 ERR_CONNECTION_REFUSED 错误页保留。建议人工 `python -m http.server 8000 --bind 127.0.0.1 --directory site` 后用浏览器 `/?diagnostics=1` 核对 `data-render-complete` 与 390px `data-doc-scroll-width`。
- **验证登记（本轮优先级调整）**：Browser runtime and 390px automated layout validation deferred to Phase 7 release validation。浏览器视觉/移动端自动验证**不作为**当前本地里程碑的提交阻断项，详见 `docs/showcase/SHOWCASE_DEFERRED_REFINEMENTS.md` §5；不声称浏览器视觉验证通过、不声称移动端自动验证通过、不声称 GitHub Pages 已验证。
