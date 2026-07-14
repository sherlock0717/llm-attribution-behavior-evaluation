# 大语言模型 Agent 决策结构对自由意志归因的影响

## 项目一句话

本项目将“AI 是否像是在自主选择”这一抽象问题，转化为一个可操作的心理学模拟实验原型，并用 DeepSeek 模拟被试预演 AI 决策解释、行动者感与自由意志归因之间的关系。

## 版本与定位（v0.2）

当前定位：一个面向可复现研究的大语言模型自由意志归因实验与模型行为评测原型。它不是成熟的通用 benchmark；多模型 / provider / benchmark 是未来方向，非当前已完成能力。

数据边界：公开的 360 条历史记录来自 **真实 DeepSeek API** 调用（模型模拟被试，非人类被试）。仓库中的 **mock（规则生成）仅用于工程与持续集成流程验证，不进入研究结果**。历史运行的 provenance（溯源元数据）不完整——数据真实性已确认，但无法逐字节完全复现历史运行。

v0.2 工程现状：
- 已完成（本地）：依赖锁定、mock-only package CLI、安全输出隔离、schema/config、跨平台运行脚本、CI 配置。
- Partial：`schema` 与 `config` 已实现基础组件，但**尚未接入正式 runner**。
- Planned：正式可追溯 runner、RunManifest 实际产出、provider abstraction、多模型执行、benchmark。
- 持续集成：**configured, remote verification pending**（已配置 Windows + Linux 矩阵，远程验证待完成）。

## 项目背景

AI 正在从回答工具变成参与判断的系统。它可能筛选简历、推荐内容、辅助办公、处理客服问题，也可能在游戏中扮演可行动的智能体。

本项目关注：当 AI 不只给出结论，而是展示候选方案、理由权衡和反思修正时，用户是否更容易把它看成一个会判断、会行动、会承担后果的系统。

## 研究问题

1. 决策过程是否会影响观察者对 AI 的行动者感？
2. 自由意志归因是否通过行动者感间接发生？
3. 这种效应是否只是因为文本更长或 AI 看起来更聪明？

## 实验设计

本项目采用 6 × 2 模拟实验设计。

6 种决策过程：

- 直接给出选择
- 长文本直接选择
- 列出可选方案
- 简洁理由权衡
- 完整理由权衡
- 反思与反馈修正

2 种身份标签：

- AI 决策者
- 人类决策者

其中，“长文本直接选择”和“简洁理由权衡”是诊断条件，用于区分文本长度效应与决策结构效应。

## 模拟流程

现实问题 → 变量拆解 → 6 × 2 材料设计 → DeepSeek 模拟被试 → 结构化数据保存 → 构念得分计算 → 事实操纵检验 → 控制回归 → 并行中介分析 → 自动报告生成

## 核心结果

基于 n-per-cell = 30 的模拟预实验：

- 总模拟响应：360
- 条件格数量：12
- 每格样本量：30
- JSON / API 失败：0
- 决策过程对行动者感的影响稳定
- 自由意志归因的直接效应不稳定，更主要通过行动者感间接发生
- 感知智能没有解释主要间接效应
- 长文本直接选择没有带来稳定提升，说明单纯文本长度不是关键
- 理由权衡和反思修正是更关键的过程线索

## 重要边界

本项目是 LLM 模拟被试的模拟预实验，不是真实人类被试研究。

本项目不能证明 AI 具有自由意志。

本项目不能替代正式心理测量信效度检验。

本项目的价值在于材料预演、理论路径诊断、分析流程验证和后续真实被试研究设计。

## 项目结构

```text
.
├── src/
│   ├── run_simulated_study.py
│   ├── analyze_results.py
│   ├── stimuli.py
│   ├── scales.py
│   └── validate_materials.py
├── docs/
│   ├── measurement_plan.md
│   ├── scale_source_mapping.md
│   ├── research_design_blueprint.md
│   ├── portfolio_research_case.md
│   └── project_one_page_summary.md
├── outputs/
│   ├── scale_scores.csv
│   ├── reliability_summary.csv
│   ├── anova_summary.csv
│   ├── controlled_regression_summary.csv
│   ├── planned_contrasts.csv
│   ├── parallel_mediation_summary.json
│   ├── final_simulated_pilot_report.md
│   ├── n30_stability_replication_report.md
│   └── plots/
├── requirements.txt
├── run_all.ps1
└── README.md
```

说明：仓库不公开完整原始 API 响应、原始 JSONL、宽表原始响应文本、日志或任何密钥文件。

## 如何运行（v0.2）

推荐使用 mock-only 的 package CLI（不读取 API key、不写入历史 `outputs/`，必须显式提供输出目录）：

```bash
python -m freewill_attribution.cli run --mock --n-per-cell 2 --out <临时目录>
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

说明：当前 package CLI 只暴露 **mock** 运行；`schema` / `config` 已实现基础组件但**尚未接入正式 runner**；真实 API 运行不由该 CLI 暴露（留待可追溯 runner 与相应授权）。

### 本地展示页预览

```bash
python scripts/build_site_data.py            # 从仓库源文件生成 site/data/*.json
python -m http.server 8000 --directory site  # 然后打开 http://localhost:8000/
```

### Legacy / Historical workflow（v0.1 历史入口，保留供参考）

v0.1 的历史研究运行通过以下入口完成（历史真实 DeepSeek API 基线即由此产生）：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:DEEPSEEK_API_KEY = "你的 DeepSeek API Key"
python .\src\run_simulated_study.py --n-per-cell 30 --out <显式输出目录> --fresh
python .\src\analyze_results.py --input <目录> --out <目录>
```

注意：不要把真实 API key 写入 README、脚本、日志或 Git；不要提交 `.env`；旧入口需显式提供输出目录，永不写入受保护的 `outputs/`。

## 展示页与文档

静态展示页（`site/`）可本地预览（见上）。页面由原生 HTML/CSS/JavaScript 构建，读取 `site/data/*.json`（由 `scripts/build_site_data.py` 从仓库源文件派生），包含 6×2 设计矩阵、过程结构梯度、流程图、条件比较条、证据三栏边界、探索性路径图与路线图等原生可视化；历史结果与 mock 明确区分，当前能力与未来方向明确分开。Research Question 栏目另有一张研究问题概念图（`site/assets/figures/attribution-research-concept.png`），仅用于解释研究结构，不承载统计结果、不计入三张历史结果图。

页面页脚的“研究数据源提交”指研究数据与设计输入最近一次变化的 commit（由 `build_site_data.py` 从这批源文件的 git 历史派生），**不是页面构建 commit、不是当前 HEAD、也不是部署 commit**；这样页面提交后 `python scripts/build_site_data.py --check` 不会因 HEAD 变化而失效。

跨平台现状：在 Windows 本地使用锁定依赖跑通 mock 流程，Bash wrapper 完成 Git Bash compatibility validation；真实 Linux 与 GitHub-hosted Windows/Linux 验证仍待发布阶段完成（Git Bash 不等于 Linux 验证）。公开部署（GitHub Pages）尚未授权，统一留待后续发布阶段。

- 研究方法（Method）：`docs/research_design_blueprint.md`
- 结果报告（Results）：`outputs/final_simulated_pilot_report.md`
- 局限与 provenance（Limitations）：`docs/audit/v1_provenance_statement.md`
- 路线图与规划（Roadmap）：`docs/planning/SHOWCASE_PLAN.md`

## 许可

暂未设置正式开源许可，仅用于作品集展示与研究原型说明。
