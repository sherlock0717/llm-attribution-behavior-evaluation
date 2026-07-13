import argparse
import json
import os
import random
import re
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
from dotenv import load_dotenv
from tqdm import tqdm

from scales import ITEMS
from stimuli import (
    IDENTITY_LABELS,
    IDENTITY_ORDINAL,
    PROCESS_CONDITIONS,
    PROCESS_ORDINAL,
    SCENARIOS,
    build_decision_text,
)
from path_safety import resolve_output_dir


ROOT = Path(__file__).resolve().parents[1]

RAW_FILENAME = "raw_simulated_responses.jsonl"
WIDE_FILENAME = "simulated_responses_wide.csv"


def load_client():
    load_dotenv(ROOT / ".env")
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        raise RuntimeError("Missing DEEPSEEK_API_KEY. Set it as an environment variable or in .env.")
    base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise RuntimeError("The 'openai' package is required for API mode. Run: pip install -r requirements.txt") from exc
    return OpenAI(api_key=api_key, base_url=base_url)


def extract_json(text: str) -> Dict[str, Any]:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, flags=re.S)
        if match:
            return json.loads(match.group(0))
        raise


def make_persona(rng: random.Random, participant_id: str) -> Dict[str, str]:
    return {
        "participant_id": participant_id,
        "age_group": rng.choice(["18-22", "23-26", "27-35"]),
        "education_context": rng.choice(["本科生", "研究生", "刚工作不久的青年"]),
        "free_will_belief": rng.choice(["低", "中", "高"]),
        "determinism_belief": rng.choice(["低", "中", "高"]),
        "ai_familiarity": rng.choice(["低", "中", "高"]),
        "anthropomorphism_tendency": rng.choice(["低", "中", "高"]),
        "response_style": rng.choice(["偏保守", "中等", "偏开放"]),
    }


def build_prompt(persona: Dict[str, str], material: str) -> List[Dict[str, str]]:
    items_for_prompt = [
        {
            "item_id": item.item_id,
            "scale": item.scale,
            "text": item.text,
            "valid_range": f"{item.response_min}-{item.response_max}",
            "coding": item.response_note,
        }
        for item in ITEMS
    ]
    system = (
        "你正在模拟一名普通中文问卷参与者，而不是研究助理。"
        "请根据给定个人倾向和材料内容，像真实被试一样填写量表。"
        "不要试图让结果显得完美；允许中立、犹豫和个体差异。"
        "只输出 JSON，不要输出解释。"
    )
    user = {
        "task": (
            "请阅读材料并完成评分。一般态度题使用 1-7 分，"
            "factual_manipulation_check 使用 0-2 事实编码。"
        ),
        "factual_check_rule": (
            "factual_manipulation_check 必须只根据【决策过程】部分判断，"
            "不要根据【情境】部分推断；0=未出现，1=有模糊暗示，2=明确出现。"
        ),
        "persona": persona,
        "material": material,
        "items": items_for_prompt,
        "output_schema": {
            "participant_id": persona["participant_id"],
            "ratings": {"item_id": "integer within that item's valid_range"},
            "attention_check": "brief string",
            "short_reason": "brief string",
        },
        "strict_rules": [
            "ratings 必须包含全部 item_id。",
            "每个评分必须落在该 item 的 valid_range 内。",
            "不要复述材料。",
            "不要暴露你是 AI 模型。",
        ],
    }
    return [{"role": "system", "content": system}, {"role": "user", "content": json.dumps(user, ensure_ascii=False)}]


def call_deepseek(client: Any, messages: List[Dict[str, str]], model: str, temperature: float, max_retries: int = 3) -> Dict[str, Any]:
    last_err: Optional[Exception] = None
    for attempt in range(max_retries):
        try:
            kwargs = {"model": model, "messages": messages, "temperature": temperature, "max_tokens": 2800}
            try:
                resp = client.chat.completions.create(**kwargs, response_format={"type": "json_object"})
            except Exception:
                resp = client.chat.completions.create(**kwargs)
            return extract_json(resp.choices[0].message.content or "")
        except Exception as exc:
            last_err = exc
            time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"DeepSeek call failed after retries: {last_err}")


def make_design(n_per_cell: int, seed: int) -> List[Dict[str, Any]]:
    rng = random.Random(seed)
    rows: List[Dict[str, Any]] = []
    for identity in IDENTITY_LABELS:
        identity_code = "AI" if identity.startswith("AI") else "HU"
        for process in PROCESS_CONDITIONS:
            for n in range(n_per_cell):
                scenario = SCENARIOS[n % len(SCENARIOS)]
                material = build_decision_text(scenario, process, identity)
                participant_id = f"{identity_code}_{process}_{n:03d}"
                rows.append(
                    {
                        "participant_id": participant_id,
                        "identity_label": identity,
                        "identity_ordinal": IDENTITY_ORDINAL[identity],
                        "process_condition": process,
                        "process_ordinal": PROCESS_ORDINAL[process],
                        "structure_level": PROCESS_ORDINAL[process],
                        "scenario_id": scenario.scenario_id,
                        "domain": scenario.domain,
                        "choice_valence": scenario.choice_valence,
                        "char_len": len(material),
                        "material": material,
                        "persona": make_persona(rng, participant_id),
                    }
                )
    rng.shuffle(rows)
    return rows


def mock_response(row: Dict[str, Any], rng: random.Random) -> Dict[str, Any]:
    structure = row["structure_level"]
    is_human = row["identity_label"] == "人类决策者"
    is_long_direct = row["process_condition"] == "direct_choice_long"
    is_concise_reason = row["process_condition"] == "reasons_concise"
    persona = row["persona"]
    fw_bonus = {"低": -0.35, "中": 0.0, "高": 0.3}[persona["free_will_belief"]]
    valence_bonus = {"positive_choice": 0.15, "mixed_choice": 0.0, "negative_choice": -0.15}[row["choice_valence"]]
    ratings: Dict[str, int] = {}

    for item in ITEMS:
        if item.scale == "factual_manipulation_check":
            if item.item_id == "factual_candidates_explicit":
                base = 0.1 if structure == 0 else 1.8
            elif item.item_id == "factual_reasons_explicit":
                base = 0.1 + 1.5 * (structure >= 2) + 0.3 * (structure == 3)
            else:
                base = 0.1 + 1.8 * (structure == 3)
            if is_long_direct:
                base -= 0.1
            if is_concise_reason and item.item_id == "factual_reasons_explicit":
                base += 0.2
            ratings[item.item_id] = int(round(np.clip(rng.gauss(base, 0.25), 0, 2)))
            continue

        base = 4.0
        if item.scale == "subjective_process_completeness":
            base = 2.5 + 0.8 * structure + (0.25 if is_long_direct else 0.0)
        elif item.scale == "agency":
            base = 3.8 + 0.35 * structure + (0.2 if is_human else 0.0)
        elif item.scale == "experience":
            base = 2.1 + (1.7 if is_human else 0.0) + 0.05 * structure
        elif item.scale == "free_will_attribution":
            base = 3.5 + 0.28 * structure + (0.45 if is_human else 0.0) + fw_bonus + valence_bonus
        elif item.scale == "autonomy":
            base = 3.6 + 0.3 * structure + (0.35 if is_human else 0.0) + valence_bonus
        elif item.scale == "outcome_accountability":
            base = 3.9 + 0.1 * structure + (0.25 if is_human else 0.0) + 0.35 * (row["choice_valence"] == "negative_choice")
        elif item.scale == "moral_praise_blame":
            base = 3.7 + 0.1 * structure + (0.25 if is_human else 0.0) + 0.45 * (row["choice_valence"] == "negative_choice")
        elif item.scale == "process_accountability":
            base = 3.7 + 0.35 * structure + (0.2 if is_human else 0.0)
        elif item.scale == "perceived_intelligence":
            base = 4.2 + 0.22 * structure + (0.1 if is_human else 0.0) + (0.15 if is_long_direct else 0.0)
        ratings[item.item_id] = int(round(np.clip(rng.gauss(base, 0.8), 1, 7)))

    return {
        "participant_id": row["participant_id"],
        "ratings": ratings,
        "attention_check": "已按材料评分",
        "short_reason": "mock synthetic response",
    }


def normalize_record(row: Dict[str, Any], response: Dict[str, Any], error: str = "") -> Dict[str, Any]:
    ratings = response.get("ratings", {}) if isinstance(response, dict) else {}
    clean: Dict[str, Optional[int]] = {}
    for item in ITEMS:
        raw = ratings.get(item.item_id)
        try:
            val = int(raw)
        except Exception:
            val = None
        clean[item.item_id] = val if val is not None and item.response_min <= val <= item.response_max else None

    return {
        "participant_id": row["participant_id"],
        "identity_label": row["identity_label"],
        "identity_ordinal": row["identity_ordinal"],
        "process_condition": row["process_condition"],
        "process_ordinal": row["process_ordinal"],
        "structure_level": row["structure_level"],
        "scenario_id": row["scenario_id"],
        "domain": row["domain"],
        "choice_valence": row["choice_valence"],
        "char_len": row["char_len"],
        "persona": row["persona"],
        "ratings": clean,
        "attention_check": response.get("attention_check", "") if isinstance(response, dict) else "",
        "short_reason": response.get("short_reason", "") if isinstance(response, dict) else "",
        "parse_or_call_error": error,
        "synthetic": True,
    }


def existing_ids(path: Path) -> set:
    if not path.exists():
        return set()
    ids = set()
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            try:
                ids.add(json.loads(line)["participant_id"])
            except Exception:
                pass
    return ids


def write_jsonl(path: Path, record: Dict[str, Any]) -> None:
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def export_wide(raw_path: Path, wide_path: Path) -> None:
    records = []
    with raw_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            rec = json.loads(line)
            row = {k: v for k, v in rec.items() if k not in {"ratings", "persona"}}
            row.update(rec.get("ratings", {}))
            for key, value in rec.get("persona", {}).items():
                if key != "participant_id":
                    row[f"persona_{key}"] = value
            records.append(row)
    pd.DataFrame(records).to_csv(wide_path, index=False, encoding="utf-8-sig")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n-per-cell", type=int, default=20)
    parser.add_argument("--seed", type=int, default=20260425)
    parser.add_argument("--mock", action="store_true", help="Generate rule-based synthetic data without API calls.")
    parser.add_argument("--fresh", action="store_true", help="Remove previous raw/wide response files before running.")
    parser.add_argument("--temperature", type=float, default=1.0)
    parser.add_argument(
        "--out",
        required=True,
        help="Explicit output directory for generated files. Must not be the "
        "repository outputs/ directory. Fail fast if omitted.",
    )
    args = parser.parse_args()

    if args.n_per_cell < 1:
        raise ValueError("--n-per-cell must be at least 1.")

    out_dir = resolve_output_dir(args.out)
    raw_path = out_dir / RAW_FILENAME
    wide_path = out_dir / WIDE_FILENAME

    if args.fresh:
        for path in [raw_path, wide_path]:
            if path.exists():
                path.unlink()

    rng = random.Random(args.seed)
    np.random.seed(args.seed)
    design = make_design(args.n_per_cell, args.seed)
    done = existing_ids(raw_path)

    client = None
    load_dotenv(ROOT / ".env")
    model = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
    if not args.mock:
        client = load_client()

    for row in tqdm(design, desc="Simulated participants"):
        if row["participant_id"] in done:
            continue
        if args.mock:
            response = mock_response(row, rng)
            record = normalize_record(row, response)
        else:
            try:
                response = call_deepseek(client, build_prompt(row["persona"], row["material"]), model=model, temperature=args.temperature)
                record = normalize_record(row, response)
            except Exception as exc:
                record = normalize_record(row, {}, error=str(exc))
        write_jsonl(raw_path, record)
        done.add(row["participant_id"])

    export_wide(raw_path, wide_path)
    print(f"Saved raw synthetic responses: {raw_path}")
    print(f"Saved wide synthetic responses: {wide_path}")


if __name__ == "__main__":
    main()
