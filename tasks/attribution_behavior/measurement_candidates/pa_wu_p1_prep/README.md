# PA—Wu P1 前置资产包（internal provisional translation + source-audited positive-control assets）

本目录是 **P1 preparation package**，在已合并的 P0 工程契约
（`../pa_wu_p0/`）基础上，建立进入真实 P1 之前所需的两类研究资产：

1. PA13 与 Wu19 的**内部暂定中文预测试译本**（internal provisional translation）；
2. **来源支持的阳性对照材料与来源审计**（source-audited positive-control assets）。

## 本目录是什么 / 不是什么（严格用语）

本目录产物**只能**称为：

- internal provisional translation（内部暂定译本）
- source-audited positive-control assets（来源审计的阳性对照资产）
- P1 preparation package（P1 前置资产包）

本目录产物**不得**称为：

- validated Chinese scale（已验证中文量表）
- validated adaptation（已验证适配）
- expert-reviewed translation（专家审阅译本）
- human-validated measure（人工验证测量）
- 正式中文版量表

## 边界声明（不越界）

- 本轮**只建设与审查资产**：不运行真实模型、不执行 P1、不产生研究结果、不选择 M1/M2/M3。
- 翻译由 **internal_agent_two_pass_translation**（内部 Agent 两次翻译）产生：两套译文来自
  内部 Agent 两次翻译过程，**但不声称统计或程序意义上的独立翻译**（无法提供可核验的
  pass_a/pass_b 上下文隔离证据）。**不等同于**人工双译、专家委员会审查或目标群体认知访谈。
- `review_status` 一律为 `internal_agent_review_only`。
- 不修改 P0 英文原题文件（`../pa_wu_p0/items_*.yaml`）。

## 阳性对照与 D/U 的边界（明确）

- 阳性对照检验的是**评分者能否识别来源支持的高/低构念线索**；
- 它**不证明** D/U 应影响 PA 或 Wu；
- 阳性对照通过**不等于**当前 D/U 材料已适配；
- 阳性对照失败**也不能**直接证明量表无效；
- D/U、identity 与来源操纵是**不同变量**，不得混为一谈。

## 目录结构

| 文件/目录 | 内容 |
|--|--|
| `translation_protocol.yaml` | internal_agent_two_pass_translation 程序与免责声明；两层状态契约 |
| `terminology_glossary.yaml` | 统一术语表（可追踪，非机械统一） |
| `items_pa_2024.zh-CN.provisional.yaml` | PA13 暂定中文译本（分层字段） |
| `items_wu_shen_2026.zh-CN.provisional.yaml` | Wu19 暂定中文译本（分层字段；MSI 含 left/right_polarity） |
| `translation_decisions.yaml` | 逐项翻译分歧与协调决策记录（含 MS2 does think 决策） |
| `adaptation_candidates.yaml` | 面向本项目的措辞适配候选（不写回正式译本） |
| `item_review_matrix.yaml` | 全部 32 项的内部多视角风险矩阵（受控枚举） |
| `positive_controls/` | 阳性对照来源审计（verbatim vs adapted-prototype 两级） |
| `positive_controls/synthetic_construct_prototypes.yaml` | 构念派生合成原型（**非**阳性对照/原刺激） |
| `../../../../tests/unit/measurement/test_pa_wu_p1_prep.py` | 轻量结构校验（无真实模型） |

## 来源状态（补充材料与 PA 校准）

- Wu 补充材料：官方文章**提供 Supplementary Data 入口**（`public_supplementary_link_available: true`），
  但**本轮尚未提取完整 Table 9 脚本**（`supplementary_retrieved_in_this_run: false`、
  `full_script_obtained: false`、`full_script_expected_location: Supplementary Table 9`）。
- PA 校准：作者公开页已提供校准视频的标签/形态/行为描述（Service/Cheating RPS/Feeder），
  记为 `public_video_action_descriptions_available: true`、`public_full_text_stimulus_available: false`、
  `video_to_text_conversion_risk: high`。原 generic high/low agency 文本已移出，重归类为
  `construct_derived_synthetic_prototype`（见 `synthetic_construct_prototypes.yaml`），
  **不用于证明 PA 校准复现**。

## 翻译层级分离

- **原文翻译层**（`reconciled_zh_cn`）：只尽量忠实翻译英文原题，禁止为 D/U 增加信息、
  禁止把 machine 改成一般"决策者"、禁止把能力题改成单次行为题、禁止删 PA 想象题、
  禁止合并 Wu 四构念、禁止把 free will 扩展成总体 agency、禁止为 AI/human 平行擅自改主语。
- **适配候选层**（`adaptation_candidates.yaml`）：任何面向本项目的措辞变化只能放这里，
  `status` 只能是 `candidate_unvalidated`，不得写回正式暂定译本。

## 与 P0 的关系

- PA13/PA8/PA5 成员关系、Wu19 成员与构念映射**沿用 P0 已核验结果**，本目录不改变。
- 不生成 Wu19 总分、machine agency 合成总分、PA+Wu 总分（与 P0 引擎一致）。

## 引用与署名

- Trafton, J. G., McCurry, J. M., Zish, K., & Frazier, C. R. (2024). The Perception
  of Agency. *ACM Transactions on Human-Robot Interaction, 13*(1), 1–23. DOI: 10.1145/3640011.
- Wu, Y., & Shen, F. (2026). Machine agency attribution in human–AI interaction.
  *Journal of Computer-Mediated Communication, 31*(3), zmag009. DOI: 10.1093/jcmc/zmag009. License: CC BY 4.0.
