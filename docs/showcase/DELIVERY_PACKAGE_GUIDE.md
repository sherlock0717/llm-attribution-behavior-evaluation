# Delivery Package Guide

> 用于把“压缩包 / 分批文件”交给网页端 GPT 检查后，安全录入本仓库的规范（SITE-005）。
> 核心纪律：**不得直接把上传的 zip 内容覆盖仓库**；一切先落临时目录、审查、再分批写入；提交授权仍归人工。

## 0. 适用场景

- 展示页文案、图片、代码、研究证据、评审材料以分批包形式在外部（网页端）产出；
- 需要把这些内容有序、可审计地并入本地仓库，且不破坏受保护资产（`outputs/**`、`src/**` 等）。

## 1. 包类型

### A. Content Package（内容包）
- 包含：页面文案、section 修改说明、方法或结果说明（Markdown / 纯文本）。
- 落库目标：`docs/showcase/*.md`、`site/index.html`（文案部分）。
- 禁止：夹带统计数字覆盖（数字只能由 `build_site_data.py` 派生）。

### B. Visual Package（视觉包）
- 包含：图片、图表、SVG、图片来源、授权说明、每个文件的 SHA-256。
- 落库目标：`site/assets/figures/`；同时回填 `PUBLIC_ASSET_INVENTORY.md`、`VISUAL_ASSET_BRIEF.md`。
- 禁止：无来源/无授权图片；含真实人脸或第三方版权素材。

### C. Site Code Package（站点代码包）
- 包含：HTML、CSS、JavaScript、JSON、测试。
- 落库目标：`site/**`、`scripts/build_site_data.py`、`tests/site/**`。
- 禁止：引入 React/Vite/npm/CDN/外部 JS；引入远程请求或第三方库。

### D. Research Evidence Package（研究证据包）
- 包含：聚合结果、报告、字段说明、证据来源。
- 落库目标：仅作为**只读引用来源**核对；**不得写入 `outputs/**`**（受保护）。
- 禁止：改动或新增研究结果数值；把 mock 当研究结果。

### E. Review Package（评审包）
- 包含：状态、diff、测试摘要、截图、待决问题。
- 落库目标：桌面审核文件夹（不入 Git），如 `SHOWCASE-REDESIGN-review-files`。
- 禁止：把本地绝对路径 / API key / 审核包路径写入公开文件。

## 2. 每个包必须附 PACKAGE_MANIFEST.md

字段：

```text
包名:
日期:
目标分支:
文件清单:            # 每个文件相对路径
预期仓库路径:        # 每个文件将落到哪
是否覆盖已有文件:    # yes/no + 覆盖项列举
内容来源:            # 谁/何工具产出
敏感性:              # 是否含路径/密钥/原始响应
是否允许公开:        # public / local_only / pending_user_approval
需人工决定的问题:    # 列表
```

## 3. 录入流程（严格按序）

```text
接收
 → 解压到临时目录（系统 temp 或 artifacts/tmp，不进 Git）
 → 路径与敏感信息检查（API key / .env / 绝对路径 / 原始响应 / node_modules）
 → 内容审查（与本仓库口径、状态系统、证据边界一致性）
 → 冲突分析（与现有文件 diff，标记覆盖项）
 → 建议落库结构（列出每个文件的目标路径与理由）
 → 人工确认
 → 分批写入仓库（一次一类，写后即验证）
 → targeted validation（build --check、tests/site、HTML/JSON/CSS/JS 检查）
 → 等待提交授权（Agent 不 commit / 不 push）
```

## 4. 硬性禁止

- 不直接覆盖仓库；不跳过临时目录与审查。
- 不写入 `outputs/**`、`src/**`、`configs/**`、`.github/**` 等受保护路径。
- 不引入外部依赖、包管理文件（`package.json` / `node_modules`）或远程脚本。
- 不把未来能力写成当前能力；不把 mock 写成研究结果。
- 不在公开文件中留下 API key、本地绝对路径或审核包路径。

## 5. 落库后验证清单（最小集）

- `python scripts/build_site_data.py --check` 通过；
- `pytest tests/site -q` 通过；
- HTML：十栏目齐全、id 唯一、无 inline onclick、无 CDN、无硬编码统计值；
- JSON：四份可解析、字段满足契约、claim 有来源、figure 有 hash；
- 敏感信息扫描通过；`git diff -- outputs` 为空。
