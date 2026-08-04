"""Bullet 量化诊断脚本。

读取 resume.yaml，分析所有 highlights 的质量问题，输出 JSON 诊断报告。
改写由 Agent 完成（需要语义理解），本脚本只负责检测问题并给出改写模板提示。

动词库分类：
  - create: 创造类（从 0 到 1）
  - optimize: 优化类（从 1 到更好）
  - analyze: 分析类（数据驱动决策）
  - manage: 管理类（团队/流程/资源）
  - technical: 技术专项（架构/性能/安全）
"""

import argparse
import json
import re
import sys
from pathlib import Path

import yaml

# ─── 模糊/弱化词 ───
VAGUE_PATTERN = re.compile(r"相关|有关|一些|等等|各种|若干|很多|大量的?|差不多|大概|似乎")
DUTY_PATTERN = re.compile(r"^(负责|承担|完成日常|配合|协助|帮忙|跟着|参与)")
RESULT_KEYWORDS = re.compile(r"提升|降低|减少|增加|优化|缩短|覆盖|达到|实现|节省|下降|增长|翻倍|节约|削减|改善|提高|缩短|加速|赋能|助力")
QUANT_PATTERN = re.compile(r"\d|%|倍|次/|个|条|行|人|天|小时|毫秒|ms|万|亿|TB|GB|MB|QPS|TPS|PV|UV|DAU|MAU|GMV|ROI")

# ─── 动词库（分类） ───
VERB_GROUPS = {
    "create": {
        "label": "创造类",
        "verbs": ["主导", "独立完成", "设计", "搭建", "构建", "创建", "开发", "实现", "落地", "交付", "发起", "创办", "推出", "上线", "从零"],
        "hint": "强调从 0 到 1 的主动性，适合项目/产品/系统从无到有的场景",
    },
    "optimize": {
        "label": "优化类",
        "verbs": ["重构", "优化", "迁移", "升级", "治理", "推动", "对齐", "沉淀", "输出", "提效", "改善", "改进", "精简", "整合", "改造", "梳理", "完善", "迭代"],
        "hint": "强调从 1 到更好的改进，适合对现有系统/流程的优化场景",
    },
    "analyze": {
        "label": "分析类",
        "verbs": ["挖掘", "分析", "建模", "验证", "度量", "调研", "评估", "诊断", "预测", "洞察", "量化", "拆解", "归因"],
        "hint": "强调数据驱动的决策过程，适合数据/算法/用研场景",
    },
    "manage": {
        "label": "管理类",
        "verbs": ["牵头", "主导", "组织", "协调", "推进", "跟进", "管理", "带领", "指导", "培训", "分配", "规划", "制定", "监督", "统筹", "把控"],
        "hint": "强调团队/项目/资源的管理能力，适合 leader/PM 场景",
    },
    "technical": {
        "label": "技术专项",
        "verbs": ["封装", "抽象", "复用", "引入", "编写", "完成", "负责", "参与", "部署", "配置", "调试", "测试", "维护", "监控", "告警", "压测", "排查", "定位", "修复"],
        "hint": "强调具体的技术实施动作，适合研发/运维场景",
    },
}

# 所有动词的扁平集合（用于检测）
ALL_VERBS = set()
for group in VERB_GROUPS.values():
    ALL_VERBS.update(group["verbs"])


def starts_with_verb(text: str) -> bool:
    for v in ALL_VERBS:
        if text.startswith(v):
            return True
    return False


def get_verb_category(text: str) -> str | None:
    """返回文本开头动词所属的类别，无则 None。"""
    for cat, group in VERB_GROUPS.items():
        for v in group["verbs"]:
            if text.startswith(v):
                return cat
    return None


def diagnose_bullet(text: str) -> dict:
    """诊断单条 bullet，返回 issues 列表 + 改写建议提示。"""
    issues = []
    text = text.strip()

    if len(text) < 10:
        issues.append("TOO_SHORT")
    if len(text) > 80:
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

    # 给出改写模板提示
    category = get_verb_category(text)
    hint = None
    if "NO_VERB" in issues:
        hint = "建议用「创造类」或「优化类」动词开头，如：主导/设计/重构/优化"
    elif "NO_RESULT" in issues and category:
        hint = f"当前动词属于「{VERB_GROUPS[category]['label']}」，{VERB_GROUPS[category]['hint']}。建议补充量化结果。"
    elif "NO_QUANT" in issues:
        hint = "缺少量化数据。模板：[动词] [做了什么] [涉及范围] [量化结果]。如找不到精确数字，可用相对量化。"

    return {"issues": issues, "verb_category": category, "rewrite_hint": hint}


def extract_highlights(resume: dict) -> list[dict]:
    results = []

    for section in ("work", "projects", "research", "activities"):
        entries = resume.get(section, []) or []
        for i, entry in enumerate(entries):
            highlights = entry.get("highlights", []) or []
            entry_name = entry.get("organization") or entry.get("name") or entry.get("title") or f"{section}[{i}]"
            for j, bullet in enumerate(highlights):
                diag = diagnose_bullet(bullet)
                results.append({
                    "section": section,
                    "index": i,
                    "entry_name": entry_name,
                    "bullet_index": j,
                    "text": bullet,
                    "issues": diag["issues"],
                    "issue_count": len(diag["issues"]),
                    "verb_category": diag["verb_category"],
                    "rewrite_hint": diag["rewrite_hint"],
                })

    return results


def run(resume_path: str) -> dict:
    with open(resume_path, "r", encoding="utf-8") as f:
        resume = yaml.safe_load(f)

    bullets = extract_highlights(resume)
    total = len(bullets)
    problematic = [b for b in bullets if b["issue_count"] > 0]

    problematic.sort(key=lambda x: x["issue_count"], reverse=True)

    # 统计常见问题类型
    issue_stats = {}
    for b in bullets:
        for issue in b["issues"]:
            issue_stats[issue] = issue_stats.get(issue, 0) + 1

    return {
        "total_bullets": total,
        "problematic_count": len(problematic),
        "healthy_count": total - len(problematic),
        "issue_distribution": issue_stats,
        "verb_categories": {cat: grp["label"] for cat, grp in VERB_GROUPS.items()},
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
