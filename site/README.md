# 静态展示页（site/）

**LLM 归因行为评测 · A Reproducible Study and Evaluation Prototype** 的静态展示页。原生 HTML/CSS/JavaScript + 静态 JSON，无框架、无 CDN、无外部字体、无第三方 JS、无后端、无远程 API。页面组织为一篇连续的研究与工程报告：项目概览 → 研究问题 → 实验设计与测量 → 历史数据 → 完整分析链 → 结果总结 → 可复现评测核心 → Mock 工程验证 → 真实模型接入准备 → 证据与来源边界 → 可复现运行 → 后续扩展。

## 本地预览

```bash
python -m http.server 8000 --directory site
```

然后在浏览器打开 http://localhost:8000/ 。

> 请通过本地静态服务器访问；直接以 `file://` 双击打开会因浏览器安全策略导致 `fetch` 加载 JSON 失败。附加 `?diagnostics=1` 可让页面把渲染诊断（`renderComplete`、文档滚动宽度等）写入 `<html>` 的 `data-*`，供浏览器验证读取。

## 数据来源

页面上的所有动态数字（记录数、条件数、构念/题项、信度、条件均值、身份效应、对比、回归、路径、mock 质量、provenance 计数、状态等）都来自 `site/data/*.json`，由仓库脚本从源文件生成，**不在 HTML 中硬编码**：

```bash
python scripts/build_site_data.py        # site_summary / roadmap / version_history / historical_results
python scripts/build_public_report.py    # evaluation_summary / evidence_matrix / engineering_status
python scripts/build_showcase_data.py    # showcase_story / measurement_summary / analysis_results / reproducibility_summary
# 各脚本均支持 --check，校验 site/data 与源文件一致
```

页面加载的 JSON：`site_summary.json`、`showcase_story.json`、`measurement_summary.json`、`analysis_results.json`、`historical_results.json`、`engineering_status.json`、`evidence_matrix.json`、`reproducibility_summary.json`。

图表以原生 SVG / HTML-CSS 渲染，支持中文标签与 390px 窄屏；三张历史结果图为既有分析产物（`outputs/plots/`），经哈希校验后复制到 `assets/figures/`。Research Question 栏目的研究问题概念图 `assets/figures/attribution-research-concept.png` 为概念插图，仅解释研究结构，不承载统计结果，也不计入三张历史结果图。

页脚「研究数据源提交」指研究数据与设计输入最近一次变化的 git commit，不是页面构建/HEAD/部署 commit；因此页面文件后续提交不会使 `--check` 失效。

## 边界声明

历史结果为历史真实 DeepSeek API 的模型输出（AI 模拟数据，非人类被试，单一模型）。mock 仅用于工程/CI 流程验证，不进入研究结论。真实模型接入方案已完成离线验证，但尚未真正运行——页面不出现任何真实 token、费用、延迟或模型表现。本页评价的是模型输出中的归因行为，不构成关于 AI 是否拥有自由意志的任何断言。

## 部署

在线地址：https://sherlock0717.github.io/llm-attribution-behavior-evaluation/ 。发布通过 GitHub Pages（`.github/workflows/pages.yml`，仅在 main push 或手动触发时部署 `site/` 目录，不运行 Jekyll、不含任何密钥或真实 Provider 运行）。
