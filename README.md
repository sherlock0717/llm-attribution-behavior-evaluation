# LLM 归因行为评测

A Reproducible Study and Evaluation Prototype

> 围绕模型如何对行动者的能动性、自由意志与责任作出归因，构建从历史研究、任务契约到可复现运行与证据审计的**测试型评测基准**。

## 项目概述

本项目是一个**可复现的测试型评测基准原型**：以「模型如何对行动者作出归因」为对象，把一套 6×2 的决策情境材料、结构化题项、评测运行器与证据审计组织在同一个可复现的仓库里。

它评价的是**模型输出中的归因行为**，不判断模型本身是否拥有自由意志，也不把模型输出当作人类总体心理结论。当前它不是成熟的多模型公开基准；多模型执行是未来方向，非当前已完成能力。

数据边界：公开的历史记录来自**真实 DeepSeek API** 调用（模型模拟，非人类被试）。仓库中的 **mock（规则生成）仅用于工程与持续集成流程验证，不进入研究结论**。历史运行的 provenance（溯源元数据）不完整——数据来源真实已确认，但无法逐字节完全复现历史运行。

## 研究问题

不同的**决策过程描述**与**行动者身份标签**，如何影响模型对行动者的能动性、自由意志与责任作出的归因。

- 把决策过程讲得更完整，模型给的能动性评分会更高吗？
- 自由意志的评分是直接跟着过程走，还是先经过能动性这一步？
- 这种变化会不会只是因为文本更长、或模型觉得对方更聪明？

## 实验设计

6 × 2 设计：六种决策过程 × 两种身份标签，每格样本量相同。

- 六种决策过程（低结构到高结构）：直接选择、长文本直接选择、列出可选方案、简洁理由权衡、完整理由权衡、反思与反馈修正。
- 两种身份标签：AI 决策者、人类决策者。
- 诊断条件：`direct_choice_long`（长文本直接选择）只加长度不加结构；`reasons_concise`（简洁理由权衡）只给结构不给长度——两者用于分离「文本更长」与「过程更完整」。
- 材料覆盖 8 个情境、6 个决策领域；测量共 10 个构念、34 个题项，构念分数为其题项均值（事实操纵检验计 0–2，其余题项计 1–7）。

链条：情境 → 过程条件 → 身份标签 → 题项响应 → 构念分数 → 条件与身份比较。

## 历史数据与主要结果

历史结果按 6 过程 × 2 身份 × 每格相同样本组织为 12 个实验单元。以下结论只描述单一模型在这套材料下的输出行为，均由脚本从 `outputs/` 派生，未手工改动：

- 能动性随过程结构总体上升，是方向最稳定的主结果；同时控制感知智能与文本长度后仍显著。
- 自由意志归因的直接过程效应在控制后不再显著，更像经由能动性的**关联性间接路径**发生（该间接效应的自助区间不跨 0；感知智能路径区间跨 0）。这是关联性路径诊断，**不是**因果中介证明。
- 身份标签本身影响明显：在自由意志、责任与体验维度上模型对人类与 AI 的评分存在系统差异，在感知智能与操纵检验上差异很弱。
- 理由/反思结构比单纯拉长文本更能提高能动性评分（预设对比中，简洁理由权衡、反思反馈显著高于长文本直接选择）。

不使用「证明了」「揭示真实心理机制」「模型具备自由意志」「与人类完全一致」等表述。

## 测试型评测基准

从研究问题到评测执行的工程链：任务规格（`TaskSpec`）→ 刺激快照 → Prompt → 模型接口（`Provider`）→ 原始响应（`ResponseRecord`）→ 解析 → 校验 → 修复 → 计分（`ScoreRecord`）→ 聚合报告（`AggregateReport`）→ 运行清单（`RunManifest`）。任务规格、模型配置、Prompt、刺激集、计分规格与运行产物各自记录 `SHA-256`，运行清单据此把一次运行的输入与产物关联起来，支持审计。

## 可复现运行

当前可复现的是**工程流程**（历史模型运行本身因元数据缺失尚不能逐字节复现）。CLI 统一使用 `python -m freewill_attribution.cli`。

```bash
uv sync --frozen                                   # 安装锁定依赖
python -m freewill_attribution.cli run --mock --n-per-cell 2 --out <临时目录>
python -m pytest -q                                # 测试
```

跨平台运行脚本（统一转调上面的 CLI，默认写系统临时目录）：

```powershell
# Windows PowerShell
scripts\run_all.ps1 -Mock -NPerCell 2
```

```bash
# Linux / macOS / Git Bash
bash scripts/run_all.sh --mock --n-per-cell 2
```

package CLI 只暴露 **mock** 运行与真实运行的**离线 dry-run**；真实 API 运行需显式开启并单独授权（见「真实模型运行计划」）。运行产物写入 `artifacts/runs/<run_id>/`（gitignored），历史 `outputs/` 永久只读、互不覆盖。

## Mock 工程验证

确定性 `mock` 验收运行（每格 2 条；smoke 为每格 1 条）用于验证运行器、解析、计分、恢复与产物链能否按契约工作。**确定性 mock 是非真实模型输出，不进入研究结论，也不代表已完成任何公开基准。**

## 真实模型运行计划

真实模型接入方案已完成**离线验证**（provider adapter、预算控制、错误分类、离线 dry-run、凭据隔离），但**尚未真正运行**。在运行日核验模型、价格与凭据后，可直接执行真实运行：

- Smoke：12 条，每个实验单元 1 条；
- Pilot：60 条，每个实验单元 5 条；
- 未来真实运行将记录 token、费用、延迟、解析与 schema 质量、条件与身份结果，并生成脱敏公开报告。

在真实运行发生前，任何 token、费用、延迟或模型表现都不会被伪造或写入公开页面。详见 `docs/runs/REAL_PILOT_RUNBOOK.md` 与 `docs/runs/REAL_PROVIDER_READINESS.md`。

## 证据来源

用四态标注每个维度可被核查到的程度：**仓库可核查**、**作者记录**、**现有材料重建**、**当前未知**。四态互不等价；作者记录与重建都不显示为已核查，标为未知的维度不会被补写成确定事实。历史记录数、实验设计、量表定义与离线 Provider 代码为仓库可核查；历史 Provider 为 DeepSeek 属作者记录；历史精确模型/Prompt 快照、token、费用、原始响应等属当前未知。

## 仓库结构

```text
src/freewill_attribution/   评测运行器、Provider 接口与计分逻辑
configs/                    任务、模型、Prompt 与研究配置契约
outputs/                    历史聚合结果、统计产物与图表（只读、不覆盖）
site/                       静态展示页与其数据
scripts/                    数据构建脚本（build_site_data / build_public_report / build_showcase_data）
docs/                       研究协议、证据审计与运行手册
tests/                      单元 / 集成 / 特征化 / 站点测试
```

仓库不公开完整原始 API 响应、原始 JSONL、宽表原始响应文本、日志或任何密钥文件。

## 快速开始

```bash
git clone https://github.com/sherlock0717/llm-attribution-behavior-evaluation.git
cd llm-attribution-behavior-evaluation
uv sync --frozen
python -m pytest -q

# 生成站点数据并本地预览展示页
python scripts/build_site_data.py
python scripts/build_public_report.py
python scripts/build_showcase_data.py
python -m http.server 8000 --directory site   # 打开 http://localhost:8000/
```

## 文档入口

- 研究方法：`docs/research_design_blueprint.md`
- 结果报告：`outputs/final_simulated_pilot_report.md`
- 证据来源声明：`docs/audit/v1_provenance_statement.md`
- 真实接入离线准备：`docs/runs/REAL_PROVIDER_READINESS.md`
- 真实运行手册：`docs/runs/REAL_PILOT_RUNBOOK.md`
- 在线展示页：https://sherlock0717.github.io/llm-attribution-behavior-evaluation/

## 许可

暂未设置正式开源许可，仅用于研究原型说明与可复现展示。
