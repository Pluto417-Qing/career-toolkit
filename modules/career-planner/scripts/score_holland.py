#!/usr/bin/env python3
"""Score Holland RIASEC assessment responses.

Usage:
    python3 scripts/score_holland.py <responses.yaml>

responses.yaml format:
    answers:
      1: 4
      2: 3
      ...  # id -> score (1..5)

Outputs a JSON with per-dimension raw score, 0-100 normalized score,
holland code (top-3 dims joined) and suggested path hints.
"""

import json
import sys
from pathlib import Path

import yaml

SKILL_DIR = Path(__file__).resolve().parent.parent
BANK_PATH = SKILL_DIR / "assets" / "assessments" / "holland-riasec.yaml"


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/score_holland.py <responses.yaml>", file=sys.stderr)
        return 2

    responses_path = Path(sys.argv[1]).resolve()
    if not responses_path.exists():
        print(f"❌ responses file not found: {responses_path}", file=sys.stderr)
        return 2

    with BANK_PATH.open("r", encoding="utf-8") as f:
        bank = yaml.safe_load(f)
    with responses_path.open("r", encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}
    answers = {int(k): int(v) for k, v in (raw.get("answers") or {}).items()}

    scores = {d: 0 for d in bank["dimensions"]}
    counts = {d: 0 for d in bank["dimensions"]}
    unanswered = []
    for item in bank["items"]:
        iid = item["id"]
        dim = item["dim"]
        if iid in answers:
            val = max(1, min(5, answers[iid]))
            scores[dim] += val
            counts[dim] += 1
        else:
            unanswered.append(iid)

    per_dim = []
    for dim, raw_score in scores.items():
        cnt = counts[dim]
        max_score = cnt * 5 if cnt else 0
        min_score = cnt * 1 if cnt else 0
        normalized = round((raw_score - min_score) / (max_score - min_score) * 100, 1) if cnt else 0.0
        per_dim.append({
            "dim": dim,
            "name": bank["dimensions"][dim]["name"],
            "raw": raw_score,
            "answered": cnt,
            "score_100": normalized,
        })
    per_dim.sort(key=lambda x: x["score_100"], reverse=True)

    top_k = bank.get("interpretation", {}).get("top_k", 3)
    code = "".join(d["dim"] for d in per_dim[:top_k])

    hints = bank.get("interpretation", {}).get("path_hints", {})
    # match by first 3 chars in any order
    matched_hint = None
    for key, val in hints.items():
        if set(key) == set(code[:3]):
            matched_hint = {"key": key, "paths": val}
            break

    result = {
        "code": code,
        "per_dimension": per_dim,
        "unanswered_ids": unanswered,
        "suggested_paths": matched_hint,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
