# 专业化改造总计划（PROFESSIONALIZATION_PLAN）

> 基线：分支 `refactor/v0.2-professionalization`，commit `00c4725`。
> 推进原则：规划 → 人工审查 → 单任务执行 → 自动测试 → Git diff 检查 → 阶段验收 → 人工批准 → 下一阶段。
> 禁止在同一 PR 中同时做：工程重构 + 刺激材料改写 + 重跑实验 + 更新网站。

每个阶段模板字段：目标 / 输入 / 具体任务 / 修改文件 / 新增文件 / 不修改内容 / 前置依赖 / 风险 / 验收命令 / 阶段验收标准 / 回滚方案 / 完成定义(DoD) / 人工决策点。

---

## 三层目标（作者决策，2026-07-10）

> 项目主定位（DEC-009）：**可复现的大模型模拟研究原型**。完整定义：本项目是一个心理学、哲学与人工智能交叉的可复现大模型模拟研究原型，用于研究观察者如何依据 AI Agent 的身份标签与决策过程，对其行动者感、自由意志、责任和相关心智属性进行归因。

### 第一层 · 当前版本核心目标（当前硬性范围）

```text
建立作品集级、专业、可复现的大模型模拟研究仓库。
```

### 第二层 · 中期研究目标（后续研究迭代）

```text
完成 v2 研究协议、材料和分析方法升级，
形成能够稳定重复运行和比较不同 prompt / 配置的研究管线。
```

### 第三层 · 长期战略目标（战略发展路线）

```text
在现有研究原型基础上，
抽象出可复用的 LLM 模型行为评测和 benchmark 能力。
```

层级约束：
- 第一层是**当前硬性范围**（对应 Phase 1–Phase 7）。
- 第二层是后续研究迭代（Phase 2/4）。
- 第三层是战略发展路线（见文末 `Strategic Horizon`）。
- **第三层不得成为 Phase 1—Phase 7 的强制完成条件**；不得把长期方向写成当前已实现能力。

---

## 阶段依赖总览

```text
Phase 0   基线冻结+审计
   ↓
Phase 0.1 规划校正（本轮：定位确认、事实校正、路线收敛）
   ↓
Phase 1   工程基础
   ↓
Phase 3A  支持 v1/mock 的可追溯 runner
   ↓
Phase 2   研究协议与刺激材料 v2
   ↓
Phase 3B  将 v2 接入可追溯 runner
   ↓
Phase 4   统计分析与证据等级
   ↓
Phase 5   专业文档体系
   ↓
Phase 6   README 与网站同步
   ↓
Phase 7   发布与归档
   ↓
Strategic Benchmark Track（长期，独立于 v0.2 门禁）
```

- Phase 1 完成工程底座后，先做 **Phase 3A**（用 v1/mock 打通可追溯 runner，不依赖 v2），再做 Phase 2（v2 研究协议+材料），最后 **Phase 3B**（把 v2 接入 runner）。
- **Phase 3 不再无条件依赖 stimuli v2**：Phase 3 依赖 Phase 1；使用哪个材料版本，该版本必须已冻结即可（v1 已冻结，v2 冻结后再接入）。
- Phase 4 依赖可追溯 runner 已产出可追溯运行（mock 或已授权真实 run）。
- Phase 6 依赖 Phase 4/5（版本化 JSON 与文档卡片）。
- `Strategic Benchmark Track` 是长期方向，**不属于 Phase 1–Phase 7 退出条件**，进入条件见 `PHASE_GATES.md`。

---

## Phase 0 · 基线冻结与现状审计

- **目标**：冻结当前 v0.1，建立治理文档，完成风险与任务拆解。
- **输入**：v0.1 仓库、smoke test 声明。
- **具体任务**：现状审计、目标架构设计、阶段计划、backlog、gate、风险表、决策日志、AGENTS/WORKLOG。
- **修改文件**：无（仅新增规划/治理文件）。
- **新增文件**：`docs/audit/current_state_v0.1.md`、`docs/planning/*.md`、`AGENTS.md`、`AGENT_WORKLOG.md`。
- **不修改内容**：`src/`、`outputs/`、`README.md`、`docs/` 既有内容。
- **前置依赖**：无。
- **风险**：v1 已由作者确认来自真实 DeepSeek API，但历史运行 provenance 不完整；不得伪造缺失的模型版本、token、费用、时间戳、prompt hash 和依赖信息。
- **验收命令**：`git status --short`（应仅显示新增规划文件）；`python -m compileall -q src`。
- **阶段验收标准**：9 个规划文件齐全；受保护资产已记录；未修改任何研究资产。
- **回滚方案**：删除新增规划文件即可（不触碰研究资产）。
- **DoD**：本文件 §"本轮停止条件"中 9 个文件全部创建，等待人工审查。
- **人工决策点**：架构方案是否批准；v1 provenance statement 的最终措辞。

---

## Phase 1 · 工程基础

- **目标**：`pyproject.toml`、锁定依赖、characterization tests、输出隔离、最小 package、最小 CLI、最小 schema/config、CI、跨平台运行。
- **输入**：Phase 0 已批准架构方案。
- **具体任务**：见 backlog `FND-001`~`FND-008`（新顺序）。**先固定旧行为**（characterization tests）→ **先解决输出覆盖风险** → 建立最小 package + 新 CLI（`python -m freewill_attribution.cli`）与旧入口**并行**（不立即改 thin wrapper）→ 最小 schema/config → CI → 跨平台脚本。
- **修改文件**：`requirements.txt`（保留作兼容）；旧运行脚本增加**显式输出目录**参数（不改研究逻辑，且默认永不写 `outputs/`）。**不动** `stimuli.py`/`scales.py` 文本。
- **新增文件**：`pyproject.toml`、`uv.lock`、`src/freewill_attribution/{__init__,cli,config,schemas,paths,runner}.py`、`tests/**`、`.github/workflows/ci.yml`、`scripts/*`。
- **不修改内容**：`outputs/**`（严禁覆盖）、刺激材料/题项**文本**、README 结果数字。**不在 Phase 1**：拆分完整分析模块、接入多模型、实现 benchmark 功能。
- **前置依赖**：Phase 0 批准。
- **风险**：重构引入行为差异（用 characterization tests 兜底）；导入路径变化破坏旧入口；意外触发写 `outputs/`。
- **验收命令**：`uv sync`；`ruff check .`；`pytest -q`；`python -m freewill_attribution.cli run --mock --n-per-cell 2 --out <tmp>`（写临时目录，不写 `outputs/`）。
- **阶段验收标准**：见 `PHASE_GATES.md` Phase 1 退出条件。
- **回滚方案**：Phase 1 全部在独立分支/PR，回滚 = 关闭 PR / `git revert`；`outputs/`、`stimuli.py`、`scales.py` 文本 hash 未变可作校验。
- **DoD**：CI 绿；旧入口仍可用；`outputs/` 与材料 hash 未变。
- **人工决策点**：包命名 `freewill_attribution`。（注：`pyproject + uv.lock` 已作为工程方案批准，见 DEC-010；许可证是独立决定 DEC-001。）

---

## Phase 2 · 研究协议与刺激材料 v2

- **目标**：明确研究问题、预定义假设、重做长度控制、减少研究意图暴露、平衡情境与效价、冻结 stimuli v2。
- **输入**：审计 §D 问题（H-02, M-01, M-06, M-07）、`docs/measurement_plan.md`。
- **具体任务**：撰写 `protocols/study_protocol_v2.md`（RQ/H 预注册式）；设计 stimuli v2（长度矩阵化控制、去元描述、valence 与 domain/fixed_choice 解耦、随机化情境分配）；题项去重与区分效度前置设计。**v1 与 v2 并存**（`data/stimuli/v1/` 冻结、`data/stimuli/v2/` 新增）。
- **修改文件**：无（v1 只读）。
- **新增文件**：`protocols/study_protocol_v2.md`、`data/stimuli/v2/**`、`data/stimuli/v1/**`（v1 快照冻结副本 + hash）。
- **不修改内容**：`src/stimuli.py`（v1 文本）、`src/scales.py`（v1 文本）、`outputs/**`。
- **前置依赖**：Phase 0 批准（可与 Phase 1 并行）。
- **风险**：v2 改写偏离原构念；长度控制仍不彻底；协议与后续分析不一致。
- **验收命令**：`pytest tests/unit/test_stimuli_v2.py -q`（长度/平衡/无元描述断言）；材料 diff 报告。
- **阶段验收标准**：协议含预定义假设与计划对比；v2 通过平衡/长度/泄露检查；v1 hash 未变。
- **回滚方案**：删除 `data/stimuli/v2/`；v1 不受影响。
- **DoD**：stimuli v2 冻结并打 hash；协议人工批准。
- **人工决策点**：是否公开完整刺激材料（DECISION）；v2 是否替换 v1 为默认。

---

## Phase 3 · 可追溯运行管线（分 3A / 3B）

> **Phase 3 不再无条件依赖 stimuli v2**。Phase 3 依赖 Phase 1；运行使用哪个材料版本，该版本必须已冻结即可。先用已冻结的 v1/mock 打通 runner（3A），v2 冻结后再接入（3B）。当前 Phase 1 最小 package 只含 `runner.py`，provider 抽象在此阶段以“可替换接口 + 单一 DeepSeek/mock 实现”落地，**不建多 provider 生态**。

### Phase 3A · 支持 v1/mock 的可追溯 runner
- **目标**：run_id、manifest、prompt/stimulus/config 版本、失败隔离、resume；provider 可替换接口（DeepSeek 可显式启用 + mock）。
- **输入**：Phase 1 package/schema；已冻结的 v1 材料。
- **具体任务**：runner 生成 `artifacts/runs/<run_id>/`（manifest/config/environment/prompts/stimuli/raw/normalized/validation）；记录 git sha、model 名称/版本、temperature、seed、retry、失败类型、checksum；**token/cost 字段允许缺失或 provider 不返回**；resume + dry-run + 预算上限。
- **修改文件**：无（新代码在 package 内）。
- **新增文件**：`src/freewill_attribution/runner.py`（最小）、后续可选 `providers/` 单实现、`artifacts/runs/.gitkeep`。
- **不修改内容**：`outputs/**`（旧结果只读，禁覆盖）；真实 API **默认不调用**。
- **前置依赖**：Phase 1。
- **风险**：真实 API 成本/密钥泄露；覆盖旧结果；resume 幂等性错误。
- **验收命令**：`python -m freewill_attribution.cli run --mock --out artifacts/runs/<id>`；`pytest tests/integration/test_run_manifest.py`。
- **阶段验收标准**：一次 mock run 产出完整可追溯目录；无写 `outputs/`；manifest 含全部可得溯源字段。
- **人工决策点**：是否保留 DeepSeek 为默认 provider（DEC-005）；真实调用授权与预算上限（DEC-012/RUN-003）。

### Phase 3B · 将 v2 接入可追溯 runner
- **目标**：把 Phase 2 冻结的 stimuli v2 接入同一 runner，保持 v1 与 v2 并存可追溯。
- **前置依赖**：Phase 3A + Phase 2（stimuli v2 已冻结）。
- **阶段验收标准**：以 v2 跑一次 mock run 产出完整可追溯目录；v1 结果与 hash 未变。

- **不修改内容（两子阶段共同）**：`outputs/**`；真实 API 默认不调用。
- **回滚方案**：删除对应 `artifacts/runs/<id>/`。
- **DoD**：run 目录 schema 稳定，checksum 可校验，resume 通过；v1/v2 均可追溯运行。
- **说明**：多 provider 矩阵、benchmark 评分、leaderboard **不属于** Phase 3，转入 `Strategic Benchmark Track` / `BMK-*`。

---

## Phase 4 · 统计分析与证据等级重构

- **目标**：6 水平分类与趋势分析分离、计划对比、效应量、置信区间、路径诊断降级、结果可追溯到 run、证据等级。
- **输入**：可追溯运行数据（Phase 3A/3B 产出）。
- **当前版本硬性要求**：
  - 六水平分类与趋势分析**分离**（解决 H-03）；
  - 计划对比；
  - 效应量；
  - 置信区间；
  - 路径分析**降级为探索性诊断**（非机制证据）；
  - 结果可追溯到具体 run。
- **当前版本非硬性要求（转入 `BMK-*` 战略 backlog，不作 Phase 4 退出条件）**：
  - 多模型稳定性；
  - 完整跨 prompt benchmark；
  - 通用模型排行榜。
- **具体任务**：拆分 `analysis/`；输出 `evidence_grades`（描述性 / 探索性路径诊断 / 非机制证据）；跨 domain/scenario 稳定性（跨 prompt/模型稳定性为可选、非硬性）。
- **修改文件**：无（新分析模块）。**不改** `outputs/` 旧文件。
- **新增文件**：`.../analysis/**`、新运行的 `analysis_summary.json`。
- **不修改内容**：v1 `outputs/**` 数字；不手工改任何分析结果。
- **前置依赖**：可追溯 runner 已产出可追溯运行。
- **风险**：分析口径变化改变结论表述（需人工确认）；对 mock 数据过度解读。
- **验收命令**：`pytest tests/unit/test_analysis.py`；对固定 mock 种子结果做数值回归测试。
- **阶段验收标准**：满足上述硬性要求；每个 headline 结论标注证据等级；6 水平与趋势编码分离报告。
- **回滚方案**：分析模块在独立 PR，可 revert。
- **DoD**：证据等级表落地；无手工数字。
- **人工决策点**：分析主口径（6 水平为主，趋势为辅——已倾向 6 水平）；哪些表述需降级。

---

## Phase 5 · 专业文档体系

- **目标**：Study Card、Data Card、Model Usage Card、Reproducibility、Limitations、Research Integrity、references。
- **输入**：Phase 0 审计、Phase 2 协议、Phase 4 证据等级。
- **具体任务**：建立 `docs/cards/*`；`references/`（含 DOI/正式出版信息，补齐 Gray et al.、FAD-Plus、Godspeed 等文献条目）；归档冗余展示材料；明确正式入口文档。
- **修改文件**：可归档/整理 `docs/` 展示材料（移动到 `docs/archive/`，不删原文）。
- **新增文件**：`docs/cards/study_card.md`、`data_card.md`、`model_usage_card.md`、`reproducibility.md`、`limitations.md`、`research_integrity.md`、`references/references.bib`。
- **不修改内容**：`outputs/**`；README 结果数字（留待 Phase 6）。
- **前置依赖**：Phase 4（证据等级）；Phase 0（受保护资产表）。
- **风险**：文档口径与代码/结果不一致。
- **验收命令**：链接检查 / markdown lint；卡片字段完整性检查。
- **阶段验收标准**：7 类文档齐全；文献含 DOI；口径与证据等级一致。
- **回滚方案**：文档 PR 可 revert；归档为移动非删除。
- **DoD**：文档卡片人工审阅通过。
- **人工决策点**：项目定位（研究原型 vs 模型行为评测）；是否公开处理后数据/prompt（DECISION）。

---

## Phase 6 · README 与网站同步

- **目标**：研究仓库生成统一 JSON；网站读取版本化结果；消除手工数字同步；显示证据等级/版本/运行信息。
- **输入**：Phase 4 `analysis_summary.json`、Phase 5 卡片。
- **具体任务**：`site_export` 从指定 run 生成 `site_summary.json`（含 run_id、版本、证据等级、数字）；README 数字改为引用/由脚本注入；网站从 JSON 读取。
- **修改文件**：`README.md`（结果数字改为可追溯来源）；网站仓库（独立 PR）。
- **新增文件**：`.../reporting/site_export.py`、`artifacts/releases/<ver>/site_summary.json`。
- **不修改内容**：`outputs/**` 历史；不手工写数字。
- **前置依赖**：Phase 4 + Phase 5。
- **风险**：网站/README 数字与来源 run 不一致；跨仓库同步冲突。
- **验收命令**：`... site-export --run <id>`；JSON schema 校验；README 数字与 JSON 一致性测试。
- **阶段验收标准**：README/网站数字均可追溯到 run_id 与版本；无手工数字。
- **回滚方案**：revert README PR；网站独立回滚。
- **DoD**：单一数据源（JSON）驱动展示。
- **人工决策点**：网站与研究仓库同步机制（DEC-007）。区分“当前能力”与“未来 benchmark 方向”表述（DEC-009/011）。

---

## Phase 7 · 版本发布与归档

- **目标**：release artifact、checksum、changelog、版本标签、归档旧材料、发布稳定研究原型；固化 v1 为历史真实 API 基线。
- **输入**：Phase 6 完成。
- **具体任务**：撰写 **v1 provenance statement**（v1 = historical DeepSeek API baseline，附 v1 hash，明确历史运行元数据不完整——见 H-00）；打 `v0.2.0` tag；`artifacts/releases/`（含 checksum、changelog）；归档 v1 材料；**当前版本能力与 benchmark 未来方向分开描述**；GitHub Release（**需人工执行**）。
- **修改文件**：`CHANGELOG.md`（新增）。
- **新增文件**：`artifacts/releases/v0.2.0/**`、`CHANGELOG.md`、v1 provenance statement。
- **不修改内容**：历史 commit；不强制重写 Git 历史；`outputs/**` 历史结果。
- **前置依赖**：Phase 6。
- **风险**：release 表述把长期 benchmark 愿景写成当前能力（R-17）；provenance 声明不完整。
- **验收命令**：checksum 校验；tag 与 artifact 对应性检查；provenance statement 存在性检查。
- **阶段验收标准**：release 内容自洽、可复现、含证据等级与边界声明；含 v1 provenance statement 与 v1 hash；能力与未来方向分开描述。
- **回滚方案**：删除 tag/release（人工）。
- **DoD**：稳定研究原型对外发布。
- **人工决策点**：许可证选择（DEC-001）；“保留为基线”已定（DEC-008），是否立即发 Release 单独决定；Release 触发（全部人工）。

---

## Strategic Horizon · 通用 LLM benchmark / 模型行为评测框架

> 本章节只做**路线设计**，不做当前实现。对应 DEC-011。以下四个成熟度等级**不属于 v0.2 必做，也不属于 Phase 1—Phase 7 退出条件**。

### BMK-L1 · 单研究可复现（= 当前项目目标）
- 单一研究任务；DeepSeek + mock；固定材料和量表；run manifest；可重复运行；可追溯结果。

### BMK-L2 · 多配置稳定性评测（中期方向）
- 多 prompt；多 temperature；多 seed；多材料版本；同一模型跨运行比较；统一稳定性指标。

### BMK-L3 · 多模型行为评测（后续重要方向）
- 多 provider；多模型；统一输入和 schema；模型间效应比较；模型版本追踪；跨模型稳健性报告。

### BMK-L4 · 通用 benchmark 框架（长期战略，不属于当前版本）
- 多研究任务；task registry；统一协议；数据卡和任务卡；标准评分；可重复发布；版本化 benchmark suite；可选 leaderboard 或报告集合。

> 演进纪律：当前处于 BMK-L1。向 L2/L3/L4 演进必须先满足 `PHASE_GATES.md` 中 `Strategic Benchmark Track` 进入条件，且经作者人工批准；不得提前实现（防 R-16）；不得把上层能力写成当前已实现（防 R-17）。
