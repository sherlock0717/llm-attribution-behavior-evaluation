# Public Asset Inventory（SITE-001）

> 对仓库相关资产逐项分类，供展示页选材使用。SHA-256 为审计时刻实测值。
> 分级：A Public（可直接公开）/ B Public After Transformation（转换后公开）/ C Internal Only / D Excluded From Site。
> 纪律：**不得把所有 outputs 自动标为 Public**；含原始逐条响应或密钥的内容一律排除。

## A. Public（可直接复制至页面）

| 资产 | 类型 | 来源 | 内容说明 | 含原始响应? | 需脱敏? | 计划站点路径 | 页面用途 | SHA-256 | 批准状态 |
|---|---|---|---|---|---|---|---|---|---|
| `configs/study.default.yaml` | 配置 | 项目配置 | 6 条件 + 2 身份 + n_per_cell + seed（设计摘要） | 否 | 否 | 页面文本（不复制文件） | Experimental Design 数字来源 | `53E22A337A45DB601EBF69C326A19E6D2791E98429F6F1C1B6051A6E64AAE1C7` | 待人工审阅 |
| `pyproject.toml`（version 字段） | 元数据 | 项目 | 版本号 `0.2.0.dev0` | 否 | 否 | site_summary.json | Hero 版本标签 | `814D821BC8A49A9F17A8F5B4713E63FC07FB8AB9FE2CCF8DD6C63F3ECB8F8A40` | 待人工审阅 |
| 项目定位与研究问题文本 | 文案 | 本文档 §SHOWCASE_CONTENT | 一句话定位、研究问题 | 否 | 否 | index.html | Hero / Research Question | N/A（原创文案） | 待人工审阅 |
| Phase 1–7 + Track S 阶段状态 | 结构 | 规划文档 | 阶段名称与状态 | 否 | 否 | roadmap.json | Roadmap | N/A（派生） | 待人工审阅 |

## B. Public After Transformation（需转换/摘要后公开）

| 资产 | 类型 | 来源 | 内容说明 | 含原始响应? | 需脱敏? | 计划站点路径 | 页面用途 | SHA-256 | 批准状态 |
|---|---|---|---|---|---|---|---|---|---|
| `outputs/plots/mean_agency.png` | 图表(1760×800) | analyze_results.py | agency 条件均值图 | 否 | 需加标题+来源+边界 | site/assets/figures/ | Historical Results | `8611DBD905130582FC49A1AF44724854EAFE5EA62D756379CDA5F1A851B6CE04` | 待人工审阅 |
| `outputs/plots/mean_free_will_attribution.png` | 图表(1760×800) | analyze_results.py | 自由意志归因均值图 | 否 | 需加标题+来源+边界 | site/assets/figures/ | Historical Results | `0814EE77E3B09815F1CF1545F8DA4DE50433E528F3183B627D4C92EAB3DC10C7` | 待人工审阅 |
| `outputs/plots/mean_subjective_process_completeness.png` | 图表(1760×800) | analyze_results.py | 主观过程完整性均值图 | 否 | 需加标题+来源+边界 | site/assets/figures/ | Historical Results | `66810828D1B9816D7F41EA624BE82B4C2BE958FB2A7A0D91E0A30C058736FE54` | 待人工审阅 |
| `outputs/scale_scores.csv` | CSV(360×22) | analyze_results.py | 每记录量表分（模型模拟评分，无原始文本） | 否（无 raw text） | 仅公开聚合，不逐行公开 | site_summary（派生） | 记录数/单元格数来源 | `C18BFA2CFA6AD82978D77A9AA140E12AAA6FFF6D70D7E017F1940CB9A44C496C` | 待人工审阅 |
| `outputs/reliability_summary.csv` | CSV | analyze_results.py | 10 量表 alpha（附"非正式人类信度"备注） | 否 | 摘要 + 边界标注 | 派生 | Evidence（信度仅流程检查） | `E9F58B44C6DC947DE9E0B739EFDD55A295A75E943710A1771FB4F23A68870EB7` | 待人工审阅 |
| `outputs/planned_contrasts.csv` | CSV | analyze_results.py | 计划对比（t/p/差值） | 否 | 摘要关键对比 | 派生 | Historical Results | `76B4F22C8DD9A552283AA29948A9DA60B587CBF37B16973F68305487E7B25F84` | 待人工审阅 |
| `outputs/parallel_mediation_summary.json` | JSON | analyze_results.py | 并行中介 indirect + CI | 否 | 标注"探索性路径诊断" | 派生 | Historical Results | `1A559C707389C00C1E35E273245B0E6B2A4AB9F3FC7AEA4779F76DB110C96EFC` | 待人工审阅 |
| `outputs/n30_stability_replication_report.md` | 报告 | generate_n30_...py | n=30 稳定性复核（含均值/对比/中介表） | 否 | 摘要引用，不整篇搬运 | 派生 | Historical Results | `FDAD6327CDBAB953044EDC58680D52259D2FECCB04429EED71D8656704DFEFE2` | 待人工审阅 |
| `outputs/final_simulated_pilot_report.md` | 报告 | 未核实生成脚本 | 最终 pilot 报告（含核心结论） | 否 | 摘要引用，不整篇搬运 | 派生 | Historical Results | `4A001D61098986D05DCC4F9CBD051E7C8B78762736394DE30836CE48233D9515` | 待人工审阅 |
| `configs/prompt.v1.yaml` | 配置 | 项目 | prompt 暴露标记 | 否 | 摘要为流程说明 | 页面文本 | Pipeline 说明 | `8D8B26E0D688C5995CEB0DB4D3664F6C9CC55FCA0404CB4B63EBC97D75FB8FBD` | 待人工审阅 |
| `configs/model.mock.yaml` | 配置 | 项目 | mock 模型描述 | 否 | 摘要为流程说明 | 页面文本 | Pipeline 说明 | `51B7D190508D01931D08C0D71FB79C55C868E85A77FC8B0467EE5E4E68641DB4` | 待人工审阅 |

### 图片资产逐项分类（`outputs/plots/`，均 AI 模拟数据、非人类被试、需标题+来源+边界）

| 图片 | 尺寸 | 分类 | SHA-256 |
|---|---|---|---|
| `mean_agency.png` | 1760×800 | **首版选用** | `8611DBD905130582FC49A1AF44724854EAFE5EA62D756379CDA5F1A851B6CE04` |
| `mean_free_will_attribution.png` | 1760×800 | **首版选用** | `0814EE77E3B09815F1CF1545F8DA4DE50433E528F3183B627D4C92EAB3DC10C7` |
| `mean_subjective_process_completeness.png` | 1760×800 | **首版选用** | `66810828D1B9816D7F41EA624BE82B4C2BE958FB2A7A0D91E0A30C058736FE54` |
| `mean_experience.png` | 1760×800 | 可选 | `800B8898D92466518D96164DFDF0098A6B4CEF3C5EB595B052AAAE1DA36B0AF5` |
| `mean_factual_manipulation_check.png` | 1760×800 | 可选 | `39E5EC679A66A9D2B0565ED24B68460E52615F10DEFBB0E8CF0A3E022368516E` |
| `mean_moral_praise_blame.png` | 1760×800 | 可选 | `29AF0F3EA7EA2D0DEED9042E1C778BC4EE5EA59FEA6E33A25F7CA0B56F81FF95` |
| `mean_outcome_accountability.png` | 1760×800 | 可选 | `D5094951FEC3A618A59946DE213BDDA0CDFE1EB76455BF34B730548872E5768A` |
| `mean_process_accountability.png` | 1760×800 | 可选 | `BA3D674A3F1D6897365D467A817E3BFE6FE248FA272E3E8BACCEBD83F3FF5F9F` |
| `mean_responsibility_total.png` | 1760×800 | 可选 | `4C6522316A0A558892EF566424DBE7CBAC46763C1F307E5AA2A7419BDE8E90F6` |
| `mean_manipulation_check.png` | 1440×800 | **旧命名/默认排除** | `73CF42E849CD98A1476905B3C49174C1460E2012967D3618851912677ACAEBB6` |
| `mean_responsibility.png` | 1760×800 | **旧命名/默认排除** | `D6BE48646755848034A34730C7EBD79377AFFFC018E629E3072F2CE255043026` |

> 首版仅复制 3 张"首版选用"图；"可选"图需人工点选后方可加入；"旧命名/默认排除"两张默认不进入首版；任何原始逐条响应图不存在。

> **SITE-005 复核（视觉重构）**：本轮**不新增图片资产**，仅放大并重新组织已在页面使用的 3 张"首版选用"图；页面首图（`mean_agency.png`）改为整行大图 + `<dialog>` 灯箱，其余两张为双列大图，均附读图结论与来源边界。复制后 SHA-256 与源图逐字节一致（`tests/site/test_static_site.py::test_figures_match_source_hashes` 校验通过）。批准维度：`local_preview_status = approved`；`public_release_status = pending_user_approval`（公开部署仍待授权）。新增插图需求以规范占位记录于 `docs/showcase/VISUAL_ASSET_BRIEF.md`。

> **SITE-005.1 复核**：VIS-002、VIS-003 已用原生网页可视化替换（Process Structure Gradient / Exploratory Path Diagram），页面**不再有任何 "Visual asset pending" 占位**；仍未新增任何图片资产（继续复用同 3 张历史图，SHA-256 不变）。VIS-001 仅保留在 `VISUAL_ASSET_BRIEF.md` 作候选，不放入公开页面。批准维度不变：`local_preview_status = approved`，`public_release_status = pending_user_approval`。

## E. 概念插图（Conceptual Visual · SITE-005.2）

| 字段 | 值 |
|---|---|
| 原始暂存路径 | `fcdb0f90-6a14-4e45-9412-9b6325cf17a3.png`（仓库根目录临时副本，导入后已删除） |
| 站点路径 | `site/assets/figures/attribution-research-concept.png` |
| 文件类型 | PNG（signature 校验通过） |
| 实际尺寸 | 1586 × 992 |
| 实际宽高比 | 1.5988（≈ 8:5） |
| SHA-256 | `FFCC3139FD2FBE71CC9049F06CF718BBBFBB6C56E2BF37210C8268FF702BC7F7` |
| 内容说明 | 概念示意：AI / 人类决策主体 → 六种决策过程描述 → 模型的能动性/自由意志/责任归因输出 |
| 页面位置 | Research Question 栏目（研究缘起/比较内容 之后，三个核心问题 之前） |
| 是否含原始响应 | No |
| 是否是统计图 | No |
| 是否需要脱敏 | No |
| 是否为概念插图 | Yes |
| local_preview_status | approved |
| public_release_status | pending_user_approval |
| 证据边界 | 只解释研究结构，不作为研究结果；不计入三张历史结果图；不承载统计证据 |

> 该资产为概念插图，**不得**标为历史数据证据，**不得**加入 `historical_results.figures`。字节未修改（源/目标 SHA-256 一致）。

## C. Internal Only（默认不公开）

| 资产 | 理由 |
|---|---|
| `AGENT_WORKLOG.md` | 内部工作日志、含本地路径与过程细节 |
| `docs/audit/current_state_v0.1.md` | 含本地绝对路径（1 处）与内部问题分级 |
| `docs/audit/repository_rebaseline_assessment.md` | 内部审计 |
| `docs/audit/baseline_hashes.txt` | 内部校验清单 |
| `docs/planning/*.md`（当前全部规划文档） | 内部规划、阶段/任务编号、决策与风险细节 |
| `docs/codex_to_chatgpt_handoff.md` | 过程性交接文档 |
| 桌面审核文件夹（FND-*/PLAN-*review-files） | 本地审核产物，不入 Git、不公开 |
| 临时测试输出 / 系统临时目录 | 非仓库正式资产 |

> 内部任务编号（FND-/SITE-/RES- 等）仅可在 Roadmap 技术详情**简述**，不在主文案出现。

## D. Excluded From Site（默认排除）

| 资产 | 理由 |
|---|---|
| `.env` / `*.env` | 密钥文件（仓库当前无此文件，且已被 gitignore） |
| credential / access token / 原始 API key | 安全风险；仓库扫描未发现真实密钥值（23 处命中均为环境变量名 `DEEPSEEK_API_KEY` / `api_key` 字样） |
| `outputs/raw_simulated_responses.jsonl` | 原始逐条响应；已被 gitignore，不在公开仓库 |
| `outputs/simulated_responses_wide.csv` | 原始宽表响应文本；已被 gitignore，不在公开仓库 |
| `*debug* / *request* / *response* / *token* / *key*`（outputs 下） | 调试/敏感产物；已被 gitignore |
| 系统临时文件、`*.log`、`*.tmp`、`*.bak` | 非正式资产 |

## 批准维度（本地预览 vs 公开发布）

本清单对 A/B 类可用资产附两个独立批准维度：

- `local_preview_status = approved`：允许在**本地静态展示页预览**中使用这些资产（图表复制、派生数字）。
- `public_release_status = pending_user_approval`：**尚未**授权公开部署（GitHub Pages / 对外发布）。

> 含义：本地页面可以使用上述资产进行开发与预览，**不代表**已授权对外公开部署；公开发布需用户单独授权（并入 REL-001 / Phase 7）。

## 版权与来源说明

- 图表与报告均由本仓库 `src/analyze_results.py` 及报告脚本从项目自有数据生成，**无第三方版权图片**。
- 历史数据来源为本项目自有的 DeepSeek API 调用记录。
- 展示前统一进行边界标注（AI 模拟数据、非人类被试、单模型、探索性路径诊断）。
