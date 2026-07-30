#!/usr/bin/env python3
"""Score MBTI-simplified assessment responses.

Usage:
    python3 scripts/score_mbti.py <responses.yaml>

responses.yaml format:
    answers:
      1: 4
      2: 3
      ...  # id -> score (1..5)

Outputs a JSON with per-dimension scores, 4-letter MBTI type,
dimension strengths, and career hints.
"""

import json
import sys
from pathlib import Path

import yaml

SKILL_DIR = Path(__file__).resolve().parent.parent
BANK_PATH = SKILL_DIR / "assets" / "assessments" / "mbti-simplified.yaml"


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/score_mbti.py <responses.yaml>", file=sys.stderr)
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

    dims = bank["dimensions"]
    # For each dimension, accumulate a score where:
    #   pole_high items contribute their raw score
    #   pole_low items contribute (6 - raw score) so they flip direction
    # This gives a range of [10, 50] per dimension (10 items each)
    # Normalized to 0-100 where 50 is the midpoint
    scores = {d: 0 for d in dims}
    counts = {d: 0 for d in dims}
    unanswered = []

    for item in bank["items"]:
        iid = item["id"]
        dim = item["dim"]
        pole = item["pole"]
        pole_high = dims[dim]["pole_high"]

        if iid not in answers:
            unanswered.append(iid)
            continue

        val = max(1, min(5, answers[iid]))
        if pole == pole_high:
            scores[dim] += val
        else:
            scores[dim] += (6 - val)
        counts[dim] += 1

    per_dim = []
    type_letters = []
    threshold = bank.get("interpretation", {}).get("type_threshold", 50)

    for dim_key, dim_meta in dims.items():
        cnt = counts[dim_key]
        raw_score = scores[dim_key]
        # Normalize: min possible = cnt*1, max possible = cnt*5
        max_score = cnt * 5 if cnt else 0
        min_score = cnt * 1 if cnt else 0
        normalized = round(
            (raw_score - min_score) / (max_score - min_score) * 100, 1
        ) if cnt else 50.0

        if normalized >= threshold:
            letter = dim_meta["pole_high"]
            preference = dim_meta["pole_high_label"]
        else:
            letter = dim_meta["pole_low"]
            preference = dim_meta["pole_low_label"]

        strength = abs(normalized - 50)
        type_letters.append(letter)

        per_dim.append({
            "dim": dim_key,
            "name": dim_meta["name"],
            "raw": raw_score,
            "answered": cnt,
            "score_100": normalized,
            "letter": letter,
            "preference": preference,
            "strength": round(strength, 1),
        })

    mbti_type = "".join(type_letters)

    hints = bank.get("interpretation", {}).get("career_hints", {})
    matched_hint = hints.get(mbti_type)

    result = {
        "type": mbti_type,
        "per_dimension": per_dim,
        "unanswered_ids": unanswered,
        "career_hints": matched_hint,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
