from pathlib import Path

import pandas as pd

from stimuli import all_materials


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"
OUT.mkdir(exist_ok=True)

rows = []
for row in all_materials():
    text = row["text"]
    rows.append(
        {
            **row,
            "has_alternative_marker": "A." in text and "B." in text,
            "has_reason_marker": "眼前代价" in text or "直接代价" in text or "后续影响" in text,
            "has_reflection_marker": "第三种做法" in text or "过去类似情境" in text or "修正后续行动" in text,
        }
    )

df = pd.DataFrame(rows)
df.to_csv(OUT / "materials_preview.csv", index=False, encoding="utf-8-sig")

summary = (
    df.groupby("process_condition")["char_len"]
    .agg(["mean", "min", "max"])
    .reindex(
        [
            "direct_choice",
            "direct_choice_long",
            "alternatives",
            "reasons_concise",
            "reasons",
            "reflection_feedback",
        ]
    )
)
print(summary)
print(f"\nSaved synthetic materials preview: {OUT / 'materials_preview.csv'}")
