# LLM 归因行为评测

A Reproducible Study and Evaluation Prototype

> 围绕模型如何对行动者的能动性、自由意志与责任作出归因，构建从历史研究、任务契约到可复现运行与证据审计的**测试型评测基准**。

## 项目概述

本项目是一个**可复现的测试型评测基准原型**：以「模型如何对行动者作出归因」为对象，把一套 6×2 的决策情境材料、结构化题项、评测运行器与证据审计组织在同一个可复现的仓库里。

它评价的是**模型输出中的归因行为**，距离判断模型本身是否拥有自由意志和以模型输出替代人类总体心理结论仍很遥远。

数据边界：公开的历史记录来自**真实 DeepSeek API** 调用（模型模拟，非人类被试）。仓库中的 **mock（规则生成）用于工程与持续集成流程验证**。

## 研究问题

不同的**决策过程描述**与**行动者身份标签**，如何影响模型对行动者的能动性、自由意志与责任作出的归因。

- 把决策过程讲得更完整，模型给的能动性评分会更高吗？
- 自由意志的评分是直接受过程影响，还是先经过能动性这一中间步骤？
- 这种变化会不会只是因为文本更长、或模型觉得对方更聪明？

## 实验设计

6 × 2 设计：六种决策过程 × 两种身份标签，每格样本量相同。

- 六种决策过程（低结构到高结构）：直接选择、长文本直接选择、列出可选方案、简洁理由权衡、完整理由权衡、反思与反馈修正。
- 两种身份标签：AI 决策者、人类决策者。
- 诊断条件：`direct_choice_long`（长文本直接选择）只加长度不加结构；`reasons_concise`（简洁理由权衡）只给结构不给长度——两者用于分离「文本更长」与「过程更完整」。
- 材料（参考心理学领域相关前沿研究设计）覆盖 8 个情境、6 个决策领域；测量共 10 个构念、34 个题项，构念分数为其题项均值（事实操纵检验计 0–2，其余题项计 1–7）。

链路：情境 → 过程条件 → 身份标签 → 题项响应 → 构念分数 → 条件与身份比较。

## 历史数据与主要结果

历史结果按 6 过程 × 2 身份 × 每格相同样本组织为 12 个实验单元。以下结论描述模型测试中的输出行为（详见`outputs/` ）：

- 能动性随过程结构总体上升，是方向最稳定的主结果；同时控制感知智能与文本长度后仍显著。
- 自由意志归因的直接过程效应在控制后不再显著，更像经由能动性的**关联性间接路径**发生（该间接效应的自助区间不跨 0；感知智能路径区间跨 0）。这是关联性路径诊断，而非因果中介证明。
- 身份标签本身影响明显：在自由意志、责任与体验维度上模型对人类与 AI 的评分存在系统差异，在感知智能与操纵检验上差异很弱。
- 理由/反思结构比单纯拉长文本更能提高能动性评分（预设对比中，简洁理由权衡、反思反馈显著高于长文本直接选择）。


## 测试型评测基准

从研究问题到评测执行的工程链：任务规格（`TaskSpec`）→ 刺激快照 → Prompt → 模型接口（`Provider`）→ 原始响应（`ResponseRecord`）→ 解析 → 校验 → 修复 → 计分（`ScoreRecord`）→ 聚合报告（`AggregateReport`）→ 运行清单（`RunManifest`）。任务规格、模型配置、Prompt、刺激集、计分规格与运行产物各自记录 `SHA-256`，运行清单据此把一次运行的输入与产物关联起来用于审计。

## 可复现运行

当前**工程流程**随时可复现。CLI 统一使用 `python -m freewill_attribution.cli`。

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


## Mock 工程验证

确定性 `mock` 验收运行（每格 2 条；smoke 为每格 1 条）用于验证运行器、解析、计分、恢复与产物链能否按设定工作。

## 多模型测评计划

模型接入已完成**离线验证**（provider adapter、预算控制、错误分类、离线 dry-run、凭据隔离），但**尚未使用多模型测试运行**。
- 未来真实运行将记录 token、费用、延迟、解析与 schema 质量、条件与身份结果，并生成脱敏公开报告。

相关内容详见 `docs/runs/REAL_PILOT_RUNBOOK.md` 与 `docs/runs/REAL_PROVIDER_READINESS.md`。



## 仓库结构

```text
src/freewill_attribution/   评测运行器、Provider 接口与计分逻辑
configs/                    任务、模型、Prompt 与研究配置契约
outputs/                    历史聚合结果、统计产物与图表
site/                       静态展示页与其数据
scripts/                    数据构建脚本（build_site_data / build_public_report / build_showcase_data）
docs/                       研究协议、证据审计与运行手册
tests/                      单元 / 集成 / 特征化 / 站点测试
```


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

暂未设置正式开源许可，仅用于研究评测原型说明与可复现展示。
