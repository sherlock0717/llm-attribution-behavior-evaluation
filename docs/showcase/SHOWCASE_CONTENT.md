# 展示页首版完整文案（SITE-001）

> **SITE-005 更新说明**：页面文案已在 `feat/showcase-v1` 分支按作者口吻整体重写（去模板化、去 AI 感），并把静态段落改为矩阵/流程图/证据三栏/时间线等原生可视化。本文件保留为首版基线文案与事实校对基准；**研究事实、统计结果、样本结构、状态标签、证据边界、版本事实、文件来源均未改变**。重构审查见 `SHOWCASE_REDESIGN_AUDIT.md`，最终页面以 `site/index.html` 为准。
>
> **SITE-005.1 措辞更正（以下表述取代本文件旧句，最终以 `site/index.html` 为准）**：
> 1. 页脚"数据来源提交"改为"研究数据源提交"，语义为研究数据/设计输入最近一次变化的 commit（非 HEAD、非构建/部署 commit）。
> 2. 操纵检验（§5）：由"随结构递增/模型能区分 6 类"改为"高结构条件的 factual manipulation check 整体高于低结构条件；两个低结构诊断条件不构成严格单调序列"，不声称严格单调或六类两两显著。
> 3. 中介（§5）：由"间接路径稳定"改为"在该探索性分析中 agency 间接效应区间未跨 0；perceived_intelligence 间接效应区间跨 0"，不写稳定机制/机制已确认/因果中介已证明。
> 4. Pipeline（§4）：分为 Historical research path / Current engineering layer / Planned 三层；`configs/`、`src/freewill_attribution/` 属当前工程组件，不再标为历史步骤；`prompt.v1.yaml` 为当前配置组件，不替代缺失的历史 prompt snapshot/hash。
> 5. 跨平台（§7）：改为"在 Windows 本地使用锁定依赖跑通 mock 流程；Bash wrapper 完成 Git Bash compatibility validation；真实 Linux 与 GitHub-hosted Windows/Linux 验证仍待发布阶段完成"，不把 Git Bash 称为 Linux 验证。
> 6. 仓库文件链接（§10）：不再用 `../` 本地相对链接；页面内部用锚点，外部仅保留 GitHub repo 根链接，具体文件以 `<code>` 路径 + "位于 GitHub 仓库中" 展示，永久链接待 REL-001。
>
> **SITE-005.2 追加**：Research Question 栏目接入用户提供的研究问题概念图（`site/assets/figures/attribution-research-concept.png`，1586×992，仅解释研究结构、不承载统计结果、不计入三张历史结果图）；修复 Historical Results 缺失 `data-slot="figures"` 导致的运行中断（三张图/路径图/版本/路线图现完整渲染）；修复 390px 页面级横向溢出；`figures`/`results`/`meta-cards` 改 `minmax(0,1fr)` 并对卡片加 `min-width:0` 与断词。

> 本文件为静态展示页首版**可直接使用**的中文文案。栏目顺序与 `SHOWCASE_PLAN.md` §4 一致。
> 页面可显示版本与阶段状态；内部任务编号仅在 Roadmap 技术详情中简述。
> 所有数字来源见 `SITE_DATA_CONTRACT.md`；能力状态词遵循状态系统（Completed / Current / Planned / Historical / Pending verification）。

---

## 1. Hero

> 注：本文件为早期内容设计记录，已被重构后的展示页取代；公开页面与 README 为权威来源。

**项目名称**：LLM 归因行为评测（A Reproducible Study and Evaluation Prototype）

**定位**：围绕模型如何对行动者的能动性、自由意志与责任作出归因，构建从历史研究、任务契约到可复现运行与证据审计的测试型评测基准。

**状态标签**：
- 研究原型
- 版本 v0.2（开发中）
- 历史真实 API 基线（DeepSeek）
- Phase 1 本地工程基础完成
- 发布验证待完成

**副标题**：通过系统改变"决策过程"的呈现方式，观察大语言模型在扮演观察者时，如何对 AI 与人类决策者做出行动者感、自由意志与责任归因。

---

## 2. Research Question

**什么是自由意志归因？**
当我们看到某个对象做出选择时，会不自觉地判断它"是不是在自己做主"——它是否有能力权衡、是否可以做出别的选择、是否要为结果负责。这种判断就是自由意志归因。它是一种观察者的主观归因，而不是关于对象内部是否"真的自由"的事实结论。

**为什么比较 AI 决策者与人类决策者？**
同样一段决策过程，如果贴上"AI 决策者"或"人类决策者"的身份标签，观察者的归因可能不同。比较两者，可以观察身份标签是否以及如何改变归因。

**为什么改变过程描述？**
一个决策者可以只给出结论，也可以展示候选方案、理由权衡、反思与修正。本项目系统改变这种"决策过程"的呈现结构，观察它是否比单纯的文本长度更能影响归因。

**重要说明**：本项目测量的是**模型输出的归因行为**，即模型在扮演观察者时给出的评分，而**不是**在证明模型本身拥有自由意志或测量真实人类的心理规律。

---

## 3. Experimental Design

**6 × 2 设计，每格 30，合计 360 条历史记录。**

**6 个决策过程条件**：
| 条件 | 含义 |
|---|---|
| direct_choice（直接选择） | 只给出最终选择，最低结构，作为基线 |
| direct_choice_long（长文本直接选择） | 拉长文本但不加入真正的理由结构，用于分离"文本长度"效应 |
| alternatives（列出可选方案） | 呈现多个候选行动 |
| reasons_concise（简洁理由权衡） | 较短文本中的理由权衡，用于检验理由结构是否在短文本中仍有效 |
| reasons（完整理由权衡） | 较完整的理由比较 |
| reflection_feedback（反思与反馈修正） | 理由 + 反思 + 反馈修正，最高结构 |

**2 个身份标签**：AI 决策者、人类决策者。

**样本结构**：每个条件格 30 条记录 → 6 × 2 × 30 = 360。

**数据来源**：历史 DeepSeek API 基线（真实 API 调用生成的模型响应）。**mock（规则生成）仅用于工程与持续集成流程测试，不进入研究结果。**

> 说明：`direct_choice_long` 与 `reasons_concise` 是诊断条件，用于区分"文本长度效应"与"决策结构效应"。

---

## 4. Pipeline

首版流程（标注每步状态）：

```text
配置与基础组件（Historical / Partial）
  → 条件与刺激（Historical）
  → Prompt（Historical）
  → 模型响应（Historical · 真实 DeepSeek API）
  → 解析与校验（Historical）
  → 标准化记录（Historical）
  → 分析与报告（Historical）
  → 静态展示页（Current）
```

工程侧现状（与研究流程并行的可复现底座）：

**Completed（本地）**：
- 依赖锁定；
- mock-only CLI；
- 安全输出；
- 跨平台 wrapper；
- 测试基础；
- CI 配置。

**Partial**：
- schema；
- config；
- 两者已实现基础组件，但尚未接入正式 runner。

**Planned**：
- 正式 runner；
- RunManifest 实际产出；
- provider abstraction。

> 说明：正式运行清单（manifest）与 provider 抽象**尚未完成**，页面不得标为已完成。

---

## 5. Historical Results

> 以下结论仅来自现有分析文件，未重新分析、未改变原结论。均限于当前实验条件与历史模型输出。

**操纵检验（模型能区分 6 类决策过程）**
factual manipulation check 随结构递增：direct_choice=0.09、direct_choice_long=0.01、alternatives=1.01、reasons_concise=1.62、reasons=1.94、reflection_feedback=2.00。
- 来源：`outputs/n30_stability_replication_report.md`、`outputs/final_simulated_pilot_report.md`。证据范围：当前条件下的均值，描述性。

**行动者感（agency）是最稳定的主结果**
条件均值从 direct_choice=4.31 上升到 reflection_feedback=5.20；同时控制感知智能与文本长度后，决策过程对 agency 仍显著（F=12.19，p<.001）。
- 来源：`outputs/n30_stability_replication_report.md`、`outputs/controlled_regression_summary.csv`、`outputs/plots/mean_agency.png`。证据范围：描述性 + 控制回归。

**理由结构不是单纯的文本长度效应（以下数值均对应 agency 结果）**
针对 **agency** 的计划对比显示：reasons_concise 显著高于 direct_choice_long（差值 0.49，t=3.34，p=.001）；reflection_feedback 显著高于 direct_choice_long（差值 1.26，t=9.40，p<.001）。仅"列出候选方案"不足以提高 agency（alternatives 与 direct_choice 差异接近 0）。
- 来源：`outputs/planned_contrasts.csv`（dv=agency 行）。证据范围：预设计划对比。
- 注意：以上为 **agency** 的计划对比，**不是** free_will_attribution 的计划对比；free_will_attribution 的效应见下一条。

**自由意志归因：直接效应不稳定，间接路径稳定**
控制感知智能与文本长度后，决策过程对 free_will_attribution 的直接效应不稳定（F=0.71，p=.62）；但"决策过程 → 行动者感 → 自由意志归因"的间接路径稳定：agency 间接效应=0.27，95% CI [0.20, 0.35]；感知智能间接效应=0.02，95% CI [-0.01, 0.04]。
- 来源：`outputs/parallel_mediation_summary.json`、`outputs/final_simulated_pilot_report.md`。证据范围：**探索性路径诊断，非机制证明**。

**责任归因仅作探索性结果**
责任相关维度方向不如 agency 稳定，仅作为探索性结果呈现。
- 来源：`outputs/n30_stability_replication_report.md`。证据范围：探索性。

> 禁止：新造统计结论；重新分析后改变原结论；将单一模型结果推广为所有 LLM；将模型模拟结果推广为真实人类心理规律。

---

## 6. Evidence And Limitations

- 360 条记录是**历史真实 DeepSeek API 输出**（模型生成的观察者评分），**不是 mock**。
- mock（规则生成数据）**只用于验证工程流程与持续集成**，不进入研究结论。
- 历史运行的 **provenance（溯源元数据）不完整**：缺少完整运行清单、服务端精确模型版本快照、调用时间戳、token 用量、费用、prompt 哈希、依赖锁定哈希、完整环境快照与调用日志；原始逐条响应文件不在公开仓库。
- **数据真实性 ≠ 完全可复现**：数据来源真实已确认，但由于历史运行级元数据缺失，无法逐字节重放当时的模型响应。
- 当前**不是多模型 benchmark**：结果来自单一模型（DeepSeek）与单一 prompt 模板。
- 当前**不包含人类被试验证**：无内容效度、EFA/CFA、区分效度或测量等价性检验。
- 提示暴露限制：历史 prompt 同时暴露构念名、题项与判断规则，模型可能迎合提示。
- 页面所有结论仅限**当前实验条件与历史模型输出**，不外推为人类心理规律或所有模型的普遍规律；不构成关于 AI 是否拥有自由意志的任何断言。

---

## 7. Reproducibility

**已完成（本地）**：
- 基线内容哈希（SHA-256 清单，基于指定提交的原始 blob 计算）；
- 依赖锁定（`uv.lock`）；
- Python package 与命令行入口（mock-only）；
- 安全输出隔离（显式输出目录，永不写入历史 `outputs/`）；
- 数据模型（schema）与配置加载；
- 单元 / 集成 / 特征化（characterization）测试；
- 跨平台运行脚本（PowerShell 与 Bash）；
- 持续集成配置（Windows 与 Linux 矩阵）。

**准确表述**：持续集成为 **CI configured, remote verification pending**（已配置，远程验证待完成）。

> 不得写 "CI passing" / "CI 已通过" / "GitHub-hosted 双平台已验证"。当前无 push 授权，尚未触发远程 CI。

---

## 8. Version History

- **v0.1**：历史研究原型与 DeepSeek API 数据（360 条真实 API 记录、6×2×30 设计、分析产物与图表）。
- **v0.2**：工程专业化，建立本地可复现基础——mock-only 命令行入口、安全输出隔离、schema/config、持续集成配置、跨平台运行脚本；历史基线保持不变。
- **未来版本**：正式可追溯 runner、v2 研究协议、多模型执行与 benchmark 方向（均为规划中）。

---

## 9. Roadmap

按状态展示（详见 Roadmap 技术详情，内部阶段/任务编号仅在此简述）：

| 阶段 | 名称 | 状态 |
|---|---|---|
| Phase 1 | Engineering Foundation And Historical Baseline | Completed（本地） / Pending verification（远程 CI） |
| Phase 2 | Research Protocol Definition | Planned |
| Phase 3A | Reproducible V1 Run | Planned |
| Phase 3B | Improved V2 Protocol And Run | Planned |
| Phase 4 | Providers And Multi-Model Execution | Planned |
| Phase 5 | Analysis And Reporting | Planned |
| Phase 6 | Benchmark Track | Planned（长期方向，非当前能力） |
| Phase 7 | Release And Audit | Planned |
| Track S | Public Showcase（并行） | Current（内容与数据契约进行中） |

---

## 10. Repository Links

（规划锚点，本轮不写死尚未确认的 Pages URL）

- GitHub 仓库
- 可复现性说明（Reproducibility）
- 研究方法（Method）
- 结果（Results）
- 路线图（Roadmap）
- 局限（Limitations）
