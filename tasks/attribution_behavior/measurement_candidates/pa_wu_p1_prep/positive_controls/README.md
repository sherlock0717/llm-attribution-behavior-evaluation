# 阳性对照来源审计（source-audited positive-control assets）

阳性对照**只用于**检查评分者能否识别**来源支持的高/低构念线索**。

## 两级严格分离

### 10.1 `source_verbatim_positive_control`
只有取得原研究**逐字**刺激文本时才可进入此级。记录 `source / study / construct /
condition / verbatim_text / license / retrieval_location / verified_on /
modifications: none`。

**本轮实际状态**：Wu & Shen 2026 正文（OUP minimal HTML, article-minimal/8692819）
在 "EXPERIMENTAL MANIPULATIONS" 一节给出了**举例性质的逐字片段**（例如低独立性
"I instruct you to generate the message now"；高目标导向 "I will write a message to
acknowledge his feelings" 及三点行动计划）。这些**片段本身是正文逐字引用**，因此以
**fragment 级**记入 verbatim（`is_full_script: false`，明确标注为正文示例片段，
不是完整脚本）。**完整逐字对话脚本位于 Supplementary Table 9，本环境未取得**。

### 10.2 `source_adapted_positive_control_prototype`
根据正文**明确描述的操纵逻辑**构造的适配原型。记录 `source_description /
adapted_text / all_added_text / all_removed_text / all_changed_text /
adaptation_reason / construct_preservation_risk / status: prototype_unvalidated`。
**不得称为原研究刺激。**

## 阳性对照与 D/U 的边界（明确）

- 阳性对照检验的是**评分者能否识别来源构念线索**；
- 它**不证明** D/U 应影响 PA 或 Wu；
- 阳性对照通过**不等于**当前 D/U 材料已适配；
- 阳性对照失败**也不能**直接证明量表无效；
- D/U、identity 与来源操纵是**不同变量**。

## 本轮取得情况一览

| 构念 | verbatim 完整脚本 | verbatim 片段 | adapted prototype |
|--|--|--|--|
| Wu independence (Study 3) | 未取得（Suppl. Table 9） | 已取得（正文片段） | 已建立 |
| Wu goal-orientation (Study 3) | 未取得（Suppl. Table 9） | 已取得（正文片段） | 已建立 |
| PA calibration (video/entity) | 未取得（无公开文本刺激） | 未取得 | 已建立（媒介转换风险） |

## Wu goal-orientation 效应强度提示

原研究中 goal-orientation 操纵效应**相对较弱**，**不得**将其当作绝对金标准
（见 `source_inventory.yaml` 与 `wu_goal_orientation_controls.yaml`）。

## 文件

| 文件 | 内容 |
|--|--|
| `source_inventory.yaml` | 来源审计总表（取得/未取得、许可、检索位置） |
| `wu_independence_controls.yaml` | Wu 独立性高/低对照（verbatim 片段 + adapted prototype） |
| `wu_goal_orientation_controls.yaml` | Wu 目标导向高/低对照（同上，含弱效应提示） |
| `pa_calibration_inventory.yaml` | PA 校准刺激清单与媒介转换风险（仅 prototype） |
