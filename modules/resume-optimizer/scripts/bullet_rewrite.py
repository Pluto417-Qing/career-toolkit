"""Bullet 量化诊断脚本。

读取 resume.yaml，分析所有 highlights 的质量问题，输出 JSON 诊断报告。
改写由 Agent 完成（需要语义理解），本脚本只负责检测问题。
"""

import argparse
import json
import re
import sys
from pathlib import Path

import yaml

VAGUE_PATTERN = re.compile(r"相关|有关|一些|等等|各种|若干|很多|大量的?")
DUTY_PATTERN = re.compile(r"^(负责|承担|完成日常|配合)")
RESULT_KEYWORDS = re.compile(r"提升|降低|减少|增加|优化|缩短|覆盖|达到|实现|节省|下降|增长|翻倍")
QUANT_PATTERN = re.compile(r"\d|%|倍|次/|个|条|行|人|天|小时|毫秒|ms|万|亿|TB|GB|MB|QPS|TPS")

VERB_LIST = [
    "主导", "设计", "搭建", "构建", "创建", "开发", "实现", "落地", "交付",
    "重构", "优化", "迁移", "升级", "治理", "推动", "对齐", "沉淀", "输出",
    "牵头", "封装", "抽象", "复用", "提效", "挖掘", "分析", "建模", "验证",
    "度量", "支撑", "引入", "制定", "编写", "完成", "负责", "参与",
]


def starts_with_verb(text: str) -> bool:
    for v in VERB_LIST:
        if text.startswith(v):
            return True
    return False


def diagnose_bullet(text: str) -> list[str]:
    issues = []
    text = text.strip()

    if len(text) < 10:
        issues.append("TOO_SHORT")
    if len(text) > 60:
        issues.append("TOO_LONG")
    if VAGUE_PATTERN.search(text):
        issues.append("VAGUE")
    if not starts_with_verb(text):
        issues.append("NO_VERB")
    if DUTY_PATTERN.match(text):
        issues.append("DUTY_LIST")
    if not RESULT_KEYWORDS.search(text):
        issues.append("NO_RESULT")
    if not QUANT_PATTERN.search(text):
        issues.append("NO_QUANT")

    return issues


def extract_highlights(resume: dict) -> list[dict]:
    results = []

    for section in ("work", "projects", "research", "activities"):
        entries = resume.get(section, []) or []
        for i, entry in enumerate(entries):
            highlights = entry.get("highlights", []) or []
            entry_name = entry.get("organization") or entry.get("name") or entry.get("title") or f"{section}[{i}]"
            for j, bullet in enumerate(highlights):
                issues = diagnose_bullet(bullet)
                results.append({
                    "section": section,
                    "index": i,
                    "entry_name": entry_name,
                    "bullet_index": j,
                    "text": bullet,
                    "issues": issues,
                    "issue_count": len(issues),
                })

    return results


def run(resume_path: str) -> dict:
    with open(resume_path, "r", encoding="utf-8") as f:
        resume = yaml.safe_load(f)

    bullets = extract_highlights(resume)
    total = len(bullets)
    problematic = [b for b in bullets if b["issue_count"] > 0]

    problematic.sort(key=lambda x: x["issue_count"], reverse=True)

    return {
        "total_bullets": total,
        "problematic_count": len(problematic),
        "healthy_count": total - len(problematic),
        "bullets": problematic,
    }


def main():
    parser = argparse.ArgumentParser(description="Bullet 量化诊断")
    parser.add_argument("resume", help="resume.yaml 路径")
    args = parser.parse_args()

    if not Path(args.resume).exists():
        print(f"错误：简历文件不存在 {args.resume}", file=sys.stderr)
        sys.exit(1)

    result = run(args.resume)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
