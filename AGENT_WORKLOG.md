# AGENT_WORKLOG · 工作日志

> 只记录真实执行的操作与真实结果。不得把未执行的测试写成通过。

---

## 2026-07-10 · Phase 0 基线冻结与现状审计

- **日期时间**：2026-07-10 16:12（本地）
- **当前分支**：`refactor/v0.2-professionalization`
- **当前 commit**：`00c4725`（full `00c4725dc7b891de3a7bfa11b4856be177d9d2a6`），message `Initial public portfolio version`
- **基线 smoke test 状态**：由上游告知“已在临时 worktree 完成隔离 smoke test 并通过”；本轮**未重跑**，仅作声明记录（`未核实`具体命令与输出）。
- **本轮目标**：完成 Phase 0 —— 现状审计、目标架构设计、实施流程规划与任务拆解；不进入 Phase 1。

### 阅读文件
- 代码：`src/stimuli.py`、`src/scales.py`、`src/run_simulated_study.py`、`src/analyze_results.py`、`src/validate_materials.py`、`src/generate_pilot_report.py`、`src/generate_n20_construct_validation_report.py`、`src/generate_n30_stability_replication_report.py`
- 配置/入口：`README.md`、`requirements.txt`、`run_all.ps1`、`.gitignore`
- 文档：`docs/scale_source_mapping.md`、`docs/measurement_plan.md`、`docs/research_design_blueprint.md`、`docs/paper_draft_simulated_study.md`、`docs/portfolio_research_case.md`、`docs/project_one_page_summary.md`、`docs/project_showcase_summary.md`、`docs/codex_to_chatgpt_handoff.md`、`docs/interview_explanation_script.md`
- 输出：`outputs/reliability_summary.csv`、`outputs/parallel_mediation_summary.json`、`outputs/plots/`（列表）

### 新增文件（本轮）
- `docs/audit/current_state_v0.1.md`
- `docs/planning/PROFESSIONALIZATION_PLAN.md`
- `docs/planning/ARCHITECTURE_PROPOSAL.md`
- `docs/planning/EXECUTION_BACKLOG.md`
- `docs/planning/PHASE_GATES.md`
- `docs/planning/RISK_REGISTER.md`
- `docs/planning/DECISION_LOG.md`
- `AGENTS.md`
- `AGENT_WORKLOG.md`

### 修改文件（本轮）
- 无（未修改任何既有研究资产）。

### 执行命令与结果（真实）
| 命令 | 结果 |
|---|---|
| `git status` / `git status --short` | `On branch refactor/v0.2-professionalization` / `nothing to commit, working tree clean`；`--short` 为空 |
| `git branch --show-current` | `refactor/v0.2-professionalization` |
| `git log -1 --oneline` | `00c4725 Initial public portfolio version` |
| `git remote -v` | `origin https://github.com/sherlock0717/llm-agent-free-will-attribution.git (fetch/push)` |
| `git rev-parse HEAD` | `00c4725dc7b891de3a7bfa11b4856be177d9d2a6` |
| `git ls-files | Measure-Object -Line` | 51 个已跟踪文件 |
| `.\.venv\Scripts\python.exe --version` | `Python 3.12.10` |
| `.\.venv\Scripts\python.exe -m pip list` | 关键：scipy 1.18.0, numpy 2.5.1, pandas 3.0.3, statsmodels 0.14.6, matplotlib 3.11.0, openai 2.45.0, pydantic 2.13.4, python-dotenv 1.2.2, tqdm 4.68.4 |
| `python -m compileall -q src` | exit 0（通过） |

> 备注：`git` 不在 PATH，使用完整路径 `C:\Program Files\Git\cmd\git.exe` 执行。

### 发现问题（摘要，详见 `current_state_v0.1.md §D`）
- **B-01（阻断）**：360 条公开结果来自真实 API 还是 mock 无法从仓库核实（原始 JSONL/宽表被 gitignore，无 manifest；信度 alpha 0.86–0.98 异常整齐）。
- **H-01**：n=360 为单模型/单 prompt 记录数，非独立样本（伪重复风险）。
- **H-02**：prompt 暴露构念名 + 全部题项 + 判断规则（迎合/泄露风险）。
- **H-03**：6 水平分类与 4 级趋势编码混用（`structure_level` 压缩为 0,0,1,2,2,3）。
- **H-05**：输出写死 `outputs/`，`--fresh` 会 unlink，无 run 隔离/manifest。
- 其余 M/L 级见审计文件。

### 未解决问题
- B-01 数据来源需作者澄清。
- `outputs/final_simulated_pilot_report.md` 生成脚本未定位（`未核实`）。
- 网站数字与运行的对应关系（`未核实`）。

### 人工决策点
- 见 `docs/planning/DECISION_LOG.md`（DEC-001 ~ DEC-009，全部 Pending）。
- 需优先澄清：B-01（数据来源）、DEC-009（项目定位）、DEC-001（许可证）。

### 下一步建议
- 人工审查本轮 9 个规划文件；批准 `ARCHITECTURE_PROPOSAL.md`。
- 批准后从 `FND-001`（冻结并记录 v0.1 基线 hash）开始 Phase 1，单任务、单分支推进。
- 本轮**停止**，不进入 Phase 1。

---

## 2026-07-10 · 作者事实补充与审计更正

项目作者确认：
当前公开的 360 条 v1 记录来自真实 DeepSeek API 调用，
不是 mock_response() 生成的数据。

因此：
- 原 B-01 的数据来源不明判断已撤销；
- 不再以 Alpha 或结果分布推测数据来源；
- 当前问题重新归类为历史运行 provenance 不完整；
- v1 保留为 DeepSeek 历史真实 API 基线；
- 不得伪造缺失的历史运行元数据。

> 说明：以上为**作者事实补充**。上文 2026-07-10 早先记录中 Agent 当时“B-01 数据来源需作者澄清”的**原始判断予以保留**（不删除），仅在此更正结论。

### Phase 0.1 · 规划事实校正与路线收敛（本轮操作）

- **分支**：`refactor/v0.2-professionalization`；**commit**：`00c4725`（未 commit 本轮改动）。
- **本轮目标**：写入作者决策（定位/建设范围/v1 provenance/benchmark 战略），校正数据来源口径，收敛架构与 Phase 1 顺序，保留 benchmark 长期路线。
- **本轮只修改规划/治理文档，未触碰代码/材料/outputs/README/网站。**
- **修改文件**：
  - `docs/audit/current_state_v0.1.md`（B-01 撤销→H-00；§F 移除“来源存疑”，保留历史元数据缺失；§E 增 v1 baseline 定性）；
  - `docs/planning/PROFESSIONALIZATION_PLAN.md`（三层目标；阶段依赖含 3A/3B；Phase 1/3/4/7 调整；新增 Strategic Horizon BMK-L1..L4）；
  - `docs/planning/ARCHITECTURE_PROPOSAL.md`（§B.1 最小 package；§B.2 保留接口/不实现清单；迁移策略改并行；RunManifest 预留 task_id/benchmark_id；§G Strategic Horizon）；
  - `docs/planning/EXECUTION_BACKLOG.md`（FND-001..008 新顺序；CLI 口径；RUN 3A/3B；新增 Future Strategic Backlog BMK-001..006）；
  - `docs/planning/PHASE_GATES.md`（Phase 1/3/4/5/7 退出条件收敛；新增 Strategic Benchmark Track）；
  - `docs/planning/RISK_REGISTER.md`（R-15 重写为 provenance 不完整；新增 R-16 过早 benchmark、R-17 愿景当能力；旧重构风险改编号 R-18）；
  - `docs/planning/DECISION_LOG.md`（DEC-008/009 → Decided；新增 DEC-010/011；DEC-001 澄清仅为许可证）；
  - `AGENTS.md`（新增“零、不可违反的项目口径”10 条）；
  - `AGENT_WORKLOG.md`（本条）。
- **执行命令**：仅只读校验（见本轮汇报）；未运行任何生成脚本，未调用 API。
- **下一步**：人工审查校正后的 9 份文档；批准后按新 FND 顺序进入 Phase 1。**本轮停止，不进入 FND-001。**

### Phase 0.2 · 规划文档一致性修正（本轮操作）

- **目标**：修正规划/治理文档间的残余不一致（旧 B-01 口径、任务/决策编号错配、runner 边界、FND-003/004 执行规则、预算决策引用）。
- **本轮只修改规划/治理文档，未触碰代码/材料/outputs/README/网站。**
- **修改文件**：
  - `PROFESSIONALIZATION_PLAN.md`（Phase 0 风险/决策点改为 v1 provenance 口径；Phase 3A 预算引用改 DEC-012）；
  - `DECISION_LOG.md`（标题“待决策条目”→“决策条目”；DEC-002 移除旧编号交叉引用并改影响范围；新增 DEC-012 真实 API 授权与预算上限，Pending）；
  - `RISK_REGISTER.md`（R-05 输出隔离改 FND-004；R-09 跨平台 FND-008 / CI FND-007；R-14 许可证改 DEC-001；R-06 关联 DEC-012+RUN-003）；
  - `ARCHITECTURE_PROPOSAL.md`（§B.1 明确 Phase 1 runner/schema 边界与 Phase 3A 交付分界，临时 manifest 标 ManifestStub）；
  - `EXECUTION_BACKLOG.md`（FND-003 characterization 安全执行方式与 `git diff -- outputs` 校验；FND-004 显式 `--out` fail-fast、`--input`/`--out` 分离；RUN-003 预算引用改 DEC-012）；
  - `AGENTS.md`（FND 分支示例更新为与 backlog 一致，并加“分支名以 backlog 为准”规则）；
  - `AGENT_WORKLOG.md`（本条）。
- **未改**：`current_state_v0.1.md`、`PHASE_GATES.md` 核心口径（PHASE_GATES 仅为预算交叉引用在 Phase 3 进入条件补 DEC-012）。
- **执行命令**：仅只读校验（见本轮汇报）；未运行生成脚本，未调用 API。
- **下一步**：人工审查；批准后进入 FND-001。**本轮停止，不进入 FND-001。**

---

## 2026-07-10 · FND-001 · 冻结 v0.1、计算 hash、建立作者 provenance 声明

- **日期时间**：2026-07-10 17:30（本地）
- **分支**：`chore/fnd-001-freeze-v01-baseline`（从 `refactor/v0.2-professionalization` 新建切出）
- **HEAD**：`00c4725dc7b891de3a7bfa11b4856be177d9d2a6`（未 commit，工作树 HEAD 未变）
- **本轮任务**：FND-001（仅冻结与声明，不进入 FND-002）
- **阅读文件**：`AGENTS.md`、`AGENT_WORKLOG.md`、`docs/audit/current_state_v0.1.md`、`docs/planning/{PROFESSIONALIZATION_PLAN,ARCHITECTURE_PROPOSAL,EXECUTION_BACKLOG,PHASE_GATES,RISK_REGISTER,DECISION_LOG}.md`（口径确认：主定位=可复现大模型模拟研究原型；v1=真实 DeepSeek API 历史基线；缺失的是 provenance 元数据而非来源事实）。
- **新增文件**：
  - `docs/audit/baseline_hashes.txt`
  - `docs/audit/v1_provenance_statement.md`
- **修改文件**：`AGENT_WORKLOG.md`（本条）。
- **执行命令（真实结果）**：
  | 命令 | 结果 |
  |---|---|
  | `git status --short` | 仅未跟踪的 Phase 0/本轮新增文件；受保护资产无已跟踪修改 |
  | `git branch --show-current` | `chore/fnd-001-freeze-v01-baseline` |
  | `git rev-parse HEAD` | `00c4725dc7b891de3a7bfa11b4856be177d9d2a6` |
  | `git diff -- src outputs README.md` | 空 |
  | `git ls-tree -r --name-only <baseline>` + `Get-FileHash SHA256` | 生成 51 条 hash 行 |
  | 重复计算并 `Compare-Object` | `REPRODUCIBLE: identical file list and SHA-256 (count=51)` |
- **hash 文件**：算法 SHA-256；共 **51** 条（= 基线 51 个已跟踪文件，未混入 Phase 0 新增规划文件）；UTF-8 无 BOM；路径相对根、正斜杠、小写 hash。
- **是否包含规定保护资产**：包含 `src/stimuli.py`、`src/scales.py`、`README.md`、全部 `outputs/**`（含 `outputs/plots/*.png`）、`requirements.txt`、`run_all.ps1` 及全部 docs 原文；未纳入 `.git/`、`.venv/`、`__pycache__/`、`*.pyc`、`.env`、Phase 0 未跟踪规划文件。
- **重复计算结果**：与首次一致（51 条文件列表与 SHA-256 完全相同）。
- **provenance 声明摘要**：v1（commit 00c4725）360 条记录=真实 DeepSeek API（非 mock），保留为 historical DeepSeek API baseline；严格区分 360 记录 ≠ 360 人类被试 ≠ 360 独立模型系统；已确认事实/机器可验证证据/历史缺失元数据三层分离；缺失元数据（服务端版本、token、费用、时间戳、prompt hash、依赖锁 hash、原始响应/宽表等）标注为“当前未完整归档或未包含在公开仓库中”，不写成“从未存在”，不伪造补写；中介=探索性路径诊断，非机制证明。
- **失败命令及修复**：可重复性校验第一次因 `Get-Content` 未显式编码被拦截；改用 `Get-Content -Encoding UTF8` 后成功，结果一致。
- **Git 状态**：受保护文件 diff 全空；新增两个 audit 文件为未跟踪；本轮未 commit、未 push。
- **未解决事项**：无阻断项；provenance 措辞与 manifest 格式待人工批准。
- **人工审查点**：① provenance statement 措辞是否批准；② hash manifest 格式是否批准。
- **停止**：完成三文件后停止，未进入 FND-002。

---

## 2026-07-10 · FND-001.1 · Canonical Hash 口径更正

- **分支**：`chore/fnd-001-freeze-v01-baseline`（未 commit）。
- **背景与更正原因**：
  1. 独立复核发现，原 `baseline_hashes.txt` 的 hash 来自 **Windows CRLF 工作树字节**（`git ls-tree` 取路径 + `Get-FileHash` 对 checkout 文件计算）；
  2. 原“重复计算一致”**仅表示同一 Windows checkout 内可重复**，不等于 commit 中 LF Git blob 字节的 SHA-256，不能作为跨机器/跨平台 canonical baseline；
  3. 本轮**重新基于 commit `00c4725` 的原始 Git blob bytes** 计算（`git ls-tree` + `git cat-file blob`，直接对字节做 SHA-256，不解码文本、不经 PowerShell 文本管道、不做换行转换），覆盖文本与二进制（PNG/CSV/JSON/MD/PS1）。
- **`.gitignore` spot check**：由旧的 `36a7c1916bd35d82e3f8350bd97a980e49333b0ae5a310b077a38ee647eb9a61`（CRLF 工作树）变更为 canonical `a7d4b6707c346880c477b9999f3d2db292d4ac2c5664b18a3ff5f3024bbdc974`（Git blob bytes），与预期一致。
- **manifest 变化**：header 增加 `hash_source=git_commit_blob_bytes` 与 `file_count=51`；共 51 条、路径唯一；仍含 `src/stimuli.py`、`src/scales.py`、`README.md`、全部 `outputs/**`。
- **二次独立计算**：改用不同实现（`git cat-file --batch` 单进程流式读取 blob）重算到系统临时文件并逐行比较，结果 `51 个路径一致 + 51 个 SHA-256 一致`；临时脚本与临时清单已删除。
- **provenance statement**：仅在 §4 SHA-256 清单处补充一句“该清单直接基于指定 Git commit 中的原始 blob bytes 计算，不受 Windows/Linux 换行转换或本地 checkout 配置影响”，未改其他研究口径。
- **未修改被保护资产**：`git diff -- src outputs README.md requirements.txt run_all.ps1` 全空。
- **失败/被跳过命令及处理**：内联 heredoc 的重算校验命令两次被执行器判定为长任务而跳过；改为将一次性校验脚本写入系统临时目录、并用单进程 `git cat-file --batch` 高效实现后成功；校验完成后删除临时脚本。
- **说明**：不改写先前 FND-001 原始记录（保留“曾用工作树 hash”的事实）；不声称“从未发生过工作树 hash”。
- **停止**：未进入 FND-002，未 commit、未 push。

---

## 2026-07-10 · FND-002 · Project Tooling

1. **分支/HEAD**：`chore/fnd-002-project-tooling`；HEAD=`2d615dbd85c773703f5612466eed4cc4dd174f91`（`2d615db merge: complete FND-001 baseline freeze`）；开始时工作区干净。
2. **uv 是否原本存在**：PATH 无 uv；`.venv\Scripts\uv.exe` **已存在**（未安装）。
3. **uv 实际版本**：`uv 0.11.28 (ebf0f43d7 2026-07-07 x86_64-pc-windows-msvc)`。
4. **新增文件**：`pyproject.toml`、`uv.lock`；修改：`AGENT_WORKLOG.md`（本条）。
5. **pyproject 关键决策**：
   - `version = "0.2.0.dev0"`（专业化开发版本，非正式 release）；
   - `requires-python = ">=3.12,<3.13"`（仅声明已验证的 Python 3.12）；
   - **未添加** `[build-system]`；`tool.uv.package = false`（本轮不构建/安装项目自身，package 与 build 配置留待 FND-005）；
   - **未添加** license 字段（DEC-001 未决）、作者隐私信息、CLI entry point；
   - 未升级依赖最低约束；未加 pydantic / 其他模型 SDK / 类型检查器 / pre-commit / coverage / benchmark 工具。
6. **运行依赖（8 项，与 requirements.txt 一致）**：openai、python-dotenv、pandas、numpy、scipy、statsmodels、matplotlib、tqdm；**开发依赖（dev group）**：pytest>=8.0、ruff>=0.9.0。
7. **uv.lock 是否成功生成**：是（`uv lock --python .venv\Scripts\python.exe` → `Resolved 40 packages in 7.75s`，无冲突）；未手工编辑。
8. **锁文件大小**：`uv.lock` = 73042 bytes（LastWriteTime 2026/7/10 18:16）。
9. **`uv sync --frozen`（隔离临时环境，`UV_PROJECT_ENVIRONMENT`=系统临时目录）**：成功，Prepared 39 packages（项目自身 package=false 不安装），Installed 39。
10. **ruff**：`uv run --frozen ruff check .` → `All checks passed!`（ruff 0.15.21；未运行 `--fix`，未改 src）。
11. **compileall**：`uv run --frozen python -m compileall -q src` → exit 0，无输出。
12. **pytest version**：`pytest 9.1.1`（仅验证已安装；本轮无测试文件，未运行 `pytest -q`）。
13. **import smoke**：8 个运行依赖全部导入成功（另隔离临时环境）：openai 2.45.0 / dotenv(not exposed) / pandas 3.0.3 / numpy 2.5.1 / scipy 1.18.0 / statsmodels 0.14.6 / matplotlib 3.11.0 / tqdm 4.68.4 → `dependency import smoke passed`；未调用任何 API。
14. **临时环境是否删除**：是（两次 `UV_PROJECT_ENVIRONMENT` 临时目录均 `TempEnvRemoved: True`；临时校验/导入脚本均已删除）。
15. **`.venv` 是否被 uv sync 重写**：否（全程使用 `UV_PROJECT_ENVIRONMENT` 指向系统临时目录，基线 `.venv` 未被改写）。
16. **失败/被跳过命令及修复**：① 合并式 uv 检查/安装命令被执行器判为长任务跳过 → 改为先只读检查（uv 已存在，无需安装）；② TOML 校验命令一次被跳过、临时脚本一度缺失 → 重写脚本后成功（`pyproject validation passed`）；③ 多命令 `git diff` 检查被跳过 → 改用 `git diff --stat` 汇总（受保护文件无差异）。
17. **受保护文件检查**：`git diff --stat -- requirements.txt src outputs README.md run_all.ps1 docs AGENTS.md` 为空；`requirements.txt` 未改（保留、未从 uv.lock 覆盖）。
18. **停止**：未进入 FND-003，未 commit、未 push。

---

## 2026-07-10 · FND-003 · Characterization Tests

- **分支/HEAD**：`test/fnd-003-characterization-tests`；HEAD=`1ddaa3ae6ddf37f5da1043d91762ca1107fce95c`（== `refactor/v0.2-professionalization`；log 含 FND-001、FND-002）；开始时工作区干净。
- **性质**：本轮只新增测试，记录 v0.1 代码**当前行为**作为回归基准；未修复源码、未改材料/题项、未运行旧 CLI、未写 outputs、未调用 API。characterization 不代表现有设计已合理，也不把现有行为定为永久规范。
- **新增测试文件**：
  - `tests/conftest.py`（把 `src` 临时加入 sys.path；设 `MPLBACKEND=Agg`）
  - `tests/characterization/test_stimuli_contract.py`
  - `tests/characterization/test_scales_contract.py`
  - `tests/characterization/test_design_contract.py`
  - `tests/characterization/test_prompt_mock_contract.py`
  - `tests/characterization/test_normalization_io_contract.py`
  - `tests/characterization/test_analysis_contract.py`
- **修改文件**：`AGENT_WORKLOG.md`（本条）。
- **测试覆盖的当前行为**：
  - stimuli：PROCESS_CONDITIONS/PROCESS_ORDINAL/IDENTITY 映射；8 情境结构（fixed_choice∈{option_a,option_b}、valence 三类、非空）；`all_materials()` 96 行、组合唯一、char_len、synthetic、三个中文标记、structure_level 一致；未知条件抛 ValueError。
  - scales：34 题、唯一；各量表题项数精确；factual 0–2、其余 1–7；ITEM_RESPONSE_RANGES / ITEM_TEXT 一致。
  - design：`make_design(2)` 24 行、12 格各 2、pid 唯一、ordinal/structure/char_len/persona 一致；固定种子两次调用完全相同；`make_design(8)` 每格 8 情境各一次。
  - prompt：2 条 message（system/user）；user JSON 含 7 个键；items 34、id 集合==ITEMS；output_schema.participant_id 一致。
  - extract_json：纯 JSON / ```json fenced / 内嵌文本 / 无效抛 `json.JSONDecodeError`。
  - mock：同 `random.Random(12345)` 两次结果相同；34 题在各自范围；participant_id/attention_check/short_reason 固定值。
  - normalization：合法值保留、数字串转 int、越界/无效/缺失→None、34 键齐全、metadata 复制、error 保留、synthetic True。
  - 临时 I/O：`write_jsonl` 追加、`existing_ids` 跳过空行/坏行、`export_wide` 展开 ratings 与 persona_ 前缀（persona 内 participant_id 不重复展开），全部写 `tmp_path`。
  - 分析纯函数：`cronbach_alpha`（<2 题/<3 行/零方差→NaN，非退化→有限 float）、`scale_scores`（量表行均值、responsibility_total=三子维度均值、metadata 保留）、`char_len_summary`（按 PROCESS_CONDITIONS 重排）。
- **未被测试认可为“正确”的已知方法问题**：测试仅记录现状，**不背书**以下当前设计——6 条件压成 4 级 structure_level（H-03）、prompt 一次暴露全部题项+构念名+判断规则（H-02）、`SCENARIOS[n % len]` 确定性情境分配（M-07）、responsibility_total 合并三子维度（M-05）、factual check 计入 alpha 的适当性（M-04）。这些留待 v2/后续阶段处理。
- **测试收集数量**：28（`--collect-only` 12.32s）。
- **两次 pytest 结果**：run1 `28 passed in 5.93s`（exit 0）；run2 `28 passed in 5.78s`（exit 0）——稳定，无 flaky。
- **Ruff**：`ruff check tests` → `All checks passed!`（exit 0）。
- **outputs 前后比较**：测试前清单 30 个文件；测试后 30 个文件；git tracked `diff --stat -- outputs` 为空、`status --short -- outputs` 为空；`git status --short --ignored` 未出现 `outputs/raw_simulated_responses.jsonl` 或 `outputs/simulated_responses_wide.csv`。（注：中途 PowerShell 临时 before-manifest 文件被系统临时目录清理，改用 git 跟踪比较 + ignored 检查 + 文件计数三重方式确认 outputs 未变。）
- **是否出现 ignored 新文件**：否。
- **临时环境是否清除**：是（隔离 uv 环境 `UV_PROJECT_ENVIRONMENT` 指向系统临时目录，`TempEnvRemoved: True`；基线 `.venv` 未被 sync 重写）。
- **失败测试与修正**：无测试失败（首次即全绿）；无需修改测试或源码。执行层面：多条组合/长命令被执行器判为长任务而跳过 → 拆成更小的独立命令逐步执行；`[System.IO.Path]::GetRelativePath` 在 PowerShell 5.1 不可用 → 改用 `Substring` 取相对路径。
- **受保护文件检查**：`src/**`、`outputs/**`、README、requirements、run_all.ps1、pyproject.toml、uv.lock、docs、AGENTS.md 均无 diff。
- **未调用 API**：是（未调用 main/load_client/call_deepseek，未运行旧 CLI）。
- **停止**：未进入 FND-004，未 commit、未 push。

## 2026-07-13 · FND-004 · Explicit Safe Output Paths

- **分支与起始 HEAD**：`fix/fnd-004-safe-output-directory`，起始 HEAD `590e43698cadae32b09faf91ae515028d0866bb3`（==`refactor/v0.2-professionalization`）。
- **批次 A 收尾（一次性人工授权）**：
  - FND-003 commit SHA：`fcc0aa25329958508b51848b8b77c2ad2742a2ff`（`test: add v0.1 characterization coverage`，8 文件 +553）。
  - FND-003 非快进 merge SHA：`590e43698cadae32b09faf91ae515028d0866bb3`（`merge: complete FND-003 characterization tests`，ort 策略）。
  - 已删除本地已合并分支 `test/fnd-003-characterization-tests`（was `fcc0aa2`）。
  - 收尾前隔离 uv 环境重跑 FND-003：`28 passed`、`ruff check tests` → All checks passed；暂存仅 8 个允许文件，受保护文件暂存检查为空、`diff --cached --check` 无空白错误。
- **搜索发现的固定输出脚本（初始匹配 26 处 / src）**：
  - `run_simulated_study.py`：`OUT = ROOT/"outputs"`、导入期 `OUT.mkdir`、`RAW_PATH`/`WIDE_PATH` 全局、`to_csv(wide_path)`。
  - `analyze_results.py`：`OUT`、导入期 `PLOTS.mkdir`、`WIDE_PATH` 与 15 个 `*_PATH` 全局、`savefig(PLOTS/...)`、多处 `to_csv`/`write_text` 使用全局路径。
  - `validate_materials.py`：导入期 `OUT.mkdir` + 模块级 `to_csv(OUT/...)`（导入即写 CSV）。
  - `generate_pilot_report.py`：`OUT`、`main` 内 `OUT.mkdir` + 读 `OUT/*` + 写 `REPORT_PATH`。
  - `generate_n20_construct_validation_report.py`、`generate_n30_stability_replication_report.py`：`OUT` + `read_raw()` 读 `OUT` + 写 `REPORT_PATH`。
  - `run_all.ps1`：无 `--out`，末尾打印 `Done. Check outputs/.`。
- **新路径安全规则（`src/path_safety.py`，仅路径逻辑，导入无副作用）**：
  - `PROJECT_ROOT`、`LEGACY_OUTPUT_DIR` 常量；`UnsafeOutputPathError`/`InputPathError`。
  - `resolve_output_dir(raw, create=True)`：必须显式提供；`expanduser().resolve()`；拒绝仓库根；拒绝等于或位于 `outputs/`、`.git/`、`.venv/`、`src/`、`docs/`、`tests/` 内部；仅在校验通过后 `mkdir(parents=True, exist_ok=True)`；错误含明确路径与原因。允许系统临时目录、未来 `artifacts/`、用户指定安全目录。
  - `resolve_input_dir(raw)`：必须显式提供、必须存在、必须是目录；只读输入可指向历史 `outputs/`；不创建目录、不修改输入。
- **每个脚本的新参数与输出位置**：
  - `run_simulated_study.py`：新增必填 `--out`；删除导入期 `OUT.mkdir` 与固定全局；运行时 `raw_path`/`wide_path` 为 `<out>/raw_simulated_responses.jsonl`、`<out>/simulated_responses_wide.csv` 局部变量；`--fresh` 只删这两个已知文件。make_design/persona/prompt/mock/DeepSeek/normalize/文件名字段全部不变。
  - `analyze_results.py`：新增必填 `--input` 与 `--out`；删除导入期 `PLOTS.mkdir` 与全部固定 `*_PATH` 全局；`<input>/simulated_responses_wide.csv` 缺失时明确报错；全部产物（15 个文件 + `plots/**`）写入 `<out>`；`plot_means`/`generate_method_report`/`generate_measurement_report` 改为接收显式路径参数，不用可变全局覆盖；统计公式/目标变量/报告文本/图表含义不变。
  - `validate_materials.py`：改为 `main()` + `if __name__=="__main__"` 结构；新增必填 `--out`；输出 `<out>/materials_preview.csv`；导入时不建目录/不构 DataFrame/不写 CSV/不打印。材料构造与字段不变。
  - 三个报告脚本（pilot/n20/n30）：均新增必填 `--input` 与 `--out`；输入全部从 `<input>` 读取，报告写入 `<out>`；文件名不变；导入不写文件；缺输入文件时报错；报告统计内容/结论逻辑不变；泄漏扫描逻辑不变（不读 `.env` 内容、只列文件名、不输出 key）；无真实 API。
  - `run_all.ps1`：新增 `[Parameter(Mandatory=$true)][string]$OutDir`；分别传 `validate_materials.py --out $OutDir`、`run_simulated_study.py --out $OutDir`、`analyze_results.py --input $OutDir --out $OutDir`；保留 `NPerCell`/`Mock`/`Fresh`；未提供 `OutDir` 时参数绑定 fail fast；末尾改为打印解析后的实际输出路径，不再打印 `Done. Check outputs/.`。
- **import 副作用如何消除**：所有 `OUT.mkdir`/模块级写 CSV/固定 `*_PATH` 均移入 `main()` 或改为函数参数；集成测试 `test_import_has_no_filesystem_side_effects` 在独立 cwd 的 subprocess 中导入 7 个模块，断言 cwd 与 `outputs/` 前后无新增文件/目录。
- **--fresh 行为**：仅删除显式 `<out>` 中的 `raw_simulated_responses.jsonl` 与 `simulated_responses_wide.csv`；不删目录、不递归、不删 sentinel、不触碰历史 `outputs/`。集成测试用 `sentinel.txt` 验证再次 `--fresh` 后 raw/wide 重生成而 sentinel 保留。
- **新增测试**：
  - `tests/characterization/test_output_path_safety.py`（18 项，含参数化）：安全临时目录接受并创建；缺路径拒绝；仓库根拒绝；历史 `outputs/` 拒绝；`outputs/` 子目录拒绝；`src/`/`docs/`/`tests/`/`.git/`/`.venv/` 及其内部拒绝；被拒路径不被创建；`create=False` 不创建；输入不存在/非目录/缺失拒绝；已存在输入解析成功；只读输入可指向 `outputs/`；导入不建目录。
  - `tests/integration/test_explicit_output_pipeline.py`（14 项，subprocess + tmp_path）：生成缺 `--out` 非零退出且不写仓库 outputs；生成拒绝 `--out=<repo>/outputs`；mock 生成写显式目录、raw/wide 存在、12 条记录、全 synthetic 无 API；`--fresh` 保留 sentinel；材料校验写 `materials_preview.csv`；分析写关键产物与 `plots/**`；分析缺 `--out` 非零；导入无副作用；三个报告脚本 `--help` 成功且含 `--input/--out`；报告脚本缺参数 fail fast 且不写仓库 outputs。
- **测试数量**：collect-only `60 tests collected`（28 原 characterization + 18 路径安全 + 14 集成）。
- **两次 pytest 结果（隔离 uv 环境）**：run1 `60 passed in 281.85s`（exit 0，含首次 matplotlib 字体缓存构建）；run2 `60 passed in 168.68s`（exit 0）——稳定，无 flaky。小样本下出现 scipy `RuntimeWarning: catastrophic cancellation`（预期，命令仍正常完成）。
- **Ruff / compileall**：`ruff check src tests` → All checks passed（exit 0，未用自动修复）；`python -m compileall -q src tests`（exit 0）。
- **固定输出路径复搜（最终剩余匹配，全部安全）**：src 22 处、run_all.ps1 5 处，均为——函数内基于显式解析目录的 `mkdir`（`analyze_results` 的 `plots_dir.mkdir`、`path_safety` 校验后的 `candidate.mkdir`）、基于函数参数的 `to_csv`/`write_text`/`savefig`；`path_safety.LEGACY_OUTPUT_DIR=(PROJECT_ROOT/"outputs").resolve()` 与 docstring 仅为拒绝用常量/注释，非写目标；无 import 阶段写入、无默认历史 outputs、无无参固定输出路径。
- **outputs 前后 Hash 比较**：before 30 文件 / after 30 文件；固定临时清单（相对路径|大小|SHA-256）经 `Compare-Object` 完全一致（文件数/路径/大小/SHA-256 全部匹配）；`git status --short --ignored -- outputs` 无输出（无测试新生成 raw/wide）；比较完成后删除临时清单。PowerShell 5.1 用 `Substring` 生成相对路径（未用 `GetRelativePath`）。
- **临时环境清理**：隔离 uv 环境 `UV_PROJECT_ENVIRONMENT` 指向系统临时目录 `llm-fnd004-env`；基线 `.venv` 未被 sync 重写；测试临时数据仅位于 `%TEMP%`/`tmp_path`。
- **失败命令与修复**：无测试失败（两次全绿）；无需为通过测试修改 `src/**` 逻辑。执行层面：组合/长命令与 `pytest -q`/重分析被执行器判为长任务跳过 → 拆分为小命令，完整 pytest 改用隔离环境 `python.exe` 后台 `Start-Process` + 轮询日志获取真实结果；`Get-Content` 无编码被安全策略拦截 → 加 `-Encoding UTF8`。
- **受保护文件检查**：`src/stimuli.py`、`src/scales.py`、`outputs/**`、README、requirements、pyproject.toml、uv.lock、AGENTS.md、docs 均无 diff；`git diff --check` 无空白错误。
- **未调用 API**：是（全程 mock，未触发 load_client/call_deepseek）。
- **停止**：FND-004 实现与测试完成即停——未 commit FND-004、未 merge、未 push、未创建 FND-005 分支、未建正式 package、未改统计方法/材料/量表、未制作展示页。
