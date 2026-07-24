"""Generate deterministic SYNTHETIC demo responses.

For every material (192) and every judge model (2) this writes one demo response
record (>= 384 records total). Records are marked data_status = synthetic_demo
and use a fixed seed. A few small, recognizable condition differences are baked
in so that the scoring / analysis / figures can be validated end-to-end.

This does NOT imitate or claim any real DeepSeek or GPT behavior and must never
be used to say which model is "better".
"""

from __future__ import annotations

import hashlib
import json
import random
from pathlib import Path

import yaml

PKG_DIR = Path(__file__).resolve().parent.parent
STIMULI = PKG_DIR / "stimuli.jsonl"
SCORING_SPEC = PKG_DIR / "scoring_spec.yaml"
DEMO_OUT = PKG_DIR / "demo" / "demo_responses.jsonl"

SEED = 20260724
JUDGE_MODELS = (("deepseek-v4-pro", "deepseek"), ("gpt-5.6-terra", "openai"))
RUN_ID = "pilot_demo_run_001"
RUN_VERSION = "demo.v1"
REPEAT_INDEX = 0

# baked-in condition offsets (synthetic, illustrative only). native scales differ.
_COND_OFFSET = {"C0": 0.0, "C1": 0.2, "C2": 0.5, "C3": 0.6, "C4": 0.7, "C5": 0.9}
# per-construct baseline midpoints on native scales.
_BASE = {"IN": 4.0, "GO": 4.0, "MSI": 3.0, "IC": 4.0, "PA5": 3.0, "PA8": 3.0}
_SCALE_MAX = {"IN": 7, "GO": 7, "MSI": 5, "IC": 7, "PA5": 5, "PA8": 5}
_SCALE_MIN = 1


def _load_scoring() -> dict:
    with SCORING_SPEC.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def _item_construct_map(spec: dict) -> dict[str, str]:
    out: dict[str, str] = {}
    for c in spec["constructs"]:
        for it in c["items"]:
            # an item can belong to more than one PA version; last wins for the
            # synthetic latent, both PA5/PA8 share pa_* items so this is fine.
            out.setdefault(it["item_id"], c["construct"])
    return out


def _all_items(spec: dict) -> list[tuple[str, str, int]]:
    """(item_id, construct, scale_max) for every scored item, dedup by item_id
    keeping its first construct (PA items appear in PA5 and PA8)."""
    seen: dict[str, tuple[str, str, int]] = {}
    for c in spec["constructs"]:
        for it in c["items"]:
            iid = it["item_id"]
            if iid not in seen:
                seen[iid] = (iid, c["construct"], c["maximum"])
    return list(seen.values())


def _scenario_effect(construct: str, scenario_id: str) -> float:
    """A small deterministic per-scenario shift so scenario random-intercept
    variance is estimable (kept small; synthetic and illustrative only)."""
    key = f"scen:{construct}:{scenario_id}"
    h = int(hashlib.sha256(key.encode()).hexdigest(), 16)
    # spread roughly in [-0.4, +0.4]
    return ((h % 1000) / 1000.0 - 0.5) * 0.8


def _latent(construct: str, cond: str, identity: str, model: str, scenario_id: str,
            rng: random.Random) -> float:
    base = _BASE[construct]
    offset = _COND_OFFSET[cond]
    # small identity effect: ai judged slightly lower on MSI-type attribution.
    identity_eff = -0.3 if (identity == "ai" and construct in ("MSI",)) else 0.0
    # small model effect (illustrative only, NOT a capability claim).
    model_eff = 0.15 if model == "gpt-5.6-terra" else -0.15
    scenario_eff = _scenario_effect(construct, scenario_id)
    # larger continuous noise so the design is full-rank and models can converge.
    noise = rng.gauss(0.0, 0.6)
    return base + offset + identity_eff + model_eff + scenario_eff + noise


def _clip_round(value: float, hi: int) -> int:
    return int(max(_SCALE_MIN, min(hi, round(value))))


def generate() -> list[dict]:
    with STIMULI.open(encoding="utf-8") as fh:
        materials = [json.loads(line) for line in fh if line.strip()]
    spec = _load_scoring()
    items = _all_items(spec)

    records: list[dict] = []
    for model_id, provider in JUDGE_MODELS:
        for mat in materials:
            # deterministic per (model, material) rng.
            seed_key = f"{SEED}:{model_id}:{mat['material_id']}"
            rng = random.Random(int(hashlib.sha256(seed_key.encode()).hexdigest(), 16) % (2**32))
            parsed: dict[str, int] = {}
            construct_latent: dict[str, float] = {}
            for iid, construct, hi in items:
                if construct not in construct_latent:
                    construct_latent[construct] = _latent(
                        construct, mat["condition_id"], mat["target_identity"],
                        model_id, mat["scenario_id"], rng,
                    )
                # per-item jitter around the shared construct latent.
                lat = construct_latent[construct] + rng.gauss(0.0, 0.4)
                parsed[iid] = _clip_round(lat, hi)
            prompt_hash = hashlib.sha256(
                (mat["complete_stimulus_text"] + model_id).encode("utf-8")
            ).hexdigest()
            rec = {
                "run_id": RUN_ID,
                "run_version": RUN_VERSION,
                "judge_model_id": model_id,
                "provider": provider,
                "material_id": mat["material_id"],
                "condition_id": mat["condition_id"],
                "d_level": mat["d_level"],
                "u_level": mat["u_level"],
                "scenario_id": mat["scenario_id"],
                "direction_version": mat["direction_version"],
                "target_identity": mat["target_identity"],
                "repeat_index": REPEAT_INDEX,
                "raw_response": json.dumps(parsed, sort_keys=True),
                "parsed_item_scores": parsed,
                "parse_status": "parsed",
                "validation_status": "valid",
                "failure_code": None,
                "prompt_hash": prompt_hash,
                "response_id": f"demo-{model_id}-{mat['material_id']}",
                "input_tokens": 512,
                "output_tokens": 128,
                "estimated_cost": 0.0,
                "timestamp": "2026-07-24T00:00:00+00:00",
                "data_status": "synthetic_demo",
                "seed": SEED,
            }
            records.append(rec)
    return records


def main() -> None:
    records = generate()
    DEMO_OUT.parent.mkdir(parents=True, exist_ok=True)
    with DEMO_OUT.open("w", encoding="utf-8") as fh:
        for rec in records:
            fh.write(json.dumps(rec, ensure_ascii=False, sort_keys=True) + "\n")
    print(f"wrote {len(records)} synthetic_demo responses -> {DEMO_OUT.relative_to(PKG_DIR.parent)}")


if __name__ == "__main__":
    main()
