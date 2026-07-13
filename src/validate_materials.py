import argparse

import pandas as pd

from stimuli import all_materials
from path_safety import resolve_output_dir

PROCESS_ORDER = [
    "direct_choice",
    "direct_choice_long",
    "alternatives",
    "reasons_concise",
    "reasons",
    "reflection_feedback",
]


def build_materials_frame() -> pd.DataFrame:
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
    return pd.DataFrame(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--out",
        required=True,
        help="Explicit output directory for materials_preview.csv. Must not be "
        "the repository outputs/ directory. Fail fast if omitted.",
    )
    args = parser.parse_args()

    out_dir = resolve_output_dir(args.out)
    preview_path = out_dir / "materials_preview.csv"

    df = build_materials_frame()
    df.to_csv(preview_path, index=False, encoding="utf-8-sig")

    summary = (
        df.groupby("process_condition")["char_len"]
        .agg(["mean", "min", "max"])
        .reindex(PROCESS_ORDER)
    )
    print(summary)
    print(f"\nSaved synthetic materials preview: {preview_path}")


if __name__ == "__main__":
    main()
