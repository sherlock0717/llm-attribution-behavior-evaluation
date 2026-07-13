# Site Data Contract（SITE-001）

> 定义未来（SITE-002）由 `scripts/build_site_data.py` 生成的静态 JSON 数据契约。
> 本轮**只定义契约，不生成 JSON、不创建脚本**。
> 原则：未知值使用 `null`；不编造 token / cost / 服务端模型快照 / 运行时间；动态数字一律由脚本从明确源文件派生，**不从工作日志手工写入**。

## 0. 状态枚举（status enum）

```text
"completed"             # 已实现且已本地验证
"current"               # 进行中
"planned"               # 规划中、未实现
"historical"            # 历史基线（v1 真实 API 数据）
"pending_verification"  # 已配置未远程验证（如 CI）
```

## 1. site/data/site_summary.json

规划结构（不再使用模糊的单一 `project_status`）：

```json
{
  "project_version": "...",
  "project_stage": "current",
  "local_engineering_status": "completed",
  "release_verification_status": "pending_verification",
  "source_commit": "...",
  "data_as_of_date": "...",
  "generated_at": "...",
  "historical_provider": "...",
  "historical_record_count": 360,
  "process_condition_count": 6,
  "identity_condition_count": 2,
  "n_per_cell": 30,
  "historical_data_type": "real_api_output",
  "mock_usage": "engineering_validation_only",
  "provenance_status": "...",
  "benchmark_status": "...",
  "token_usage_total": null,
  "estimated_cost_usd": null,
  "model_version_snapshot": null
}
```

字段契约：

| JSON path | type | required | source file | source field | derivation | null policy | display rule | evidence level |
|---|---|---|---|---|---|---|---|---|
| `project_version` | string | yes | `pyproject.toml` | `project.version` | 直接读取 | 不为空 | Hero 版本标签 | direct_fact |
| `project_stage` | string(enum) | yes | 规划文档 | Phase 1 阶段 | 固定 `"current"`（属通用 status enum） | 不为空 | Hero 状态 | direct_fact |
| `local_engineering_status` | string(enum) | yes | 规划 Phase 1 | — | 固定 `"completed"` | 不为空 | Hero / Reproducibility | direct_fact |
| `release_verification_status` | string(enum) | yes | `ci.yml` + 无 push 记录 | — | 固定 `"pending_verification"`（禁止 `"passing"`/`"completed"`） | 不为空 | Hero / Reproducibility | direct_fact |
| `source_commit` | string | yes | Git | `git rev-parse HEAD` | 构建时读取当前 commit（完整 SHA） | 不为空 | 页脚 | direct_fact |
| `data_as_of_date` | string(ISO date) | yes | 输入源明确日期 / Git 提交日期 | — | 取输入源的明确日期或源 commit 的提交日期；**不使用每次构建的随机当前时间作为研究数据日期** | 不为空 | Historical Results 标注 | direct_fact |
| `generated_at` | string(ISO datetime) | no | 构建时刻 | — | 构建生成时间；**仅构建信息，不作研究证据日期** | 不为空 | 页脚（构建信息） | null_missing |
| `historical_provider` | string | yes | `docs/audit/v1_provenance_statement.md` | provider | 固定 `"DeepSeek API"` | 不为空 | Design/Evidence | direct_fact |
| `historical_record_count` | int | yes | `outputs/scale_scores.csv` | 数据行数 | 统计行数（=360） | 不允许 null | Design | direct_fact |
| `process_condition_count` | int | yes | `configs/study.default.yaml` | `design.process_conditions` | 计数（=6） | 不允许 null | Design | direct_fact |
| `identity_condition_count` | int | yes | `configs/study.default.yaml` | `design.identity_labels` | 计数（=2） | 不允许 null | Design | direct_fact |
| `n_per_cell` | int | yes | `outputs/scale_scores.csv` | cell 计数 | 每格记录数（历史=30） | 不允许 null | Design | direct_fact |
| `historical_data_type` | string | yes | provenance statement | — | 固定 `"real_api_output"` | 不为空 | Evidence | direct_fact |
| `mock_usage` | string | yes | `.github/workflows/ci.yml` / CLI | — | 固定 `"engineering_validation_only"` | 不为空 | Evidence | direct_fact |
| `provenance_status` | string | yes | provenance statement §5 | — | 固定 `"incomplete_run_metadata"` | 不为空 | Evidence | derived |
| `benchmark_status` | string(enum) | yes | 规划 Phase 6 | — | 固定 `"planned"` | 不为空 | Roadmap | direct_fact |
| `token_usage_total` | int\|null | no | 历史运行 | — | 历史缺失 → `null`（不编造） | 允许 null | 不展示或标"未记录" | null_missing |
| `estimated_cost_usd` | number\|null | no | 历史运行 | — | 历史缺失 → `null`（不编造） | 允许 null | 不展示或标"未记录" | null_missing |
| `model_version_snapshot` | string\|null | no | 历史运行 | — | 历史缺失 → `null`（不编造） | 允许 null | 不展示或标"未记录" | null_missing |

> 说明：状态字段一律取自通用 status enum（§0），不得引入不属于该 enum 的复合状态值；Phase 1 用 `project_stage`/`local_engineering_status`/`release_verification_status` 三个字段分别表达。

## 2. site/data/roadmap.json

结构：`{ "phases": [ <roadmap_item>, ... ], "track_s": [ <roadmap_item>, ... ] }`

**roadmap item schema**：

| field | type | required | derivation | null policy | display rule |
|---|---|---|---|---|---|
| `id` | string | yes | 阶段/任务编号（如 `"phase-1"`、`"site-001"`） | 不为空 | 技术详情 |
| `name` | string | yes | 阶段/任务名称 | 不为空 | 卡片标题 |
| `status` | string(enum) | yes | 状态枚举 | 不为空 | 状态徽章 |
| `summary` | string | yes | 一句话说明 | 不为空 | 卡片正文 |
| `depends_on` | array[string] | no | 依赖编号 | 空数组 | 技术详情 |
| `evidence_ref` | array[string] | no | 佐证文件相对路径 | 空数组 | "来源"链接 |
| `local_status` | string(enum) | no | 本地实现状态（如 Phase 1 = `"completed"`） | 允许 null | 状态徽章（本地） |
| `release_status` | string(enum) | no | 远程/发布验证状态（如 Phase 1 = `"pending_verification"`） | 允许 null | 状态徽章（发布） |

约束：Phase 6 与所有 benchmark 项 `status` 只能是 `"planned"`；`remote_ci` / 发布相关项 `release_status` 只能是 `"pending_verification"`。

Phase 1 示例（页面显示**两个**状态标签，不将 Phase 1 简化成单一 Completed）：

```json
{
  "id": "phase-1",
  "name": "Engineering Foundation And Historical Baseline",
  "status": "current",
  "local_status": "completed",
  "release_status": "pending_verification",
  "summary": "...",
  "depends_on": [],
  "evidence_ref": ["docs/audit/repository_rebaseline_assessment.md"]
}
```

## 3. site/data/version_history.json

结构：`{ "versions": [ <version_item>, ... ] }`

**version history schema**：

| field | type | required | derivation | null policy | display rule |
|---|---|---|---|---|---|
| `version` | string | yes | 版本号（如 `"v0.1"`、`"v0.2"`） | 不为空 | 时间线节点 |
| `status` | string(enum) | yes | 状态枚举 | 不为空 | 徽章 |
| `title` | string | yes | 简短标题 | 不为空 | 节点标题 |
| `highlights` | array[string] | yes | 要点列表 | 非空数组 | 节点正文 |
| `is_future` | bool | yes | 是否未来版本 | 不允许 null | 未来版本弱化显示 |

约束：`is_future=true` 的版本不得含具体已完成能力表述；`v0.2` 的 CI 相关要点须写 "configured, remote verification pending"。

## 4. figure metadata schema（图表元数据）

用于 `site/assets/figures/` 中每张图：

| field | type | required | derivation | null policy | display rule |
|---|---|---|---|---|---|
| `file` | string | yes | 站点内图片相对路径 | 不为空 | `<img src>` |
| `source_file` | string | yes | 源图相对路径（如 `outputs/plots/mean_agency.png`） | 不为空 | "来源" |
| `title` | string | yes | 图标题 | 不为空 | figure caption |
| `alt` | string | yes | 无障碍替代文本 | 不为空 | `alt` 属性 |
| `dimensions` | string | no | 像素尺寸（如 `"1760x800"`） | 允许 null | 技术详情 |
| `evidence_level` | string(enum) | yes | 见 §5 | 不为空 | caption 边界标注 |
| `boundary_note` | string | yes | 固定含 "AI 模拟数据；非人类被试" | 不为空 | caption |

约束：仅纳入与当前分析脚本一致的图；`mean_manipulation_check.png`（1440×800，旧命名遗留）默认**不纳入**首版。

## 5. source citation schema + evidence level（来源引用与证据等级）

**source citation schema**：

| field | type | required | derivation | null policy |
|---|---|---|---|---|
| `claim` | string | yes | 页面结论文本 | 不为空 |
| `source_file` | string | yes | 源文件相对路径 | 不为空 |
| `source_field` | string | no | 字段/表列/指标 | 允许 null |
| `method` | string | no | 计算/统计方法 | 允许 null |
| `evidence_level` | string(enum) | yes | 见下 | 不为空 |
| `updated_at` | string(ISO date) | yes | 构建时刻 | 不为空 |

**evidence_level 枚举**：

```text
"direct_fact"                    # 直接事实（如记录数、条件数）
"derived"                        # 由源文件派生的汇总/口径
"descriptive"                    # 描述性统计（均值、趋势）
"planned_contrast"               # 预设计划对比
"exploratory_path_diagnostic"    # 探索性路径诊断（如中介，非机制证明）
"null_missing"                   # 历史缺失、值为 null、不编造
```

约束：中介/间接效应类结论只能标 `"exploratory_path_diagnostic"`；缺失历史元数据只能标 `"null_missing"`，不得推测补写。

## 6. site/data/historical_results.json

结构：

```json
{
  "claims": [
    {
      "id": "agency-process-effect",
      "title": "...",
      "summary": "...",
      "metrics": [
        {
          "name": "...",
          "value": 12.19,
          "display": "F = 12.19",
          "source_file": "outputs/controlled_regression_summary.csv",
          "source_field": "...",
          "evidence_level": "derived"
        }
      ],
      "source_refs": ["outputs/controlled_regression_summary.csv"],
      "figure_id": "mean-agency",
      "evidence_level": "descriptive",
      "boundary_note": "单一模型的历史 AI 模拟数据；非人类被试。"
    }
  ],
  "figures": [
    {
      "id": "mean-agency",
      "file": "assets/figures/mean_agency.png",
      "source_file": "outputs/plots/mean_agency.png",
      "title": "Agency by process condition",
      "alt": "Bar chart of mean agency across six process conditions",
      "dimensions": "1760x800",
      "evidence_level": "descriptive",
      "boundary_note": "AI 模拟数据；非人类被试",
      "sha256": "..."
    }
  ]
}
```

> `figures[]` 每项遵循 §4 figure metadata schema，并附源图 `sha256`（示例中以 `"..."` 占位，实际由 build 脚本填入完整 64 位 hash）。

**claim 至少覆盖**（`id` 建议）：
1. `factual-check`（factual manipulation check）— evidence_level `descriptive`；source `outputs/n30_stability_replication_report.md`。
2. `agency-condition-means`（agency 条件均值）— `descriptive`；source `outputs/scale_scores.csv` / `outputs/n30_stability_replication_report.md`；figure `mean-agency`。
3. `agency-controlled-regression`（agency 控制回归）— `derived`；source `outputs/controlled_regression_summary.csv`（dv=agency 行，process_F/process_p）。
4. `agency-planned-contrasts`（agency 计划对比）— `planned_contrast`；source `outputs/planned_contrasts.csv`（dv=agency 行）。
5. `freewill-controlled-regression`（free_will_attribution 控制回归）— `derived`；source `outputs/controlled_regression_summary.csv`（dv=free_will_attribution 行）。
6. `parallel-mediation`（并行中介）— **固定 `exploratory_path_diagnostic`**；source `outputs/parallel_mediation_summary.json`。
7. `responsibility-exploratory`（责任归因探索性说明）— `exploratory_path_diagnostic`；**可以没有数字**，但必须有 `source_refs` 与探索性标签。

**metric 契约**：

| field | type | required | derivation | null policy |
|---|---|---|---|---|
| `name` | string | yes | 指标名 | 不为空 |
| `value` | number\|null | no | 由 build 从 source_file 提取 | 缺失 → null |
| `display` | string | yes | 展示字符串（如 `"F = 12.19"`） | 不为空 |
| `source_file` | string | yes | 源文件相对路径 | 不为空 |
| `source_field` | string | yes | 字段/表列/单元格定位 | 不为空 |
| `evidence_level` | string(enum) | yes | 见 §5 | 不为空 |

**硬性要求**：
- 数字由 `scripts/build_site_data.py` 从 `outputs` 文件提取，**不得在 HTML 中手工硬编码统计值**；
- 每个 metric 必须有 `source_file` 与 `source_field`；
- 未找到精确字段/列/单元格时，build **必须失败**，不得猜测；
- 中介类固定 `exploratory_path_diagnostic`；
- 责任归因可无数字，但要有来源与探索性标签；
- `figures[]` 每项含 §4 figure metadata + `sha256`（源图 SHA-256）。
