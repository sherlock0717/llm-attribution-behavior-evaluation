# 真实模型接入离线准备

> 本轮权威状态块：

```
provider_adapter_status: offline_validated
credential_status:       not_configured
live_api_status:         not_run
real_smoke_status:       not_run
real_pilot_status:       not_run
model_id_status:         requires_runtime_verification
pricing_status:          requires_runtime_verification
result_analysis_status:  not_applicable
network_calls_made:      0
actual_requests:         0
actual_token_usage:      null
actual_cost_usd:         null
```

## 已完成的部分

- 存在 DeepSeek provider **适配器**（`src/freewill_attribution/providers/deepseek.py`），采用依赖注入的客户端接口（`DeepSeekClientProtocol`）；**不会**在导入或初始化时联网。
- **预算控制器**（`src/freewill_attribution/budget.py`）使用 `Decimal`，先按最坏情况预留、再按实际用量结算、支持释放与硬上限。
- **错误分类**（401/402/429/500/503/400 → 稳定的错误类别），仅用伪造异常验证。
- **离线 dry-run 规划器**（`runner.plan_dry_run`），把 12（smoke）/ 60（pilot）条记录规划到 `artifacts/plans/<plan_id>/`，**不产生**任何响应、分数、用量、费用或延迟。
- CLI 门禁（`--real-api`、`--confirm-paid-run`、`--dry-run`、`--run-profile`、`--provider deepseek`），本轮对任何 live 运行一律硬拒绝。
- 完整离线测试覆盖：禁用套接字，且从不读取 API Key。

## 明确未完成的部分

本轮**没有**：

- 读取或检查真实的 `DEEPSEEK_API_KEY`；
- 核验真实的 DeepSeek **接口 / 基础地址**；
- 核验真实的**模型 ID**；
- 核验真实的**价格**；
- 核验真实的**响应字段**（request_id、system_fingerprint、usage）；
- 核验真实的 **token 记账 / 计费**；
- 运行任何真实 **smoke** 或 **pilot**；
- 产生或分析任何**真实模型输出**。

本仓库中任何标为 `fake` / `synthetic` / `test-only` / `null` 的值都不是真实运行的测量结果，也不会作为真实结果写入公开报告。

## 凭据隔离

- 密钥只存在于环境变量 `DEEPSEEK_API_KEY`。
- 只在 `DeepSeekProvider.load_api_key` 内读取，而该方法只在所有门禁通过后的显式 live 路径上运行。
- dry-run、单元测试与展示页构建从不调用它。
- 密钥绝不写入任何配置文件、产物、日志或错误信息。
- `configs/model.deepseek.local.yaml` 已 `.gitignore`，绝不提交。

未来的真实运行流程见 `docs/runs/REAL_PILOT_RUNBOOK.md`。
