# 决策日志（DECISION_LOG）

> 登记决策问题，**不替用户做决定**。Pending = 待人工决策；Decided = 作者已决定。
> 2026-07-10 更新：作者已就 DEC-008（v1 保留为历史真实 API 基线）、DEC-009（项目定位）作出决定，并新增 DEC-010（建设范围）、DEC-011（benchmark 战略）为 Decided。

## 模板

```text
编号：DEC-xxx
日期：YYYY-MM-DD
问题：
备选方案：
最终决定：
理由：
影响范围：
是否可逆：
何时复审：
状态：Pending / Decided / Superseded
```

---

## 决策条目

### DEC-001 · 许可证选择
- 日期：待定
- 问题：项目采用何种开源**许可证**（或明确“暂不开源”）？（注意：本条**只涉及许可证**，不涉及 uv/pyproject 工程方案——后者已作为当前工程方案批准，见 DEC-010 与 backlog FND-002。）
- 备选方案：MIT / Apache-2.0 / CC-BY-4.0（文档/数据）/ 双许可（代码+材料分开）/ 暂不设许可。
- 最终决定：`待定（人工）`
- 理由：`待补`
- 影响范围：代码、刺激材料、数据、文档的可复用与署名。
- 是否可逆：部分可逆（已发布版本难追回）。
- 何时复审：Phase 7 发布前。
- 状态：Pending

### DEC-002 · 是否公开处理后数据
- 问题：是否公开清洗/分析后的数据（scores、summary），以及公开到哪一层（原始/清洗/分析/公开）？
- 备选方案：全部公开 / 仅公开分析汇总 / 仅公开 schema 与聚合 / 不公开。
- 最终决定：`待定（人工）`
- 影响范围：可复现性、文件体积、API 原始响应的公开必要性，以及历史运行元数据不完整情况下的披露边界。
- 是否可逆：不可逆（公开后难收回）。
- 何时复审：Phase 5/6。
- 状态：Pending

### DEC-003 · 是否公开完整刺激材料
- 问题：是否公开 v1/v2 完整刺激材料原文？
- 备选方案：全公开 / 公开 v2 保留 v1 / 仅公开样例 / 不公开。
- 最终决定：`待定（人工）`
- 影响范围：可复现性 vs 材料再利用/泄露研究意图。
- 是否可逆：不可逆。
- 何时复审：Phase 2/5。
- 状态：Pending

### DEC-004 · 是否公开 prompt
- 问题：是否公开完整 prompt 模板（含构念暴露版本历史）？
- 备选方案：公开最新版 / 公开全部版本 / 仅描述不贴原文 / 不公开。
- 最终决定：`待定（人工）`
- 影响范围：可复现性 vs 迎合/泄露分析（关联 R-03）。
- 是否可逆：不可逆。
- 何时复审：Phase 3/5。
- 状态：Pending

### DEC-005 · 是否保留 DeepSeek 为默认 provider
- 问题：默认 provider 保持 DeepSeek，还是改为 mock 默认 / 多 provider？
- 备选方案：DeepSeek 默认 / mock 默认（真实需显式开启）/ 可配置无默认。
- 最终决定：`待定（人工）`
- 影响范围：成本、复现、跨模型能力。
- 是否可逆：可逆（配置项）。
- 何时复审：Phase 3。
- 状态：Pending

### DEC-006 · 是否接入其他模型
- 问题：是否引入除 DeepSeek 外的模型以做跨模型稳定性复核？
- 备选方案：单模型 / 增加 1 个对照模型 / 多模型矩阵。
- 最终决定：`待定（人工）`
- 影响范围：证据强度（解决 H-01 独立性）vs 成本/复杂度。
- 是否可逆：可逆。
- 何时复审：Phase 3/4。
- 状态：Pending

### DEC-007 · 网站与研究仓库如何同步
- 问题：网站数字如何与研究仓库结果同步？
- 备选方案：网站读取版本化 JSON（推荐方向）/ CI 自动推送 / 手工同步（现状，不推荐）。
- 最终决定：`待定（人工）`
- 影响范围：数字一致性与可追溯性（关联 R-10）。
- 是否可逆：可逆。
- 何时复审：Phase 6。
- 状态：Superseded
- 取代说明（2026-07-13，PLAN-001.1）：本条已由 DEC-013、DEC-018 与 `docs/showcase/SITE_DATA_CONTRACT.md` 取代。当前决定为：页面读取版本化静态 JSON；JSON 由本地 `scripts/build_site_data.py` 从明确仓库源文件生成；不由 CI 自动推送；不手工维护动态研究数字；部署统一留到 Phase 7。（上述历史备选与原始表述保留，不删除。）

### DEC-008 · 是否将 v1 结果作为 baseline 固化
- 日期：2026-07-10
- 问题：如何处理当前 v1 的 360 条结果？
- 备选方案：保留为历史基线 / 重新生成 / 废弃。
- 最终决定：**v1 的 360 条结果保留为 DeepSeek 历史真实 API 基线（historical DeepSeek API baseline）。**
- 说明：
  - 当前先**冻结并补 provenance**（FND-001：hash + 作者 provenance 声明）；
  - 是否**立即创建 GitHub Release** 仍留待 Phase 7；
  - “保留为基线”与“立即公开发布 Release”是**两个不同的决定**——本条只决定前者。
- 理由：作者已确认数据来自真实 DeepSeek API（非 mock），原数据来源存疑（旧 B-01）已撤销，重归类为 H-00（历史 provenance 不完整）。
- 影响范围：`outputs/**`、Data Card、Phase 7 发布、研究诚信表述。
- 是否可逆：保留为基线可逆；一旦发布 Release 不可逆（故 Release 单列 Phase 7）。
- 何时复审：Phase 7（发布前需完成 provenance 声明）。
- 状态：Decided

### DEC-009 · 项目定位：研究原型 vs 模型行为评测
- 日期：2026-07-10
- 问题：项目对外主定位是什么？
- 备选方案：研究原型 / 模型行为评测框架 / 双定位分层表述。
- 最终决定：**当前主定位为“可复现的大模型模拟研究原型”；通用 LLM benchmark 或通用模型行为评测框架是正式的长期战略发展方向，但不属于当前版本已经完成的能力。**
- 理由：
  - 当前仓库围绕一个明确研究问题展开；
  - 当前数据主要来自单一 DeepSeek 配置；
  - 当前最重要任务是建立可复现和可追溯能力；
  - benchmark 化需要多任务、多模型、多 prompt、统一 schema 和稳定评测协议；
  - 这些条件应在当前研究原型稳定后逐步发展。
- 影响范围：README、网站、研究文档、架构、backlog、证据等级、后续版本路线。
- 是否可逆：可逆（但影响广）。
- 何时复审：Phase 4/5。
- 状态：Decided

### DEC-010 · 当前工程建设范围
- 日期：2026-07-10
- 问题：当前 v0.2 版本的工程建设范围边界在哪里？
- 备选方案：作品集级专业研究仓库（可复现运行）/ 直接建通用 benchmark 平台。
- 最终决定：**建设作品集级专业研究仓库，并具备真实可复现运行能力；当前不建设完整通用 benchmark 平台。**
- 说明：`pyproject.toml + uv.lock` 已作为当前工程方案批准（与许可证决定 DEC-001 无关）。当前架构必须为未来 benchmark 方向保留扩展接口，但不提前实现完整 benchmark 系统。
- 影响范围：架构、Phase 1 范围、backlog、门禁。
- 是否可逆：可逆。
- 何时复审：Strategic Benchmark Track 启动前。
- 状态：Decided

### DEC-011 · benchmark 战略路线
- 日期：2026-07-10
- 问题：通用 LLM benchmark / 模型行为评测框架在路线图中的地位？
- 备选方案：当前实现 / 列为长期战略后续启动 / 不纳入。
- 最终决定：**把通用 LLM benchmark / 模型行为评测框架列为项目长期战略方向，在当前研究原型和可追溯运行管线稳定后再启动。**
- 说明：对应 `Strategic Horizon`（BMK-L1..L4）与 `Future Strategic Backlog`（BMK-001..006）；不得成为 Phase 1–Phase 7 的强制退出条件。
- 影响范围：路线图、backlog、门禁、对外表述。
- 是否可逆：可逆。
- 何时复审：研究原型稳定发布后。
- 状态：Decided

### DEC-012 · 真实 API 调用授权与预算上限

- 日期：待定
- 问题：后续真实模型运行由谁授权，以及单次运行的调用数、token 或费用上限如何设置？
- 备选方案：
  - 每次运行单独人工授权；
  - 设置固定 max_calls；
  - 设置固定 max_cost；
  - 同时设置 max_calls 与 max_cost。
- 最终决定：待定（人工）
- 影响范围：Phase 3 真实 provider、成本、安全与运行中止策略。
- 是否可逆：可逆。
- 何时复审：Phase 3A 真实 DeepSeek 调用前。
- 状态：Pending

> 注：当前不需要作者立即决定 DEC-012；仅在 Phase 3A 真实调用前决策即可。

---

## PLAN-001 重定基线决策（2026-07-13）

### DEC-013 · Showcase 改为并行开发主线
- 日期：2026-07-13
- 问题：展示页应排在最后阶段，还是与研究开发并行？
- 备选方案：末阶段一次性建设 / 并行主线（Track S）。
- 最终决定：**将 Showcase 设为与研究开发并行的展示主线（Track S），S1–S4 本地建设，S5 部署并入 Phase 7。**
- Context：旧 backlog 把 SITE-* 排到 Phase 6/末尾；审计（§6/§9）表明展示可在本地并行、不依赖远程 CI。
- Consequences：SITE-001 重定义为内容与数据契约；下一分支 `feat/showcase-v1` 可立即建设静态页。
- Revisit condition：Track S 完成或研究主线优先级重大调整时。
- 状态：Decided

### DEC-014 · Phase 1 本地完成与正式退出分开记录
- 日期：2026-07-13
- 问题：Phase 1 是否可在本地实现完成后即宣布退出？
- 备选方案：本地完成即退出 / 本地完成与正式退出分离。
- 最终决定：**Phase 1 记为"Local implementation complete / Release verification pending"；正式退出以 GitHub-hosted 双平台 CI 实际变绿为准。**
- Context：CI 仅配置完成，无 GitHub-hosted 运行记录（审计 §3）。
- Consequences：文档不得声称 Phase 1 已正式退出。
- Revisit condition：获 push 授权并完成远程 CI 后。
- 状态：Decided

### DEC-015 · GitHub-hosted CI 推迟到统一发布验证
- 日期：2026-07-13
- 问题：远程 CI 验证应在 Phase 1 还是统一发布阶段？
- 备选方案：Phase 1 内验证 / 统一 Phase 7 验证。
- 最终决定：**GitHub-hosted Windows/Linux CI 与远程发布验证统一集中在 Phase 7（Release And Audit），并作为 Level 3 测试。**
- Context：无 push 授权，Track S 不应被远程 CI 阻塞。
- Consequences：本地开发可持续推进；不得声称 CI 已绿。
- Revisit condition：REL-001 执行时。
- 状态：Decided

### DEC-016 · 采用三级测试策略
- 日期：2026-07-13
- 问题：每类改动应执行何种测试强度？
- 备选方案：一律完整回归 / 分级测试。
- 最终决定：**采用 Level 1（本地针对性）/ Level 2（里程碑合并）/ Level 3（发布验证）三级策略；文档、文案、样式、图片排列、roadmap 状态、站点说明类改动不执行完整回归。**
- Context：文档/文案改动不需 186 项回归（审计 §6）。
- Consequences：降低文档类任务成本，保留合并/发布强校验。
- Revisit condition：测试体系重大变化时。
- 状态：Decided

### DEC-017 · 展示页区分 completed/current/planned
- 日期：2026-07-13
- 问题：展示页如何标注能力成熟度？
- 备选方案：统一"已完成" / 分状态标注。
- 最终决定：**展示页统一使用状态系统 Completed / Current / Planned / Historical / Pending verification，禁止将 Planned/Configured 写成 Completed/Verified。**
- Context：防 R-17（把未来写成当前能力）。
- Consequences：所有页面数字与能力必须带状态与来源。
- Revisit condition：能力状态变化时。
- 状态：Decided

### DEC-018 · 静态页面首版使用原生 HTML/CSS/JS
- 日期：2026-07-13
- 问题：展示页首版技术栈？
- 备选方案：React/Vite/npm 前端 / 原生 HTML+CSS+JS+静态 JSON。
- 最终决定：**首版使用原生 HTML/CSS/JavaScript + 静态 JSON + GitHub Pages，不引入 React/Vite/npm/后端/数据库/远程 API。**
- Context：研究可信度优先、部署简单、可复现。
- Consequences：SITE-003 以原生静态实现。
- Revisit condition：交互复杂度显著上升时。
- 状态：Decided

### DEC-019 · 项目定位为研究与模型行为评测原型（不声称成熟 benchmark）
- 日期：2026-07-13
- 问题：对外定位如何表述（在 DEC-009 基础上细化到展示层）？
- 备选方案：成熟 benchmark / 研究与模型行为评测原型。
- 最终决定：**对外定位为"用于研究和评估大语言模型自由意志归因行为的可复现实验与模型行为评测原型"；benchmark 为长期方向，不声称已完成。**
- Context：承接 DEC-009/011，用于展示文案统一口径。
- Consequences：README/网站/release 分开写当前能力与未来方向。
- Revisit condition：Strategic Benchmark Track 启动时。
- 状态：Decided

### DEC-020 · 历史 DeepSeek 结果真实性与 provenance 完整性分开表述
- 日期：2026-07-13
- 问题：展示页如何表述历史数据的真实性与可复现性？
- 备选方案：合并表述 / 分层表述。
- 最终决定：**明确区分：数据真实性（已确认，真实 DeepSeek API）/ 运行可审计性（历史元数据不完整）/ 完全复现能力（受限）；缺失元数据不得推测补写。**
- Context：承接 H-00/R-15/DEC-008 与审计 §5。
- Consequences：展示页 Evidence 栏与数据契约 provenance_status 字段据此表述。
- Revisit condition：新可追溯运行产生后。
- 状态：Decided
