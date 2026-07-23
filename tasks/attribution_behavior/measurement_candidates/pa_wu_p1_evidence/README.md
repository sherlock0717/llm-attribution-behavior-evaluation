# PA—Wu P1 证据缺口核验与执行路线决策（research only）

本目录是**研究性证据审计与路线决策**，在已合并的 P0（`../pa_wu_p0/`）与 P1-prep
（`../pa_wu_p1_prep/`）资产基础上：核验 Wu Supplementary Table 9 获取状态、审计 PA 校准视频、
比较三条 P1 施测路线、形成 P1 路线决策与进入门槛。

**本轮只做来源检索、证据审计与路线决策。** 不运行真实模型、不执行 P1、不产生评分结果、
不把暂定中文译本称为有效中文版、不把内部风险矩阵称为内容效度证据、不在证据不足时自补原刺激。

## 文件

| 文件 | 内容 |
|--|--|
| `wu_supplementary_retrieval.yaml` | Wu Suppl. Table 9 获取日志（本轮 403 失败；公开入口存在；许可范围不明；未下载） |
| `wu_table9_stimulus_audit.yaml` | Table 9 逐条件刺激审计（未取得 → 逐条件 deferred，未伪造） |
| `pa_calibration_media_audit.yaml` | PA 校准视频审计（Service/Cheating RPS/Feeder；无直链/无许可 → 仅链接+元数据） |
| `p1_route_decision.yaml` | R1/R2/R3 三路线 + 决策矩阵（每维度带理由；R3 非默认） |
| `p1_scope_decision.md` | P1 研究问题分层（RQ1–RQ5；RQ3–5 不因 RQ1–2 自动成立） |
| `README.md`（本文件） | 进入门槛、request 重核算、最终结论 |
| `../../../../tests/unit/measurement/test_pa_wu_p1_evidence.py` | 轻量结构校验（无真实模型） |

## 证据缺口小结（本轮实测）

- **Wu Supplementary Table 9**：正式 OUP Vol.31/Issue 3 文章页**提供 Supplementary data 链接**，
  其在线补充材料目标可解析到**签名 OUP CDN 地址**，文件名 **`zmag009_supplementary_data.zip`**
  （`resolved_download_target_discovered: true`）。但本环境对 OUP 文章/期号页与 CDN 均返回 **HTTP 403**
  （bot 防护），本轮**无法捕获实时签名 URL 或下载 ZIP**，故 `retrieval_status: failed_with_resolved_signed_url`；
  补充材料**无单独许可声明**（仅整篇 CC BY 4.0，是否覆盖补充未说明）。→ 完整脚本**本轮未取得**、
  未下载任何文件。**已发现正式下载目标，但当前环境获取失败；"获取失败" ≠ "材料不存在"。**
- **PA 校准视频**：作者页仅列标签/形态/行为（Service·Cheating RPS 为 Humanoid；Feeder 为 Arm），
  **无视频直链、无时长、无媒体许可**，视频不可直接访问。→ 不下载、不重托管，仅链接+审计元数据。
  校准实体只能作为"熟悉量尺"的示例，**不能作为正式阳性对照**（无 LLM 适用性证据 + 媒介需转换）。

## request 重核算（沿用 P0 account_requests 语义；仅计划量，非运行）

以 P0 表单 F1=32 项、F2(PA13)=13 项、F3(Wu19)=19 项计。`api_requests = 唯一材料数 × repeats × orders`，
`item_ratings = api_requests × item_count`。以下为**路线级规划量**，本轮不发起任何请求。

- **R1 英文 machine-only（示例：24 材料 × 3 repeats）**
  - F1 pa_first：24×3×1 = **72** 请求 / 72×32 = **2304** item ratings
  - （如加 F2/F3 单量表：PA13 与 Wu19 另计，按需扩展）
- **R2 暂定中文 machine-only**：与 R1 同量级（单语言、machine-only），请求量 ≈ R1。
- **R3 AI/human 平行**：至少 **×2**（AI 版 + human 版），另需等价性/不变性前置检验的额外材料。

> 正式 P1 的确切数字须在选定唯一主路线、固定 Prompt/identity 策略后再冻结；上表为规划量级。

## 进入 P1 执行包的门槛（section 10）

| 门槛项 | 状态 | 说明 |
|--|--|--|
| 来源题项完整 | ✅ 满足 | PA13 + Wu19 逐字（P0 已核验） |
| 量尺与评分规则固定 | ✅ 满足 | PA 5点；Wu IN/GO/IC 7点、MSI 5点语义差异；PA13/8/5、IN4/GO4/MSI6/IC5 |
| 选定唯一主路线 | ⬜ 未满足 | 本轮仅比较，未冻结唯一主路线 |
| 阳性对照来源状态明确 | ⚠️ 部分 | 状态明确（片段级 + prototype），但**完整原刺激未取得** |
| Prompt 语言固定 | ⬜ 未满足 | 随路线（英文/中文）而定，未冻结 |
| identity 策略固定 | ⬜ 未满足 | machine-only vs AI/human 未冻结 |
| 禁止总分规则固定 | ✅ 满足 | 无 Wu19/machine-agency/PA+Wu 总分（P0 引擎强制） |
| request 数量重新核算 | ⚠️ 部分 | 已给规划量级，未按选定路线冻结 |
| 真实模型调用授权 | ⬜ 未满足 | 需单独授权 |
| API 预算与失败恢复策略 | ⬜ 未满足 | 另行审批 |

**多个关键项（唯一主路线、Prompt/identity 冻结、完整阳性对照、真实调用授权、预算/恢复策略）未满足，
故最终结论不得写为"可运行 P1"。**

## 最终结论

**C — 仍需补证。**
原因（修正）：Wu 完整 Table 9 的**正式下载目标已发现**（签名 OUP CDN，`zmag009_supplementary_data.zip`），
**但当前环境获取失败**（403 bot 防护）；叠加唯一主路线未冻结、Prompt/identity 未固定、完整阳性对照未取得、
真实调用未授权、预算/恢复策略未审批。故不得写为"可运行 P1"。
"执行包设计"仍**不等于**运行真实模型。

## 边界声明（不越界）

- 不声称中文译本有效 / PA·Wu 适配 D/U / AI·human 测量不变性成立 / 阳性对照已校准 / 可直接执行真实 P1。
- 内部风险矩阵（P1-prep）是 internal_agent_review_only，**不是内容效度证据**。
- 来源文件是否提交取决于许可范围；本轮因许可范围不明 + 获取失败，**未提交任何来源原始文件**。

## 引用

- Trafton, J. G., et al. (2024). The Perception of Agency. *ACM THRI, 13*(1). DOI: 10.1145/3640011.
- Wu, Y., & Shen, F. (2026). Machine agency attribution in human–AI interaction. *JCMC, 31*(3), zmag009.
  DOI: 10.1093/jcmc/zmag009. License: CC BY 4.0（补充材料许可范围未单独声明）.
