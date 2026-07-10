# 架构方案（ARCHITECTURE_PROPOSAL）

> 本轮只做架构与 schema 设计，不实现代码。原则：避免为目录整齐而过度拆分。

---

## A. 当前架构

```text
llm-agent-free-will-attribution/
├── src/
│   ├── stimuli.py                     # 材料 + 6 条件 + scenario（受保护）
│   ├── scales.py                      # 34 题项（受保护）
│   ├── run_simulated_study.py         # 设计+prompt+provider调用+归一化+导出（耦合）
│   ├── analyze_results.py             # 分析+报告生成（720 行，混合职责）
│   ├── validate_materials.py          # 材料预览校验
│   ├── generate_pilot_report.py       # 过时（4 条件/旧scale名）
│   ├── generate_n20_construct_validation_report.py
│   └── generate_n30_stability_replication_report.py
├── docs/                              # 9 份 md（展示材料冗余）
├── outputs/                           # CSV/JSON/MD/PNG（受保护；写死路径，会被覆盖）
│   └── plots/
├── requirements.txt                   # 仅 >= 约束，未锁定
├── run_all.ps1                        # PowerShell 一键脚本（仅 Windows）
└── README.md
```

当前流程（简）：
```text
stimuli → design → persona → prompt → DeepSeek/mock → raw.jsonl → wide.csv
       → scale_scores → {reliability, anova, controlled, contrasts, mediation, robustness}
       → plots + report.md → docs（手工）→ website（手工）
```

**主要架构问题**：provider 与 runner 耦合（L02）；分析与报告耦合（L03）；输出无隔离（H-05）；无 schema 校验（L04）；路径写死（L01）；无 package/CLI/tests/CI。

---

## B. 目标架构

```text
llm-agent-free-will-attribution/
├── pyproject.toml                     # 构建/依赖/工具配置
├── uv.lock                            # 锁定依赖
├── configs/                           # 声明式配置
│   ├── study.default.yaml
│   ├── model.deepseek.yaml
│   └── prompt.v1.yaml
├── src/freewill_attribution/
│   ├── __init__.py
│   ├── cli.py                         # 统一 CLI 入口（run/analyze/site-export/validate）
│   ├── config.py                      # 加载/解析/校验配置
│   ├── schemas.py                     # pydantic 数据对象（见 §D）
│   ├── providers/
│   │   ├── base.py                    # Provider 抽象接口
│   │   ├── deepseek.py                # DeepSeek 实现
│   │   └── mock.py                    # 规则化 mock（仅测试/流程）
│   ├── study/
│   │   ├── design.py                  # 6×2 设计、平衡、随机化
│   │   ├── prompts.py                 # prompt 构造 + 版本
│   │   └── runner.py                  # 运行编排、resume、失败隔离、manifest
│   ├── stimuli/                       # 材料加载（读取 data/stimuli/<ver>）
│   │   └── loader.py
│   ├── measurement/
│   │   ├── items.py                   # 题项加载（读取 data/scales/<ver>）
│   │   └── scoring.py                 # 量表计分
│   ├── analysis/
│   │   ├── reliability.py
│   │   ├── models.py                  # anova/回归/对比
│   │   ├── mediation.py               # 路径诊断
│   │   ├── stability.py               # 跨情境/prompt/模型
│   │   └── evidence.py                # 证据等级
│   └── reporting/
│       ├── report.py                  # md 报告（与分析解耦）
│       └── site_export.py             # 生成 site_summary.json
├── data/
│   ├── stimuli/v1/                    # v1 材料冻结快照 + hash（受保护）
│   ├── stimuli/v2/                    # v2 材料
│   ├── scales/v1/                     # v1 题项冻结快照 + hash（受保护）
│   └── scales/v2/
├── protocols/
│   └── study_protocol_v2.md
├── docs/
│   ├── audit/
│   ├── planning/
│   ├── cards/                         # study/data/model_usage/reproducibility/limitations/integrity
│   └── archive/                       # 归档冗余展示材料
├── references/
│   └── references.bib
├── artifacts/
│   ├── runs/<run_id>/                 # 每次运行隔离目录（见 §E）
│   └── releases/<version>/            # 发布产物 + checksum
├── outputs/                           # v1 历史结果（只读保留，兼容旧引用）
├── tests/
│   ├── unit/
│   └── integration/
├── scripts/
│   ├── run_all.ps1                    # 兼容旧入口（转调 CLI）
│   └── run_all.sh                     # 跨平台
└── .github/workflows/ci.yml
```

**过度拆分的规避**：不为每个函数建独立包；`analysis/` 只按“可复用统计单元”分文件；`reporting` 与 `analysis` 分离但不再细分；旧 `outputs/` 保留而非立即迁移。

> **重要**：上方 §B 是**目标终态（end-state）**，不是当前 Phase 1 一次性建成的目录。当前建设范围为“作品集级专业研究仓库 + 真实可复现运行能力”（DEC-010），按 §B.1 收敛实现，其余目录**按需增长**。

### B.1 当前 Phase 1 最小 package（当前实际建设）

```text
src/freewill_attribution/
├── __init__.py
├── cli.py         # 统一 CLI 入口：python -m freewill_attribution.cli
├── config.py      # 配置加载/解析
├── schemas.py     # 最小 schema（见下方“Phase 1 schema”）
├── paths.py       # 输出路径解析（输出隔离，显式 --out，禁写 outputs/）
└── runner.py      # 最小编排（见下方“Phase 1 runner”）
```

当前先解决：安装 / CLI / 配置 / 输出路径 / 最小 schema / 最小编排 / 测试 / CI。

#### Phase 1 runner（边界：只做最小编排）
- 只负责：新 CLI 的最小编排；调用当前 mock 路径；输出目录（`--out`）传递；**不写受保护 `outputs/`**；为后续 Phase 3A 保留接口。
- **不做**：完整 RunManifest、environment snapshot、prompt/stimulus/config version、checksum、resume、token/cost/retry、完整运行目录协议——这些是 **Phase 3A** 的交付。
- 若 Phase 1 确需一个临时 manifest 对象，只能标为 `ManifestStub / minimal metadata`，**不得**把 Phase 3A 的完整交付提前写成 Phase 1 完成项。

#### Phase 1 schema（边界：只做基础对象）
- 只需要：`RunConfig`、`RawResponse`、`NormalizedResponse`、基础错误对象（`ValidationError`）。
- 完整 `RunManifest`、`AnalysisManifest`、`SiteSummary`、`StimulusRecord`/`PersonaRecord` 等的完整字段属后续阶段（Phase 3A/4/6）。

#### Phase 3A 才实现（不得提前计入 Phase 1）
- 完整 `RunManifest`；environment snapshot；prompt/stimulus/config version；checksum；resume；token/cost/retry；完整运行目录协议（见 §E）。

**Phase 1 不提前建立**以下完整子包（除非实际任务已需要）：
```text
analysis/  reporting/  stimuli/  measurement/  providers/  study/
```
它们在对应 Phase（分析 Phase 4、文档 Phase 5、runner/provider Phase 3、材料 Phase 2）**按需**从 §B 目标结构中生长出来。

### B.2 必须保留的未来扩展接口（当前不实现）

架构设计（schema 与接口）**必须预留**，以便未来向 benchmark 方向演进：
- provider 可替换（接口稳定，当前单一 DeepSeek/mock 实现）；
- `ModelConfig` 可版本化；
- `PromptConfig` 可版本化；
- stimulus / version 可标识；
- RunManifest 可支持多个模型（字段允许，当前只填单模型）；
- schema **不绑定 DeepSeek 专有字段**；
- 分析结果能记录 `source_run_id`；
- 预留可选 `task_id` / `benchmark_id`（当前不启用）。

**当前明确不实现**：task registry、leaderboard、多模型批量 runner、benchmark suite 管理、通用评分插件、大量 provider 子模块、无使用场景的空目录。

> 原则：**当前实现最小、数据结构可扩展、长期路线明确**（防 R-16 范围失控）。新抽象必须有当前真实使用场景或明确即将执行的任务支持。

---

## C. 模块职责

| 模块 | 职责 | 明确不做 |
|---|---|---|
| `config` | 加载/合并/校验 YAML 配置，产出 `StudyConfig` 已解析对象；记录 resolved config 到 run 目录。 | 不含实验逻辑 |
| `schemas` | 定义所有 pydantic 数据对象与版本字段；严格校验 provider 返回。 | 不做 I/O |
| `providers` | 统一接口 `generate(messages, model_cfg) -> RawModelResponse`；DeepSeek/mock 实现；记录 token/cost/retry/失败类型。 | 不含题项/材料/分析逻辑 |
| `study/design` | 生成 6×2 设计矩阵、情境随机化与平衡、persona 分配、结构编码（分类+趋势分离）。 | 不调用模型 |
| `study/prompts` | 构造并版本化 prompt；控制构念名是否暴露、题项是否分批。 | 不含 provider 细节 |
| `study/runner` | 编排 design→prompt→provider→normalize→validate；resume、dry-run、预算、失败隔离；写 `artifacts/runs/<id>/`。 | 不做统计分析 |
| `stimuli` | 从 `data/stimuli/<ver>` 加载材料 + hash 校验。 | 不硬编码材料文本（迁移后） |
| `measurement` | 从 `data/scales/<ver>` 加载题项；计分；区分事实检验与 Likert。 | 不做推断统计 |
| `analysis` | reliability/models/mediation/stability/evidence；输出 `analysis_summary.json`。 | 不写 md/网站 |
| `reporting` | 从 analysis 产物生成 md 报告与 `site_summary.json`。 | 不重算统计 |
| `site_export` | 把指定 run 的分析结果导出为版本化 JSON 供网站消费（含 run_id/版本/证据等级）。 | 不手工填数字 |

---

## D. 数据对象（概念级 schema，仅设计不实现）

```text
StudyConfig
  study_id: str
  design: {factors: [process_condition(6), identity_label(2)], n_per_cell: int, seed: int}
  stimuli_version: str            # e.g. "v1" / "v2"
  scales_version: str
  prompt_config_ref: str
  model_config_ref: str
  output_dir: path                # 可配置，默认 artifacts/runs/<run_id>
  budget: {max_calls: int, max_cost_usd: float|null}

ModelConfig
  provider: str                   # "deepseek" | "mock"
  model: str                      # "deepseek-chat"
  model_version_snapshot: str|null
  temperature: float
  seed: int|null
  max_tokens: int
  response_format: str

PromptConfig
  prompt_id: str
  version: str
  expose_construct_names: bool    # 默认 False（修复 H-02）
  items_batching: str             # "all" | "by_scale" | "single"
  system_template: str
  user_template: str

StimulusRecord
  scenario_id: str
  domain: str
  choice_valence: str
  process_condition: str
  identity_label: str
  structure_level_ordinal: int    # 趋势编码（辅）
  process_category: str           # 6 水平分类（主）
  char_len: int
  material_text: str
  stimuli_version: str
  content_hash: str

PersonaRecord
  participant_id: str             # 记录编号，非独立被试
  attributes: {...}
  is_independent_source: bool     # 恒 False（单模型/单prompt时）

RawModelResponse
  participant_id: str
  provider: str
  model: str
  request_id: str|null
  raw_text: str
  finish_reason: str
  usage: {prompt_tokens, completion_tokens, total_tokens}
  latency_ms: int
  retry_count: int
  timestamp: iso8601

NormalizedResponse
  participant_id: str
  stimulus_ref: StimulusRecord
  ratings: {item_id: int|null}
  attention_check: str
  short_reason: str
  parse_status: str               # ok | repaired | failed
  errors: [ValidationError]

ValidationError
  type: enum{api, parse, schema, range, missing, runtime}
  item_id: str|null
  message: str
  severity: enum{warn, error}

RunManifest
  run_id: str
  git_commit_sha: str
  study_config_ref: str
  model_config: ModelConfig
  prompt_config: PromptConfig
  stimuli_version: str
  scales_version: str
  schema_version: str
  python_version: str
  dependency_lock_hash: str
  seed: int
  started_at / finished_at: iso8601
  n_records / n_runs / n_prompt_configs / n_models / n_independent_model_systems / n_human_subjects
  token_usage_total / estimated_cost_usd   # 允许缺失/null（provider 可能不返回）
  retry_summary / failure_summary
  data_checksums: {file: sha256}
  task_id: str|null                         # 预留（当前不启用，为未来多任务/benchmark）
  benchmark_id: str|null                    # 预留（当前不启用）

AnalysisManifest
  analysis_id: str
  source_run_id: str
  git_commit_sha: str
  methods: [...]                  # 每个统计单元 + 参数
  evidence_grades: {finding_id: grade}  # descriptive | exploratory_path_diagnostic | not_mechanism_evidence
  schema_version: str

SiteSummary
  version: str
  source_run_id / source_analysis_id: str
  headline_numbers: {...}         # 均可追溯
  evidence_grade_labels: {...}
  disclaimers: [...]
  generated_at: iso8601
```

---

## E. 运行目录（每次运行隔离）

```text
artifacts/runs/<run_id>/
├── manifest.json                 # RunManifest
├── config.resolved.yaml          # 解析后的完整配置
├── environment.txt               # python + 依赖 + OS
├── prompts.json                  # 本次实际使用的 prompt（含版本）
├── stimuli.json                  # 本次材料快照（含 hash/version）
├── raw_responses.jsonl           # RawModelResponse（每行一条）
├── normalized_responses.jsonl    # NormalizedResponse
├── validation_report.json        # 汇总错误分类
├── scores.parquet                # 量表分
├── analysis_summary.json         # AnalysisManifest + 结果
├── report.md                     # 报告
└── figures/                      # 图
```

`run_id` 建议：`<UTC时间戳>_<git短sha>_<provider>_<n>`，保证可并存、可追溯、可 resume。

---

## F. 迁移策略

1. **先固定旧行为，再重构**：Phase 1 先为旧代码建立 characterization tests（FND-003）固定当前行为；建立最小 package + 新 CLI（`python -m freewill_attribution.cli`）与旧入口**并行**。**当前不立即把旧脚本改成 thin wrapper**——新 CLI 与旧入口共存一段时间，待稳定后再收敛。
2. **先解决输出覆盖风险**：先给旧运行脚本增加安全显式输出目录（FND-004），确保永不覆盖 `outputs/`；再做后续封装。
3. **先封装的功能**：schema 校验、run 目录写入、run manifest（Phase 1 最小 / Phase 3 完整）。
4. **后拆分的功能**：`analyze_results.py` 拆为 `analysis/*` + `reporting/*`（Phase 4/5），**不在 Phase 1 拆分**；拆分时用数值回归测试（固定 mock 种子）保证等价。
5. **材料迁移**：`stimuli.py`/`scales.py` 文本在 Phase 2 复制到 `data/stimuli/v1/`、`data/scales/v1/` 并打 hash；旧模块暂时保留；**v1 文本 hash 全程不变**。
6. **旧入口可用性保障**：旧入口在每个 Phase 的 gate 中做 mock 冒烟；输出改写到临时/指定目录，永不写 `outputs/`。
7. **何时废弃旧入口**：Phase 6/7，当 CLI + CI 稳定、文档更新后，标记旧入口 deprecated（保留一个版本周期）再移除。
8. **避免一次性重写 / 避免过早通用化**：每个 Phase 单独 PR；禁止跨层（工程/材料/分析/网站）合并 PR；每步以 `outputs/` 与材料 hash 未变作为安全护栏；不在 Phase 1 接入多模型、不在 Phase 1 实现 benchmark 功能。

---

## G. Strategic Horizon · 通用 LLM benchmark / 模型行为评测框架（仅路线设计）

> 对应 DEC-011。**只做路线设计，不做当前实现**；不属于 v0.2 必做，不属于 Phase 1–Phase 7 退出条件。当前处于 BMK-L1。

| 等级 | 内容 | 定位 |
|---|---|---|
| BMK-L1 | 单研究任务；DeepSeek + mock；固定材料/量表；run manifest；可重复运行；可追溯结果 | **当前项目目标** |
| BMK-L2 | 多 prompt / 多 temperature / 多 seed / 多材料版本；同一模型跨运行比较；统一稳定性指标 | 中期方向 |
| BMK-L3 | 多 provider / 多模型；统一输入与 schema；模型间效应比较；模型版本追踪；跨模型稳健性报告 | 后续重要方向 |
| BMK-L4 | 多研究任务；task registry；统一协议；数据卡/任务卡；标准评分；版本化 benchmark suite；可选 leaderboard | 长期战略（不属于当前版本） |

架构层面为上述演进保留的接口已在 §B.2 列明（provider 可替换、config 可版本化、schema 不绑定专有字段、RunManifest 预留 `task_id`/`benchmark_id`、分析记录 `source_run_id`）。**当前一律不实现** task registry / leaderboard / 多模型批量 runner / benchmark suite 管理。
