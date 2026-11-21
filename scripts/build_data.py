"""Regenerate data.json untuk dashboard dari dataset Kaggle (xlsx).

Pakai: python scripts/build_data.py <path.xlsx>
Output: data.json (agregat 5 stadium x hipertensi x diabetes x anemia = 40 sel)
"""
import csv
import json
import sys
from pathlib import Path

import pandas as pd

T, H, D, A = "Target", "Hypertension (yes/no)", "Diabetes mellitus (yes/no)", "Anemia (yes/no)"
AGE, BP = "Age of the patient", "Blood pressure (mm/Hg)"
ORDER = ["No_Disease", "Low_Risk", "Moderate_Risk", "High_Risk", "Severe_Disease"]
BANDS = ["<30", "30-44", "45-59", "60-74", "75+"]
EDGES = [0, 30, 45, 60, 75, 200]


def main(xlsx: str) -> None:
    raw = pd.read_excel(xlsx)
    hdr = [h.strip() for h in str(raw.columns[0]).split(",")]
    rows = list(csv.reader([str(v) for v in raw[raw.columns[0]].tolist()]))
    df = pd.DataFrame(rows, columns=hdr)
    df[AGE] = pd.to_numeric(df[AGE], errors="coerce")
    df[BP] = pd.to_numeric(df[BP], errors="coerce")
    df["band"] = pd.cut(df[AGE], bins=EDGES, labels=BANDS, right=False)

    g = df.groupby([T, H, D, A, "band"], observed=False).agg(
        n=(T, "size"), age=(AGE, "sum"), bp=(BP, "sum")
    ).reset_index()

    cells = []
    for (t, h, d, a), sub in g.groupby([T, H, D, A], observed=True):
        sub = sub.set_index("band").reindex(BANDS).fillna(0)
        cells.append({
            "t": t, "h": h, "d": d, "a": a,
            "n": int(sub["n"].sum()),
            "buckets": [
                {"n": int(r["n"]), "age": round(float(r["age"]), 1), "bp": round(float(r["bp"]), 1)}
                for _, r in sub.iterrows()
            ],
        })
    out = {
        "meta": {"source": "Chronic Kidney Disease Dataset (Kaggle)",
                 "file": Path(xlsx).name, "rows": len(df)},
        "labels": ORDER,
        "bands": BANDS,
        "totals": {
            "patients": len(df),
            "avgAge": round(df[AGE].mean(), 2),
            "avgBP": round(df[BP].mean(), 2),
        },
        "cells": cells,
    }
    Path(__file__).resolve().parent.parent.joinpath("data.json").write_text(
        json.dumps(out, indent=1), encoding="utf-8"
    )
    print(f"{len(df)} baris, {len(cells)} sel -> data.json")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1
         else r"C:\Users\farre\Downloads\kidney_disease_dataset (1).xlsx")
