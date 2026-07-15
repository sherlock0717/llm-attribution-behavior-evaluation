# 风险登记表（RISK_REGISTER）

> 概率 / 影响：低 / 中 / 高。状态：Open / Mitigating / Watching / Closed。
> 关联审计问题编号见 `docs/audit/current_state_v0.1.md §D`。

| 编号 | 风险 | 概率 | 影响 | 触发条件 | 预防措施 | 应对措施 | 负责人 | 状态 |
|---|---|---|---|---|---|---|---|---|
| R-01 | **研究结论夸大**：把描述性/探索性结果表述为心理机制或 AI 心智证据 | 中 | 高 | 撰写报告/README/网站/面试稿时使用“证明/机制/被试”等措辞 | 证据等级制度（ANA-003）；文档卡片统一边界声明；AGENTS 禁止事项 | 降级表述；回退到证据等级标签；人工复核 | 研究 Agent + 作者 | Open (关联 H-01) |
| R-02 | **模拟响应伪重复**：单模型/单 prompt 的 360 条被当作独立观测 | 高 | 高 | 报告用 n=360 讲信度/中介独立性 | Data Card 严格区分记录/运行/prompt/模型/独立系统/人类被试；schema `is_independent_source=False` | 明确注明记录数≠独立样本；跨模型/跨 prompt 复核（Phase 3+） | 分析 Agent | Open (H-01) |
| R-03 | **prompt 泄露研究意图**：构念名、全部题项、判断规则同时暴露 | 高 | 高 | 使用当前 `build_prompt`（含 scale 字段与 factual_check_rule） | PromptConfig `expose_construct_names=False`、题项分批；prompt 版本化 | stimuli/prompt v2 重构（RES-002/RUN-001）；对比泄露前后结果 | 研究 Agent | Open (H-02) |
| R-04 | **材料控制失败**：长度/自然度/信息密度/元描述未对齐，valence 与 domain/选项耦合 | 中 | 高 | 直接沿用 v1 材料做正式分析 | v2 长度矩阵化、去元描述、valence 解耦、随机化（RES-002） | 材料 diff + 平衡检查未过则不冻结 | 研究 Agent | Open (M-01,M-07) |
| R-05 | **输出被覆盖**：`--fresh` unlink 或写死 `outputs/` 覆盖公开基线 | 中 | 高 | 在正式仓库运行任何写 `outputs/` 的脚本 | 输出隔离（FND-004，显式 `--out` fail-fast）；gate 校验 `outputs/` hash | 从 git 恢复 `outputs/`；用 baseline_hashes 校验 | 工程 Agent | Mitigating (H-05) |
| R-06 | **真实 API 成本失控** | 中 | 中 | 误用非 mock 模式或大 n | 默认 mock；dry-run 预估；`max_calls`/`max_cost` 硬上限（RUN-003）；授权与预算上限由 DEC-012 决定 | 预算超限即停；人工授权方可真实调用 | 工程 Agent + 作者 | Open (DEC-012,RUN-003) |
| R-07 | **密钥泄露**：API key 进入代码/日志/git | 低 | 高 | key 写入文件或被提交 | `.gitignore` 已排除 `.env`；泄露扫描脚本；provider 只从环境读 | 撤销并轮换 key；清理历史 | 工程 Agent + 作者 | Watching |
| R-08 | **依赖升级改变结果**：无 lockfile，pandas 3.x/numpy 2.x 漂移 | 中 | 中 | 换环境/升级依赖后重算 | `uv.lock` 锁定（FND-002）；mock 数值回归测试 | 固定版本；记录 dependency_lock_hash 到 manifest | 工程 Agent | Open (H-04) |
| R-09 | **Windows/WSL 差异**：换行、编码、路径、字体 | 中 | 中 | 跨平台运行/CI | 跨平台脚本（FND-008）；CI 双平台矩阵（FND-007）；utf-8 显式 | 修复平台分支；统一路径 API | 工程 Agent | Open |
| R-10 | **网站数字不同步**：手工填写、与来源 run 脱节 | 高 | 中 | 手工更新网站/README 数字 | 单一 JSON 来源（SITE-001/003）；一致性测试 | 回退到 JSON 数字；标注来源 run_id | 工程/前端 Agent | Open (H-06) |
| R-11 | **多 Agent 同时修改冲突**：工程/材料/分析/网站在同一 PR | 中 | 高 | 跨层任务合并 | AGENTS 分支规范；禁止跨层 PR；一次一任务 | 拆分 PR；rebase 解冲突 | 全体 Agent | Open |
| R-12 | **结果文件被手工修改** | 低 | 高 | 直接编辑 CSV/JSON/报告数字 | 禁止手工改数字（AGENTS）；结果由脚本生成 | 从 git 恢复；追溯改动 | 全体 Agent | Watching |
| R-13 | **测量来源不完整**：缺 DOI/正式出版信息、理论与量表来源混同 | 中 | 中 | 撰写测量文档/发表 | references 库（DOC-004）；来源类型分列 | 补齐文献；标注 `未核实` | 研究/文档 Agent | Open (M-04,M-06) |
| R-14 | **开源许可证选择错误** | 中 | 中 | 自动/随意添加许可证 | 禁止自动加许可证（AGENTS）；DEC-001 人工决策 | 更换许可证；说明适用范围 | 作者 | Open (DEC-001) |
| R-15 | **v1 历史真实 API 基线的 provenance 不完整**：真实 DeepSeek API 来源已由作者确认（**不再是 mock 风险**），但缺少机器可验证的完整历史 manifest（模型服务端版本、token、费用、时间戳、prompt hash、依赖版本、原始命令） | 中 | 中 | 第三方要求完整复现或严格运行审计 | FND-001 计算 v1 hash + provenance 声明；明确“历史运行溯源不完整”而非“来源不明”；后续新运行全部走可追溯管线 | 在 Data Card / release 标注 historical baseline 与元数据缺失；**不得伪造历史元数据** | 作者 + 分析 Agent | Open (H-00) |
| R-16 | **过早 benchmark 化导致范围失控**：单研究仓库提前建通用框架 | 中 | 高 | 大量无使用场景抽象；多模型/多任务/leaderboard 同时启动 | 当前以研究原型为主（DEC-009/010）；benchmark 任务进 Future Backlog（BMK-*）；至少两个稳定研究任务后再考虑 task registry | 冻结通用化任务；回收空模块；回到最小实现 | 全体 Agent + 作者 | Open (DEC-011) |
| R-17 | **把长期 benchmark 愿景描述为当前已实现能力** | 中 | 中 | README/网站/release 使用“通用 benchmark 已建立”等措辞 | README 和网站分开写“当前能力”与“未来方向”；每个 release 标注成熟度等级（BMK-L1..L4）；AGENTS 口径 | 更正表述；降级为“未来方向” | 文档 Agent + 作者 | Open (DEC-009/011) |
| R-18 | **重构改变数值行为**：拆分 analyze_results 引入差异 | 中 | 中 | Phase 4 拆分后结果与 v1 不一致 | characterization tests（FND-003）+ mock 固定种子数值回归；小步 PR | revert PR；定位差异 | 分析 Agent | Open (L-03) |
