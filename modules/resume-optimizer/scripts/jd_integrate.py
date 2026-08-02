"""JD 自然融入脚本。

读取简历 + JD 匹配结果（evidence_gap 列表），为每个 gap 生成「自然不刻意」的改写建议。

核心原则：
  1. 关键词融入已有经历，不新增虚假经历
  2. 单条 bullet 最多融入 1 个新关键词，避免堆砌
  3. 融入后的句子必须语义通顺，不能生硬插入
  4. 优先融入「相关度最高」的经历段
  5. 标注置信度，低置信度的建议需用户确认

Usage:
    # 先跑 jd_match 生成匹配结果
    python3 scripts/jd_match.py resume.yaml --jd jd.txt > match.json
    # 再跑 jd_integrate 生成融入建议
    python3 scripts/jd_integrate.py resume.yaml --match match.json
"""

import argparse
import json
import re
import sys
from pathlib import Path

import yaml

SKILL_DIR = Path(__file__).resolve().parent.parent
SYNONYMS_PATH = SKILL_DIR / "assets" / "synonyms.yaml"
CONCEPTS_PATH = SKILL_DIR / "assets" / "concepts.yaml"


def normalize(text: str) -> str:
    return text.strip().lower()


def load_synonyms() -> dict[str, str]:
    if not SYNONYMS_PATH.exists():
        return {}
    with SYNONYMS_PATH.open("r", encoding="utf-8") as f:
        groups = yaml.safe_load(f) or []
    mapping = {}
    for group in groups:
        if not group:
            continue
        canonical = str(group[0]).strip().lower()
        for word in group:
            mapping[str(word).strip().lower()] = canonical
    return mapping


def load_concepts() -> list[dict]:
    if not CONCEPTS_PATH.exists():
        return []
    with CONCEPTS_PATH.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or []


# ═══════════════════════════════════════════
# 经历段提取
# ═══════════════════════════════════════════

def extract_all_bullets(resume: dict) -> list[dict]:
    """提取简历中所有 bullet，记录来源位置和上下文。"""
    bullets = []

    for section in ("work", "projects", "research", "activities"):
        entries = resume.get(section, []) or []
        for i, entry in enumerate(entries):
            org = entry.get("organization") or entry.get("name") or entry.get("title") or f"{section}[{i}]"
            pos = entry.get("position") or entry.get("role") or ""
            tech = entry.get("tech", []) or []
            summary = entry.get("summary", "") or ""
            highlights = entry.get("highlights", []) or []
            for j, hl in enumerate(highlights):
                bullets.append({
                    "section": section,
                    "entry_index": i,
                    "entry_name": org,
                    "position": pos,
                    "tech": tech,
                    "summary": summary,
                    "bullet_index": j,
                    "text": hl,
                    "text_lower": hl.lower(),
                })

    return bullets


# ═══════════════════════════════════════════
# 相关度评分
# ═══════════════════════════════════════════

def score_relevance(gap_keyword: str, bullet: dict, synonym_map: dict) -> float:
    """计算 gap 关键词与某个 bullet 的相关度。

    返回 0-1 分数：
    - 1.0：bullet 已有同义词，只需要补写规范名
    - 0.8：bullet 的 tech 列表中有概念关联词
    - 0.6：bullet 文本中有概念关联词
    - 0.4：bullet 所属 entry 的 summary 中有相关内容
    - 0.2：同 section 的其他 entry 有相关内容
    - 0.0：无关联
    """
    smap = synonym_map
    kw_lower = normalize(gap_keyword)

    # 检查 bullet 的 tech 列表
    for tech in bullet.get("tech", []):
        tech_lower = normalize(tech)
        tech_canon = smap.get(tech_lower, tech_lower)
        kw_canon = smap.get(kw_lower, kw_lower)
        if tech_canon == kw_canon:
            return 1.0
        # 概念关联检查
        concepts = load_concepts()
        for concept in concepts:
            related = [normalize(r) if isinstance(r, str) else "" for r in concept.get("related", [])]
            if kw_canon in related and tech_canon in related:
                return 0.8

    # 检查 bullet 文本中是否有概念关联词
    concepts = load_concepts()
    for concept in concepts:
        related = concept.get("related", [])
        concept_name = concept.get("concept", "")
        # JD 关键词是否是某个概念的关联词
        kw_is_related = kw_lower in [normalize(r) if isinstance(r, str) else "" for r in related]
        if kw_is_related:
            # bullet 文本中是否有该概念的其他关联词
            for r in related:
                if isinstance(r, str) and normalize(r) != kw_lower and normalize(r) in bullet["text_lower"]:
                    return 0.6

    # 检查 summary
    summary_lower = bullet.get("summary", "").lower()
    if kw_lower in summary_lower:
        return 0.4

    # 概念名本身出现在 summary 中
    for concept in concepts:
        if concept.get("concept", "").lower() in summary_lower:
            related = [normalize(r) if isinstance(r, str) else "" for r in concept.get("related", [])]
            if kw_lower in related:
                return 0.4

    return 0.0


# ═══════════════════════════════════════════
# 融入位置选择
# ═══════════════════════════════════════════

def find_best_bullet(gap: dict, bullets: list[dict], synonym_map: dict) -> dict | None:
    """为 gap 关键词找到最佳融入 bullet。

    返回 bullet + 相关度分数 + 融入策略。
    """
    kw = gap.get("keyword", gap.get("canonical", ""))
    scored = []

    for bullet in bullets:
        score = score_relevance(kw, bullet, synonym_map)
        if score > 0:
            scored.append((score, bullet))

    if not scored:
        return None

    scored.sort(key=lambda x: x[0], reverse=True)
    best_score, best_bullet = scored[0]

    # 确定融入策略
    strategy = determine_strategy(kw, best_bullet, best_score, synonym_map)

    return {
        "bullet": best_bullet,
        "relevance_score": best_score,
        "strategy": strategy,
    }


def determine_strategy(kw: str, bullet: dict, score: float, synonym_map: dict) -> str:
    """根据相关度确定融入策略。"""
    if score >= 1.0:
        return "explicit"  # bullet 已有同义词，建议显式写规范名
    elif score >= 0.8:
        return "tech_list"  # tech 列表有关联，建议在文本中体现
    elif score >= 0.6:
        return "enrich"    # 文本有概念关联词，建议补充具体技术名
    elif score >= 0.4:
        return "summary"   # summary 有关联，建议在 highlights 中展开
    else:
        return "new_context"  # 需要在相关经历中新增一条


# ═══════════════════════════════════════════
# 改写建议生成
# ═══════════════════════════════════════════

def generate_rewrite_suggestion(gap: dict, best: dict, synonym_map: dict) -> dict:
    """生成一条具体的改写建议。"""
    kw = gap.get("keyword", "")
    strategy = best["strategy"]
    bullet = best["bullet"]
    original = bullet["text"]
    relevance = best["relevance_score"]

    suggestions = {
        "explicit": _suggest_explicit,
        "tech_list": _suggest_tech_list,
        "enrich": _suggest_enrich,
        "summary": _suggest_summary,
        "new_context": _suggest_new_context,
    }

    generator = suggestions.get(strategy, _suggest_new_context)
    rewrite_text, confidence, note = generator(kw, bullet, original, synonym_map)

    return {
        "keyword": kw,
        "gap_type": gap.get("gap_type", "evidence_gap"),
        "target_section": bullet["section"],
        "target_entry": bullet["entry_name"],
        "target_bullet_index": bullet["bullet_index"],
        "original_text": original,
        "suggested_text": rewrite_text,
        "strategy": strategy,
        "strategy_description": _strategy_description(strategy),
        "relevance_score": relevance,
        "confidence": confidence,
        "note": note,
    }


def _strategy_description(strategy: str) -> str:
    desc = {
        "explicit": "显式补写：已有同义技术，只需写出规范名",
        "tech_list": "技术栈补写：tech 列表有关联技术，建议在文本中体现",
        "enrich": "丰富描述：文本中有概念关联词，建议补充具体技术名",
        "summary": "展开描述：summary 有关联，建议在 highlights 中展开",
        "new_context": "新增语境：需在相关经历中补充一条描述",
    }
    return desc.get(strategy, strategy)


def _suggest_explicit(kw, bullet, original, smap):
    """策略1：已有同义词，建议显式写规范名。"""
    # 找到同义词
    kw_canon = smap.get(normalize(kw), normalize(kw))
    for tech in bullet.get("tech", []):
        tech_canon = smap.get(normalize(tech), normalize(tech))
        if tech_canon == kw_canon and normalize(tech) != kw_canon:
            rewrite = original.replace(tech, f"{tech}（{kw}）") if tech in original else f"{original}（基于 {kw}）"
            return rewrite, 0.9, f"简历 tech 列表已有 {tech}（{kw} 的同义词），建议在文本中显式写出 {kw}"

    rewrite = f"{original}（基于 {kw}）"
    return rewrite, 0.8, f"建议显式提及 {kw}"


def _suggest_tech_list(kw, bullet, original, smap):
    """策略2：tech 列表有概念关联技术。"""
    rewrite = original.rstrip("。") + f"，引入 {kw} 优化技术方案"
    return rewrite, 0.7, f"该经历的 tech 列表有概念关联技术，建议在描述中自然提及 {kw}"


def _suggest_enrich(kw, bullet, original, smap):
    """策略3：文本有概念关联词，补充具体技术名。"""
    # 尝试在句尾自然补充
    if original.endswith(("。", "！", "；")):
        rewrite = original[:-1] + f"，使用 {kw} 实现核心模块"
    else:
        rewrite = original + f"，使用 {kw} 实现核心模块"
    return rewrite, 0.6, f"该 bullet 已有概念关联内容，建议补充 {kw} 作为具体技术手段"


def _suggest_summary(kw, bullet, original, smap):
    """策略4：summary 有关联，建议在 highlights 中展开。"""
    rewrite = f"使用 {kw} 重构核心模块，覆盖 {bullet.get('summary', '该模块')} 场景"
    return rewrite, 0.5, f"该经历的 summary 已提及相关内容，建议在 highlights 中用 {kw} 展开"


def _suggest_new_context(kw, bullet, original, smap):
    """策略5：需要新增一条 bullet。"""
    rewrite = f"引入 {kw}，优化 [?] 模块的 [?] 指标，提升 [?]"
    return rewrite, 0.3, f"该经历与 {kw} 关联度较低，建议确认是否有真实经历可补充（含 [?] 的部分需用户确认）"


# ═══════════════════════════════════════════
# 堆砌检测
# ═══════════════════════════════════════════

def detect_stuffing(suggestions: list[dict]) -> list[dict]:
    """检测是否有同一个 bullet 被多个 gap 关键词塞入。

    返回警告列表。
    """
    bullet_targets = {}
    for s in suggestions:
        key = f"{s['target_section']}[{s['target_entry']}].bullet[{s['target_bullet_index']}]"
        bullet_targets.setdefault(key, []).append(s)

    warnings = []
    for key, group in bullet_targets.items():
        if len(group) > 1:
            keywords = [g["keyword"] for g in group]
            warnings.append({
                "target": key,
                "keywords": keywords,
                "warning": f"该 bullet 被建议融入 {len(group)} 个关键词（{', '.join(keywords)}），可能导致堆砌感，建议只选 1 个最相关的",
                "recommended": group[0]["keyword"],
            })

    return warnings


# ═══════════════════════════════════════════
# 主流程
# ═══════════════════════════════════════════

def run(resume_path: str, match_path: str) -> dict:
    with open(resume_path, "r", encoding="utf-8") as f:
        resume = yaml.safe_load(f)
    with open(match_path, "r", encoding="utf-8") as f:
        match_result = json.load(f)

    synonym_map = load_synonyms()
    bullets = extract_all_bullets(resume)

    # 只处理 evidence_gap
    evidence_gaps = match_result.get("evidence_gaps", [])

    suggestions = []
    unprocessable = []

    for gap in evidence_gaps:
        best = find_best_bullet(gap, bullets, synonym_map)
        if best:
            suggestion = generate_rewrite_suggestion(gap, best, synonym_map)
            suggestions.append(suggestion)
        else:
            unprocessable.append({
                "keyword": gap.get("keyword", ""),
                "reason": "在简历中未找到任何相关经历，无法自然融入",
                "suggestion": "如确实有相关经历，建议手动补充；如没有，不建议虚构",
            })

    # 按置信度排序
    suggestions.sort(key=lambda x: x["confidence"], reverse=True)

    # 堆砌检测
    stuffing_warnings = detect_stuffing(suggestions)

    return {
        "total_gaps": len(evidence_gaps),
        "processable": len(suggestions),
        "unprocessable": len(unprocessable),
        "suggestions": suggestions,
        "unprocessable_list": unprocessable,
        "stuffing_warnings": stuffing_warnings,
        "principles": [
            "每个 bullet 最多融入 1 个新关键词",
            "融入后的句子必须语义通顺",
            "优先融入已有相关技术的经历段",
            "标注 [?] 的部分需要用户确认真实数据",
            "低置信度建议必须用户确认后才采用",
        ],
    }


def main():
    parser = argparse.ArgumentParser(description="JD 关键词自然融入建议")
    parser.add_argument("resume", help="resume.yaml 路径")
    parser.add_argument("--match", required=True, help="jd_match.py 输出的 JSON 文件路径")
    args = parser.parse_args()

    if not Path(args.resume).exists():
        print(f"错误：简历文件不存在 {args.resume}", file=sys.stderr)
        sys.exit(1)
    if not Path(args.match).exists():
        print(f"错误：匹配结果文件不存在 {args.match}", file=sys.stderr)
        sys.exit(1)

    result = run(args.resume, args.match)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
