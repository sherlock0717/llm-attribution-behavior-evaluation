# 阶段门禁（PHASE_GATES）

> 每个阶段都有明确的进入条件与退出条件。未满足退出条件不得进入下一阶段。
> 通用安全护栏（所有阶段退出都必须满足）：
> - `outputs/**` 未变化（与 `docs/audit/baseline_hashes.txt` 比对）；
> - `src/stimuli.py` 与 `src/scales.py` 文本 hash 未变化（除非 Phase 2 授权的 v2 且 v1 副本 hash 仍不变）；
> - 未真实调用付费 API；未 commit / push（除非人工执行）；
> - 未进入下一阶段前已获人工批准。

---

## Phase 0 · 基线冻结与现状审计

**进入条件**
- 仓库已克隆、分支为 `refactor/v0.2-professionalization`；
- 工作区干净；
- Python 3.12 环境可用。

**退出条件**
- 9 个规划/治理文件已创建（audit + 6 planning + AGENTS + WORKLOG）；
- 受保护资产已记录；
- 未修改任何研究资产（`git status --short` 仅显示新增规划文件）；
- 人工审查通过并批准架构方案。

---

## Phase 1 · 工程基础

**进入条件**
- Phase 0 文档完成；
- 工作区干净；
- 受保护资产已记录（`baseline_hashes.txt`）；
- 架构方案已人工确认；
- 工程方案（`pyproject + uv.lock`）已批准（DEC-010）。（注：DEC-001 是**许可证**决定，非本阶段前置。）

**退出条件（当前版本）**
- 依赖可锁定：`uv sync` 通过；`ruff check .` 通过；
- characterization tests 通过（`pytest tests/characterization -q`，固定旧行为）；
- 输出隔离生效：旧脚本/新 CLI 均可指定输出目录，**永不写 `outputs/`**；
- 最小 CLI 可用：`python -m freewill_attribution.cli run --mock --out <tmp>`；
- 最小 schema/config 单测通过；
- CI 在 Windows + Linux 均绿；
- 旧入口仍可用（`python .\src\run_simulated_study.py --mock --out <tmp>` 等）；
- `outputs/` 未变化；`stimuli.py` / `scales.py` 文本 hash 未变化。

**不要求（明确不作为 Phase 1 退出条件）**
- 多 provider；多模型；benchmark registry；leaderboard；完整分析模块拆分。

---

## Phase 2 · 研究协议与刺激材料 v2

**进入条件**
- Phase 0 批准（可与 Phase 1 并行）；
- `protocols/` 目录规划确定；
- DEC-003（是否公开完整刺激材料）已决策或明确挂起。

**退出条件**
- `study_protocol_v2.md` 含预定义假设与计划对比；
- v1 材料/题项已冻结到 `data/stimuli/v1/`、`data/scales/v1/` 并附 hash，且与 `src/` 中 v1 文本 hash 一致；
- v2 通过长度/平衡/泄露/去元描述检查（`pytest tests/unit/test_stimuli_v2.py`）；
- `outputs/` 未变化；v1 文本 hash 未变化；
- 协议与 v2 人工批准。

---

## Phase 3 · 可追溯运行管线（3A / 3B）

**进入条件**
- Phase 1 退出条件满足（最小 package/schema/CLI/CI）；
- 运行所使用的材料版本**已冻结**（v1 已冻结即可；**不再无条件依赖 stimuli v2**——v2 接入属 Phase 3B，前置 Phase 2）；
- DEC-005（默认 provider）已决策；真实调用授权与预算上限（DEC-012）在 Phase 3A 真实 DeepSeek 调用前决策。

**退出条件（当前版本）**
- 一次 **mock 可追溯运行** 生成完整 `artifacts/runs/<id>/`（manifest/config/env/prompts/stimuli/raw/normalized/validation/checksum）；
- **DeepSeek provider 可显式启用**（默认不真实调用）；
- run manifest 含 git sha / model 名称与版本 / seed / temperature / retry / 失败类型 / checksum，以及 prompt、材料、配置版本；
- **token/cost 字段允许缺失或 provider 不返回**；
- runner 支持 resume + dry-run + 预算上限；
- 全流程**未覆盖 v1、未写 `outputs/`**；未真实调用付费 API（除非人工单独授权并记录）；
- `pytest tests/integration/test_run_manifest.py` 通过；
- （Phase 3B）以 v2 跑一次可追溯 mock run，且 v1 hash 未变。

**不要求（明确不作为 Phase 3 退出条件）**
- 多模型矩阵；benchmark 评分体系；leaderboard。

---

## Phase 4 · 统计分析与证据等级重构

**进入条件**
- Phase 3 退出条件满足；
- 存在至少一个可追溯 run（mock 或已授权真实 run）；
- DEC-009（项目定位）与分析主口径已决策。

**退出条件（当前版本硬性）**
- 六水平分类与趋势分析**分离**、分别报告；
- 计划对比、效应量、置信区间齐全；
- 路径分析**降级为探索性诊断**（非机制证据）；
- 结果可追溯到具体 run；
- 跨 domain/scenario 稳定性诊断产出；
- 每个 headline 结论附证据等级；
- mock 固定种子数值回归测试通过；
- 未手工修改任何分析数字；`outputs/` 未变化。

**不要求（转入 `BMK-*` 战略 backlog，非 Phase 4 退出条件）**
- 多模型稳定性；完整跨 prompt benchmark；通用模型排行榜。

---

## Phase 5 · 专业文档体系

**进入条件**
- Phase 4 证据等级产出；
- Phase 0 受保护资产表可用；
- v1 provenance 定性完成（H-00）：Data Card 明确 v1 = historical DeepSeek API baseline（真实来源已确认），历史运行元数据不完整。

**退出条件**
- Study/Data/Model Usage/Reproducibility/Limitations/Research Integrity 卡片齐全；
- `references.bib` 含 DOI/正式出版信息，理论来源与量表来源分列；
- 冗余展示材料已归档（移动非删除），正式入口确立；
- 文档口径与证据等级一致；
- `outputs/` 未变化；README 结果数字仍未改（留待 Phase 6）。

---

## Phase 6 · README 与网站同步

**进入条件**
- Phase 4 `analysis_summary.json` 与 Phase 5 卡片就绪；
- DEC-007（网站/仓库同步机制）已决策。

**退出条件**
- `site_export` 从指定 run 生成版本化 `site_summary.json`（含 run_id/版本/证据等级/数字）；
- README 结果数字来源单一、可追溯，一致性测试通过；
- 网站从 JSON 读取（网站改动为独立 PR）；
- 无手工数字同步；
- `outputs/` 历史未被覆盖。

---

## Phase 7 · 版本发布与归档

**进入条件**
- Phase 6 退出条件满足；
- v1 provenance statement 已完成（H-00 / DEC-008）；
- DEC-001/002/003/004（许可证、公开数据、公开材料、公开 prompt）已决策。（DEC-008“保留 v1 为基线”已定；是否**立即发 Release**为单独决定。）

**退出条件**
- v1 **provenance statement** 齐备：明确 v1 = historical DeepSeek API baseline，附 **v1 hash**，说明历史运行元数据不完整；
- **当前版本能力与 benchmark 未来方向分开描述**（不得把长期愿景写成当前能力，防 R-17）；
- `CHANGELOG.md` 完整；
- `artifacts/releases/<ver>/` 含 checksum，校验通过；
- 版本 tag 与 artifact 对应；
- release 含证据等级与边界声明；
- commit / push / tag / release 由**人工**执行并记录。

---

## Strategic Benchmark Track（长期，独立于 v0.2 门禁）

> 对应 DEC-011 与 `Strategic Horizon`（BMK-L1..L4）。**不属于 Phase 1–Phase 7 退出条件。**

**进入条件（建议）**
- 当前研究原型已稳定发布（Phase 7 完成）；
- 可追溯 runner 已稳定；
- 至少存在一个第二模型或第二研究任务的**真实需求**；
- 当前项目作者**人工批准**；
- benchmark 协议**先设计后实现**（不得直接堆功能）。

**纪律**
- 防 R-16（过早 benchmark 化范围失控）：不提前建 task registry / leaderboard / 多模型批量 runner；
- 防 R-17：release/README/网站分开写“当前能力”与“未来方向”，标注成熟度等级（BMK-L1..L4）。
