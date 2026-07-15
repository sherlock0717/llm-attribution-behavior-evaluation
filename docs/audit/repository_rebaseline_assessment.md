# Repository Rebaseline Assessment

> 本文件为 PLAN-001 的只读审计结论，形成于修改任何既有规划文件之前。
> 所有能力判断基于当前仓库实际文件与代码，历史结果数字直接来自 `outputs/**` 分析文件，不重新计算、不改写。
> 无法仅凭仓库确认的内容标记为 `未核实`。

审计分支：`docs/phase-and-showcase-plan`（基于 `refactor/v0.2-professionalization`，起始 HEAD `0aa8919d49af4d709dc2640385094e2e00731b00`）。

---

## 1. 审计范围与方法

**检查目录**：仓库根、`configs/`、`docs/`（含 `docs/audit/`、`docs/planning/`）、`outputs/`（含 `outputs/plots/`）、`scripts/`、`src/`（含 `src/freewill_attribution/`）、`tests/`（含 `unit/`、`integration/`、`characterization/`）、`.github/workflows/`。

**排除目录**：`.git`、`.venv`、`__pycache__`、`.pytest_cache`、`.ruff_cache`、系统临时目录、外部依赖包。

**未读取内容**：任何 `.env`、API key、access token、credential、Git credential 配置。经检查，仓库内**不存在** `.env` 文件，且 `.env` 已被 `.gitignore` 忽略（`git check-ignore .env` 命中）。

**程序化扫描**（一次性临时脚本，未入 Git）：
- 全部文本文件 UTF-8 编码检查；
- `pyproject.toml` TOML 解析、`configs/*.yaml` 与 `.github/workflows/ci.yml` YAML 解析、`outputs/*.json` JSON 解析；
- 全部 `outputs/` CSV 行列统计、JSONL/JSON 记录统计、PNG 尺寸读取；
- `scale_scores.csv` 逐行统计单元格分布；
- Markdown 本地链接目标存在性检查；
- 本地绝对路径扫描；
- secret-like 字符串扫描（只报文件/行号/命中类型，不显示疑似值）；
- TODO/FIXME/placeholder 扫描；
- `benchmark`/`production-ready`/`fully reproducible`/`SOTA` 等高风险表述扫描；
- 文档版本号与 `pyproject` 版本对照。

**不能直接确认的二进制内容**：11 个 PNG 图像的**具体视觉内容**无法在文本审计中查看；仅通过文件名、尺寸、以及对应生成脚本（`src/analyze_results.py`）与报告确认其用途，不臆测图形形态。

**测试收集**：仅执行 `pytest --collect-only -q`（见 §14），不运行完整回归。

---

## 2. 文件与资产总览

| 类别 | 数量 | 说明 |
|---|---|---|
| Git 跟踪文件 | 91 | `git ls-files` |
| 非排除项本地文件（含未跟踪，排除 .git/.venv/缓存） | 96 | 差异主要为规划/审计新文档草稿位置与本地临时无关文件；工作区 `git status` 干净 |
| 规划文档（`docs/planning/`） | 6 | PROFESSIONALIZATION_PLAN / ARCHITECTURE_PROPOSAL / EXECUTION_BACKLOG / PHASE_GATES / RISK_REGISTER / DECISION_LOG |
| 审计文档（`docs/audit/`） | 3 | baseline_hashes.txt / current_state_v0.1.md / v1_provenance_statement.md |
| 其他 docs | 8 | 研究设计、测量、量表来源、论文草稿、4 份展示/交接材料 |
| Python 文件（`src/`） | 15 | 旧研究脚本 8 + package 6 + `path_safety.py` 1 |
| 测试文件 | 14 | characterization 7 + integration 3 + unit 3 + conftest 1 |
| 配置（`configs/`） | 3 | study.default / prompt.v1 / model.mock（YAML 全部解析通过） |
| CI | 1 | `.github/workflows/ci.yml`（YAML 解析通过） |
| wrapper / 运行脚本 | 3 | 根 `run_all.ps1` + `scripts/run_all.ps1` + `scripts/run_all.sh` |
| 历史 outputs | 30 | 11 CSV + 11 PNG + 6 MD + 2 JSON |
| 图片/图表 | 11 | `outputs/plots/*.png` |
| 历史研究响应 | 360 | 由 `outputs/scale_scores.csv` 360 数据行直接证明（原始 JSONL 被 gitignore，不在仓库） |

程序化解析结果：编码全部 UTF-8（无非 UTF-8 文件、无 BOM 问题阻断）；TOML/YAML/JSON 全部解析通过；Markdown 本地链接**缺失目标 0**。

---

## 3. 当前真实能力

| 能力 | 状态 | 依据 |
|---|---|---|
| 历史研究基线（v1） | Historical only | `outputs/**` 30 文件；`scale_scores.csv` 360 行、12 单元格×30；`v1_provenance_statement.md` |
| Python package (`freewill_attribution`) | Partial | 仅 `__init__/cli/runner/config/schemas/paths`；无分析/provider/manifest 生产逻辑 |
| CLI (`python -m freewill_attribution.cli`) | Complete（mock-only） | `cli.py`：`run` 子命令强制 `--mock` + 必填 `--out`；不暴露真实 API |
| 安全输出（path safety） | Complete | `src/path_safety.py` + CLI/runner 强制显式 `--out`、拒绝写仓库 `outputs/` |
| schema / config | Partial | `schemas.py` 定义 RunManifest/ModelConfig 等；`config.py` 只读加载校验 YAML；**均未接入实际运行** |
| CI | Configured but unverified | `ci.yml` 配置 ubuntu+windows×py3.12 全流程；**无 GitHub-hosted 实际运行记录**（未 push） |
| wrapper（跨平台） | Complete（mock-only） | `scripts/run_all.{ps1,sh}` 转调 CLI，显式 mock 门禁，默认写系统临时目录 |
| analysis | Historical only | 分析逻辑在旧 `src/analyze_results.py`（720 行单文件），产出即 `outputs/**`；package 内无拆分分析模块 |
| reporting | Historical only | 旧 `generate_*_report.py` 产出历史 MD；无 site 导出脚本 |
| provider abstraction | Planned | 代码中**不存在** provider 接口；旧脚本直接耦合 openai/DeepSeek 客户端 |
| RunManifest（实际产出） | Planned | `schemas.RunManifest` 仅为数据模型定义；**无 runner 产出真实 manifest** |
| benchmark registry | Planned | 仅 `RunManifest.task_id/benchmark_id` 为保留字段（默认 None，未启用） |
| showcase（公开展示页） | Planned | 仓库内**无** `site/`、无 HTML/CSS/JS；README 引用一个外部作品集页 URL |

关键结论：`runner.py` 是**转调旧脚本 `src/run_simulated_study.py` 的 subprocess adapter**，明确声明不复制研究逻辑、不生成 manifest、不重试。因此"可追溯 runner / RunManifest / provider abstraction"当前均为 **Planned**，不得写成已完成。

---

## 4. 历史研究证据

- **记录数 360**：`outputs/scale_scores.csv` 恰 360 数据行（22 列）；`reliability_summary.csv` 全部 10 量表 `n_cases_complete=360`。
- **6×2×30 设计可由文件直接验证**：`scale_scores.csv` 中 `identity_label × process_condition` 共 **12 单元格，每格均为 30**。
  - identity_label：`AI 决策者`、`人类决策者`（2）。
  - process_condition：`direct_choice`、`direct_choice_long`、`alternatives`、`reasons_concise`、`reasons`、`reflection_feedback`（6），与 `configs/study.default.yaml` 完全一致。
- **provider**：历史基线来自 **DeepSeek API**（作者确认为真实 API 调用，见 `v1_provenance_statement.md`）。
- **真实输出与 mock 区分**：历史 360 条为真实 DeepSeek API 的模型生成记录（LLM 模拟被试）；`reliability_summary.csv` 备注统一为"Synthetic AI-simulated data; not formal human psychometric evidence."（此处 synthetic = AI/模型生成、非人类，**不等于** rule-based mock）。当前 package 的 mock 路径产出 `short_reason="mock synthetic response"`，仅用于工程/CI 流程验证，与历史研究输出分离。
- **已有结果**（均来自现有分析文件，未重算）：
  - factual manipulation check 随结构递增：`direct_choice=0.094`、`direct_choice_long=0.011`、`alternatives=1.011`、`reasons_concise=1.617`、`reasons=1.939`、`reflection_feedback=2.000`。
  - agency 条件均值：`direct_choice=4.308`…`reflection_feedback=5.200`；控制 perceived_intelligence + char_len 后 `process→agency` 仍显著（F=12.19，p<.001）。
  - free_will_attribution 直接 process 效应不稳定（控制后 F=0.711，p=.616）；但计划对比 `reasons_concise > direct_choice_long`（t=2.29，p=.024）、`reflection_feedback > direct_choice_long`（t=4.59，p<.001）。
  - 并行中介：agency indirect=0.2699，95% CI [0.1985, 0.3507]；perceived_intelligence indirect=0.0184，95% CI [-0.0068, 0.0442]。
- **证据边界**：单模型、单 prompt、提示暴露（构念名/题项/判断规则可见）、记录独立性有限；中介为探索性路径诊断，非机制证明；不外推为人类心理规律或所有模型的一般规律。

---

## 5. Provenance 缺口

严格区分三个层次（不得混同）：

1. **数据真实性**：`已确认`。360 条为真实 DeepSeek API 模型生成记录（作者确认，非 mock）。
2. **运行可审计性**：`不完整`。缺少完整历史 run manifest、DeepSeek 服务端精确模型快照、调用时间戳、token 用量、费用、prompt hash、dependency lock hash、完整环境快照、完整调用日志；原始 `raw_simulated_responses.jsonl` 与 `simulated_responses_wide.csv` 被 gitignore、不在公开仓库。
3. **完全复现能力**：`受限`。基于当前公开仓库可验证 commit、代码、聚合输出与 SHA-256 清单，并可运行 mock/分析流程；但**无法逐字节重放**历史 API 响应。

统一口径：provenance 不完整 = **运行级元数据缺失**，**不等于**数据真伪存疑。缺失元数据不得推测补写。

---

## 6. 现有规划冲突

| 文件 | 当前表述 | 实际状态 | 建议修改 |
|---|---|---|---|
| PROFESSIONALIZATION_PLAN.md §基线 L3 | "基线：commit `00c4725`" | 实际专业化主分支已推进至 `0aa8919`（FND-001~008 已合并） | 补注当前主分支 HEAD 与 Phase 1 本地完成状态 |
| PROFESSIONALIZATION_PLAN / PHASE_GATES Phase 1 | Phase 1 退出条件含"CI 在 Windows+Linux 均绿" | CI 仅**配置完成**，无 GitHub-hosted 运行 | 将 Phase 1 拆为"本地实现完成"与"远程发布验证待完成"两态；CI 绿移入统一发布验证（Phase 7） |
| EXECUTION_BACKLOG SITE-001 | "版本化 JSON 导出"（Phase 6） | 展示线被排到最后阶段 | 重定义 SITE-001 为"Showcase Content And Data Contract"并前移为并行 Track S；JSON 导出降为 SITE-002 |
| EXECUTION_BACKLOG FND-001~008 | 列为待执行任务 | 已全部本地实现、测试、提交并合并 | 标记为 Complete（本地实现），远程验证单列 |
| PHASE_GATES Phase 依赖 | Showcase 仅在 Phase 6 出现 | 展示可在本地并行建设、不依赖远程 CI | 新增 Track S 并明确不被 Phase 1 远程 CI 阻塞 |
| 全局测试策略 | 每次合并要求完整回归 | 文档/文案类改动不需 186 项回归 | 引入三级测试策略（Local/Milestone/Release） |
| README.md（**本轮不改**） | 仍为 v0.1 口径：`python .\src\run_simulated_study.py`、真实 API key 运行示例、n-per-cell 30；未提及新 package/CLI/mock-only 边界 | 与 v0.2 当前能力不同步 | 记录为冲突，留待后续获授权的 README 任务（Phase 6 / 专门任务），本轮不修改 |

---

## 7. 展示页可用资产

| 分级 | 资产 |
|---|---|
| 可直接公开 | 项目定位与研究问题文本；6×2 设计与 6 条件名称（来自 config/代码）；版本与阶段状态；`pyproject` 版本号 `0.2.0.dev0` |
| 需要摘要后公开 | `outputs/` 聚合 CSV 的派生数字（agency 均值、计划对比、中介 CI、factual check）；`outputs/plots/*.png` 中与当前脚本一致的 9 张图（需标题+来源+边界）；技术流程说明 |
| 暂不公开 | 论文草稿全文、内部报告全文（可摘要引用，不整篇搬运）；旧展示材料（去重后择一） |
| 禁止公开 | `AGENT_WORKLOG.md`、审计原文中的本地绝对路径、内部任务编号细节（仅在 Roadmap 技术详情简述）、任何原始响应/密钥/调试文件、`.env` |

图表说明：`outputs/plots/` 共 11 PNG，其中 9 张为 1760×800（与当前 `analyze_results.py` 输出一致），`mean_manipulation_check.png` 为 1440×800（尺寸不同，属旧命名遗留，见 current_state M-03），`mean_responsibility.png` 亦为旧命名候选。展示应仅复用与当前构念一致的图，并逐图标注来源与"AI 模拟数据"边界。

---

## 8. 展示页内容风险

| 风险 | 处置 |
|---|---|
| 过度声称 | 定位统一为"可复现的大模型模拟研究与模型行为评测原型"，不写 production benchmark |
| 将 mock 当研究结果 | 明确 360 = 真实 DeepSeek API 历史输出；mock 仅工程/CI 验证 |
| 将单模型结果推广为所有 LLM | 明示单模型（DeepSeek）、单 prompt，不外推 |
| 将模型模拟当人类心理规律 | 明示 LLM 模拟被试、非人类被试、不证明 AI 拥有自由意志 |
| 将配置完成写成验证通过 | CI 写 "configured, remote verification pending"，不写 "CI passing" |
| 将未来 benchmark 写成当前能力 | benchmark/多模型/provider/manifest 一律标 Planned |
| 暴露内部日志 | 不公开 AGENT_WORKLOG 与调试信息 |
| 暴露本地路径 | 展示资产不得含用户主目录形式的本地绝对路径；仅 `docs/audit/current_state_v0.1.md` 内部保留 1 处绝对路径（Internal-Only） |
| provenance 表述失真 | 数据真实性与运行可审计性分开表述 |

---

## 9. 阶段重新划分建议

- **Phase 1 · Engineering Foundation And Historical Baseline** — Local implementation complete / Release verification pending。
- **Phase 2 · Research Protocol Definition** — v1/v2 协议、RQ、假设、条件、材料/量表版本、prompt 暴露策略、解析契约、分析计划、成败判据（不要求真实 API）。
- **Phase 3A · Reproducible V1 Run** — 正式 runner、RunManifest、resolved config、prompt snapshot、hashes、artifacts、结构化失败、token/cost 可空、v1 mock/real 同结构。
- **Phase 3B · Improved V2 Protocol And Run** — blind construct names、改进 prompt、修订批次、retry/repair、v1/v2 比较。
- **Phase 4 · Providers And Multi-Model Execution** — provider abstraction、model matrix、并发、retry、rate limit、cost/token、model snapshot。
- **Phase 5 · Analysis And Reporting** — 标准化分析输入、自动报告、图表、v1/v2 比较、稳健性、失败分析、site-ready summary。
- **Phase 6 · Benchmark Track** — task registry、benchmark_id、task_id、多任务/模型/运行、BMK-L1~L4（不得写成当前能力）。
- **Phase 7 · Release And Audit** — 完整回归、GitHub-hosted Windows/Linux CI、provenance audit、release tag、GitHub Release、Pages 部署、在线链接校验、阶段退出记录。
- **Track S · Public Showcase（并行）** — S1 内容与数据契约（本轮）/ S2 站点数据导出 / S3 静态展示 MVP / S4 本地内容校验 / S5 部署（并入 Phase 7）。Track S **不被 Phase 1 远程 CI 阻塞**。

---

## 10. 推荐下一步

- **可立即推进（本地、并行）**：Track S 的 S1（本轮完成内容与数据契约）→ 下一分支 `feat/showcase-v1` 建设静态页 MVP（S2/S3/S4）。
- **可推迟**：Phase 4 多模型/provider、Phase 6 benchmark（保持 Planned）。
- **需统一发布验证（Phase 7）**：完整回归、GitHub-hosted 双平台 CI、Pages 部署、在线链接校验。
- **需用户额外授权**：真实 API 调用（DEC-012）、许可证选择（DEC-001）、公开数据/材料/prompt 范围（DEC-002/003/004）、push / tag / GitHub Release、README 改写。

---

## 阻断项自检（第二阶段·五）

| 检查 | 结果 |
|---|---|
| 所有跟踪文件已纳入清单 | 是（91 tracked） |
| 所有规划文件已实际阅读 | 是（6 planning + 3 audit） |
| 所有 Python 与测试文件已分类 | 是（15 src + 14 tests） |
| 所有历史 outputs 已程序化扫描 | 是（30 文件） |
| 未读取 secret | 是（仅报文件/行号，无 `.env`，无真实密钥值） |
| 未修改历史 outputs | 是 |
| 未修改既有规划文档（撰写本报告前） | 是 |
| 报告未把推测写成事实 | 是 |

阻断问题检查：
- 历史 360 条记录存在 → 是（`scale_scores.csv` 360 行）。
- 文件是否显示历史数据实为 mock → 否（synthetic=AI 模拟、非 rule-based mock；作者确认真实 DeepSeek API）。
- 当前分支与基线是否严重不一致 → 否（任务分支基于 `0aa8919`，工作区干净）。
- 是否发现未处理 secret 已被 Git 跟踪 → 否（23 处命中均为环境变量名 `DEEPSEEK_API_KEY` / `api_key` 字样，非密钥值）。
- 规划文件是否存在无法裁决的重大冲突 → 否（冲突均可依据现有材料给出建议，见 §6）。
- 页面公开是否导致明显隐私/版权风险 → 否（公开资产已分级，禁止公开项已隔离）。

**结论：无阻断问题。**

`AUDIT_GATE=PASS`
