#!/usr/bin/env python3
"""Validate a resume.yaml against the resume schema.

Usage:
    python3 scripts/validate.py <resume.yaml>
"""

import json
import sys
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

SKILL_DIR = Path(__file__).resolve().parent.parent
SCHEMA_PATH = SKILL_DIR / "assets" / "schema" / "resume.schema.json"


def load_yaml(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/validate.py <resume.yaml>", file=sys.stderr)
        return 2
    resume_path = Path(sys.argv[1]).resolve()
    if not resume_path.exists():
        print(f"❌ Resume file not found: {resume_path}", file=sys.stderr)
        return 2

    data = load_yaml(resume_path)
    with SCHEMA_PATH.open("r", encoding="utf-8") as f:
        schema = json.load(f)

    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(data), key=lambda e: list(e.absolute_path))
    if not errors:
        print(f"✅ {resume_path.name} passes schema validation.")
        return 0

    print(f"❌ Found {len(errors)} validation issue(s) in {resume_path.name}:", file=sys.stderr)
    for err in errors:
        loc = ".".join(str(p) for p in err.absolute_path) or "<root>"
        print(f"  • {loc}: {err.message}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
