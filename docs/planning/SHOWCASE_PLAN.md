# Public Showcase Plan

> 对应 Track S（并行展示主线）与 SITE-001。依据 `docs/audit/repository_rebaseline_assessment.md`（`AUDIT_GATE=PASS`）与 DEC-013~DEC-020。
> 本文件为展示线的规划与验收契约；首版完整文案见 `docs/showcase/SHOWCASE_CONTENT.md`，数据契约见 `docs/showcase/SITE_DATA_CONTRACT.md`，资产清单见 `docs/showcase/PUBLIC_ASSET_INVENTORY.md`。

## 1. 展示目标

展示页服务于：
- 招聘方：快速判断工程与研究能力、严谨性与诚信表述；
- 研究者：理解研究问题、设计、证据边界与可复现方式；
- AI 产品与评测从业者：理解模型行为评测原型的方法与路线；
- GitHub 访问者：从仓库跳转获得结构化、可信的项目概览。

## 2. 项目公开定位

推荐核心表述：

> "一个面向可复现研究的大语言模型自由意志归因实验与模型行为评测原型。"

**不得**写：production benchmark；fully reproducible historical run；human psychology conclusion；multi-model benchmark already complete。

## 3. 目标读者和阅读路径

- **30 秒浏览**：Hero + 一句话定位 + 关键状态标签（研究原型 / 历史真实 API 基线 / 本地工程实施完成 / 发布验证待完成）+ 一张核心结果图。
- **3 分钟理解**：Research Question → Experimental Design（6×2×30）→ Pipeline → Historical Results 要点 → Evidence And Limitations。
- **深入技术阅读**：Reproducibility（baseline hash / uv.lock / package / CLI / schema/config / tests / CI 配置 / wrapper）→ Version History → Roadmap（Phase 1–7 + Track S）→ Repository Links。

## 4. 页面结构

固定包含（顺序）：
1. Hero
2. Research Question
3. Experimental Design
4. Pipeline
5. Historical Results
6. Evidence And Limitations
7. Reproducibility
8. Version History
9. Roadmap
10. Repository Links

## 5. 状态系统

| 状态 | 含义 | 展示规则 |
|---|---|---|
| Completed | 已实现且已本地验证 | 可标"已完成"，需可指向文件/测试 |
| Current | 进行中 | 标"进行中"，不承诺完成时间 |
| Planned | 规划中、未实现 | 明确"规划/未来"，不得写成能力 |
| Historical | 历史基线（v1 真实 API 数据） | 标"历史"，附证据边界 |
| Pending verification | 已配置未远程验证（如 CI） | 写 "configured, remote verification pending"，禁止写 "passing" |

## 6. 数据来源

每个页面数字必须对应：具体文件；字段；计算方法；更新时间；是否直接事实；是否派生值。
统一由 `docs/showcase/SITE_DATA_CONTRACT.md` 定义；未来由 `scripts/build_site_data.py` 从明确源文件派生，**不从工作日志手工写入动态数字**。

## 7. 页面技术方案

首版使用：原生 HTML；CSS；JavaScript；静态 JSON；GitHub Pages。
不使用：React；Vite；npm；后端；数据库；远程 API。

## 8. 目录方案

```text
site/
  index.html
  assets/
    css/site.css
    js/site.js
    figures/
  data/
    site_summary.json
    roadmap.json
    version_history.json
  README.md

scripts/
  build_site_data.py
```

> 本轮（SITE-001）**只定义，不创建**上述代码/页面文件。

## 9. 视觉原则

- 研究可信度优先，不做营销式夸张；
- 研究线与工程线并列呈现；
- 清晰标注限制与证据边界；
- 响应式布局；基本可访问性（语义标签、对比度、alt 文本）；
- 图表必须有标题与来源；
- 避免大段内部技术日志与内部任务编号。

## 10. 分阶段实施

- **SITE-001（本轮）**：信息架构、首版完整文案、数据契约、公开资产清单、证据边界。
- **SITE-002**：`scripts/build_site_data.py` 从 `outputs/**` 与规划文档派生 `site_summary.json` / `roadmap.json` / `version_history.json`。
- **SITE-003**：静态展示 MVP（原生 HTML/CSS/JS，读取静态 JSON，响应式）。
- **SITE-004**：本地静态服务 + JSON 校验 + 路径校验 + 移动端布局 + 证据检查。
- **REL-001**：Pages 部署、远程 CI、最终 URL、发布证据（Phase 7 统一，需 push 授权）。

## 11. 验收标准

| 任务 | 输入 | 输出 | 测试 | 人工审阅点 | 停止条件 |
|---|---|---|---|---|---|
| SITE-001 | 审计报告、outputs 派生数字、规划文档 | 4 份 showcase 文档（plan/content/data contract/asset inventory） | Level 1：markdown 链接检查、规划一致性检查、敏感内容扫描 | 定位表述、证据边界、资产分级 | 文案出现过度声称或把 Planned 写成 Completed |
| SITE-002 | SITE-001 数据契约 | `build_site_data.py` + 3 个 JSON | Level 1：JSON schema 校验、字段来源校验 | 数字与来源文件一致性 | 出现手工写入动态数字 |
| SITE-003 | SITE-001/002 | `site/` 静态页 | Level 1：本地打开、控制台无错、响应式检查 | 视觉、可访问性、状态标注 | 页面把配置写成验证通过 |
| SITE-004 | SITE-003 | 校验脚本/报告 | Level 1：本地服务 + JSON/路径/移动端校验 | 证据检查通过 | 存在死链或缺失素材 |
| REL-001 | SITE-004 + Phase 1 本地实现 | Pages 发布 + release 证据 | Level 3：完整回归 + 远程 CI + 链接校验 | 发布内容与边界声明 | 无 push 授权 / CI 未绿 |
