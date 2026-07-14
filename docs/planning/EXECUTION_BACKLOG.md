# 执行任务清单（EXECUTION_BACKLOG）

> 编号前缀：`FND-`(工程基础) `RES-`(研究协议) `RUN-`(运行管线) `ANA-`(分析) `DOC-`(文档) `SITE-`(网站) `REL-`(发布)。
> 每个任务的粒度：一个 Agent 可在一个独立分支 / 一次明确工作中完成、测试并汇报。
> 本轮不执行任何任务，仅规划。

字段：编号 / 名称 / 阶段 / 优先级 / 前置 / 描述 / 涉及文件 / 明确不修改 / 交付物 / 验收命令 / 验收标准 / 风险 / 是否改变研究结果 / 需人工确认 / 推荐 Agent。

---

## 重定基线 Backlog（PLAN-001 · 2026-07-13）

> 本节为**当前权威任务清单**，依据 `docs/audit/repository_rebaseline_assessment.md`（`AUDIT_GATE=PASS`）。
> 本节之下的历史 backlog 条目保留作背景；SITE-001 的语义已由本节重定义（旧 SITE-001「版本化 JSON 导出」下移为 SITE-002）。冲突时以本节为准。

### 已完成（Phase 1 本地实现）
- **FND-001 ~ FND-008**：状态 **Complete（本地实现、测试、提交、合并均完成）**。远程 GitHub-hosted CI 验证单列，属 Phase 7 / Level 3。

### 已完成（规划与契约里程碑）
- **PLAN-001 · Rebaseline Phases And Showcase Track** — 状态：**Complete（local documentation and contract）**。已重设 Phase 1–7、加入并行 Track S、三级测试策略、更新 backlog 与决策日志。
- **SITE-001 · Showcase Content And Data Contract** — 状态：**Complete（local documentation and contract）**。已产出 information architecture、page copy、evidence boundaries、asset inventory、site data contract（见 `docs/planning/SHOWCASE_PLAN.md`、`docs/showcase/*`）。

### 展示页里程碑（`feat/showcase-v1` 分支连续完成）
- **SITE-002 · Site Data Export** — 状态：**Complete**。已产出 `scripts/build_site_data.py`、`site/data/site_summary.json`、`roadmap.json`、`version_history.json`、`historical_results.json`（`--check` 通过）。
- **SITE-003 · Static Showcase MVP** — 状态：**Complete**。已产出原生 HTML/CSS/JS 静态展示页（`site/`）。
- **SITE-004 · Local Showcase Validation** — 状态：**Complete**。本地静态服务 HTTP smoke、JSON/路径校验、证据检查通过。
- **SITE-005 · Public Showcase Content And Visual Redesign** — 状态：**Local implementation complete；Public refinement deferred to Phase 5/7；Deployment pending Phase 7**（已提交 `680de6c`、合并 `b375d5a`、推送 `origin/refactor/v0.2-professionalization`；公开发布未授权）。文案去模板化/去 AI 感重写，信息层级与视觉结构重构，新增 6×2 设计矩阵、流程图、条件比较条、证据三栏、复现组件链、版本时间线、路线图高亮等原生可视化；复用同 3 张历史图并放大 + `<dialog>` 灯箱；新增 `SHOWCASE_REDESIGN_AUDIT.md`、`VISUAL_ASSET_BRIEF.md`、`DELIVERY_PACKAGE_GUIDE.md`；扩展 site_summary 的 `design` 块。
- **SITE-005.1 · Showcase Accuracy, Native Visuals And Release-Safe Data** — 状态：**Complete locally；SITE-005 仍为 Current / awaiting human visual approval，未标为公开发布完成**。修正 source_commit 自引用（改为研究源最近提交，`--check` 稳定）、移除 `../` 失效链接（锚点 + `<code>` 路径）、Pipeline 三层化并纠正 `src/freewill_attribution/` 误标 Historical、跨平台表述（Windows + Git Bash，非 Linux/远程）、VIS-002/003 原生替换（页面无 "Visual asset pending"）、factual/中介表述收紧、mediation 结构化字段（estimate/ci_low/ci_high/crosses_zero/path_role）、read_note 数据化（移除 JS FIGURE_READS）、比较条中文标签。targeted：`--check` 通过、`tests/site` 44 passed、collect-only 230、HTTP+链接检查全 200。停在未提交，重新等待人工视觉与文案审核。
- **SITE-005.2 · Runtime Completion, Mobile Layout And Concept Visual** — 状态：**Complete locally；SITE-005 仍为 Current / awaiting human visual approval**。修复 Historical Results 缺失 `data-slot="figures"` 导致的 JS 运行中断（三张图/路径图/版本/路线图恢复渲染）；新增 `requireSlot` DOM slot 契约与 render-complete/diagnostics 标记；修复 390px 移动端横向溢出（`minmax(0,1fr)` + `min-width:0` + 断词）；过程梯度 6 列网格 + 独立 scale header；接入用户提供的研究问题概念图（`attribution-research-concept.png`，1586×992，SHA `FFCC3139…`，仅解释研究结构、不计入三张结果图），根目录暂存副本已删除。targeted：`--check` 通过、`tests/site` 57 passed、collect-only 243、HTTP smoke 12 项全 200。浏览器 dump-dom/截图命令被用户拒绝，故未做浏览器视觉/运行时验证（运行时经静态 slot 契约测试验证），已登记为 deferred validation（Phase 7）。展示页里程碑已人工授权提交并合并推送：commit `680de6cebb7c119f0bafb504e6fd069781a769fd`、merge `b375d5a421e6c7d46412dc262b14cc0e659bd251`、pushed `origin/refactor/v0.2-professionalization`；`feat/showcase-v1` 本地分支已删除；main 未改、未创建 PR。
- **REL-001 · Push, CI And Pages Release** — 状态：**Planned / requires push authorization**。统一发布验证（完整回归、GitHub-hosted Windows/Linux CI、Pages 部署、在线链接校验），需用户 push 授权（Phase 7）。

### 研究与运行主线（活动 ID 见下方权威表）
- **RES-001 · Research Protocol And Benchmark Contract** — 状态：**Ready for review after RBC-001.1**。产出 `docs/audit/research_protocol_source_map.md`（`PROTOCOL_SOURCE_GATE=PASS`，`gate_scope: historical_protocol_reconstruction_only`）、v1 历史协议（historical_reconstructed, executable=false）、v2 协议（draft_specification, executable=false）。
- **BMK-001 · Benchmark, Metric And Failure Contract** — 状态：**Ready for review after RBC-001.1**。产出 `BENCHMARK_SPEC.md`（benchmark_id=llm-attribution-behavior，current_maturity=pre-BMK-L1，target_maturity=BMK-L1，release_status=planned）、`METRIC_SPEC.md`、`FAILURE_TAXONOMY.md`、四份 YAML、契约测试。**current maturity: pre-BMK-L1；target maturity: BMK-L1**（不得写 BMK-L1 achieved）。不实现 runner/provider，不调用 API。
- **RUN-001 · Reproducible Mock Run Core** — 状态：**Blocked pending contract approval**。范围：TaskSpec → Runner → Mock Provider → Raw Response → Parser → Validation → Score → RunManifest → Aggregate Report（仅 mock；真实 DeepSeek provider/budget/retry/resume/concurrency/真实 API 门禁属 RUN-003）。依赖：RES-001、BMK-001 审核通过 + v2 Open Questions 人工裁决 + 运行授权。

<!-- ACTIVE_TASK_IDS_START -->
RES-001 | Research Protocol And Benchmark Contract
RES-002 | V2 Protocol Decision And Freeze
RES-003 | V2 Stimulus Set Design And Freeze
RES-004 | V2 Measurement And Construct Validation Plan
BMK-001 | Benchmark, Metric And Failure Contract
BMK-002 | Prompt Variant And Stability Protocol
BMK-003 | Second Model And Cross-Model Comparison
BMK-004 | Benchmark Metric Implementation
BMK-005 | Task Card And Benchmark Card
BMK-006 | Multi-Task Registry
BMK-007 | Benchmark Release Specification
RUN-001 | Reproducible Mock Run Core
RUN-002 | V2 Task Pack Integration
RUN-003 | Provider Interface And Run Control
<!-- ACTIVE_TASK_IDS_END -->

> 上表为 **RBC-001.1 权威活动任务 ID**。每个活动 ID 仅一个正式标题；本文件下方历史 backlog 中同号但不同含义的条目已标 **LEGACY**，不再作为活动任务。RUN-001 = Reproducible **Mock** Run Core（真实 provider/预算/重试/续跑/并发/真实 API 门禁在 RUN-003）。

### 发布
- **REL-001 · Push, CI And Pages Release** — 依赖：SITE-004、Phase 1 local implementation、**用户 push 授权**。统一执行完整回归、GitHub-hosted Windows/Linux CI、Pages 部署、在线链接校验、release。

> 纪律：SITE 任务**不推迟到最后阶段**，与研究开发并行；REL-001 之前不得 push、不得声称 CI 已绿。

---

## 第一批（Phase 1 工程基础，严格按序 · 2026-07-10 收敛后）

> 新顺序原则：**先固定旧行为 → 先解决输出覆盖风险 → 新 CLI 与旧入口并行（不立即改 thin wrapper）→ 不在 Phase 1 拆分完整分析模块、不接入多模型、不实现 benchmark**。
> CLI 统一使用 `python -m freewill_attribution.cli`，**不使用** `python -m src.freewill_attribution.cli`。

### FND-001 · 冻结 v0.1、计算 hash、建立作者 provenance 声明
- 阶段：Phase 0/1 交界 · 优先级：P0 · 前置：无
- 描述：记录并冻结基线 commit、依赖、环境；计算 `src/stimuli.py`/`src/scales.py`/`outputs/**` 的 sha256 清单；建立 **v1 provenance 声明**（v1 = historical DeepSeek API baseline，真实来源已由作者确认，历史运行元数据不完整，见 H-00；**不得伪造缺失元数据**）。
- 涉及文件（新增）：`docs/audit/baseline_hashes.txt`、`docs/audit/v1_provenance_statement.md`。
- 明确不修改：`src/**`、`outputs/**`。
- 交付物：hash 清单 + provenance 声明。
- 验收命令：`git rev-parse HEAD`；对受保护资产计算 sha256。
- 验收标准：清单可用于后续每个 gate 的 hash 比对；provenance 声明措辞与 DEC-008/H-00 一致。
- 风险：低（措辞需作者确认）。是否改变研究结果：否。需人工确认：是（provenance 措辞）。推荐 Agent：通用/研究。

### FND-002 · 建立 pyproject、uv、ruff、pytest 基础
- 阶段：Phase 1 · 优先级：P0 · 前置：FND-001
- 描述：新增 `pyproject.toml`（包元数据 + ruff + pytest 配置）；用 `uv` 生成 `uv.lock` 锁定当前依赖。保留 `requirements.txt`。
- 涉及文件（新增）：`pyproject.toml`、`uv.lock`；（可改）`requirements.txt`。
- 明确不修改：`src/stimuli.py`、`src/scales.py`（文本）、`outputs/**`。
- 交付物：可 `uv sync` 的锁定环境。
- 验收命令：`uv sync`；`ruff check .`；`python -m compileall -q src`（exit 0）。
- 验收标准：锁定后编译通过。
- 风险：依赖解析冲突。是否改变研究结果：否。需人工确认：否（工程方案 DEC-010 已批准；许可证 DEC-001 与此**无关**）。推荐 Agent：通用工程。

### FND-003 · 为当前旧代码建立 characterization tests
- 阶段：Phase 1 · 优先级：P0 · 前置：FND-002
- 描述：**先固定旧行为**：为现有 `src/*.py`（mock 固定种子）建立 characterization tests，捕获当前设计矩阵、材料长度、量表计分、mock 输出等的当前行为快照，作为后续重构的回归基准。
- **执行方式（重要）**：旧脚本在 FND-004 前**尚无安全 `--out` 参数**，因此 FND-003 **不得**直接在正式仓库调用会写 `outputs/` 的完整旧 CLI。
  - **允许的方法**：① import 函数进行纯函数测试；② 使用 pytest `monkeypatch` 替换模块级输出路径（如 `RAW_PATH`/`WIDE_PATH`/`OUT`）；③ 使用 `tmp_path`；④ 在临时 Git worktree 中运行；⑤ 对设计矩阵、材料、计分和 mock 响应做**内存级快照**。
  - **禁止**：在正式仓库执行旧脚本默认写入；修改 `outputs/**`；为了测试提前修改旧脚本；调用真实 API。
- 涉及文件（新增）：`tests/characterization/**`。
- 明确不修改：`src/**` 逻辑与文本；`outputs/**`。
- 交付物：可复跑的行为快照测试。
- 验收命令：`pytest tests/characterization -q`（写 `tmp_path`/系统临时目录，不写 `outputs/`）；**额外校验** `git diff -- outputs` 应为空。
- 验收标准：固定 mock 种子下行为被稳定捕获；`git diff -- outputs` 为空。
- 风险：快照过脆。是否改变研究结果：否。需人工确认：否。推荐 Agent：通用工程。

### FND-004 · 为旧运行脚本增加安全显式输出目录
- 阶段：Phase 1 · 优先级：P0 · 前置：FND-003
- 描述：**先解决输出覆盖风险**。**统一设计为：生成类命令必须显式提供 `--out`**（不使用模糊的“默认写临时/指定目录”）。不改研究逻辑。
- **输出规则**：
  - 未提供 `--out` 时 **fail fast**，显示使用帮助；
  - `--out` **不得解析到仓库受保护的 `outputs/`**；
  - `--fresh` 只能清理**该次显式指定**的输出目录；
  - 分析脚本的**读取与写入目录都必须显式提供**：只读兼容历史入口须区分 `--input`（读）与 `--out`（写），**不得根据当前工作目录隐式推断**；
  - 测试使用 pytest `tmp_path` 或系统临时目录；
  - **不保留任何可能默认覆盖历史 `outputs/` 的路径**。
- 涉及文件（改）：`src/run_simulated_study.py`、`src/analyze_results.py` 的输入/输出路径参数（不动统计/材料逻辑）。
- 明确不修改：`outputs/**`（只读保留）；`stimuli.py`/`scales.py` 文本。
- 交付物：旧脚本必须显式 `--out`/`--input`，无隐式默认写路径。
- 验收命令：`python .\src\run_simulated_study.py --mock --n-per-cell 2 --out <tmp>`；不带 `--out` 应 fail fast；随后 `git diff -- outputs` 为空。
- 验收标准：无路径可意外覆盖 `outputs/`；characterization tests 仍通过；`git diff -- outputs` 为空。
- 风险：入口签名变化影响旧调用习惯。是否改变研究结果：否。需人工确认：否。推荐 Agent：通用工程。

### FND-005 · 建立最小 package 与新 CLI，旧入口暂时保持不动
- 阶段：Phase 1 · 优先级：P0 · 前置：FND-004
- 描述：创建最小 package `src/freewill_attribution/{__init__,cli,paths,runner}.py` 与新 CLI `python -m freewill_attribution.cli`；**新 CLI 与旧入口并行，暂不把旧脚本改成 thin wrapper**。
- 涉及文件（新增）：`src/freewill_attribution/**`。
- 明确不修改：`src/*.py` 旧脚本（保持不动）；`stimuli.py`/`scales.py` 文本；`outputs/**`。
- 交付物：`python -m freewill_attribution.cli --help` 可用；`... run --mock --out <tmp>` 可用。
- 验收命令：`python -m freewill_attribution.cli run --mock --n-per-cell 2 --out <tmp>`；`pytest -q`。
- 验收标准：新 CLI 可跑 mock 并写独立目录；旧入口仍可用。
- 风险：CLI 与旧入口行为漂移。是否改变研究结果：否。需人工确认：是（包命名）。推荐 Agent：通用工程。

### FND-006 · 建立最小 schema 与 config
- 阶段：Phase 1 · 优先级：P0 · 前置：FND-005
- 描述：用 pydantic 实现**最小** `schemas.py`（RunManifest/NormalizedResponse/ValidationError 等核心对象，预留 `task_id`/`benchmark_id`，不绑定 DeepSeek 专有字段）与 `config.py`；错误分类 api/parse/schema/range/missing/runtime。**不建完整 providers/study 子包**。
- 涉及文件（新增）：`.../schemas.py`、`.../config.py`、`configs/*.yaml`。
- 明确不修改：`outputs/**`、材料/题项文本。
- 交付物：schema 单测通过。
- 验收命令：`pytest tests/unit/test_schemas.py -q`。
- 验收标准：非法响应被正确分类拦截；schema 保留扩展字段。
- 风险：schema 过严。是否改变研究结果：否。需人工确认：否。推荐 Agent：通用工程。

### FND-007 · 建立 GitHub Actions
- 阶段：Phase 1 · 优先级：P1 · 前置：FND-006
- 描述：`.github/workflows/ci.yml`：矩阵 Windows + Linux；`uv sync` + `ruff check` + `pytest` + mock smoke。**不含**多 provider/多模型/benchmark 步骤。
- 涉及文件（新增）：`.github/workflows/ci.yml`。
- 明确不修改：`outputs/**`。
- 交付物：CI 绿。
- 验收命令：CI run（或本地等价命令）。
- 验收标准：两平台通过；CI 不触真实 API、不写 `outputs/`。
- 风险：CI 环境差异。是否改变研究结果：否。需人工确认：否。推荐 Agent：CI/DevOps。

### FND-008 · 建立跨平台运行脚本
- 阶段：Phase 1 · 优先级：P1 · 前置：FND-005
- 描述：`scripts/run_all.ps1`(兼容旧) + `scripts/run_all.sh`(Linux/WSL)，统一转调新 CLI，默认写临时/指定目录，永不写 `outputs/`。
- 涉及文件（新增）：`scripts/run_all.sh`、`scripts/run_all.ps1`（兼容封装；根目录 `run_all.ps1` 暂不动）。
- 明确不修改：`outputs/**`；根目录 `run_all.ps1`（Phase 1 保持不动）。
- 交付物：两平台 mock 冒烟一致。
- 验收命令：`bash scripts/run_all.sh --mock`；`pwsh scripts/run_all.ps1 -Mock`。
- 验收标准：跨平台行为一致。
- 风险：换行/编码差异。是否改变研究结果：否。需人工确认：否。推荐 Agent：通用工程。

---

## LEGACY 研究协议草案（Phase 2 · 已被上方权威活动表取代）

> **LEGACY**：本节任务编号为历史草案，已被"活动主线任务 ID 权威表"取代，**不得作为活动任务**。活动含义以权威表为准。

### LEGACY RES-001(old) · 研究协议 v2（预定义假设）
- 阶段：Phase 2 · 优先级：P1 · 前置：FND-005
- 描述：撰写 `protocols/study_protocol_v2.md`：RQ、预定义假设、计划对比、变量独立性、随机化与平衡方案、证据等级预设。
- 涉及文件（新增）：`protocols/study_protocol_v2.md`。
- 明确不修改：`src/stimuli.py`、`src/scales.py`、`outputs/**`。
- 交付物：协议文档。
- 验收命令：markdown lint；人工审阅。
- 验收标准：假设与后续分析口径一一对应。
- 风险：与既有报告口径冲突。是否改变研究结果：是（表述）。需人工确认：是。推荐 Agent：研究。

### LEGACY RES-002(old) · 刺激材料 v2 设计与冻结
- 阶段：Phase 2 · 优先级：P1 · 前置：RES-001、FND-004（输出隔离）
- 描述：设计 v2：长度矩阵化控制、去元描述、valence 与 domain/fixed_choice 解耦、情境随机化；v1 冻结到 `data/stimuli/v1/`。
- 涉及文件（新增）：`data/stimuli/v1/**`、`data/stimuli/v2/**`、`tests/unit/test_stimuli_v2.py`。
- 明确不修改：`src/stimuli.py` v1 文本（hash 不变）、`outputs/**`。
- 交付物：v2 材料 + 平衡/长度/泄露检查报告。
- 验收命令：`pytest tests/unit/test_stimuli_v2.py -q`。
- 验收标准：长度跨条件可控；无元描述；valence 独立。
- 风险：改写偏离构念。是否改变研究结果：是。需人工确认：是（DEC 公开材料）。推荐 Agent：研究。

### LEGACY RES-003(old) · 题项去重与区分效度前置设计
- 阶段：Phase 2 · 优先级：P2 · 前置：RES-001
- 描述：针对 agency/autonomy/free_will/perceived_intelligence 重叠（M-06）设计区分度改写与 EFA/CFA 计划；补 factual check 不算 alpha（M-04）。
- 涉及文件（新增）：`data/scales/v2/**`、`protocols/measurement_protocol_v2.md`。
- 明确不修改：`src/scales.py` v1 文本、`outputs/**`。
- 交付物：v2 题项池 + 验证计划。
- 验收标准：题项重叠显著降低（人工+相似度检查）。
- 风险：改动构念含义。是否改变研究结果：是。需人工确认：是。推荐 Agent：研究/测量。

---

## LEGACY 运行管线草案（Phase 3A/3B · 已被上方权威活动表取代）

> **LEGACY**：本节任务编号为历史草案，已被权威活动表取代，**不得作为活动任务**。新 RUN-001 = Reproducible Mock Run Core；provider/预算/重试/续跑属 RUN-003。

### LEGACY RUN-001(old) · provider 可替换接口 + mock/DeepSeek 单实现（Phase 3A）
- 阶段：Phase 3A · 优先级：P1 · 前置：FND-006（schema）
- 描述：定义**可替换** provider 接口 + `mock` + 单一 `deepseek` 实现；记录 retry/失败类型，**token/cost 允许缺失或 provider 不返回**；默认不真实调用。**不建多 provider 生态/多模型批量**。
- 涉及文件（新增）：`.../providers/**`（单实现）。
- 明确不修改：`outputs/**`；真实 API 默认关闭。
- 验收命令：`pytest tests/unit/test_providers.py`（mock）。
- 验收标准：接口可替换；DeepSeek 走 dry-run/契约测试。
- 风险：密钥泄露/费用。是否改变研究结果：否。需人工确认：是（DEC-005 provider）。推荐 Agent：工程。

### LEGACY RUN-002(old) · run manifest 与运行目录（Phase 3A）
- 阶段：Phase 3A · 优先级：P1 · 前置：RUN-001、FND-004（输出隔离）
- 描述：runner 生成完整 `artifacts/runs/<id>/`（manifest/config/env/prompts/stimuli/raw/normalized/validation/checksum）；使用**已冻结的 v1/mock 材料**（不依赖 v2）。
- 涉及文件（新增）：`.../runner.py`（在最小 runner 上扩展）。
- 明确不修改：`outputs/**`。
- 验收命令：`python -m freewill_attribution.cli run --mock --out artifacts/runs/<id>`；`pytest tests/integration/test_run_manifest.py`。
- 验收标准：manifest 含全部**可得**溯源字段（token/cost 可空）；checksum 可校验。
- 风险：resume 幂等。是否改变研究结果：否。需人工确认：否。推荐 Agent：工程。

### LEGACY RUN-004(old) · 将 stimuli v2 接入 runner（Phase 3B）
- 阶段：Phase 3B · 优先级：P2 · 前置：RUN-002、RES-002（v2 冻结）
- 描述：把冻结的 stimuli v2 接入同一 runner，v1/v2 并存可追溯。
- 明确不修改：`outputs/**`、v1 文本 hash。
- 验收命令：`python -m freewill_attribution.cli run --mock --stimuli v2 --out artifacts/runs/<id>`。
- 验收标准：v2 可追溯运行；v1 hash 未变。是否改变研究结果：否。需人工确认：否。推荐 Agent：工程。

### LEGACY RUN-003(old) · resume / dry-run / 预算上限
- 阶段：Phase 3 · 优先级：P2 · 前置：RUN-002
- 描述：断点续跑、dry-run 预估调用数/费用、`max_calls`/`max_cost` 硬上限。
- 涉及文件（改）：`.../study/runner.py`、`config.py`。
- 验收命令：中断后重跑不重复；`--dry-run` 只预估。
- 验收标准：预算超限即停。是否改变研究结果：否。需人工确认：是（DEC-012 授权与预算上限）。推荐 Agent：工程。

---

## 分析（Phase 4）

### ANA-001 · 分析模块拆分 + 6 水平/趋势分离
- 阶段：Phase 4 · 优先级：P1 · 前置：RUN-002
- 描述：拆 `analysis/*`；6 水平分类为主口径，趋势编码显式声明为辅（修复 H-03）；效应量 + CI。
- 涉及文件（新增）：`.../analysis/**`。
- 明确不修改：`outputs/**` 旧数字；不手工改结果。
- 验收命令：`pytest tests/unit/test_analysis.py`；mock 数值回归。
- 验收标准：两种编码分别报告；效应量/CI 齐全。
- 风险：口径变化改结论。是否改变研究结果：是。需人工确认：是。推荐 Agent：分析。

### ANA-002 · 计划对比与跨情境稳定性
- 阶段：Phase 4 · 优先级：P2 · 前置：ANA-001
- 描述：预注册计划对比；**跨 domain/scenario 稳定性（当前硬性）**；跨 prompt/model 稳定性为**可选、非硬性**（转 `BMK-*`，不作 Phase 4 退出条件）。
- 涉及文件（新增）：`.../analysis/stability.py`。
- 验收命令：`pytest tests/unit/test_stability.py`。是否改变研究结果：是。需人工确认：是。推荐 Agent：分析。

### ANA-003 · 证据等级标注
- 阶段：Phase 4 · 优先级：P1 · 前置：ANA-001
- 描述：为每个结论打 descriptive / exploratory_path_diagnostic / not_mechanism_evidence；中介归为路径诊断。
- 涉及文件（新增）：`.../analysis/evidence.py`。
- 验收标准：每个 headline 结论有等级。是否改变研究结果：是（表述）。需人工确认：是。推荐 Agent：分析/研究。

---

## 文档（Phase 5）

### DOC-001 · Study Card
- 阶段：Phase 5 · 优先级：P1 · 前置：ANA-003
- 涉及文件（新增）：`docs/cards/study_card.md`。不修改：`outputs/**`。需人工确认：是（定位）。推荐 Agent：文档。

### DOC-002 · Data Card + Model Usage Card
- 阶段：Phase 5 · 优先级：P1 · 前置：RUN-002、FND-001（v1 provenance）
- 描述：数据来源、n 记录/运行/prompt/模型/独立模型系统/人类被试的严格区分；模型版本/温度/seed/费用；**v1 明确标注为 historical DeepSeek API baseline（真实来源已确认，历史 provenance 不完整，见 H-00），不得写成 mock**。
- 涉及文件（新增）：`docs/cards/data_card.md`、`docs/cards/model_usage_card.md`。需人工确认：是（provenance 措辞）。推荐 Agent：文档。

### DOC-003 · Reproducibility + Limitations + Research Integrity
- 阶段：Phase 5 · 优先级：P1 · 前置：FND-006、ANA-003
- 涉及文件（新增）：`docs/cards/reproducibility.md`、`limitations.md`、`research_integrity.md`。推荐 Agent：文档。

### DOC-004 · 文献库
- 阶段：Phase 5 · 优先级：P2 · 前置：无
- 描述：补齐 Gray/Wegner、FAD-Plus、Godspeed 等 DOI 与正式出版信息，区分理论来源与量表来源。
- 涉及文件（新增）：`references/references.bib`。需人工确认：否。推荐 Agent：研究/文档。

### DOC-005 · 归档冗余展示材料 + 正式入口梳理
- 阶段：Phase 5 · 优先级：P2 · 前置：DOC-001
- 描述：将 4 份重叠展示材料移入 `docs/archive/`（移动非删除），确立正式入口。
- 涉及文件（移动）：`docs/portfolio_research_case.md` 等。不修改：`outputs/**`、README 数字。推荐 Agent：文档。

---

## 网站（Phase 6）

### SITE-001 · 版本化 JSON 导出
- 阶段：Phase 6 · 优先级：P1 · 前置：ANA-003
- 涉及文件（新增）：`.../reporting/site_export.py`、`artifacts/releases/<ver>/site_summary.json`。
- 验收命令：`... site-export --run <id>`；JSON schema 校验。需人工确认：是（DEC 同步）。推荐 Agent：工程。

### SITE-002 · 网站读取版本化结果
- 阶段：Phase 6 · 优先级：P1 · 前置：SITE-001
- 描述：网站（独立仓库/PR）改为读取 `site_summary.json`，展示证据等级/版本/run 信息。
- 明确不修改：研究仓库 `outputs/**`。需人工确认：是。推荐 Agent：前端。

### SITE-003 · README 数字单一来源
- 阶段：Phase 6 · 优先级：P1 · 前置：SITE-001
- 描述：README 结果数字改为引用 JSON / 由脚本注入，加一致性测试。
- 涉及文件（改）：`README.md`。需人工确认：是。推荐 Agent：文档/工程。

---

## 发布（Phase 7）

### REL-001 · changelog + checksum + release artifact
- 阶段：Phase 7 · 优先级：P2 · 前置：SITE-003、DOC-003
- 涉及文件（新增）：`CHANGELOG.md`、`artifacts/releases/v0.2.0/**`。需人工确认：是（DEC 固化 v1/许可证）。推荐 Agent：发布。

### REL-002 · 版本标签与 GitHub Release
- 阶段：Phase 7 · 优先级：P2 · 前置：REL-001
- 描述：打 tag、创建 Release。**commit/push/tag/release 全部由人工执行**，Agent 不自动执行。
- 需人工确认：是（强制）。推荐 Agent：发布（仅准备产物）。

---

## 依赖速查（2026-07-10 收敛后）

```text
FND-001 → FND-002 → FND-003 → FND-004 → FND-005 → FND-006 → FND-007
FND-005 → FND-008
FND-006 → RUN-001 → RUN-002(+FND-004) → RUN-003        # Phase 3A
FND-005 → RES-001 → RES-002(+FND-004), RES-003          # Phase 2
RUN-002 + RES-002 → RUN-004                              # Phase 3B
RUN-002 → ANA-001 → ANA-002, ANA-003                     # Phase 4
ANA-003 → DOC-001/003, SITE-001 → SITE-002/003 → REL-001 → REL-002
FND-001 → DOC-002（v1 provenance）
[BMK-001..006 · Future · 不在上面链路中，不属于 Phase 1–7 退出条件]
```

---

## LEGACY Future Strategic Backlog · Benchmark Evolution（已被权威活动表取代）

> **LEGACY**：以下 `BMK-*` 历史草案编号已被上方权威活动表取代，不得作为活动任务。

> 对应 DEC-011 与 `PROFESSIONALIZATION_PLAN.md` 的 `Strategic Horizon`。
> 所有 `BMK-*` 任务统一标记：
> ```text
> 状态：Future
> 不属于当前 v0.2 必做
> 不属于 Phase 1—Phase 7 退出条件
> ```
> 未经作者人工批准，不得提前执行；不得为其预先创建大量空模块（防 R-16）。

### LEGACY BMK-001(old) · 多 prompt 配置与稳定性协议
- 成熟度：BMK-L2 · 描述：支持 blinded / exposed / batched 等 prompt 配置；统一版本与比较方法。
- 前置：RUN-002 稳定。状态：Future。

### LEGACY BMK-002(old) · 第二模型接入与跨模型比较
- 成熟度：BMK-L3 · 描述：在 runner 稳定后接入一个额外模型，做跨模型比较；**不在当前 Phase 1 执行**。
- 前置：RUN-001/002 稳定 + 作者批准。状态：Future。

### LEGACY BMK-003(old) · 统一模型行为指标
- 成熟度：BMK-L2/L3 · 描述：定义条件敏感性、稳定性、方向一致性、prompt 依赖、模型间差异等指标。
- 前置：BMK-001/002。状态：Future。

### LEGACY BMK-004(old) · Task Card 与 Benchmark Card
- 成熟度：BMK-L4 · 描述：为未来多任务扩展建立任务描述规范（任务卡/benchmark 卡）。
- 前置：至少一个第二研究任务的真实需求。状态：Future。

### LEGACY BMK-005(old) · 多任务 registry 设计
- 成熟度：BMK-L4 · 描述：task registry 设计与实现；**仅在至少存在两个真实研究任务后执行**。
- 前置：BMK-004 + 两个真实任务。状态：Future。

### LEGACY BMK-006(old) · Benchmark release 规范
- 成熟度：BMK-L4 · 描述：版本、数据、模型、配置、评分、报告的统一发布规范；版本化 benchmark suite。
- 前置：BMK-005。状态：Future。
