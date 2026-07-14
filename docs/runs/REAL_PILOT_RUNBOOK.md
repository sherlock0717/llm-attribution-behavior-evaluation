# 真实 Pilot 运行手册（未来，暂缓）

> 本手册描述的是**未来**流程。目前尚无任何真实运行：`live_api_status: not_run`、`real_smoke_status: not_run`、`real_pilot_status: not_run`。不得声称任何真实运行已完成。

仅在真实运行被显式授权并已列入预算时，才按以下步骤执行。

1. **运行当天先读官方文档。** 模型 ID、基础地址与价格会变化；把此前记录的一切值都视为过期。
2. **更新 `base_url`**：把本地配置改为当前官方 API 基础地址。
3. **更新 `model_id`**：改为当前官方模型 ID。
4. **更新价格快照**：填写 `input_cache_hit`、`input_cache_miss`、`output`、`checked_at`、`source`，并设 `status: verified`。
5. **创建 gitignored 的本地配置**：把 `configs/model.deepseek.local.yaml.example` 复制为 `configs/model.deepseek.local.yaml`（绝不提交），然后设 `enabled: true`、`live_api_allowed: true`。
6. **设置环境变量**（绝不把密钥写入文件）：
   - PowerShell：`$env:DEEPSEEK_API_KEY = "sk-..."`
   - bash：`export DEEPSEEK_API_KEY="sk-..."`
7. **先跑 dry-run**，检查计划与准备状态报告：
   ```
   python -m freewill_attribution.cli benchmark-run --provider deepseek \
     --dry-run --run-profile smoke \
     --model-config configs/model.deepseek.local.yaml \
     --artifact-root artifacts
   ```
8. **人工核对预算**：对照 `budgets.*` 与已核验价格。
9. **仅在确认预算后，运行 12 条 smoke（付费）**：
   ```
   python -m freewill_attribution.cli benchmark-run --provider deepseek \
     --real-api --confirm-paid-run --run-profile smoke \
     --model-config configs/model.deepseek.local.yaml \
     --artifact-root artifacts
   ```
10. **若 smoke 通过**，用相同参数、`--run-profile pilot` 运行 60 条 pilot。
11. **生成并审阅脱敏公开报告**（仅聚合；不含 API Key、不含逐请求原始凭据）。只有到这一步，展示页才可以把 `real_smoke_status` / `real_pilot_status` 移出 `not_run`。

始终成立的安全不变式：

- 没有同时满足 `--real-api` + `--confirm-paid-run` + 已核验配置 ⇒ 不读取密钥、不发送任何请求。
- 历史 `outputs/` 永不修改；新运行写入 `artifacts/runs/<run_id>/`（gitignored）。
- mock 与 dry-run 的值永远不作为真实模型结果呈现。
