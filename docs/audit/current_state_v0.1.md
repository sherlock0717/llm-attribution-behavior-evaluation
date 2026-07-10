# 现状审计报告 · v0.1 基线（Phase 0）

> 本文件为只读审计，不修改任何研究资产。所有无法仅凭仓库确认的内容标记为 `未核实`。

---

## A. 基线信息

| 项目 | 值 |
|---|---|
| 仓库路径 | `C:\Users\magnussun\Desktop\llm-agent-free-will-attribution` |
| 远程 | `https://github.com/sherlock0717/llm-agent-free-will-attribution.git` |
| 当前分支 | `refactor/v0.2-professionalization` |
| 当前 commit（short） | `00c4725` |
| 当前 commit（full） | `00c4725dc7b891de3a7bfa11b4856be177d9d2a6` |
| commit message | `Initial public portfolio version` |
| 已跟踪文件数 | 51 |
| Git 工作区状态 | `git status --short` 为空（干净） |
| Python | 3.12.10（`.venv`） |
| SciPy | 1.18.0 |
| 关键依赖 | numpy 2.5.1, pandas 3.0.3, statsmodels 0.14.6, matplotlib 3.11.0, scipy 1.18.0, openai 2.45.0, pydantic 2.13.4, python-dotenv 1.2.2, tqdm 4.68.4 |
| `compileall src` | exit 0（通过） |
| smoke test（隔离 worktree） | 由上游告知已通过；本轮未重跑（见 `AGENT_WORKLOG.md`） |

**依赖声明与实际环境的差异**：`requirements.txt` 只用下限约束（`>=`），未锁定版本；实际环境为 2025/2026 年的较新版本（pandas 3.x、numpy 2.x）。这会造成结果可复现性风险（见问题 H-04）。

---

## B. 当前目录与模块

### B.1 代码文件（`src/`）

| 文件 | 职责 | 依赖 |
|---|---|---|
| `src/stimuli.py` | 定义 6 个 `PROCESS_CONDITIONS`、`PROCESS_ORDINAL`（4 级）、`IDENTITY_LABELS`、8 个 `Scenario`（含 `domain`/`choice_valence`/`fixed_choice`），并用 `build_decision_text()` 拼接刺激材料。**受保护资产。** | 无外部依赖 |
| `src/scales.py` | 定义 34 个 `Item`（10 个 scale），`SCALE_ITEMS`、`ITEM_TEXT`、`ITEM_RESPONSE_RANGES`。**受保护资产。** | 无外部依赖 |
| `src/run_simulated_study.py` | 生成 6×2 设计、persona，构造 prompt，调用 DeepSeek 或 mock，规范化并写入 `raw_simulated_responses.jsonl` + 导出宽表 CSV。CLI：`--n-per-cell --seed --mock --fresh --temperature`。 | `scales`, `stimuli`, openai, dotenv, pandas, numpy, tqdm |
| `src/analyze_results.py` | 读取宽表 → 计算量表分、信度、ANOVA、控制回归、计划对比、bootstrap 中介、并行中介、分组稳健性；生成图与 `method_revision_report.md` / `measurement_and_construct_revision_report.md`。 | `scales`, `stimuli`, statsmodels, scipy, matplotlib, pandas |
| `src/generate_pilot_report.py` | 生成 `deepseek_simulated_pilot_report.md`，含运行环境、数据质量、信度、ANOVA、中介、泄露扫描。**已过时**（见问题 M-02）。 | pandas |
| `src/generate_n20_construct_validation_report.py` | 生成 `n20_construct_validation_report.md`（6 条件版本）。 | `scales`, pandas |
| `src/generate_n30_stability_replication_report.py` | 生成 `n30_stability_replication_report.md`（6 条件版本，含冻结判据）。 | `scales`, pandas |
| `src/validate_materials.py` | 枚举 `all_materials()`，写 `materials_preview.csv`，打印各条件字符长度并做关键词标记。 | `stimuli`, pandas |

### B.2 文档文件（`docs/`）

| 文件 | 职责 | 备注 |
|---|---|---|
| `docs/research_design_blueprint.md` | 研究设计蓝图：定位、理论来源、主/竞争模型、变量定义。 | 正式入口候选 |
| `docs/measurement_plan.md` | 测量与信效度计划、构念来源、责任归因边界、正式研究步骤。 | 正式入口候选 |
| `docs/scale_source_mapping.md` | 逐题项来源映射表（34 项），来源类型/依据/可否继承/验证要求。 | 关键治理文档 |
| `docs/paper_draft_simulated_study.md` | 论文草稿（摘要、引言、假设 H1–H3、方法、结果）。 | 与报告口径需核对 |
| `docs/portfolio_research_case.md` | 作品集案例长文。 | 展示材料 |
| `docs/project_one_page_summary.md` | 一页概览。 | 展示材料 |
| `docs/project_showcase_summary.md` | 项目展示摘要。 | 展示材料 |
| `docs/interview_explanation_script.md` | 面试讲解稿（30 秒 / 1 分钟 / 3 分钟）。 | 展示材料 |
| `docs/codex_to_chatgpt_handoff.md` | Agent 交接文档。 | 过程性文档，建议归档 |

**文档冗余**：`portfolio_research_case.md`、`project_one_page_summary.md`、`project_showcase_summary.md`、`interview_explanation_script.md` 内容高度重叠（同一套“一句话 + 6×2 设计 + 边界声明”）。四份展示材料 + README + 论文草稿共 6 处独立复述核心结果，存在数字口径不一致风险。

### B.3 输出文件（`outputs/`）

| 文件 | 类型 | 生成者 |
|---|---|---|
| `materials_preview.csv` | 材料预览 | `validate_materials.py` |
| `scale_scores.csv` | 量表分（每被试） | `analyze_results.py` |
| `reliability_summary.csv` | Cronbach alpha（n=360） | `analyze_results.py` |
| `anova_summary.csv` | 6×2 ANOVA | `analyze_results.py` |
| `char_len_summary.csv` | 各条件字符长度 | `analyze_results.py` |
| `controlled_regression_summary.csv` | 控制回归 | `analyze_results.py` |
| `process_dummy_coefficients.csv` | dummy 系数 | `analyze_results.py` |
| `planned_contrasts.csv` | 计划对比 | `analyze_results.py` |
| `mediation_summary.json` | 单中介 | `analyze_results.py` |
| `parallel_mediation_summary.json` | 并行中介（n=360） | `analyze_results.py` |
| `grouped_mediation_summary.csv` | 分身份中介 | `analyze_results.py` |
| `domain_robustness_summary.csv` | 按 domain 稳健性 | `analyze_results.py` |
| `scenario_robustness_summary.csv` | 按 scenario 稳健性 | `analyze_results.py` |
| `method_revision_report.md` | 方法修订报告 | `analyze_results.py` |
| `measurement_and_construct_revision_report.md` | 测量修订报告 | `analyze_results.py` |
| `n20_construct_validation_report.md` | n=20 报告 | `generate_n20_...py` |
| `n30_stability_replication_report.md` | n=30 报告 | `generate_n30_...py` |
| `final_simulated_pilot_report.md` | 最终 pilot 报告 | 生成者未在当前脚本中定位（`未核实`） |
| `deepseek_simulated_pilot_report.md` | pilot 报告 | `generate_pilot_report.py`（过时脚本） |
| `plots/*.png`（11 个） | 均值图 | `analyze_results.py` |

**说明**：`raw_simulated_responses.jsonl` 与 `simulated_responses_wide.csv` 被 `.gitignore` 排除，不在公开仓库中。

### B.4 图表命名

`outputs/plots/` 现存 11 个 PNG。其中：
- 与当前 `analyze_results.py` 输出一致的：`mean_agency.png`、`mean_free_will_attribution.png`、`mean_responsibility_total.png`、`mean_outcome_accountability.png`、`mean_moral_praise_blame.png`、`mean_process_accountability.png`、`mean_experience.png`、`mean_factual_manipulation_check.png`、`mean_subjective_process_completeness.png`。
- **疑似陈旧遗留**：`mean_manipulation_check.png`、`mean_responsibility.png`（当前脚本不再生成这两个名称，对应旧的 4 条件 / 旧 scale 命名）。见问题 M-03。

---

## C. 当前研究数据流

```text
stimuli.py (SCENARIOS + build_decision_text)
  → make_design()            [run_simulated_study.py]  6×2×n 行，含 material/persona/structure_level
  → make_persona()           [run_simulated_study.py]  随机 persona 标签
  → build_prompt()           [run_simulated_study.py]  system + user(JSON, 含全部题项)
  → call_deepseek() / mock_response()  [run_simulated_study.py]
  → raw response (dict)       extract_json()
  → normalize_record()        [run_simulated_study.py]  范围裁剪 → clean ratings
  → raw_simulated_responses.jsonl (gitignored)
  → export_wide()             [run_simulated_study.py]  → simulated_responses_wide.csv (gitignored)
  → scale_scores()            [analyze_results.py]     → scale_scores.csv
  → reliability/anova/controlled/contrasts/mediation/parallel_mediation/robustness
                              [analyze_results.py]     → 多个 CSV/JSON
  → plot_means()              [analyze_results.py]     → plots/*.png
  → generate_method_report()/generate_measurement_report()  → outputs/*.md
  → generate_n20/n30_report.py                          → outputs/n20/n30_*.md
  → docs/*.md（论文草稿、展示材料）                        [手工撰写，数字手工填写]
  → 网站 GitHub Pages（作品集页）                          [手工填写，未核实同步机制]
```

**逐步对应文件/函数已在上图标注。** 关键断点：
- `raw → wide` 之后所有分析依赖 `simulated_responses_wide.csv`，但该文件 gitignored，公开仓库无法从原始数据重算 CSV/JSON（复现链断裂）。
- `report → docs → website` 之间无自动化，全部手工同步（数字可追溯性缺失）。

---

## D. 问题分级

> 图例：`是否改变当前结果解释` = 若修复/澄清是否会改变目前 README/报告的表述方式。

### D.1 阻断级（BLOCKER）

> 2026-07-10 更新：经项目作者正式确认，公开的 360 条 v1 记录来自真实 DeepSeek API 调用（非 mock）。原 B-01（曾把 v1 数据来源当作存疑、并列为研究诚信阻断）的判断**已撤销**，不再作为 Blocker。相关问题重新归类为 `H-00`（高优先级，历史运行 provenance 不完整）。

**当前无阻断级问题。**

### D.2 高优先级（HIGH）

| ID | 问题 | 证据位置 | 影响 | 改变结果解释? | 建议阶段 | 需人工决策? |
|---|---|---|---|---|---|---|
| H-00 | **v1 历史真实 API 基线的运行溯源不完整**。作者确认 360 条数据来自真实 DeepSeek API（非 mock）。但仓库中 `raw_*.jsonl`、`*_wide.csv` 被 gitignore，且无 run manifest，第三方**无法完整恢复当时的运行条件**（模型服务端精确版本、token、费用、完整时间戳、prompt hash、依赖版本、原始运行命令等）。该问题影响运行审计、完全复现与模型版本追踪，**但不否定 v1 结果的真实性**。v1 应作为 historical DeepSeek API baseline 保存；后续新运行必须建立完整 manifest。**不得以 Alpha 或结果分布反推数据来源，不得伪造缺失的历史运行元数据。** | `.gitignore` L16-17；`outputs/reliability_summary.csv`；`outputs/parallel_mediation_summary.json`；作者 provenance 确认（见 `AGENT_WORKLOG.md` 2026-07-10 补充） | 影响历史运行审计与第三方完全复现能力；不影响 v1 数据真实性。 | 否（不改变 v1 结果解释的真实性，仅限定“完全可复现”表述） | Phase 1(FND-001 provenance 声明) / Phase 7(v1 baseline 固化) | 是（provenance 声明措辞由作者确认） |
| H-01 | **样本量 ≠ 独立信息量**。360 条全部来自单一模型 `deepseek-chat`、单一 prompt 模板；`participant_id` 仅为记录编号（`{identity}_{process}_{n:03d}`）；persona 只改标签不改信息源。称“360 被试/样本”会夸大独立性。 | `run_simulated_study.py` `make_design()` L134-161、`make_persona()` L60-70 | 信度/中介的 n=360 被误读为统计独立观测；构成伪重复。 | 是 | Phase 4/5 | 否（工程+表述） |
| H-02 | **prompt 泄露研究结构**。`build_prompt()` 一次性展示全部题项且带 `scale` 字段（构念名），并在 `factual_check_rule` 中直接告诉模型判断规则（“只根据【决策过程】判断，0/1/2 编码”）。模型易推断假设并配合。 | `run_simulated_study.py` L73-115（`items_for_prompt` 含 `scale`；`factual_check_rule` L95-98） | manipulation check 与主效应可能由“模型迎合提示”产生，而非材料操纵。 | 是 | Phase 2/3 | 否 |
| H-03 | **6 水平分类 vs 4 级趋势混用**。`structure_level = PROCESS_ORDINAL[process]`，把 6 个条件压成 4 级（0,0,1,2,2,3），中介分析用 `structure_level` 作连续 X，而 ANOVA/回归用 6 水平 dummy。趋势变量把诊断条件（`direct_choice_long`、`reasons_concise`）与其“最近实质条件”强行同级。 | `stimuli.py` `PROCESS_ORDINAL` L25-32；`run_simulated_study.py` L151；`analyze_results.py` `bootstrap_mediation()` L267、`parallel_mediation()` L311 | 中介系数依赖人为赋序，效应量与解释受编码方式影响。 | 是 | Phase 4 | 是（分析口径决策） |
| H-04 | **依赖未锁定 + 版本漂移**。`requirements.txt` 仅 `>=`；实际 pandas 3.x / numpy 2.x / statsmodels 0.14.6。不同环境结果可能不一致。 | `requirements.txt` L1-8；`pip list` | 复现性无法保证；无 lockfile。 | 否（但影响可复现性） | Phase 1 | 否 |
| H-05 | **输出无隔离、会被覆盖**。所有脚本写死 `OUT = ROOT/"outputs"`，`--fresh` 会 `unlink` 原始文件；无法并存多次运行，无 run_id/manifest。 | `run_simulated_study.py` L26-30, L296-299；`analyze_results.py` L16-34 | 一次误运行即覆盖公开基线结果，且无法追溯是哪次运行产出。 | 否 | Phase 3/Phase 1(FND-008) | 否 |
| H-06 | **报告数字→docs→网站全手工**。无从 JSON 生成展示数字的机制；6 处独立复述核心结果。 | README L43-56；`docs/*.md`；网站 `未核实` | 数字口径易漂移、不可追溯。 | 否 | Phase 6 | 是（同步方案） |

### D.3 中优先级（MEDIUM）

| ID | 问题 | 证据位置 | 影响 | 改变结果解释? | 建议阶段 | 需人工决策? |
|---|---|---|---|---|---|---|
| M-01 | **choice_valence 与 domain、fixed_choice 绑定**，非独立操纵。每个 `Scenario` 的 valence 与 domain 固定，`fixed_choice` 也与 valence 耦合（negative_choice 情境固定选“回避/被动”项）。 | `stimuli.py` `SCENARIOS` L49-122 | 无法把效价效应与领域/所选项分离；责任归因受混淆。 | 是（限责任归因表述） | Phase 2 | 否 |
| M-02 | **`generate_pilot_report.py` 已过时**：使用 4 条件 `PROCESS_ORDER` 和旧 scale 名 `manipulation_check`、`mc_` 前缀，与当前 6 条件 / `factual_manipulation_check` 不符，对当前数据大概率报错或产出错误表。 | `generate_pilot_report.py` L14-23, L145-146 | 死代码/误导；`deepseek_simulated_pilot_report.md` 可能是旧口径。 | 否 | Phase 1/Phase 5 | 否 |
| M-03 | **陈旧图表遗留**：`plots/mean_manipulation_check.png`、`plots/mean_responsibility.png` 不在当前脚本输出集合内。 | `outputs/plots/`；`analyze_results.py` L700-701 | 展示旧命名图，易与当前结果混淆。 | 否 | Phase 3/Phase 6 | 否 |
| M-04 | **factual_manipulation_check 计算了 Cronbach alpha（0.895）**，但它是 0–2 事实编码题、非同质 Likert 构念，alpha 不适用。 | `analyze_results.py` `reliability_summary()` L131-144；`outputs/reliability_summary.csv` L10 | 信度指标被误用。 | 是（限信度表述） | Phase 4 | 否 |
| M-05 | **responsibility_total 合并三子维度**，而子维度方向可能不一致（文档已承认仅探索性）。 | `analyze_results.py` L125-127；`docs/measurement_plan.md` L29-38 | 合并分掩盖子维度差异。 | 否 | Phase 4 | 否 |
| M-06 | **构念重叠未做区分效度**：agency / autonomy / free_will_attribution 题项语义高度重叠（均含“自主/根据理由/不被推着走”）；perceived_intelligence 与理由质量重叠。 | `scales.py` L16-43（如 `autonomy_not_merely_pushed` vs `freewill_not_merely_pushed`） | 高 alpha 可能来自题项近义重复而非构念良好。 | 是 | Phase 4 | 否 |
| M-07 | **情境分配非随机**：`scenario = SCENARIOS[n % len(SCENARIOS)]` 为确定性循环，与 cell 内序号绑定；`rng.shuffle(rows)` 仅打乱运行顺序不改变分配。 | `run_simulated_study.py` L141, L160 | 情境与条件的平衡由取模保证，但非随机化。 | 否 | Phase 2 | 否 |

### D.4 低优先级（LOW）

| ID | 问题 | 证据位置 | 影响 | 建议阶段 |
|---|---|---|---|---|
| L-01 | 全局硬编码路径 `ROOT/OUT`，不可配置。 | 各脚本顶部 | 工程化障碍 | Phase 1/3 |
| L-02 | provider（DeepSeek/openai）与 runner 强耦合，无 provider 抽象。 | `run_simulated_study.py` L33-43, L118-131 | 无法跨模型 | Phase 3 |
| L-03 | 分析与报告生成混在 `analyze_results.py` 单文件（720 行）。 | `analyze_results.py` | 可维护性 | Phase 1/4 |
| L-04 | JSON 解析用正则兜底（`extract_json`），非严格 schema 校验（虽已装 pydantic 未使用）。 | `run_simulated_study.py` L46-57 | 解析鲁棒性 | Phase 1/3 |
| L-05 | 无单元测试、集成测试、CI。 | 仓库无 `tests/`、无 `.github/` | 质量保障缺失 | Phase 1 |
| L-06 | 报告脚本各自重复实现 `markdown_table`/`fmt`/`leak_scan`。 | 三个 report 脚本 | 重复代码 | Phase 5 |

### D.5 暂不处理（WON'T FIX NOW）

| ID | 问题 | 理由 |
|---|---|---|
| W-01 | 未接入真实人类被试 | 超出模拟原型范围，属未来 Human Study Extension |
| W-02 | 未做 EFA/CFA/测量等价性 | 需真实被试数据，Phase 之外 |
| W-03 | 未跨多模型系统复核 | 需 provider 抽象先落地（Phase 3 后再议） |

---

## E. 受保护资产清单

以下资产未经单独人工授权**不得修改/覆盖**：

| 资产 | 路径 | 说明 |
|---|---|---|
| v1 刺激材料 | `src/stimuli.py`（`SCENARIOS`、`build_decision_text`、各 `_*_block`） | 原文 |
| v1 测量题项 | `src/scales.py`（`ITEMS`） | 34 题原文 |
| v1 输出（全部） | `outputs/**`（CSV/JSON/MD/PNG） | 当前公开结果 |
| v1 研究报告 | `outputs/*_report.md`、`docs/paper_draft_simulated_study.md` | 结果口径 |
| v1 图表 | `outputs/plots/*.png` | |
| README 结果数字 | `README.md` L43-56 | |
| 网站结果数字 | 作品集页 `https://sherlock0717.github.io/projects/llm-agent-free-will-attribution/` | `未核实` 同步来源 |
| 基线 commit | `00c4725dc7b891de3a7bfa11b4856be177d9d2a6` | v0.1 冻结点 |

> **v1 provenance 定性（作者确认）**：`outputs/**` 的 360 条结果为 **DeepSeek 历史真实 API 基线（historical DeepSeek API baseline）**。处理原则：不删除、不覆盖、不重新生成后冒充原始结果、不改写为 mock；计算并保存文件 hash（FND-001）；补 provenance 声明；明确历史运行元数据不完整（H-00）；v1 与后续 v2 结果并存；后续新运行全部走可追溯管线。

---

## F. 尚未核实事项（未核实）

以下内容无法仅凭当前仓库确认，标记 `未核实`，不作猜测。

> 说明：**“360 条数据是否来自真实 API”不再是未核实事项** —— 作者已确认来自真实 DeepSeek API（见 H-00）。以下仅保留“历史运行的具体元数据”缺失项，属于 provenance 不完整（H-00），不属于数据来源存疑。

1. `未核实`：v1 运行当时的 DeepSeek **精确模型服务端版本快照**（代码默认 `deepseek-chat`，但未记录服务端版本）。
2. `未核实`：v1 运行的 **token 使用量、调用费用、完整时间戳、原始运行命令、prompt hash、依赖版本（dependency lock hash）**（均未记录到任何产物中）。
3. `未核实`：`outputs/final_simulated_pilot_report.md` 的生成脚本（当前 `src/` 中未定位到直接生成它的脚本）。
4. `未核实`：网站（GitHub Pages）当前展示的数字与哪一次运行/哪个 CSV 对应，以及是否手工填写。
5. `未核实`：上游告知的“隔离 worktree smoke test 通过”的具体命令与输出（本轮未重跑，仅记录声明）。
6. `未核实`：`outputs/plots/` 中 11 个 PNG 是否全部由同一次运行生成（存在疑似旧命名图）。
7. `未核实`：commit `00c4725` 是否等于远程 `main` 的当前 HEAD（未执行 fetch/远程比对）。
