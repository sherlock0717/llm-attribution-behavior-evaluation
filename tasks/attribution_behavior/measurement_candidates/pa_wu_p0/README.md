# PA–Wu P0 候选测量契约（mock-only 工程资产）

本目录是 **P0 mock 工程资产**，用于验证 PA（Trafton et al. 2024）与 Wu & Shen
（2026）两套候选测量工具能否被任务契约、施测表单、评分派生与错误校验管线承载。

## 这是什么 / 不是什么

- **是**：opt-in、experimental、mock-only、非默认的候选测量契约与工程校验。
- **不是**正式量表部署；**不是**默认 benchmark 的一部分。
- 引入本目录/模块**不会**改变默认 `benchmark-run`、默认 34 项旧题项、默认场景/条件、
  默认 Prompt、默认运行 TaskSpec、legacy DeepSeek 链路或站点数据。

## 明确声明（边界）

- 没有中文验证：本轮**不生成中文题项**，题项保留作者公开的英文原文。
- 没有 LLM 评分效度：mock 输出**只用于工程验证，不能用于任何研究结论**。
- 没有 AI/human 测量不变性：未验证。
- PA 与 Wu **仍是候选方案**，未选定为最终测量。
- 真实 P1 需要**单独授权**；暂定翻译、阳性对照与真实运行**均不属于本 PR**。

## 资产

| 文件 | 内容 |
|--|--|
| `manifest.yaml` | 候选测量声明、记录字段、不变量 |
| `items_pa_2024.yaml` | PA 13 正式题项（英文逐字）+ PA13/PA8/PA5 官方成员映射 |
| `items_wu_shen_2026.yaml` | Wu Table 1 最终 19 项 + 四构念映射 |
| `forms.yaml` | F1(32)/F2(13)/F3(19) 表单与题项顺序 |
| `scoring.yaml` | PA/Wu 子分数派生规则；禁止 Wu19/合成总分 |

## 关键事实与对 step-8 模板的偏差（如实记录）

1. **PA 许可**：正式 ACM 论文（及其中发表的 PA13 题项文本）为 **CC BY 4.0**。本目录使用的
   **PA13/PA8/PA5 版本成员归属**取自作者公开页面（gregtrafton.com/agency），该网页
   **本身未单独声明网页内容许可**。三项事实分开记录（见 `items_pa_2024.yaml` 的
   `license` 字段），不把整个工具收敛为单一标签。Wu & Shen 2026 为 CC BY 4.0。
2. **PA 量尺为 5 点**（Likert 强烈不同意…强烈同意；两道情境题 terrible…great），
   而非 7 点。按作者公开信息如实记录。
3. **PA8/PA5 成员**取自作者公开页面的版本归属表（逐条 x 标记，2026-07-22 核验），
   **未自行推断或缩减**。PA8=8 项、PA5=5 项，均为 PA13 的官方子集。
4. **Wu 逐字题项**：官方 HTML Table 1 含全部最终 19 项。MSI 六项概念指标
   （consciousness/thinking/free will/desires/self-awareness/intentionality）在正文确认，
   已录入。IN/GO/IC 各项及 MSI 语义差异两端锚点的**逐字英文原文，在本工作环境无法从
   官方页面直接获取**（OUP 全文对本环境返回 403），因此这些字段暂标为
   `pending_source_verbatim`，**不臆造、不翻译、不改写**；待取得 Table 1 逐字英文原文后
   录入。工程校验（表单构建、评分派生、错误校验）不依赖题项文本内容即可运行。
   **仅初始项目池、完整实验刺激、补充分析**另属 Supplementary 待核验。
5. **三阶段是组织框架，不是三个量表总分**：无 Wu19 总分、无四构念合成总分、
   无 PA+Wu 总分；`scoring.yaml` 与引擎均拒绝这些。
6. **注意力检查不计入 PA 总分**（源中存在，但不作为 PA 评分项，故未录入）。

## 派生分数

`PA13 / PA8 / PA5`（各版本成员均值；PA8/PA5 是**综合表单上下文中的子分数**，
不等同于独立短表施测）、`IN4 / GO4 / MSI6 / IC5`（各 Wu 子量表分别取均值）。
缺失成员题项时**不静默计算完整分数**，改为记录 `scoring_warnings`。

## 引用与署名

- Trafton, J. G., McCurry, J. M., Zish, K., & Frazier, C. R. (2024). The Perception
  of Agency. *ACM Transactions on Human-Robot Interaction, 13*(1), 1–23.
  DOI: 10.1145/3640011.
- Wu, Y., & Shen, F. (2026). Machine agency attribution in human–AI interaction.
  *Journal of Computer-Mediated Communication, 31*(3), zmag009.
  DOI: 10.1093/jcmc/zmag009. License: CC BY 4.0.
