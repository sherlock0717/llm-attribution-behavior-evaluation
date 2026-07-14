# Real Pilot Runbook (future, deferred)

> This runbook describes a FUTURE procedure. As of REAL-SETUP-001 no real run has
> happened: `live_api_status: not_run`, `real_smoke_status: not_run`,
> `real_pilot_status: not_run`. Do not claim any real run is complete.

Follow these steps only when a real run is explicitly authorized and budgeted.

1. **Read the official docs on the run day.** Model ids, base URL and pricing
   change; treat all previously recorded values as stale.
2. **Update `base_url`** in your local config to the current official API base URL.
3. **Update `model_id`** to the current official model id.
4. **Update the pricing snapshot**: fill `input_cache_hit`, `input_cache_miss`,
   `output`, `checked_at`, `source`, and set `status: verified`.
5. **Create the gitignored local config**: copy
   `configs/model.deepseek.local.yaml.example` to
   `configs/model.deepseek.local.yaml` (never commit it), then set
   `enabled: true` and `live_api_allowed: true`.
6. **Set the environment variable** (never store the key in a file):
   - PowerShell: `$env:DEEPSEEK_API_KEY = "sk-..."`
   - bash: `export DEEPSEEK_API_KEY="sk-..."`
7. **Run the dry-run** and review the plan + readiness report:
   ```
   python -m freewill_attribution.cli benchmark-run --provider deepseek \
     --dry-run --run-profile smoke \
     --model-config configs/model.deepseek.local.yaml \
     --artifact-root artifacts
   ```
8. **Manually confirm the budget** against `budgets.*` and the verified pricing.
9. **Run the 12-record smoke** (paid) only after confirming budget:
   ```
   python -m freewill_attribution.cli benchmark-run --provider deepseek \
     --real-api --confirm-paid-run --run-profile smoke \
     --model-config configs/model.deepseek.local.yaml \
     --artifact-root artifacts
   ```
10. **If smoke passes**, run the 60-record pilot with the same flags and
    `--run-profile pilot`.
11. **Generate and review a public, de-identified report** (aggregate only; no
    API key, no raw per-request credentials). Only then may the showcase move
    `real_smoke_status` / `real_pilot_status` off `not_run`.

Safety invariants that always hold:

- No `--real-api` + `--confirm-paid-run` + verified config ⇒ no key is read and
  no request is sent.
- Historical `outputs/` is never modified; new runs write under
  `artifacts/runs/<run_id>/` (gitignored).
- Mock and dry-run values are never presented as real-model results.
