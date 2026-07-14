# Static Showcase (site/)

本地静态展示页（SITE-002/003/004）。原生 HTML/CSS/JavaScript + 静态 JSON，无框架、无 CDN、无外部字体、无第三方 JS、无后端、无远程 API。

## 本地预览

```bash
python -m http.server 8000 --directory site
```

然后在浏览器打开 http://localhost:8000/ 。

> 请通过本地静态服务器访问；直接以 `file://` 双击打开会因浏览器安全策略导致 `fetch` 加载 JSON 失败。

## 数据来源

页面上的所有动态数字（记录数、条件数、每格样本量、回归/对比/中介数值、版本、提交号、图表哈希、状态）都来自 `site/data/*.json`，由仓库脚本从源文件生成：

```bash
python scripts/build_site_data.py            # 生成 site/data/*.json
python scripts/build_site_data.py --check    # 校验 site/data 与源文件一致
```

生成的 JSON：
- `data/site_summary.json`
- `data/roadmap.json`
- `data/version_history.json`
- `data/historical_results.json`

静态文案（非数字）由 `docs/showcase/site_manifest.yaml` 维护并在页面中直接书写。图下"读图"说明来自 manifest 的 `read_note_zh`（经 `figures[*].read_note` 注入），不硬编码在 JS。

Research Question 栏目的研究问题概念图 `assets/figures/attribution-research-concept.png`（1586×992）为概念插图，仅解释研究结构，不承载统计结果，也不计入 Historical Results 的三张统计图。

页脚"研究数据源提交"（`source_commit`）指研究数据与设计输入（`outputs/` 分析文件、三张选定图、`configs/study.default.yaml`、provenance 声明）最近一次变化的 git commit，不是页面构建/HEAD/部署 commit；因此页面文件后续提交不会使 `--check` 失效。

跨平台现状：Windows 本地跑通 mock 流程 + Bash wrapper 的 Git Bash compatibility validation；真实 Linux 与 GitHub-hosted 双平台验证待发布阶段（Git Bash 不等于 Linux 验证）。

## 边界声明

历史结果为历史真实 DeepSeek API 的模型输出（AI 模拟数据，非人类被试，单一模型）。mock 仅用于工程/CI 流程验证，不进入研究结论。本页不构成关于 AI 是否拥有自由意志的任何断言。

## 部署

本地预览已可用；公开部署（GitHub Pages）尚未授权，统一留待 REL-001 / Phase 7，需用户 push 授权。
