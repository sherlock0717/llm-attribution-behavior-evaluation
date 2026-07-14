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

## 2026-07-13 · FND-005 · Minimal Package And CLI

- **分支与起始 HEAD**：`refactor/fnd-005-minimal-package-cli`，起始 HEAD `d5671e26648dc1c91312ab1ce7fd0fb54c0c08fe`（==`refactor/v0.2-professionalization`，即 FND-004 merge 提交）。
- **批次 A · FND-004 收尾（一次性人工授权）**：
  - 提交前隔离 uv 环境重测：`60 passed in 373.51s`、`ruff check src tests` All checks passed、`compileall` exit 0。
  - FND-004 commit SHA：`0c9b9504f154f7de6fb5ba7a55508104c1607145`（`fix: require explicit safe output paths`，11 文件 +732 −137）。
  - FND-004 非快进 merge SHA：`d5671e26648dc1c91312ab1ce7fd0fb54c0c08fe`（`merge: complete FND-004 safe output paths`，ort 策略）。
  - 已删除本地已合并分支 `fix/fnd-004-safe-output-directory`（was `0c9b950`）。
- **新 package 文件**：`src/freewill_attribution/__init__.py`、`paths.py`、`runner.py`、`cli.py`。
- **package 名**：`freewill_attribution`（正式批准）；CLI 形式 `python -m freewill_attribution.cli`（不使用 `python -m src.freewill_attribution.cli`）。
- **pyproject build-system 变化**：新增 `[build-system]`（`requires=["setuptools>=77.0.3"]`、`build-backend="setuptools.build_meta"`）。
- **package=false → true**：`[tool.uv] package = true`。
- **setuptools src-layout 配置**：`[tool.setuptools] package-dir = {"" = "src"}`；`[tool.setuptools.packages.find] where=["src"], include=["freewill_attribution*"], namespaces=false`。保持 project.name/version/description/readme/requires-python、全部运行依赖、dependency-groups、ruff、pytest 配置不变；未新增 `[project.scripts]`/license/authors/CLI 框架依赖（无 click/typer/rich，仅标准库 argparse）。
- **uv.lock 更新**：`uv lock --python .venv/Scripts/python.exe`（Resolved 40 packages）；未手工编辑，运行依赖未增删；setuptools 仅作为构建后端，未混入项目 runtime dependency。
- **CLI 命令和参数**：顶层 `python -m freewill_attribution.cli --help`；子命令 `run`：`--out`（必填）、`--n-per-cell`（int，默认 20）、`--seed`（int，默认 20260425）、`--temperature`（float，默认 1.0）、`--mock`（flag）、`--fresh`（flag）；`build_parser()` 独立可测；`main(argv=None)->int` 返回旧脚本退出码；`if __name__=="__main__": raise SystemExit(main())`。
- **runner 采用 subprocess adapter 的原因**：不复制研究逻辑（不 import/复制 make_design/mock_response/normalize_record），以最小改动复用已通过 FND-004 安全校验的旧入口；`build_legacy_run_command` 用 `sys.executable` + 绝对 `LEGACY_RUN_SCRIPT` + 参数列表（非 shell 字符串、无 shell=True/os.system/PowerShell）；布尔 flag 仅 true 时加入；`run_legacy_study` 用 `subprocess.run` 不捕获/吞掉 stdout/stderr、返回原始 return code、不重试、不建 manifest、不改 cwd。
- **旧入口保持不动**：`src/run_simulated_study.py` 等 6 个旧脚本与 `run_all.ps1` 零 diff；旧入口仍可 `python src/run_simulated_study.py ...` 并行使用，未改成 thin wrapper。
- **新旧 CLI parity 结果**：集成测试 `test_new_cli_matches_legacy_bytewise` 对同参 mock 运行比较，`raw_simulated_responses.jsonl` 与 `simulated_responses_wide.csv` 字节完全一致。
- **测试收集数**：`78 tests collected`（60 既有 + 11 unit `test_minimal_package.py` + 7 integration `test_new_cli.py`）。
- **两次 pytest 结果（隔离 uv 环境）**：run1 `78 passed in 316.81s`（exit 0，含首次 matplotlib 字体缓存构建）；run2 `78 passed in 322.65s`（exit 0）。稳定，无 flaky；小样本 scipy RuntimeWarning 为预期，命令正常完成。
- **Ruff / compileall**：`ruff check src tests` → All checks passed（exit 0，未用自动修复）；`python -m compileall -q src tests`（exit 0）。
- **从仓库外 cwd 执行 CLI**：隔离环境为可编辑安装（`llm-agent-free-will-attribution==0.2.0.dev0` from local file），在系统临时 cwd 用环境 python 运行 `python -m freewill_attribution.cli --help` 成功（exit 0）；`paths.LEGACY_RUN_SCRIPT` 正确解析到真实仓库 `src/run_simulated_study.py`（存在）。未手工设置 PYTHONPATH。（注：`uv run` 从仓库外 cwd 无法定位项目，故 CLI 外部可用性用环境 python.exe 直接验证。）
- **outputs 前后 Hash / ignored 检查**：`git diff -- outputs` 为空，outputs 文件数保持 30；`git status --short --ignored -- outputs` 无输出（无测试新生成的 raw/wide，测试产物均写入 `tmp_path`）。
- **失败命令与修复**：无测试失败（两次全绿）。执行层面：`pytest -q` 完整套件被执行器判为长任务跳过 → 改用隔离环境 `python.exe` 后台 `Start-Process` + 轮询日志取真实 exit code 与摘要；`uv run` 从仓库外 cwd 找不到项目 → CLI 外部可用性改用环境 `python.exe` 直接运行；`Get-Content` 无编码被安全策略拦截 → 加 `-Encoding UTF8`。
- **当前 package 的过渡边界**：FND-005 是 source-checkout 内的过渡 CLI adapter；`runner` 通过 subprocess 调用旧脚本的绝对路径，**当前不声称生成的 standalone wheel 已包含全部旧研究运行逻辑**（旧脚本不在 `freewill_attribution` 包内，仅在可编辑/源码检出布局下可定位）；后续 runner 重构将逐步移除对旧脚本位置的依赖。
- **未调用 API**：是（全程 mock）。
- **停止**：FND-005 实现与测试完成即停——未 commit FND-005、未 merge、未 push、未创建 FND-006 分支、未新增 schemas.py/config.py/providers、未改旧入口、未改材料/量表/outputs、未制作展示页。

## 2026-07-13 · FND-005.1 · Explicit Mock Gate And Packaging Ignore

- **审核发现问题 1**：新 CLI 的 `--mock` 原为 `action="store_true"` 且非必填，默认 `False`。
- **原行为风险**：`python -m freewill_attribution.cli run --out <dir>` 会把 `mock=False` 转发给旧脚本，进而尝试真实 API——FND-005 过渡阶段不允许。
- **CLI 改为显式要求 `--mock`**：`run_parser.add_argument("--mock", action="store_true", required=True, ...)`；`--out/--n-per-cell/--seed/--temperature/--fresh` 保持不变；未给 `--mock` 设虚假默认 True、未新增 `--real-api`、未读 API key、未在 runner 篡改参数、未删除 runner 对 `mock=False` 的底层表达能力、未改旧脚本。
- **当前 package CLI 暂不暴露真实 API**：cli.py 顶部说明与 `run` 子命令 help 已更新为“Run a mock simulated study via the safe legacy entry point.”，明确真实 API 尚未通过该 CLI 开放（等待 DEC-012 与正式运行治理）。
- **runner 和旧入口能力未修改**：`runner.py`（subprocess 适配结构）、`src/run_simulated_study.py` 等旧脚本零 diff；runner 仍能表达 `mock=False`，安全门禁仅在 package CLI 层。
- **新增单元测试**（`tests/unit/test_minimal_package.py`）：
  - `test_build_parser_has_run_subcommand` 改为解析 `["run","--mock","--out","somewhere"]` 且断言 `args.mock is True`；
  - `test_run_without_out_exits_nonzero` 改用 `["run","--mock"]` 仍非零退出；
  - 新增 `test_run_requires_explicit_mock_flag`：`["run","--out","somewhere"]` 抛 SystemExit 且 code 非零；
  - 新增 `test_missing_mock_does_not_reach_runner`：monkeypatch 替换 `cli.runner.run_legacy_study`，调用 `cli.main(["run","--out","somewhere"])` 在 argparse 阶段抛 SystemExit，替换函数从未被调用（未用真实/虚假 API key 验证）。
- **新增集成测试**（`tests/integration/test_new_cli.py`）：`test_new_cli_without_mock_fails_before_execution`——`run --out <tmp>/must-not-run`（无 `--mock`）：returncode 非零、stderr 含 `--mock`、`must-not-run` 目录不存在、无 raw JSONL、无 wide CSV、仓库 outputs manifest 前后一致。
- **缺少 `--mock` 时 runner 未被调用**：由 `test_missing_mock_does_not_reach_runner` 证明（argparse 门禁先于 runner）。
- **缺少 `--mock` 时输出目录未创建**：由集成测试断言 `must-not-run` 不存在证明。
- **`.gitignore` 增加 `*.egg-info/`**：置于 `.pytest_cache/` 之后，使用通用规则（非具体目录名）；本轮未加 build//dist/ 等其他规则。
- **`git check-ignore` 验证**：临时探针 `src/fnd005_ignore_probe.egg-info` → `.gitignore:10:*.egg-info/	src/fnd005_ignore_probe.egg-info`（exit 0），探针已删除、未加入 Git；再次隔离 `uv sync --frozen` 未生成 egg-info（前次已构建，工作区 status 未出现 egg-info）。
- **两次针对性测试结果**（隔离 uv 环境，`tests/unit/test_minimal_package.py tests/integration/test_new_cli.py`）：run1 `21 passed in 18.33s`、run2 `21 passed in 14.20s`（较原 18 项 +3）。
- **一次完整回归测试结果**：`81 passed in 143.63s`（exit 0；原 78 项全部保留，新增 3 项 FND-005.1 测试）。
- **针对性 Ruff**：`ruff check src/freewill_attribution tests/unit/test_minimal_package.py tests/integration/test_new_cli.py` → All checks passed（exit 0）。
- **全量 Ruff / compileall**：`ruff check src tests` → `All checks passed`（exit 0）；`python -m compileall -q src tests` → exit 0。
- **outputs 前后**：`git diff -- outputs` 为空，文件数保持 30；无 ignored raw/wide。
- **未调用 API**：是（所有 run 测试带 `--mock`，或明确测试缺 `--mock` 的解析失败；未设 DEEPSEEK_API_KEY、未调用 load_client/call_deepseek）。
- **停止**：未进入 FND-006（未 commit/merge/push、未创建 FND-006 分支）。

## 2026-07-13 · FND-006 · Minimal Schema And Config

1. **分支与起始 HEAD**：`refactor/fnd-006-minimal-schema-config`，起始 HEAD `ed3a7fc5a28f073408718361473a4f1ec645253e`（== `refactor/v0.2-professionalization`，即 FND-005 merge 提交）；开始时工作区干净；已校验 `HEAD == refactor/v0.2-professionalization`。
2. **新增 schema/config 文件**：`src/freewill_attribution/schemas.py`、`src/freewill_attribution/config.py`（均位于既有 package 内，非新建子包）。
3. **新增 YAML 配置**：`configs/study.default.yaml`、`configs/model.mock.yaml`、`configs/prompt.v1.yaml`（当前 schema/config 基础设施的可验证样例，尚未接入 CLI/runner）。
4. **新增直接运行依赖**：`pyproject.toml` 与 `requirements.txt` 均增加 `pydantic>=2.12,<3` 与 `PyYAML>=6.0,<7`；未增加 pydantic-settings / ruamel.yaml / jsonschema / dataclasses-json / CLI 框架 / provider SDK；未改动其他依赖下限；`setuptools` 仍仅作为 `[build-system]` 后端。
5. **ExtensibleModel 的 extra allow 策略**：`ConfigDict(extra="allow", str_strip_whitespace=True, validate_by_alias=True, validate_by_name=True, protected_namespaces=())`。未识别的扩展字段被保留且在 `model_dump()`/`model_dump_json()` 中可见；未使用 `populate_by_name`；未启用全局 `strict=True`；未使用 `arbitrary_types_allowed`。**补充说明**：额外加入 `protected_namespaces=()` 仅用于消除 Pydantic 对合法配置引用字段（`model_config_ref`、`model_version_snapshot`）的 `model_` 保护命名空间告警，不改变校验行为；四项必需设置均已应用（实测两次针对性测试 `52 passed` 无告警输出）。
6. **所有枚举**（均继承 `str, Enum`，JSON 序列化稳定）：`ErrorType`=api/parse/schema/range/missing/runtime；`ErrorSeverity`=warn/error；`ParseStatus`=ok/repaired/failed；`ItemsBatching`=all/by_scale/single。
7. **ValidationError 与 PydanticValidationError 的命名区分**：`from pydantic import ValidationError as PydanticValidationError`；项目自有模型仍名为 `class ValidationError(ExtensibleModel)`（type/item_id/message/severity=ERROR/context，context 用 `default_factory=dict`）。
8. **NormalizedResponse 的最小字段和宽松边界**：participant_id / stimulus_ref(StimulusReference) / ratings(`dict[str, int | None]`) / attention_check="" / short_reason="" / parse_status=OK / errors=`default_factory=list` / metadata=`default_factory=dict`；ratings 允许为空（表缺失/解析失败），键不得为空（field_validator 拒绝空键），值只允许 int 或 None（list/dict/非整数 float 被拒）；**未绑定具体题项名称、未绑定 0–2 或 1–7 范围**（范围校验留给后续 normalization 层）。
9. **RunManifest 的字段**：run_id / git_commit_sha / study_config_ref / model(alias) / prompt_config / stimuli_version / scales_version / schema_version(默认 "0.1") / python_version / dependency_lock_hash / seed / started_at / finished_at(可空)；计数字段 n_records(默认0,≥0) / n_runs(默认1,≥0) / n_prompt_configs(默认1,≥0) / n_models(默认1,≥0) / n_independent_model_systems(默认0,≥0) / n_human_subjects(默认0,≥0)；可空资源字段 token_usage_total / estimated_cost_usd（若提供则 ≥0）；汇总字段 retry_summary / failure_summary / data_checksums（均 `default_factory=dict`）；预留 task_id / benchmark_id。不要求 git SHA 40 位、不要求 checksum 已存在、不要求 cost 已提供、不要求历史 provenance 完整。
10. **model_config alias 处理**：因 Pydantic 保留 `model_config` 为类配置属性，字段命名为 `model`，用 `Field(alias="model_config", serialization_alias="model_config")`；输入 YAML/JSON 可用 `model_config` 键（validate_by_alias），`model_dump(by_alias=True)` 输出 `model_config`（测试 19/20 验证）。
11. **task_id / benchmark_id 仅为预留**：默认 None，可为字符串，当前不启用、不接入任何运行流程（为未来多任务/benchmark 保留）。
12. **Pydantic 错误分类规则**（`validation_errors_from_pydantic` 纯函数）：`missing`→MISSING；前缀 `greater_than`/`less_than`/`multiple_of`→RANGE（含 `greater_than_equal`/`less_than_equal`）；`json_invalid`/`json_type`→PARSE；其余结构/类型错误→SCHEMA。item_id：loc 中含 `ratings, <item_id>` 时提取该题项名，否则 None；message 取 Pydantic 的 msg；severity 默认 error；保留全部错误（不丢位置、不只留第一条）；不凭空生成 api/runtime 错误。`validate_normalized_response` 成功返回 `(model, [])`、失败返回 `(None, 分类错误列表)`，不吞非 Pydantic 编程异常、不写日志/文件。
13. **config safe_load**：`load_yaml_mapping` 用 `expanduser().resolve()`+`yaml.safe_load`；文件必须存在且为文件；空 YAML 返回 `{}`；顶层非 mapping 拒绝；malformed YAML 包装为 `ConfigLoadError`；错误信息含路径但不含完整文件正文（实测 secret 行不泄漏）；不返回 None。`load_study/model/prompt_config` 校验失败包装为 `ConfigLoadError` 并 `raise ... from exc` 保留原因链、含路径与 Pydantic 摘要。
14. **config 引用路径逃逸防护**（`_resolve_config_ref`）：ref 必须相对（拒绝绝对路径 / drive / root）；resolve 后必须位于 base_dir 内（`relative_to` 校验，拒绝 `../` 逃逸）；不创建文件/目录；不把路径写回 model extra。`load_config_bundle` 以 study config 所在目录为 base 安全解析 model/prompt 引用后加载。
15. **当前配置尚未接入 CLI/runner**：schemas.py 与 config.py 为可验证基础设施；未修改 `cli.py`/`runner.py`/`paths.py`/`__init__.py`/旧脚本；未生成正式 RunManifest 文件；未实现 provider 抽象。
16. **prompt.v1 的 expose_construct_names=true 只记录 v1 当前行为**：记录当前 v1 的暴露事实（H-02），**不代表 v2 推荐默认值**（schema 默认仍为 False）。
17. **model.mock 不含 API key**：`configs/model.mock.yaml` 仅 provider=mock / model=rule-based-v1 / 温度 / seed / max_tokens / response_format，无 DeepSeek 配置或密钥；schema 亦不定义 deepseek_api_key/base_url/request_id 等专有字段（测试 27 验证 JSON 与 schema 均不含）。
18. **uv.lock 更新**：`uv lock --python .venv\Scripts\python.exe` → `Resolved 41 packages`，Added pyyaml v6.0.3（pydantic 原为间接依赖，现为直接依赖）；未手工编辑；根项目 `dependencies` 与 `requires-dist` 均列出 pydantic 与 pyyaml；setuptools 仅在 build-system。
19. **针对性测试两次结果**（隔离 uv 环境 `UV_PROJECT_ENVIRONMENT` 指向系统临时目录）：`test_schemas.py`+`test_config.py` run1 `52 passed in 1.91s`（SECONDS=5，含环境冷启动）、run2 `52 passed in 0.99s`（SECONDS=2），exit 0，无 flaky、无 pydantic 告警。
20. **完整回归结果**（新隔离环境）：`pytest -q` → `133 passed in 173.24s`（exit 0，SECONDS=176，含首次 matplotlib 字体缓存构建）；原 81 项全部保留，新增 52 项（27 schema 相关，含参数化展开；21 config，含 subprocess 导入副作用测试）→ 81+52=133。未调用真实 API、未写历史 outputs、未改 mock 输出、未改 CLI 行为。
21. **Ruff / compileall**：针对性 `ruff check`（4 文件）→ All checks passed；全量 `ruff check src tests` → All checks passed（exit 0）；`compileall -q src/freewill_attribution tests/unit` 与 `compileall -q src tests` 均 exit 0。
22. **仓库外 cwd 加载**：隔离环境为可编辑安装，在系统临时 cwd 用环境 python 运行 `load_config_bundle(<Root>/configs/study.default.yaml)`（绝对路径）→ `outside-cwd config load passed`（provider==mock、n_per_cell==20），exit 0；单测 `test_load_from_outside_cwd_with_absolute_path` 亦用 `monkeypatch.chdir` 覆盖。
23. **outputs 前后 Hash**：before 30 文件 / after 30 文件；固定清单（相对路径|大小|SHA-256）`Compare-Object` `OUTPUTS_IDENTICAL=YES`（针对性与完整回归两次均一致）；PowerShell 5.1 用 `Substring` 生成相对路径（未用 `GetRelativePath`）；比较完成后删除临时清单。
24. **ignored 文件检查**：`git status --short --ignored -- outputs` 空；工作区无 `.env`/`*.egg-info/`/`artifacts/`/`manifest.json`/`config.resolved.yaml`/日志/临时测试文件；`git diff --check` 仅 uv.lock 的 CRLF 换行信息性 warning（非空白错误）。`git status --short` 仅：`M pyproject.toml`、`M requirements.txt`、`M uv.lock`、`M AGENT_WORKLOG.md`、`?? configs/`、`?? src/freewill_attribution/{config,schemas}.py`、`?? tests/unit/test_{config,schemas}.py`。
25. **失败命令与修复**：首次针对性脚本在 `$ErrorActionPreference="Stop"` 下，`uv sync` 的进度 stderr 被 PowerShell 转为终止错误，脚本在记录 `UV_SYNC_EXIT` 前退出 → 改为 `$ErrorActionPreference="Continue"` 并以 `$LASTEXITCODE` 手动判定后成功；完整 `pytest -q` 被执行器判为长任务 → 用隔离环境 `python.exe` 后台 `Start-Process` + 轮询日志取真实 exit code/passed 数/耗时；`Get-Content` 加 `-Encoding UTF8`。无测试失败（针对性两次、完整一次均全绿），无需为通过测试修改受保护源码。
26. **未调用 API**：是（schemas/config 无任何网络/subprocess/密钥读取；`test_loading_does_not_read_deepseek_api_key` 设置 DEEPSEEK_API_KEY sentinel 后加载，断言其不出现在配置序列化输出中且不被使用）。
27. **未进入 FND-007**：FND-006 实现、测试、日志完成即停——未 commit/merge/push、未创建 FND-007 分支、未修改 CLI/runner、未把 schema/config 接入运行流程、未生成正式 manifest、未创建 provider/task registry/benchmark、未制作展示页。

## 2026-07-13 · FND-006.1 · Strict Ratings And Preserved Error Locations

> 本轮仅修复 FND-006 代码审核发现的三个问题，未改写原 FND-006 记录。仅修改 `src/freewill_attribution/schemas.py`、`tests/unit/test_schemas.py`、`AGENT_WORKLOG.md`。

1. **审核发现 `protected_namespaces=()` 关闭了全局保护**：原 `ExtensibleModel.model_config` 含 `protected_namespaces=()`，等于全局关闭 Pydantic 的 `model_` 命名空间保护（含对 `model_dump`/`model_validate` 等真实成员的冲突检测）。
2. **已恢复 Pydantic 默认保护**：删除 `protected_namespaces=()` 及“仅用于消除告警、不改变行为”的说明；未另设任何 protected_namespaces；`ExtensibleModel.model_config` 仅保留四项必需设置（extra=allow / str_strip_whitespace / validate_by_alias / validate_by_name）。
3. **`model_config_ref` 和 `model_version_snapshot` 仍正常工作**：恢复默认保护后，这两个非冲突 `model_` 前缀字段照常校验（实测针对性 `39 passed`、完整 `141 passed`，均无报错）；RunManifest 的 `model`（alias `model_config`）不受影响（字段名为 `model`，保护基于字段名而非 alias）。
4. **审核发现 ratings 会转换 `"3"`、`3.0`**：原 `ratings: dict[str, int | None]` 在 Pydantic lax 模式下会把数字串 `"3"` 与整值浮点 `3.0` 强转为 int。
5. **ratings 改为 `StrictInt | None`**：新增 `from pydantic import StrictInt`；`ratings: dict[str, StrictInt | None]`。接受 3/0/-1/None；拒绝 `"3"`/`3.0`/`1.5`/`[1]`/`{"value":1}`（均 `int_type`）。未开启全局 strict、未对其他数字字段用 StrictInt、未在 validator 中手工 `int(...)`、未自动修复/转换 rating。
6. **未绑定具体题项范围**：本层仍不校验量表范围，负整数（如 -1）可通过；范围校验仍留给后续 normalization 层。
7. **审核发现结构化错误丢失完整 loc**：原 `validation_errors_from_pydantic` 仅从 loc 提取 `item_id`，未保留完整位置与原始 Pydantic error type。
8. **context 现保存 loc 和 pydantic_type**：每条错误 `context={"loc": list(loc), "pydantic_type": pydantic_type}`；保留完整 loc（数字索引保持为 int）、保留原始 type、多个错误逐项转换、`item_id` 提取行为不变、API/runtime 不凭空生成；函数说明同步改为“完整 loc 与原始 type 已保存”。
9. **不保存原始 input 或完整 payload**：context 只存 loc 与 pydantic_type；未保存 `raw["input"]`、未保存完整 payload、未保存异常对象、未原样保存 `raw["ctx"]`（避免不可序列化对象）。
10. **新增测试**（`tests/unit/test_schemas.py`）：导入 `ExtensibleModel`；ratings 非整数参数化加入 `"3"`、`3.0`（保留 `1.5`/`[1,2]`/`{"nested":1}`）；`test_ratings_do_not_coerce_numeric_string`（断言含 `int_type`）；`test_ratings_do_not_coerce_integral_float`（断言含 `int_type`）；`test_ratings_accept_int_none_and_negative`；`test_structured_error_preserves_full_location`（ratings `{"q1":"3"}` → item_id `q1`、context loc `["ratings","q1"]`、pydantic_type `int_type`）；`test_missing_error_preserves_field_location`（缺 participant_id → loc `["participant_id"]`、type `missing`）；`test_extensible_model_keeps_pydantic_protected_namespaces`（定义 `model_dump: str` 子类 → `pytest.raises(ValueError, match="model_dump")`，防止再次关闭保护）。既有测试（extra 保留 / model_config alias / task_id·benchmark_id / 时间顺序 / 错误分类 / 配置 schema / 无 DeepSeek 专有字段）继续通过。
11. **两次针对性测试结果**（隔离 uv 环境）：`pytest tests/unit/test_schemas.py -q` run1 `39 passed in 0.66s`、run2 `39 passed in 0.20s`（exit 0，较 FND-006 的 31 项 +8：+2 参数化 +6 新函数）。
12. **strict ratings 行为探针结果**：`"3"`/`3.0`/`1.5`/`[1]`/`{"value":1}` 全部被拒 → `strict ratings probe passed`；合法 `{"q1":3,"q2":None,"q3":-1}` 通过并保持原值 → `legal ratings accepted`（exit 0）。（说明：探针最初以内联多行 `-c` 传入时被 PowerShell 拆断为语法错误；改写入临时 `.py` 并以 `PYTHONPATH=src` 运行后成功，临时文件已删除。）
13. **一次完整回归结果**（新隔离环境）：`pytest -q` → `141 passed in 165.70s`（exit 0，SECONDS=169）；原 133 项全部保留，新增 8 项被收集并通过；未调用真实 API、未写历史 outputs。
14. **Ruff / compileall**：针对性 `ruff check schemas.py test_schemas.py` → All checks passed；全量 `ruff check src tests` → All checks passed（exit 0）；`compileall` 针对性与全量均 exit 0。
15. **outputs 前后 Hash**：before 30 / after 30，`OUTPUTS_IDENTICAL=YES`（针对性与完整回归两次均一致）；`git status --short --ignored -- outputs` 空，无 ignored raw/wide。
16. **其他 FND-006 文件 Hash 未变化**：开始前记录 8 个文件 SHA-256，结束时逐一比对全部 `UNCHANGED`：`config.py`(530EAB90…) / `study.default.yaml`(53E22A33…) / `model.mock.yaml`(51B7D190…) / `prompt.v1.yaml`(8D8B26E0…) / `test_config.py`(6FB22AB4…) / `pyproject.toml`(814D821B…) / `requirements.txt`(F3572E90…) / `uv.lock`(5BFDAA70…)。旧源码/CLI/runner/旧脚本/outputs/docs/既有测试零 diff。
17. **未调用 API**：是（仅 schema 校验与本地探针；未设/未读 API key、未 subprocess、未网络）。
18. **未进入 FND-007**：修复、测试、日志完成即停——未 commit/merge/push、未创建 FND-007 分支、未修改 config/YAML/依赖、未重生成 uv.lock、未修改 CLI/runner/旧脚本、未接入运行流程、未生成正式 manifest。

## 2026-07-13 · FND-007 · GitHub Actions CI

1. **分支与起始 HEAD**：`ci/fnd-007-github-actions`，起始 HEAD `f3ad07169ddd515b82b78dbb460bb542a00ce7be`（== `refactor/v0.2-professionalization`，即 FND-006 merge 提交）；分支创建前工作区干净、基线一致。
2. **FND-006 commit SHA**（批次 A 一次性人工授权）：`a347bdb1845e56fa3fed3e6c64fed511524b84fc`（`feat: add minimal schemas and config loading`，11 文件 +1180）；提交前隔离环境重测：针对性 `60 passed`、完整 `141 passed in 196.53s`、ruff All checks passed、compileall exit 0、`git diff -- outputs` 空、无 ignored outputs。
3. **FND-006 merge SHA**：`f3ad07169ddd515b82b78dbb460bb542a00ce7be`（`merge: complete FND-006 minimal schemas and config`，ort 非快进策略）；合并后工作区干净；已 `git branch -d` 删除本地已合并分支 `refactor/fnd-006-minimal-schema-config`（was a347bdb）。
4. **新增 workflow**：`.github/workflows/ci.yml`（本轮唯一新增源文件）；除此与 `AGENT_WORKLOG.md` 外不改任何文件。
5. **触发条件**：`push`、`pull_request`、`workflow_dispatch`（`"on"` 加引号，避免本地 PyYAML 按 YAML 1.1 解析为布尔）。
6. **只读 permissions**：`permissions.contents: read`；checkout 设 `persist-credentials: false`。
7. **Windows/Linux 矩阵**：`os = [ubuntu-latest, windows-latest]`，`fail-fast: false`，`timeout-minutes: 30`，`concurrency` 取消同 ref 在途运行；唯一 job 为 `test`。
8. **Python 3.12**：`matrix.python-version = ["3.12"]`（单版本）。
9. **Action 版本**：`actions/checkout@v7`、`actions/setup-python@v6`、`astral-sh/setup-uv@11f9893b081a58869d3b5fccaea48c9e9e46f990`（v8.3.2，锁定 SHA）。
10. **uv 版本**：`0.11.28`，`enable-cache: true`，`cache-dependency-glob` 为 `pyproject.toml` + `uv.lock`。
11. **sync/Ruff/compileall/pytest**：`uv sync --frozen` → `uv run --frozen ruff check src tests` → `uv run --frozen python -m compileall -q src tests` → `uv run --frozen pytest -q`。
12. **mock smoke 参数**：`uv run --frozen python -m freewill_attribution.cli run --mock --n-per-cell 1 --seed 20260425 --out "${{ env.SMOKE_OUT }}"`（含必填 `--mock`）。
13. **smoke 输出位于 runner.temp**：`SMOKE_OUT = ${{ runner.temp }}/freewill-attribution-smoke`，绝不写仓库 `outputs/`。
14. **smoke 12 条结果验证**：CI 步骤断言 raw JSONL 恰 12 行、全部 `synthetic is True`、`short_reason == "mock synthetic response"`、wide CSV 存在。
15. **outputs 保护**：CI 末步 `git diff --exit-code` + `git status --porcelain --untracked-files=all` 为空 + `git status --porcelain --ignored -- outputs` 为空，确保仓库与历史 outputs 未变。
16. **不使用 secrets/API key**：workflow 无 `secrets.`、无 `DEEPSEEK_API_KEY`、无 provider matrix、无 benchmark、无 artifact 上传、无 push/commit。
17. **workflow 静态契约验证**：一次性临时脚本（系统临时目录、未入仓、`yaml.safe_load`、23 项检查：name/on 三触发/只读 permissions/单 test job/os 矩阵/py3.12/checkout v7/setup-python v6/setup-uv SHA/sync/ruff/compileall/pytest/CLI/--mock/runner.temp/无 secrets/无 DEEPSEEK/无 provider matrix/无 benchmark/无 --out outputs/无 artifact upload/无 push-commit）→ `workflow contract validation passed`（exit 0），脚本已删除。
18. **Windows 本地等价结果**（隔离 uv 环境）：`uv sync --frozen` exit 0；ruff All checks passed；compileall exit 0；`pytest -q` `141 passed in 216.63s`（exit 0）；mock smoke `run --mock --n-per-cell 1 --seed 20260425 --out <temp>` exit 0；smoke 校验 `local mock smoke validated`（12 条、全 synthetic、short_reason 正确、wide 存在）。临时环境与 smoke 目录已清理，基线 `.venv` 未被 sync 重写。
19. **完整 pytest 数量与时间**：`141 passed`，本地隔离环境 216.63s（批次 A 提交前另一次隔离环境为 196.53s）。
20. **是否执行 WSL 等价验证**：否。本机 `wsl` 可执行程序存在，但**未安装任何 Linux 发行版**（`wsl -e bash` 返回“未安装适用于 Linux 的 Windows 子系统”）；按纪律不得为此安装软件，故未运行 Linux 等价命令。
21. **GitHub-hosted 双平台实际运行尚待 push**：本轮未 push，GitHub Actions 尚未真正运行。**未声称 CI 已绿 / Ubuntu job 通过 / Windows GitHub-hosted job 通过**。已完成：workflow 静态契约验证通过、Windows 本地等价命令通过、workflow 已配置 Ubuntu + Windows 矩阵；两平台真实 GitHub-hosted 验证需在后续获准 push 后完成。
22. **失败命令与修复**：① 用仓库基线 `.venv` 直接跑 workflow 校验脚本报 `ModuleNotFoundError: yaml`（基线 .venv 未装 PyYAML）→ 改在隔离 uv 环境（含锁定 PyYAML）内运行校验，未改动基线 `.venv`；② 完整 pytest 被执行器判长任务 → 隔离环境后台 `Start-Process` + 轮询日志取真实 exit/passed/时长；③ `git status --short` 以目录粒度显示 `?? .github/` → 用 `--untracked-files=all` 确认其下仅 `ci.yml`。
23. **未调用 API**：是（全程 mock/静态校验；workflow 不含 secrets/API key；本地 smoke 带 `--mock`）。
24. **未进入 FND-008**：FND-007 workflow、验证、日志完成即停——未 commit/merge/push FND-007、未创建 FND-008 分支、未开始跨平台脚本任务、未修改 workflow 之外的工程文件、未制作展示页。

## 2026-07-13 · FND-008 · Cross-Platform Run Scripts

1. **分支与起始 HEAD**：`chore/fnd-008-cross-platform-scripts`，起始 HEAD `686cbf8fc63f14510d6d0639ce86111ff824986c`（== `refactor/v0.2-professionalization`，即 FND-007 merge 提交）；创建时基线一致、工作区干净。
2. **FND-007 commit / merge SHA**（批次 A 一次性人工授权）：commit `3682087e370694c43b9fb88bca14e1108d16142b`（`ci: add Windows and Linux validation workflow`，2 文件 +131）；非快进 merge `686cbf8fc63f14510d6d0639ce86111ff824986c`（`merge: complete FND-007 GitHub Actions CI`，ort）；已 `git branch -d` 删除 `ci/fnd-007-github-actions`（was 3682087）。提交前隔离环境重验：workflow 契约验证通过、ruff/compileall 通过、`141 passed in 193.37s`、outputs 干净。
3. **新增两个脚本和测试**：`scripts/run_all.ps1`、`scripts/run_all.sh`、`tests/integration/test_cross_platform_scripts.py`（本轮唯一新增）；另修改 `AGENT_WORKLOG.md`。
4. **根目录 run_all.ps1 保持不变**：未触碰根 `run_all.ps1`（受保护文件哈希前后一致）。
5. **两脚本参数**：PowerShell `-Mock/-OutDir/-NPerCell(默认20)/-Seed(默认20260425)/-Temperature(默认1.0)/-Fresh/-Help`；Bash `--mock/--out[=]PATH/--n-per-cell[=]N/--seed[=]N/--temperature[=]VALUE/--fresh/--help`。两者统一转调 `python -m freewill_attribution.cli run`。
6. **显式 mock 门禁**：缺 `-Mock`/`--mock` → stderr 明确错误 + exit 2，不创建输出目录、不进入 CLI；无真实 API 模式、不读 API key。
7. **默认系统临时输出**：未提供输出目录时写唯一临时路径——PS `<%TEMP%>\freewill-attribution\run-<UTCstamp>-<GUID>`（`GetTempPath`）；Bash `${TMPDIR:-/tmp}/freewill-attribution/run-<UTCstamp>-<pid>-<rand>`；绝不以仓库目录为默认。
8. **显式输出相对路径处理**：在改变 cwd 前按调用者当前目录解析——PS 先记录 `CallerCwd`，展开环境变量，相对路径 `Join-Path $CallerCwd`，转绝对 `GetFullPath`，不预建目录；Bash 先存 `caller_pwd=$PWD`，绝对路径原样、相对路径 `$caller_pwd/$out_arg`，允许空格，不预建目录；最终安全性由现有 CLI/path_safety 校验。
9. **uv 查找顺序**：PATH `uv` → `<repo>\.venv\Scripts\uv.exe` → `<repo>\.venv\bin\uv`（Bash 依次 `command -v uv` → `.venv/bin/uv` → `.venv/Scripts/uv.exe`）；均无则明确错误 + exit 127；不下载/安装 uv。
10. **数组执行、无 shell eval**：PS 用 `& $UvExecutable @UvArgs`（数组，无 Invoke-Expression/Start-Process/shell 字符串）；Bash 用 `uv_args=(...)` 数组 + 子 shell `( cd -- "$repo_root"; exec "$uv_bin" "${uv_args[@]}" )`（无 eval、无字符串拼接、不 source .env）。均用 invariant/字面量传数字（PS `InvariantCulture`）。
11. **CLI 参数转发**：完整转发 `--n-per-cell/--seed/--temperature`，`--mock` 恒定加入，`--fresh` 仅在 fresh 时加入；不复制研究逻辑、不调用旧 `src/run_simulated_study.py`、不调用根 `run_all.ps1`。
12. **退出码转发**：PS 保存 `$LASTEXITCODE` 并 `exit $code`；Bash `exec` 保留 CLI 退出码。
13. **路径含空格验证**：集成测试 `test_explicit_safe_output_with_spaces` 用含空格目录（`safe out dir`）验证成功、raw/wide 存在、12 条、全 synthetic、short_reason 正确。
14. **wrapper 与直接 CLI 字节一致**：集成测试 `test_wrapper_matches_direct_cli_bytewise` + 本机三方比较（见 18）证明 raw JSONL 与 wide CSV 字节一致。
15. **fresh sentinel**：`test_fresh_preserves_sentinel` 首次运行→加 sentinel.txt→再次 `--fresh`→raw/wide 重建且 sentinel 保留。
16. **历史 outputs 拒绝**：`test_wrapper_rejects_repo_outputs` 将 `<repo>/outputs` 作为输出 → 非零退出、历史 outputs manifest 前后一致。
17. **PowerShell 本地结果**：`scripts/run_all.ps1 -Mock -NPerCell 1 -Seed 20260425 -OutDir <temp>` exit 0；raw 12 条（`PS_RAW_COUNT=12`）；`-Help` exit 0 且不产出。
18. **Git Bash compatibility 结果**：本机 `C:\Program Files\Git\bin\bash.exe` 存在；`bash -n scripts/run_all.sh` exit 0；`bash scripts/run_all.sh --mock --n-per-cell 1 --seed 20260425 --out <temp>` exit 0。三方字节比较：PowerShell wrapper / Git Bash wrapper / 直接 package CLI 的 `raw_simulated_responses.jsonl`（SHA-256 `2DF3A75E…`）与 `simulated_responses_wide.csv`（`70E31B71…`）三者完全一致（`PARITY_MATCH=True`）。此项仅为 **Git Bash compatibility validation**，非真实 Linux 验证。
19. **是否有真实 Linux 验证**：无。本机未安装 Linux 发行版，按纪律未安装；真实 Ubuntu 验证由后续获准 push 后的 GitHub-hosted CI 完成。
20. **针对性测试两次结果**（隔离 uv 环境）：`pytest tests/integration/test_cross_platform_scripts.py -q` run1 `30 passed in 30.31s`、run2 `30 passed in 21.39s`（exit 0）。
21. **完整 pytest 结果**（隔离 uv 环境）：`pytest -q` `171 passed in 212.06s`（exit 0）；原 141 项全部保留，新增 30 项被收集并通过；未调用真实 API、未写历史 outputs。
22. **Ruff / compileall**：`ruff check src tests` All checks passed；`compileall -q src tests` exit 0；另 `bash -n` exit 0、PS `-Help` exit 0。
23. **outputs 前后 Hash**：before 30 / after 30，固定清单（相对路径|大小|SHA-256）`OUTPUTS_IDENTICAL=True`；`git status --porcelain --ignored -- outputs` 空，无 ignored raw/wide。
24. **保护文件 Hash**：`run_all.ps1`、`.github/workflows/ci.yml`、`src/freewill_attribution/{cli,runner,paths}.py`、`src/path_safety.py`、`pyproject.toml`、`requirements.txt`、`uv.lock` 前后哈希 `PROTECTED_IDENTICAL=True`。
25. **失败命令与修复**：① `run_all.sh` 初次写入后规范化为 UTF-8 无 BOM + LF（去除潜在 CR），校验 `HAS_BOM=False/HAS_CR=False/首行 shebang`；② 完整 pytest 与多脚本运行被执行器判长任务 → 隔离环境后台 `Start-Process` + 轮询日志取真实结果；③ Git Bash 传路径用正斜杠形式避免转义歧义。无测试失败。
26. **未调用 API**：是（全程 mock；测试 subprocess 均删除 `DEEPSEEK_API_KEY`、设 `MPLBACKEND=Agg`、不设 PYTHONPATH、cwd 位于仓库外；wrapper 不读 key、无真实 API 模式）。
27. **未进入下一阶段**：FND-008 脚本、测试、验收、日志完成即停——未 commit/merge/push FND-008、未修改 CI、未创建 FND-009 或后续分支、未进入 Phase 2/provider/正式 manifest/benchmark、未制作展示页。

## 2026-07-13 · FND-008.1 · Wrapper Missing-Value Guards

分支 `chore/fnd-008-cross-platform-scripts`，起始/结束 HEAD `686cbf8fc63f14510d6d0639ce86111ff824986c`（未提交）。本轮只修复审核发现的参数解析边界，改动文件仅 `scripts/run_all.sh`、`scripts/run_all.ps1`、`tests/integration/test_cross_platform_scripts.py`、`AGENT_WORKLOG.md`。

1. **审核发现**：Bash 旧 `require_value()` 只检查“剩余参数数量”是否为 0，无法识别下一个 token 本身是另一个 option，也不拒绝等号形式的空值。
2. **`--out --fresh --mock` 缺陷**：旧实现把 `--fresh` 当作 `--out` 的值转发，wrapper 返回 0 并在调用者 cwd 下写文件（危险）。
3. **`--out=` 缺陷**：旧实现空值退化为 `$caller_pwd/`，即调用者当前目录。
4. **新增 separated/equal 检查**：以 `require_separate_value(option, $#, ${2-})`（`$#<2` 或下一个值以 `--` 开头 → `missing value`；下一个值为空 → `empty value`）替换旧 `require_value`；新增 `require_equal_value(option, value)`（等号形式空值 → `empty value`）。四个分离形式（`--out/--n-per-cell/--seed/--temperature`）与四个等号形式全部改用新检查。合法参数转发行为不变。
5. **所有缺值输入在 uv 前 exit 2**：伪 uv 探针（见 9）确认 12 个案例全部 `exit=2`、`reached_uv=no`、无 `OUTPUT_DIR=`、cwd 无新增文件。
6. **PowerShell 空 OutDir**：在 mock/数字检查后、查找 uv 前新增 `ContainsKey("OutDir") -and IsNullOrWhiteSpace($OutDir) → stderr + exit 2`；输出目录分支简化为仅按 `ContainsKey("OutDir")` 判定。`-OutDir ""` 与 `-OutDir "   "` 均 exit 2、不查 uv、不打印 `OUTPUT_DIR`、不建默认临时目录；未提供 `-OutDir` 时默认临时输出行为不变。
7. **合法负 seed 未被误拒绝**：`--seed -1`（单连字符，不以 `--` 开头）仍被转发进入 CLI；伪 uv 收到完整数组含 `--seed -1`；直接执行时由 numpy（CLI 内部，`Seed must be between 0 and 2**32 - 1`）拒绝，证明确已进入 CLI 而非被 wrapper 判为缺值。
8. **新增测试数量**：集成测试由 30 增至 45（新增 15）：Bash 参数化缺值/空值 12 条（`test_bash_rejects_missing_or_empty_option_values`）、Bash 合法负 seed 1 条（`test_bash_accepts_negative_seed`）、PowerShell 空 OutDir 参数化 2 条（`test_powershell_rejects_empty_outdir`）。原 30 项全部保留通过。
9. **伪 uv pre-uv gate（独立于 pytest）**：系统临时目录建伪 `uv`（仅记录 `"$@"` 到文件并 exit 0），置于 PATH 首位（`cygpath -u` 转 MSYS 路径）。合法调用 `--mock --out "relative path" --n-per-cell 1 --seed -1 --temperature 0.5 --fresh` → `RESOLVED_UV` 命中伪 uv、`LEGAL_EXIT=0`、伪 uv 收到完整数组（`run --frozen python -m freewill_attribution.cli run --mock --n-per-cell 1 --seed -1 --temperature 0.5 --out <cwd>/relative path --fresh`，相对路径按调用者 cwd 解析、含空格仍为单个参数）。随后 12 个缺值/空值案例逐个执行：全部 `exit=2`、伪 uv 记录文件不存在（`reached_uv=no`、`REACHED_ANY=0`）、无 `OUTPUT_DIR`、`WORK_FILE_COUNT=0` → 输出 `bash malformed-value pre-uv gate passed`。
10. **两次针对性测试**（隔离 uv 环境）：`pytest tests/integration/test_cross_platform_scripts.py -q` run1 `45 passed in 26.46s`、run2 `45 passed in 25.32s`（exit 0）。
11. **完整回归**（隔离 uv 环境）：`pytest -q` `186 passed in 210.24s`（exit 0）；原 171 项全部保留，新增 15 项被收集并通过。
12. **三方字节一致性**：PowerShell wrapper / Git Bash wrapper / 直接 package CLI（`--mock --n-per-cell 1 --seed 20260425`）三者 exit 0；`raw_simulated_responses.jsonl` SHA-256 `2DF3A75EDC3267AD44575B95227E1CBD074366FB8E1849CC0749FDDA41BE5AF3`、`simulated_responses_wide.csv` `70E31B71385FC38613239567D03CC096691B8F2710EEC7A814509D31907587FC`，三方完全一致（`MATCH=True`），与 FND-008 一致。
13. **Ruff / compileall / bash -n / -Help**：`ruff check src tests` All checks passed；`compileall -q src tests` exit 0；`bash -n scripts/run_all.sh` exit 0；`run_all.ps1 -Help` exit 0。
14. **outputs 前后 Hash**：before 30 / after 30，路径|大小|SHA-256 固定清单完全一致；无 ignored raw/wide。
15. **保护文件 Hash（前后一致）**：`run_all.ps1` `18D8436D…`、`.github/workflows/ci.yml` `3B3393F2…`、`src/freewill_attribution/cli.py` `71019220…`、`runner.py` `1CABEAC4…`、`paths.py` `155299C1…`、`src/path_safety.py` `A8194387…`、`pyproject.toml` `814D821B…`、`requirements.txt` `F3572E90…`、`uv.lock` `643F9256…`，全部与开始前一致。
16. **未调用 API**：是（全程 mock/静态；测试 subprocess 删除 `DEEPSEEK_API_KEY`、设 `MPLBACKEND=Agg`、不设 PYTHONPATH、cwd 在仓库外；wrapper 不读 key、无真实 API 模式；伪 uv 探针不进入真实 CLI）。
17. **未进入后续阶段**：修复、测试、验收、日志、审核文件夹完成即停——未 commit/merge/push、未创建后续分支、未修改 CLI/runner/CI/依赖/根 `run_all.ps1`、未进入 Phase 2、未制作展示页。
18. **失败命令与修复**：① 负 seed 测试初版断言 `returncode==0` 过严（numpy 拒绝 -1）→ 改为断言“未被 wrapper 判为缺值 + 已进入 CLI（打印 OUTPUT_DIR，CLI 内部报 seed 错）”；② 伪 uv 探针初版把 Windows 路径 `C:/...` 放入以 `:` 分隔的 PATH 被 bash 拆断，导致回退到真实 uv → 改用 `cygpath -u` 转 MSYS 路径；③ 探针内联 `$([ -f ] && echo yes || echo no)` 嵌套引号求值失真、`reached_uv` 假阳性 → 改用清晰 helper/`if` 判断，得干净全绿结果。

## 2026-07-13 · PLAN-001 + SITE-001 · Repository Rebaseline And Showcase Content Contract

1. **分支与起始 HEAD**：任务分支 `docs/phase-and-showcase-plan`，基于 `refactor/v0.2-professionalization`，起始/当前 HEAD `0aa8919d49af4d709dc2640385094e2e00731b00`；创建时干净、与基线一致。
2. **全仓审计范围**：91 个 Git 跟踪文件；6 规划 + 3 审计文档全部实际阅读；15 个 `src/` Python + 14 测试文件分类；3 configs + 1 CI（YAML 全部解析通过）；30 个历史 outputs 全部程序化扫描。排除 `.git/.venv/__pycache__/.pytest_cache/.ruff_cache`。未读取任何 secret；仓库无 `.env` 且 `.env` 已 gitignore。
3. **跟踪文件数量**：91（`git ls-files`）。
4. **outputs 扫描情况**：11 CSV + 11 PNG + 6 MD + 2 JSON = 30；`scale_scores.csv` 恰 **360 行、22 列、12 单元格（6 过程 × 2 身份）× 30**，6×2×30 由文件直接验证；`reliability_summary.csv` 10 量表 n=360，备注“Synthetic AI-simulated data; not formal human psychometric evidence.”；9 张图 1760×800，`mean_manipulation_check.png` 为 1440×800（旧命名遗留）。
5. **测试收集数量**：见本轮 §轻量验证（仅 `pytest --collect-only`，未运行完整回归）。
6. **当前真实能力**：历史基线=Historical only；package/CLI(mock-only)/安全输出/wrapper=Complete（本地）；schema+config=Partial（未接入运行）；CI=Configured but unverified（无 GitHub-hosted 运行）；provider/正式 RunManifest 产出/benchmark=Planned。`runner.py` 为转调旧脚本的 subprocess adapter，不生成 manifest。
7. **发现的规划冲突**：Phase 1 门禁含“CI 双平台绿”但 CI 仅配置未远程运行；SITE-001 旧义为 Phase 6 JSON 导出、展示被排到末阶段；FND-001~008 已完成却未标记；测试策略要求逐次完整回归；README 仍为 v0.1 口径（本轮不改，记录为冲突）。
8. **是否存在阻断问题**：无。360 记录存在且为真实 DeepSeek API（非 mock）；分支与基线一致；无被跟踪真实 secret（23 处命中均为环境变量名/`api_key` 字样）；规划冲突均可裁决；公开资产已分级。
9. **AUDIT_GATE**：PASS（终端已输出 `AUDIT_GATE=PASS`）。新增 `docs/audit/repository_rebaseline_assessment.md`（先于修改任何旧规划）。
10. **修改的规划文档**：`docs/planning/PROFESSIONALIZATION_PLAN.md`（新增 PLAN-001 权威阶段结构 + 三级测试策略，旧阶段标为历史细节）、`docs/planning/PHASE_GATES.md`（新增重定基线门禁 + Phase 1 双态）、`docs/planning/EXECUTION_BACKLOG.md`（新增重定基线 backlog）、`docs/planning/DECISION_LOG.md`（新增 DEC-013~DEC-020）、`AGENT_WORKLOG.md`（本条）。
11. **新阶段结构**：Phase 1 Engineering Foundation And Historical Baseline（Local complete / Release verification pending）→ Phase 2 Research Protocol Definition → Phase 3A Reproducible V1 Run → Phase 3B Improved V2 → Phase 4 Providers And Multi-Model → Phase 5 Analysis And Reporting → Phase 6 Benchmark Track（Planned，非当前能力）→ Phase 7 Release And Audit（统一远程/发布验证）。
12. **Showcase Track**：新增并行 Track S（S1 内容与数据契约=本轮 / S2 站点数据导出 / S3 静态 MVP / S4 本地校验 / S5 部署并入 Phase 7），明确不被 Phase 1 远程 CI 阻塞。
13. **测试策略调整**：三级——Level 1 本地针对性（文档/文案/页面/单模块，不跑完整回归）、Level 2 里程碑合并（+一次完整 pytest）、Level 3 发布验证（完整 pytest + 双平台 CI + provenance + 链接 + 部署）。
14. **新增展示文档**：`docs/planning/SHOWCASE_PLAN.md`、`docs/showcase/SHOWCASE_CONTENT.md`、`docs/showcase/SITE_DATA_CONTRACT.md`、`docs/showcase/PUBLIC_ASSET_INVENTORY.md`。
15. **页面定位**：“一个用于研究和评估大语言模型自由意志归因行为的可复现实验与模型行为评测原型”；10 栏目（Hero/Research Question/Experimental Design/Pipeline/Historical Results/Evidence And Limitations/Reproducibility/Version History/Roadmap/Repository Links）；状态系统 Completed/Current/Planned/Historical/Pending verification。
16. **公开资产分类**：A 可直接公开（定位文案、设计数字、版本、阶段状态）、B 转换后公开（聚合 CSV 派生数字、9 张一致图、报告摘要）、C 内部（工作日志、审计、规划、审核文件夹）、D 排除（.env/credential/原始 raw jsonl 与 wide csv/调试文件）。含 SHA-256、无第三方版权图片。
17. **数据契约**：定义 `site_summary.json`/`roadmap.json`/`version_history.json` 逐字段（path/type/required/source/derivation/null policy/display rule/evidence level）+ roadmap/version/figure/source citation schema + status/evidence enum；未知值 null，不编造 token/cost/模型快照/时间，未来由 `build_site_data.py` 派生。
18. **没有运行完整 pytest**：是（仅 `pytest --collect-only -q`）。
19. **没有修改代码或 outputs**：是（未改 Python/PowerShell/Bash/YAML/CI/运行逻辑；未改 `outputs/**`；未创建 `site/`、HTML/CSS/JS、`build_site_data.py`）。
20. **没有调用 API**：是。
21. **下一步**：`feat/showcase-v1`（建设静态展示页 MVP，SITE-002/003/004）。
22. **未 push**：是（未 commit/merge/push；未创建后续分支；未进入 Phase 2）。

### PLAN-001.1 · Showcase Contract Corrections

1. **DEC-007 superseded**：由 Pending 改为 Superseded，注明由 DEC-013/DEC-018 与 `SITE_DATA_CONTRACT.md` 取代（页面读版本化静态 JSON、由本地 `build_site_data.py` 生成、非 CI 推送、不手工维护动态数字、部署留 Phase 7）；历史内容保留未删。
2. **backlog 状态更新**：PLAN-001、SITE-001 → Complete（local documentation and contract）；SITE-002/003/004 → Current，注明在同一 `feat/showcase-v1` 分支连续完成。
3. **页面能力状态修正**：Hero "本地工程实施完成" → "Phase 1 本地工程基础完成"；定位改为"一个面向可复现研究的大语言模型自由意志归因实验与模型行为评测原型"（SHOWCASE_CONTENT 与 SHOWCASE_PLAN 一致）；Pipeline 末步改为"静态展示页（Current）"、删除"报告与展示 (Completed/Planned)"；工程底座拆为 Completed（依赖锁定/mock-only CLI/安全输出/wrapper/测试/CI 配置）、Partial（schema/config 未接入正式 runner）、Planned（正式 runner/RunManifest 产出/provider abstraction）；"理由结构非长度效应"段明确对应 **agency**（非 free_will_attribution）。
4. **双状态 roadmap**：`SITE_DATA_CONTRACT.md` roadmap item schema 增加 `local_status`/`release_status`，Phase 1 = current + completed + pending_verification，两个状态标签并列。
5. **site_summary 契约修正**：移除不属 enum 的 `local_complete_release_pending`；改用 `project_stage`/`local_engineering_status`/`release_verification_status`；新增 `source_commit`（git rev-parse HEAD）、`data_as_of_date`（源明确日期/提交日期，不用随机构建时间）、`generated_at`（仅构建信息）。
6. **historical_results.json 契约**：新增，含 claims（factual check / agency 均值 / agency 回归 / agency 计划对比 / free_will 回归 / 并行中介固定 exploratory_path_diagnostic / 责任归因探索性）+ figures；每 metric 必带 source_file+source_field，未找到精确字段 build 必须失败、不猜测，数字不在 HTML 硬编码。
7. **资产完整 Hash**：补齐 `pyproject.toml`、`configs/prompt.v1.yaml`、`configs/model.mock.yaml` 完整 64 位 SHA-256；图片改为逐项分类（首版选用 3 张 / 可选 6 张 / 旧命名默认排除 2 张：mean_manipulation_check、mean_responsibility）；删除"其余 8 张按需纳入"与固定"6 份"计数。
8. **本地预览与公开发布批准分离**：新增 `local_preview_status=approved`、`public_release_status=pending_user_approval`。
9. **未运行完整 pytest**：是（仅 collect-only）。
10. **未修改代码和 outputs**：是。

## 2026-07-13 · SITE-002/003/004 · Static Showcase V1

1. **分支与起始 HEAD**：`feat/showcase-v1`，起始 HEAD `8fc1d6a7f9678b3bbb707fbb2e70731214163e5d`（= PLAN/SITE merge），从 `refactor/v0.2-professionalization` 创建，工作区干净。
2. **PLAN/SITE commit 与 merge**：commit `f4dc5f3f889544d8db13705870c26a49e999291d`（docs: rebaseline phases and define showcase contract）；非快进 merge `8fc1d6a7f9678b3bbb707fbb2e70731214163e5d`（merge: complete PLAN-001 and SITE-001）；已 `git branch -d docs/phase-and-showcase-plan`（was f4dc5f3）。
3. **manifest**：`docs/showcase/site_manifest.yaml` 仅存人工维护静态信息（名称/定位/Hero/导航/研究问题/设计文案/流程/版本历史/roadmap 阶段名与状态/选用图表/边界/仓库相对链接）；不含任何可计算动态数字（360/6/2/30/回归 F/p/中介/图表 Hash/版本/Git SHA）。
4. **build script**：`scripts/build_site_data.py`，只读源文件、不写 outputs、不联网、不调 API、不跑研究脚本、不重估模型；缺文件/列/指标/单元格即失败、不猜测；输出 UTF-8/indent=2/sort_keys；`--check` 内存重建比较（generated_at 作为构建信息排除在数据内容等值之外）→ “site data is up to date”。
5. **四份 JSON 关键字段**：`site_summary.json`（project_version=0.2.0.dev0、source_commit=8fc1d6a…、data_as_of_date=2026-07-13、historical_record_count=360、process/identity=6/2、n_per_cell=30、historical_provider=DeepSeek API、local_engineering_status=completed、release_verification_status=pending_verification、benchmark_status=planned、token/cost/model snapshot=null）；`roadmap.json`（phases×8 + track_s×5，phase-1 = current+completed+pending_verification，phase-6=planned）；`version_history.json`（v0.1/v0.2/future）；`historical_results.json`（7 claims + 3 figures）。
6. **数据来源**：pyproject.toml、configs/study.default.yaml、docs/audit/v1_provenance_statement.md、site_manifest.yaml、outputs/scale_scores.csv、outputs/controlled_regression_summary.csv、outputs/planned_contrasts.csv、outputs/parallel_mediation_summary.json、outputs/n30_stability_replication_report.md、三张选定 PNG；git rev-parse/commit date。
7. **历史数字提取**：factual check（n30 报告表）、agency 条件均值（n30 报告表）、agency 控制回归（controlled_regression_summary.csv dv=agency spec=control_both，F≈12.19）、agency 计划对比（planned_contrasts.csv dv=agency）、free_will 控制回归（dv=free_will_attribution spec=control_both）、并行中介（parallel_mediation_summary.json，固定 exploratory_path_diagnostic）、责任归因（无数字、含来源与探索性标签）；每 metric 带 source_file+source_field，未在 HTML 硬编码统计值。
8. **图表复制与 Hash**：复制 mean_agency.png（8611DBD9…）、mean_free_will_attribution.png（0814EE77…）、mean_subjective_process_completeness.png（66810828…）至 site/assets/figures/，复制前后 SHA-256 一致；未修改/重绘；historical_results.figures 记录源图 SHA-256。
9. **页面结构**：`site/index.html` 10 栏目（Hero/Research Question/Experimental Design/Pipeline/Historical Results/Evidence And Limitations/Reproducibility/Version History/Roadmap/Repository Links）；原生 HTML/CSS/JS，无 CDN/外部字体/第三方 JS/远程 API/inline handler；语义化、响应式、键盘可访问、focus 样式、图有 alt+caption、prefers-reduced-motion；JS 加载四份 JSON，失败显式报错；状态徽章区分 Historical/Completed/Current/Planned/Pending verification；Hero 显示 360 / 6×2 / 30 / DeepSeek historical baseline / 本地基础完成 / 发布验证待完成（均由 JSON 注入）。
10. **README 更新**：新增 v0.2 定位与数据边界、package CLI、两个 wrapper、schema/config 未接入正式 runner、CI configured/remote verification pending、本地展示页预览命令；旧 v0.1 入口移入 Legacy/Historical workflow；加 Method/Results/Limitations/Roadmap 链接；未写 Pages URL、未写 CI passing、未写成熟 benchmark；未改 L43-56 核心结果数字。
11. **targeted tests**：`pytest tests/site -q` = 26 passed；`build_site_data.py --check` exit 0；`compileall scripts/build_site_data.py tests/site` exit 0。
12. **HTTP smoke**：临时端口启动 `http.server --directory site`，请求 /、index.html、css、js、四份 JSON、三张图 → 全部 HTTP 200；随后关闭服务器，无长期后台进程。
13. **其他检查**：HTML 解析 ok；README/site README 相对链接缺失 0；敏感值扫描仅命中 README Legacy 段 `DEEPSEEK_API_KEY = "你的 …Key"` 占位指令（非真实密钥值）；本地绝对路径 0；`git diff --check` exit 0。
14. **collect-only 数量**：`pytest --collect-only -q` = 212（186 既有 + 26 新增 site）。
15. **视觉浏览器自动化未执行**：本机未使用浏览器自动化，未安装浏览器、未扩大范围；仅完成本地 HTTP smoke。
16. **未完整 pytest / 未 API / 未改 outputs / 未 push / 公开部署仍待授权**：均满足；`git diff -- outputs` 为空；未 commit/merge 页面分支；公开 Pages 部署待用户授权（REL-001）。

---

## 2026-07-14 · SITE-005 · Showcase Content And Visual Redesign

1. **分支与起始 HEAD**：继续在 `feat/showcase-v1`（规则 A：分支已存在且有未提交页面变更）；起始 HEAD `8fc1d6a7f9678b3bbb707fbb2e70731214163e5d`；未新建分支、未覆盖已有修改。
2. **页面审查范围**：完整阅读 `site/index.html`、`site/assets/css/site.css`、`site/assets/js/site.js`、`site/data/*.json`、`site/README.md`、`docs/showcase/site_manifest.yaml`、`scripts/build_site_data.py`、`tests/site/**`、`README.md`、`SHOWCASE_CONTENT.md`、`SITE_DATA_CONTRACT.md`、`PUBLIC_ASSET_INVENTORY.md`、`SHOWCASE_PLAN.md`、`configs/study.default.yaml`、`outputs/plots/`（列表）。产出 `docs/showcase/SHOWCASE_REDESIGN_AUDIT.md`（10 小节 + REDESIGN_AUDIT=PASS）后才修改页面。
3. **主要 AI 感来源**：定位口号三处重复（meta/tagline/manifest）；"通过……的方式，观察……""系统改变……观察是否"模板句；边界声明"AI 模拟数据；非人类被试；单一模型"在页脚/每图/每 claim 重复堆叠；Pipeline/Evidence/Reproducibility 均为等长 `<li>` 平铺；全页无作者第一人称。
4. **文案重写范围**：Hero、Research Question、Experimental Design、Pipeline、Historical Results 导读、Evidence、Reproducibility、Roadmap、Repository Links 文案整体按作者口吻重写；未改研究事实/统计结果/样本结构/状态标签/证据边界/版本事实/文件来源。
5. **页面结构变化**：Hero 改左右双栏（介绍 + 概览面板 + Research/Engineering 双状态线）；Research Question 分研究缘起/实际比较/不研究什么/三问卡；Experimental Design 加 6×2 矩阵 + Historical/Mock 对照 + 数据来源/测量维度/实验单元卡；Pipeline 改原生流程图 + current/future 对照；Historical Results 改双列 + 首图整行大图 + `<details>` 统计 + 比较条；Evidence 改 Directly/Partially/Not claimed 三栏 + Data authenticity/Run auditability/Full reproducibility 三态 + 三个 `<details>`；Reproducibility 加组件链 + 能/不能复现两栏；Version History 时间线 4 节点；Roadmap 当前高亮/未来弱化 + 交付 `<details>`；Repository Links 改任务入口 + 用途。
6. **新增原生可视化（≥5，实为 8）**：6×2 设计矩阵、Pipeline 状态流程图、Historical/Mock 对照、Evidence 三栏边界、Phase+Track S 路线图高亮、条件比较条、复现组件链、版本时间线。均由 JSON/manifest 驱动，`<noscript>` 保留文字兜底。
7. **使用的仓库图表与完整 SHA-256（复用，无新增）**：
   - `mean_agency.png` `8611DBD905130582FC49A1AF44724854EAFE5EA62D756379CDA5F1A851B6CE04`
   - `mean_free_will_attribution.png` `0814EE77E3B09815F1CF1545F8DA4DE50433E528F3183B627D4C92EAB3DC10C7`
   - `mean_subjective_process_completeness.png` `66810828D1B9816D7F41EA624BE82B4C2BE958FB2A7A0D91E0A30C058736FE54`
   页面复制件与 `outputs/plots/` 源图逐字节一致（`test_figures_match_source_hashes` 通过）；放大展示 + `<dialog>` 灯箱。
8. **新增视觉占位数量**：2（VIS-002 过程结构梯度、VIS-003 中介路径图），带 `data-visual-id`、显示 "Visual asset pending"、不显示破损图、不影响主内容；VIS-001 仅作候选未放置。
9. **VISUAL_ASSET_BRIEF**：`docs/showcase/VISUAL_ASSET_BRIEF.md`，VIS-001/002/003 含页面位置/图名/用途/为何现有资产不足/类型/尺寸/宽高比/配色/必含/禁含/alt/caption/生图提示词/可否 SVG 代替/状态。
10. **DELIVERY_PACKAGE_GUIDE**：`docs/showcase/DELIVERY_PACKAGE_GUIDE.md`，定义 Content/Visual/Site Code/Research Evidence/Review 五类包 + PACKAGE_MANIFEST 字段 + 接收→临时目录→敏感检查→审查→冲突→建议落库→人工确认→分批写入→targeted validation→等待提交授权流程；明确不直接覆盖仓库。
11. **数据与 manifest 变化**：`build_site_data.py` 新增 `_design_block`（site_summary 增 `design`：process_conditions key/label/note、identity_labels、n_per_cell、total_records，均派生/校验，不手写）；manifest 校正 Track S（site-002/003/004 → completed）、新增 site-005（current）、version_history 扩为 v0.1/v0.2/next/future；`SITE_DATA_CONTRACT.md` 登记 design 块。研究结果数值未改。
12. **README 更新**：仅"展示页与文档"段落，补充原生可视化与历史/mock、当前/未来区分说明；未写线上地址、未写 CI passing。
13. **targeted tests**：`build_site_data.py --check` = "site data is up to date"（exit 0）；`pytest tests/site -q` = 26 passed；`compileall scripts/build_site_data.py tests/site` exit 0。
14. **collect-only 数量**：`pytest --collect-only -q` = 212，无收集错误。
15. **HTTP smoke**：临时端口 8137 启动 `http.server --directory site`，/、index.html、css、js、四份 JSON、三张图 → 全部 HTTP 200；随后 Stop-Process，无后台残留。
16. **静态检查**：HTML 无硬编码统计值（"360"/"F = "/"p < ." 等，已移除误留的 "360"）、无 inline onclick、无空 href、`<script>/<link>` 均本地；JS 无 `https?://`、无 `import…from`、无 eval/innerHTML/远程请求；CSS 有 CSS variables、focus-visible、prefers-reduced-motion、1024/768/390 断点、正文 17px（390 断点 16px）。
17. **浏览器视觉自动化未执行**：为遵守"不安装浏览器/前端工具"，本机未使用现成浏览器自动化，**未执行截图**，不声称视觉检查通过；建议人工 `python -m http.server 8000 --directory site` 本地视觉审核。
18. **保护检查**：`git diff -- outputs` 为空；`src/**`、`configs/**`、`.github/**`、`pyproject.toml`、`requirements.txt`、`uv.lock`、`scripts/run_all.*`、`run_all.ps1`、`tests/unit|integration|characterization/**` 均无改动；未引入 Node/package.json/node_modules/外部依赖。
19. **停止状态**：未 commit / 未 merge / 未 push / 未部署 / 未建新分支 / 未调用 API / 未改历史 outputs / 未运行完整 pytest；停在 `feat/showcase-v1` 未提交，等待人工视觉与文案审核。

---

### SITE-005.1 · Accuracy And Release-Safe Showcase Data

- **分支与状态**：`feat/showcase-v1`，起始 HEAD `8fc1d6a7f9678b3bbb707fbb2e70731214163e5d`；变更全部落在 SITE-005 已批准范围；SITE-005 状态仍为 **Current / awaiting human visual approval**，未标为公开发布完成。
- **source_commit 自引用问题**：原 `build_site_data.py` 用 `git rev-parse HEAD` 生成 `source_commit`，页面提交后 HEAD 变化会使已提交的 `site_summary.json` 立即过期、`--check` 失败。
- **研究源提交语义**：新增 `RESEARCH_SOURCE_PATHS`（outputs 分析文件 + 三张选定图 + `configs/study.default.yaml` + provenance 声明）与 `_latest_source_commit()`（`git log -1 --format=%H -- <paths>`）；`source_commit` 改为研究数据/设计输入最近一次变化的 commit（实测 `a347bdb1845e56fa3fed3e6c64fed511524b84fc`，≠ HEAD），`data_as_of_date` 取该 commit 的提交日期（2026-07-13）；页脚"数据来源提交"→"研究数据源提交"。
- **失效相对链接**：移除 `../docs/...`、`../outputs/...` 本地相对链接；页面内部改锚点（Method→#experimental-design、Results→#historical-results、Limitations→#evidence-limitations、Roadmap→#roadmap），外部仅保留 GitHub repo 根链接，具体仓库文件以 `<code>` 路径 + "位于 GitHub 仓库中"展示，永久链接待 REL-001。
- **Pipeline 状态修正**：拆为 Historical research path（条件与刺激 / Prompt 构造〔exact prompt snapshot/hash unavailable〕/ DeepSeek API 响应 / 解析与量表记录 / 分析与报告）、Current engineering layer（Package·safe paths·wrapper=Completed locally / Schema·config=Partial / 站点导出·展示页=Current）、Planned；纠正原"配置与基础组件"把 `configs/`、`src/freewill_attribution/` 误标 Historical；注明 `prompt.v1.yaml` 是当前配置组件，不替代历史精确 prompt snapshot/hash。
- **Windows/Git Bash/Linux 表述修正**："在 Windows 本地使用锁定依赖跑通 mock 流程；Bash wrapper 完成 Git Bash compatibility validation"，"真实 Linux 与 GitHub-hosted Windows/Linux 验证仍待发布阶段完成"；不把 Git Bash 称为 Linux 验证。
- **VIS-002 原生替换**：删除占位，改由 `site_summary.design.process_conditions` 驱动的 Process Structure Gradient（低→高结构，六节点显示序号/key/中文标签/note/层级；`direct_choice_long` 标 Length-control diagnostic）；`<noscript>` 兜底；VISUAL_ASSET_BRIEF 状态 → `resolved_with_native_web_visual`。
- **VIS-003 原生替换**：删除占位，扩展 `historical_results.json` mediation metrics（estimate/ci_low/ci_high/crosses_zero/path_role，不从 display 反解析），新增原生 Exploratory Path Diagram（主路径 process→agency→free-will、次路径 process→perceived_intelligence→free-will，显示间接效应估计/CI/是否跨 0/Exploratory/非机制证明）；VISUAL_ASSET_BRIEF 状态 → `resolved_with_native_svg_or_html`。页面**不再出现 "Visual asset pending"**。
- **factual check 表述收紧**：标题改"操纵检验反映出低结构与高结构条件的整体差异"；摘要改"高结构整体高于低结构；两个低结构诊断条件不构成严格单调序列"；不声称严格单调或六类两两显著。
- **中介区间表述**："在该探索性分析中 agency 间接效应区间未跨 0；perceived_intelligence 间接效应区间跨 0"；不写稳定机制/机制已确认/因果中介已证明。Evidence 三栏同步。
- **read_note 数据化**：移除 JS `FIGURE_READS`；manifest figures_selected.items 增 `read_note_zh`，build 输出到 `figures[*].read_note`，JS 用 `fig.read_note`；比较条主标签改中文 label、key 作次级 `<code>`。
- **新增测试**：`tests/site` +18（26→44）：source_commit=研究源提交、data_as_of 对应该提交、页面无 Visual asset pending / VIS-002 / VIS-003、无 `href="../"`、所有本地 href 可解析、mediation 结构化字段、agency CI 未跨 0 / 感知智能 CI 跨 0、figures 有 read_note、JS 无 FIGURE_READS、Pipeline 不把 `src/freewill_attribution/` 标 Historical、页面无"Windows/Linux 本地跑通"、factual 文案不过度声称、design 六条件 + length-control。
- **targeted 验证**：`build_site_data.py`（写）ok；`--check` = "site data is up to date"；`pytest tests/site -q` = **44 passed**；`compileall` exit 0；`pytest --collect-only -q` = **230**；HTTP smoke（127? 用 localhost 的 Invoke-WebRequest）/、css、js、四份 JSON、三图 = 全 200，bad=0。
- **浏览器截图结果**：本机存在 Edge（`C:\Program Files (x86)\...\msedge.exe`），无 CDP。headless 截图初次得到 `ERR_CONNECTION_REFUSED` 错误页（Edge 将 `localhost` 解析到 IPv6，与 `http.server` 的 IPv4 绑定不匹配）；改用 `127.0.0.1` 的重试命令被用户拒绝。**因此本轮浏览器视觉验证未完成、不声称通过**；那张错误页截图无效、应忽略。建议人工 `python -m http.server 8000 --directory site` + 浏览器本地审核。
- **保护检查**：`git diff -- outputs` 为空；`src/**`、`configs/**`、`.github/**`、`pyproject.toml`、`requirements.txt`、`uv.lock`、`scripts/run_all.*`、`run_all.ps1`、`tests/unit|integration|characterization/**` 无差异；`git diff --check` exit 0；site 目录敏感信息/绝对路径扫描 0 命中。
- **未运行完整 pytest / 未修改 outputs / 未调用 API / 未 push / 未 commit / 未 merge / 未部署 / 未建新分支**：均满足。停在 `feat/showcase-v1` 未提交，重新等待人工视觉与文案审核。

---

### SITE-005.2 · Runtime Completion, Mobile Layout And Concept Visual

- **分支与状态**：`feat/showcase-v1`，起始 HEAD `8fc1d6a7f9678b3bbb707fbb2e70731214163e5d`；变更均在允许范围；SITE-005 仍为 **Current / awaiting human visual approval**，未标为 public release complete。
- **输入图片检查**：`fcdb0f90-6a14-4e45-9412-9b6325cf17a3.png` 存在、PNG signature 正确、非空；大小 1,298,354 字节；1586×992；比例 1.5988（≈8:5）；SHA-256 `FFCC3139FD2FBE71CC9049F06CF718BBBFBB6C56E2BF37210C8268FF702BC7F7`；内容与研究主题相符（AI/人类主体 → 过程 → 归因输出），无水印/错误文字。
- **导入与清理**：复制到 `site/assets/figures/attribution-research-concept.png`，源/目标 SHA-256 完全一致，字节未改；校验通过后删除根目录暂存副本（本轮授权）；`root_exists=False`、`target_exists=True`。
- **figures 运行中断修复**：确认 `data-slot="figures"` 确实缺失（SITE-005.1 替换 VIS-003 块时误删），导致 `renderFigures` 崩溃并中断路径图/版本/路线图。已在 results 之后补回 figures 容器（含 `<noscript>` 兜底与导读），结果区顺序＝导读→claim→三张图→比较条→路径图。
- **DOM slot 契约**：新增 `requireSlot`，核心容器改用它；`catch` 区分 `file:`/其他；成功写 `data-render-complete="true"`、失败写 `"false"`；`?diagnostics=1` 下双 rAF 写 doc/matrix/figures client/scroll 宽度。
- **移动端溢出修复**：`.results`/`.figures`→`repeat(2,minmax(0,1fr))`、`.meta-cards`→`repeat(3,minmax(0,1fr))`；卡片加 `min-width:0`；caption/fig-read/code/flow-ref 加 `overflow-wrap:anywhere;word-break:break-word`；1024px 结果/图表单列；未用 `body{overflow-x:hidden}`。过程梯度改 6 列网格 + 独立 scale header，移动端单列，`direct_choice_long` 仍标 Length-control diagnostic。
- **概念图接入**：Research Question 栏目（研究缘起/比较之后、三问之前）桌面左文右图（`.research-question-layout` 1.15fr:0.85fr），移动端上文下图；`object-fit:contain`；width=1586 height=992；未叠加像素文字，改图下三项图例（决策主体/过程描述/归因输出）。alt：AI 决策系统与人类决策者经过不同决策过程后被模型评估其能动性、自由意志归因和责任归因的概念示意；caption 含"该图只用于解释研究结构，不承载统计结果"。
- **文档更新**：PUBLIC_ASSET_INVENTORY 新增概念插图条目（含 SHA、边界、local approved / public pending）；VISUAL_ASSET_BRIEF VIS-001 → `provided_and_integrated_for_local_preview`；site_manifest 新增 `conceptual_visuals`（不进 historical_results.figures，build 不读取）；SITE_DATA_CONTRACT/SHOWCASE_CONTENT/README/site README 同步；概念图不计入三张研究图。
- **新增测试**：`tests/site` +13（44→57）：JS slot 全部存在于 HTML、figures slot 存在、requireSlot 用于核心容器、render 链路与 render-complete/diagnostics 标记、概念图存在/有效 PNG/尺寸与 HTML 一致/Hash 与清单一致/alt/caption 含边界/不在 historical figures/根目录副本已删、移动端网格 minmax+min-width+断词、无 body overflow-x hack。
- **targeted 验证**：`--check` = "site data is up to date"；`pytest tests/site -q` = **57 passed**；`compileall` exit 0；`pytest --collect-only -q` = **243**。
- **HTTP smoke（127.0.0.1）**：/、index.html、css、js、四份 JSON、三张历史图、概念图 = **全部 200，bad=0**。
- **浏览器 dump-dom 与截图**：按要求以 `127.0.0.1` + Edge `--headless=new --dump-dom` + 截图设计了运行时校验与 6 张截图命令，但**该命令被用户拒绝执行**。因此 dump-dom 运行时断言（render-complete / figures=3 / path-row=2 / version=4 / phase=8 / track=6 / 概念图 / 无 pending）与截图**未执行、不声称通过**；未保留任何错误页。运行时修复以静态 DOM slot 契约测试验证。**未取得 390px document overflow 实测数值**（需浏览器），建议人工用 `?diagnostics=1` 核对。
- **保护检查**：`git diff -- outputs` 为空；受保护路径（src/configs/.github/pyproject/requirements/uv.lock/run_all/tests unit-integration-char）无差异；`git diff --check` 干净；根目录不再有临时图片副本；无 Node/npm/外部依赖。
- **未 commit / 未 push / 未部署 / 未调用 API / 未修改历史 outputs / 未运行完整 pytest**：均满足。停在 `feat/showcase-v1` 未提交，等待最终人工视觉审核。

### SITE-005.2 收尾 · Deferred Validation 登记与人工提交准备（2026-07-14）

- **优先级调整（本轮）**：浏览器自动截图与 390px 自动读取**不再作为当前提交阻断项**，统一登记为 deferred validation，留到 **Phase 7 发布验证**。本轮不再尝试被拒绝的浏览器命令，不安装任何工具。
- **新增文档**：`docs/showcase/SHOWCASE_DEFERRED_REFINEMENTS.md`（文案自然度 / 内部流程不面向公众 / 数字图表化 / 页面清理时机 / §5 浏览器运行时与 390px 自动验证 deferred to Phase 7）。
- **审计文档更新**：`SHOWCASE_REDESIGN_AUDIT.md` 追加验证登记：Browser runtime and 390px automated layout validation deferred to Phase 7 release validation；不声称浏览器视觉/移动端自动/GitHub Pages 已验证。
- **重新执行的定向验证**：`--check` = site data is up to date；`pytest tests/site -q` = **57 passed**；`compileall` exit 0；`pytest --collect-only -q` = **243**；HTTP smoke（127.0.0.1:临时端口）index/css/js/四 JSON/三历史图/概念图 = **11/11 全 200**；概念图 signature ok、1586×992、SHA-256 `FFCC3139FD2FBE71CC9049F06CF718BBBFBB6C56E2BF37210C8268FF702BC7F7`；`git diff -- outputs` 为空；受保护路径无差异；`git diff --check` 干净；敏感信息扫描（api_key/access_token/secret/authorization/`C:\\Users\\`/.env value）在 site 与新增文档中 0 命中真实值。
- **Git 决策**：遵循 AGENTS.md §二/§七——Agent **不执行** `git add/commit/merge/branch -d/push/switch`；仅准备变更并向作者输出精确人工提交命令（提交信息 `feat: complete local research showcase`，随后人工 `--no-ff` 合并入 `refactor/v0.2-professionalization` 并删除 `feat/showcase-v1`，不 push）。
- **停止点**：输出人工命令后停止；在收到人工 merge SHA 前**不创建** `docs/research-and-benchmark-contract`、**不开始** RES-001 + BMK-001、不在展示页分支混入研究协议文件。
