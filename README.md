# 大语言模型 Agent 决策结构对自由意志归因的影响

## 项目一句话

本项目将“AI 是否像是在自主选择”这一抽象问题，转化为一个可操作的心理学模拟实验原型，并用 DeepSeek 模拟被试预演 AI 决策解释、行动者感与自由意志归因之间的关系。

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

## 如何运行

PowerShell 示例：

```powershell
git clone https://github.com/sherlock0717/llm-agent-free-will-attribution.git
cd llm-agent-free-will-attribution
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:DEEPSEEK_API_KEY = "你的 DeepSeek API Key"
python .\src\run_simulated_study.py --n-per-cell 30 --fresh
python .\src\analyze_results.py
```

注意：不要把真实 API key 写入 README、脚本、日志或 Git。也不要提交 `.env` 文件。

如果只想测试分析流程，可以使用 mock 模式：

```powershell
python .\src\run_simulated_study.py --n-per-cell 5 --mock --fresh
python .\src\analyze_results.py
```

## 作品集页面

项目展示页：https://sherlock0717.github.io/projects/llm-agent-free-will-attribution/

## 许可

暂未设置正式开源许可，仅用于作品集展示与研究原型说明。
