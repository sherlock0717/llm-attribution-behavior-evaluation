# Real Provider Readiness (REAL-SETUP-001)

> Status block (authoritative for this round):

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

## What is done

- A DeepSeek provider **adapter** exists (`src/freewill_attribution/providers/deepseek.py`)
  with a dependency-injected client interface (`DeepSeekClientProtocol`). It does
  **not** connect at import or init.
- A **budget controller** (`src/freewill_attribution/budget.py`) using `Decimal`
  with worst-case reservation, actual-usage commit, release, and a hard limit.
- **Error classification** (401/402/429/500/503/400 → stable categories) validated
  with fake exceptions only.
- An **offline dry-run planner** (`runner.plan_dry_run`) that plans 12 (smoke) /
  60 (pilot) records into `artifacts/plans/<plan_id>/` and produces **no**
  responses, scores, usage, cost or latency.
- CLI gates (`--real-api`, `--confirm-paid-run`, `--dry-run`, `--run-profile`,
  `--provider deepseek`) and a hard refusal of any live run this round.
- Full offline test coverage with sockets disabled and the API key never read.

## What is explicitly NOT done

This round did **not**:

- read or check the real `DEEPSEEK_API_KEY`;
- verify the actual DeepSeek **endpoint / base URL**;
- verify the actual **model id**;
- verify the actual **pricing**;
- verify the actual **response fields** (request_id, system_fingerprint, usage);
- verify actual **token accounting / billing**;
- run any real **smoke** or **pilot**;
- produce or analyze any **real model output**.

No value labelled `fake` / `synthetic` / `test-only` / `null` in this codebase is
a real-run measurement, and none is written into the public report as one.

## Credential isolation

- The key lives ONLY in the environment variable `DEEPSEEK_API_KEY`.
- It is read ONLY inside `DeepSeekProvider.load_api_key`, which runs ONLY on the
  explicit live path after every gate passes.
- Dry-run, unit tests and showcase builds never call it.
- The key is never written into any config file, artifact, log, or error message.
- `configs/model.deepseek.local.yaml` is `.gitignore`d and never committed.

See `docs/runs/REAL_PILOT_RUNBOOK.md` for the future run procedure.
