"""Score demo responses into item-level and construct-level tables.

Item-level table: one row per material x judge model x repeat x item.
Construct-level table: one row per material x judge model x repeat x construct.

Scoring follows scoring_spec.yaml: native-scale mean; a construct is only scored
when ALL its member items are present and valid (no imputation). Raw responses
are read, never overwritten. A display-only 0-1 standardized column is added.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import yaml

PKG_DIR = Path(__file__).resolve().parent.parent
DEMO = PKG_DIR / "demo" / "demo_responses.jsonl"
SCORING_SPEC = PKG_DIR / "scoring_spec.yaml"
OUT_DIR = PKG_DIR / "outputs"
ITEM_OUT = OUT_DIR / "demo_item_scores.csv"
CONSTRUCT_OUT = OUT_DIR / "demo_construct_scores.csv"

_KEY_FIELDS = [
    "run_id", "run_version", "judge_model_id", "provider", "material_id",
    "condition_id", "d_level", "u_level", "scenario_id", "direction_version",
    "target_identity", "repeat_index",
]


def _load_spec() -> dict:
    with SCORING_SPEC.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def _load_records() -> list[dict]:
    with DEMO.open(encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def score() -> tuple[pd.DataFrame, pd.DataFrame]:
    spec = _load_spec()
    records = _load_records()

    # item metadata: item_id -> (min, max, exploratory)
    item_meta: dict[str, dict] = {}
    for c in spec["constructs"]:
        for it in c["items"]:
            item_meta.setdefault(it["item_id"], {
                "minimum": c["minimum"], "maximum": c["maximum"],
                "exploratory": bool(it.get("exploratory_item", False)),
            })

    item_rows: list[dict] = []
    construct_rows: list[dict] = []

    for rec in records:
        keys = {k: rec[k] for k in _KEY_FIELDS}
        parsed = rec.get("parsed_item_scores", {})
        # --- item-level ---
        for iid, meta in item_meta.items():
            val = parsed.get(iid)
            valid = isinstance(val, (int, float)) and meta["minimum"] <= val <= meta["maximum"]
            item_rows.append({
                **keys,
                "item_id": iid,
                "raw_score": val if valid else None,
                "valid": bool(valid),
                "exploratory_item": meta["exploratory"],
                "data_status": rec.get("data_status", "unknown"),
            })
        # --- construct-level ---
        for c in spec["constructs"]:
            member_ids = [it["item_id"] for it in c["items"]]
            vals = []
            all_valid = True
            for iid in member_ids:
                v = parsed.get(iid)
                if isinstance(v, (int, float)) and c["minimum"] <= v <= c["maximum"]:
                    vals.append(float(v))
                else:
                    all_valid = False
            if c["require_all_items"] and not all_valid:
                score_val = None
                std = None
            else:
                score_val = sum(vals) / len(vals) if vals else None
                if score_val is not None:
                    std = (score_val - c["minimum"]) / (c["maximum"] - c["minimum"])
                else:
                    std = None
            construct_rows.append({
                **keys,
                "construct": c["construct"],
                "construct_name": c["name"],
                "native_min": c["minimum"],
                "native_max": c["maximum"],
                "n_items": len(member_ids),
                "all_items_valid": all_valid,
                "construct_score": score_val,           # native scale (inference)
                "construct_score_std01": std,           # display-only 0-1
                "primary_or_secondary": c["primary_or_secondary"],
                "data_status": rec.get("data_status", "unknown"),
            })

    return pd.DataFrame(item_rows), pd.DataFrame(construct_rows)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    item_df, construct_df = score()
    item_df.to_csv(ITEM_OUT, index=False)
    construct_df.to_csv(CONSTRUCT_OUT, index=False)
    print(f"wrote {len(item_df)} item rows -> {ITEM_OUT.relative_to(PKG_DIR.parent)}")
    print(f"wrote {len(construct_df)} construct rows -> {CONSTRUCT_OUT.relative_to(PKG_DIR.parent)}")


if __name__ == "__main__":
    main()
