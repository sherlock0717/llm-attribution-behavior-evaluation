# 静态展示页

`site/` 展示决策过程表述和行动者身份如何影响模型的归因评分。页面使用原生 HTML、CSS、JavaScript 和静态 JSON，不依赖外部字体、CDN、第三方脚本或后端服务。

页面以研究问题和当前结果为主，详细的运行状态、来源记录和复现说明通过仓库文档提供。

## 本地预览

```bash
python -m http.server 8000 --directory site
```

然后打开 http://localhost:8000/ 。

页面通过 `fetch` 读取本地 JSON，因此需要使用静态服务器访问。附加 `?diagnostics=1` 后，页面会把渲染完成状态和文档宽度等诊断信息写入 HTML 属性，供自动测试读取。

## 生成页面数据

页面中的设计规模、构念信息、统计结果、运行状态和文档入口由脚本从仓库源文件生成：

```bash
uv run python scripts/build_site_data.py
uv run python scripts/build_public_report.py
uv run python scripts/build_showcase_data.py
```

生成结果写入 `site/data/`。三个脚本均支持 `--check`，用于确认静态 JSON 与源文件一致。可计算的统计数字不直接维护在 HTML 中。

## 图表与材料

结果图来自仓库分析产物，页面构建过程会检查对应文件和哈希。研究结构示意图只解释输入、模型判断和归因输出之间的关系。

题项与文献来源见：

- [`../docs/research_and_measurement_sources.md`](../docs/research_and_measurement_sources.md)
- [`../docs/scale_source_mapping.md`](../docs/scale_source_mapping.md)
- [`../docs/STUDY_CARD.md`](../docs/STUDY_CARD.md)

## 解释范围

页面展示的是模型在当前材料和评分任务下的输出变化。现有数据来自单一模型，部分材料和题项仍有待进一步解耦，结果以描述性比较和关联性诊断为主。

确定性 `mock` 运行只检查配置、解析、计分和产物生成，不进入结果解释。

## 部署

在线地址：https://sherlock0717.github.io/llm-attribution-behavior-evaluation/

`.github/workflows/pages.yml` 在主分支更新或手动触发时发布 `site/` 目录。部署过程不调用模型接口，也不读取 API 密钥。
