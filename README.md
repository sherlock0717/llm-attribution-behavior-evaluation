# LLM 行动者归因评测

这个项目研究一个具体问题：**决策过程的写法和行动者身份，会怎样改变语言模型对能动性、选择自主性与责任的判断？**

- 在线页面：https://sherlock0717.github.io/llm-attribution-behavior-evaluation/
- 研究说明：[`docs/STUDY_CARD.md`](docs/STUDY_CARD.md)
- 研究与测量来源：[`docs/research_and_measurement_sources.md`](docs/research_and_measurement_sources.md)

## 研究任务

项目使用八个决策情境。每个情境分别呈现六种决策过程，并将行动者标记为 AI 决策者或人类决策者。模型阅读材料后，对行动控制、理由响应、选择自主性、体验性、感知智能和责任等题项评分。

当前设计包含：

- 六种过程表述：直接选择、较长的直接选择、列出方案、简洁理由比较、完整理由比较、反思与反馈修正；
- 两种行动者身份：AI 决策者、人类决策者；
- 八个情境，覆盖道德冲突、自我控制、人际关系、风险决策、责任困境与服从情境；
- 结构化响应、题项计分、条件比较和运行记录。

分析单位是**模型对一份材料给出的评分响应**。这些数据用于观察模型的归因判断如何随文本线索变化。

## 当前观察

现有公开结果支持三项较稳妥的描述：

1. 能动性评分对过程表述最敏感，包含理由比较和行为修正的材料通常获得更高评分。
2. 行动者身份会明显影响体验性、自由意志与责任相关评分，模型对 AI 与人类标签采用了不同判断方式。
3. 在加入感知智能与文本长度后，自由意志评分的直接过程差异明显减弱；能动性与自由意志评分之间的关系目前只作为关联性诊断。

这些结果来自单一模型和当前材料。现阶段更适合将其理解为**模型归因敏感性测试**，而不是关于人类心理或 AI 主体性的结论。刺激材料、题项区分度和重复调用的统计处理仍需继续完善。

## 可核查链路

仓库保留以下对象，使页面结论能够回到具体输入和产物：

```text
情境与条件
→ 实际 Prompt
→ 模型响应
→ 题项与构念分数
→ 条件比较
→ 图表与报告
```

运行器会记录任务配置、刺激快照、Prompt、响应、评分、错误信息和运行清单，并使用哈希关联输入与产物。确定性 `mock` 仅用于检查解析、校验、计分和文件生成流程。

## 本地运行

项目使用 Python 3.12 和 `uv` 管理依赖。

```bash
git clone https://github.com/sherlock0717/llm-attribution-behavior-evaluation.git
cd llm-attribution-behavior-evaluation

uv sync --frozen
uv run pytest -q

# 在临时目录执行确定性模拟运行
uv run python -m freewill_attribution.cli run \
  --mock \
  --n-per-cell 2 \
  --out <临时目录>
```

生成并预览展示页：

```bash
uv run python scripts/build_site_data.py
uv run python scripts/build_public_report.py
uv run python scripts/build_showcase_data.py
python -m http.server 8000 --directory site
```

## 仓库结构

```text
src/freewill_attribution/   任务运行、模型接口、解析、计分与运行记录
configs/                    任务、Prompt、模型和指标配置
outputs/                    当前公开分析产物
scripts/                    报告与展示页数据生成脚本
site/                       静态展示页
search/                     预留检索目录（如存在）
docs/                       研究说明、测量来源和复现文档
tests/                      单元、集成和站点测试
```

## 文档入口

- 项目研究对象与解释范围：[`docs/STUDY_CARD.md`](docs/STUDY_CARD.md)
- 研究设计：[`docs/research_design_blueprint.md`](docs/research_design_blueprint.md)
- 研究与测量来源：[`docs/research_and_measurement_sources.md`](docs/research_and_measurement_sources.md)
- 题项来源映射：[`docs/scale_source_mapping.md`](docs/scale_source_mapping.md)
- 在线展示页：https://sherlock0717.github.io/llm-attribution-behavior-evaluation/

## 权利与使用

仓库暂未采用开放许可证。代码、材料、数据和文档的复制、再分发或用于其他项目，需先获得作者许可。引用公开页面或研究说明时请注明项目名称与仓库地址。
