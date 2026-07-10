# AGENTS.md · 本地协作最高优先级规范

> 本文件是所有后续 Agent 的**最高优先级**本地协作规范。任何任务开始前必须先阅读本文件。
> 冲突时优先级：本文件 > `docs/planning/PHASE_GATES.md` > `docs/planning/EXECUTION_BACKLOG.md` > 其他文档。

---

## 零、不可违反的项目口径（2026-07-10 作者决策）

1. 当前主定位是**可复现的大模型模拟研究原型**（DEC-009）。
2. 通用 LLM benchmark / 模型行为评测框架是**长期战略方向**（DEC-011），不是当前能力。
3. **不得把长期路线写成当前已完成能力**（README/网站/release 必须分开写“当前能力”与“未来方向”）。
4. v1 的 360 条记录来自**真实 DeepSeek API**，**不得写成 mock**。
5. v1 缺失的是**完整历史 provenance**（元数据），**不是数据来源事实**（H-00）。
6. **不得伪造/倒推历史运行元数据**（模型服务端版本、token、费用、时间戳等）。
7. 当前建设范围是**作品集级专业研究仓库 + 真实可复现运行能力**（DEC-010），不建通用 benchmark 平台。
8. benchmark Future Backlog（`BMK-*`）**未经人工批准不得提前执行**。
9. **不得为未来扩展创建大量空模块**。
10. 新抽象必须有**当前真实使用场景**或明确即将执行的任务支持。

> 附：CLI 统一使用 `python -m freewill_attribution.cli`，不使用 `python -m src.freewill_attribution.cli`。

---

## 一、必读文件（每个 Agent 开始前）

```text
AGENTS.md
AGENT_WORKLOG.md
docs/planning/PROFESSIONALIZATION_PLAN.md
docs/planning/EXECUTION_BACKLOG.md
docs/planning/PHASE_GATES.md
```

建议同时查阅：`docs/audit/current_state_v0.1.md`（受保护资产与问题分级）、`docs/planning/RISK_REGISTER.md`、`docs/planning/DECISION_LOG.md`、`docs/planning/ARCHITECTURE_PROPOSAL.md`。

---

## 二、禁止事项

- 不得真实调用付费 API（DeepSeek 等）；默认使用 mock。
- 不得自动 `git commit`。
- 不得自动 `git push`。
- 不得删除 v1 资产（`src/stimuli.py`、`src/scales.py` 文本、`outputs/**`）。
- 不得覆盖 `outputs/`（禁止对正式仓库运行写 `outputs/` 的脚本；禁止 `run_all.ps1 -Fresh` 于正式仓库）。
- 不得手工写/改分析数字（结果只能由脚本生成）。
- 不得把模型模拟描述成人类被试结果。
- 不得把 mock 数据作为研究证据（mock 仅用于单测/集成/schema/CLI/报告流程验证）。
- 不得在未通过阶段验收（`PHASE_GATES.md`）时进入下一阶段。
- 不得在同一任务/PR 中同时修改工程 + 材料 + 分析 + 网站。
- 不得自动选择/添加开源许可证。
- 不得强制重写 Git 历史；不得创建 GitHub Release（人工执行）。

---

## 三、受保护资产（未经单独人工授权不得修改）

```text
src/stimuli.py    （v1 刺激材料原文）
src/scales.py     （v1 题项原文）
outputs/**        （v1 全部公开结果：CSV/JSON/MD/PNG）
README.md 结果数字（L43-56 区域）
网站结果数字
基线 commit：00c4725dc7b891de3a7bfa11b4856be177d9d2a6
```

---

## 四、分支规范

```text
chore/fnd-001-freeze-v01-baseline
chore/fnd-002-project-tooling
test/fnd-003-characterization-tests
fix/fnd-004-safe-output-directory
feat/fnd-005-minimal-package-cli
feat/fnd-006-minimal-schema-config
ci/fnd-007-github-actions
chore/fnd-008-cross-platform-scripts
research/res-001-protocol-v2
research/res-002-stimuli-v2
feat/run-001-provider-abstraction
feat/run-002-run-manifest
analysis/ana-001-six-level-analysis
analysis/ana-003-evidence-grades
docs/doc-001-study-card
site/site-001-data-export
release/rel-001-changelog
```

规则：`<类型>/<任务编号小写>-<简短描述>`；一个分支只承载一个任务编号。
**分支名称必须以当前 `EXECUTION_BACKLOG.md` 中的任务名称为准；若 backlog 任务已改名，AGENTS.md 中的旧示例不得继续使用。**

---

## 五、工作规则（每次任务必须）

1. 确认任务编号（来自 `EXECUTION_BACKLOG.md`）。
2. 确认允许修改文件（任务的“涉及文件”）。
3. 确认受保护文件（本文件 §三 + 任务的“明确不修改”）。
4. 执行前记录 Git 状态（`git status --short`、`git rev-parse HEAD`）。
5. 只修改本任务范围内的文件。
6. 执行任务的验收命令（真实运行，记录真实结果）。
7. 更新 `AGENT_WORKLOG.md`。
8. 停止并汇报（按 §六格式）。
9. 等待人工批准。
10. 不得自行开始下一任务。

补充：
- 运行任何生成脚本必须写入临时目录或 `artifacts/runs/<run_id>/`，严禁写 `outputs/`。
- 修改前后用 `docs/audit/baseline_hashes.txt` 校验 `outputs/`、`stimuli.py`、`scales.py` 未变。
- 遇到需人工决策的问题（见 `DECISION_LOG.md`），停下并汇报，不擅自决定。

---

## 六、汇报格式（统一输出）

```text
## 任务编号
## 目标
## 修改文件
## 未修改的受保护文件（确认清单）
## 执行命令
## 真实测试结果（不得把未执行写成通过）
## Git diff（摘要）
## Git status（--short）
## 风险
## 未完成事项
## 下一任务建议
```

---

## 七、Git 安全

- 绝不更新 git config；绝不 `push --force` / hard reset / `--no-verify`。
- commit / push / tag / release 一律由人工执行。
- Agent 仅准备变更并汇报 diff，等待人工提交。
