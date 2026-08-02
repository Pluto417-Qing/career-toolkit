"""JD 匹配分析脚本（三层匹配引擎）。

三层匹配：
  Layer 1: 关键词 + 同义词匹配
  Layer 2: 概念匹配（高并发↔QPS，分布式↔微服务...）
  Layer 3: 证据匹配（年限/学历/团队规模/量化指标）

Gap 分类：
  evidence_gap  — 有相关经历但没写出来（最容易补）
  partial_gap   — 有相关但不完全对口
  real_gap      — 真正缺失

Usage:
    python3 scripts/jd_match.py <resume.yaml> --jd <jd.txt>
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

# ─── 学历等级（与 jd_parser 一致）───
DEGREE_MAP = {
    "大专": 1, "专科": 1,
    "本科": 2, "学士": 2,
    "硕士": 3, "研究生": 3,
    "博士": 4, "phd": 4,
}


def normalize(text: str) -> str:
    return text.strip().lower()


# ═══════════════════════════════════════════
# 数据加载
# ═══════════════════════════════════════════

def load_synonyms() -> dict[str, str]:
    """加载同义词库 → word → canonical 映射。"""
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
    """加载概念映射库。"""
    if not CONCEPTS_PATH.exists():
        return []
    with CONCEPTS_PATH.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or []


def try_jieba():
    """尝试加载 jieba 分词。"""
    try:
        import jieba
        jieba.setLogLevel(60)
        if SYNONYMS_PATH.exists():
            with SYNONYMS_PATH.open("r", encoding="utf-8") as f:
                groups = yaml.safe_load(f) or []
            for group in groups:
                if not group:
                    continue
                for word in group:
                    if len(word) >= 2:
                        jieba.add_word(word)
        # 加载概念库
        if CONCEPTS_PATH.exists():
            with CONCEPTS_PATH.open("r", encoding="utf-8") as f:
                concepts = yaml.safe_load(f) or []
            for concept in concepts:
                jieba.add_word(concept.get("concept", ""))
                for r in concept.get("related", []):
                    if len(r) >= 2:
                        jieba.add_word(r)
        return jieba
    except ImportError:
        return None


# ═══════════════════════════════════════════
# JD 关键词提取（从原始文本）
# ═══════════════════════════════════════════

SOFT_SKILLS = {
    "沟通", "协作", "团队合作", "抗压", "自驱", "主动", "责任心",
    "学习能力", "表达能力", "团队精神", "责任心强", "积极主动",
}

STOPWORDS = {
    "熟悉", "了解", "掌握", "精通", "熟练", "使用", "具备", "能够", "负责",
    "参与", "完成", "岗位要求", "任职资格", "工作职责", "职位描述", "加分项",
    "优先考虑", "工作内容", "基本要求", "技能要求", "必备条件", "有经验",
    "相关经验", "开发经验", "以上学历", "本科及以上", "硕士及以上",
    "年以上", "工作经验", "相关工作", "优先", "有较强", "有良好",
    "进行", "实现", "支持", "包括", "以及", "等", "及", "和", "与", "或",
    "具有", "拥有", "需要", "要求", "希望", "期望", "理想", "合适",
    "我们", "团队", "公司", "平台", "业务", "产品", "系统", "项目",
    "能力", "精神", "意识", "思维", "观念", "态度",
}

SECTION_WEIGHT = {
    "required": 2.0,
    "preferred": 1.0,
    "bonus": 0.5,
    "responsibilities": 1.0,
    "unclassified": 1.0,
}

en_pattern = re.compile(r"[A-Za-z][A-Za-z0-9+#./_-]{1,}")
zh_pattern = re.compile(r"[\u4e00-\u9fff]{2,}")


def extract_jd_keywords(jd_text: str, jieba_mod, synonym_map: dict[str, str]) -> list[dict]:
    """从 JD 文本中提取关键词。"""
    lines = jd_text.strip().splitlines()
    section = "required"
    keywords = []
    seen = set()

    bonus_re = re.compile(r"加分|优先|plus|preferred|bonus", re.IGNORECASE)
    required_re = re.compile(r"要求|资格|必备|must|required|任职", re.IGNORECASE)
    resp_re = re.compile(r"职责|工作内容|职位描述|你将负责", re.IGNORECASE)

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if bonus_re.search(stripped):
            section = "bonus"
        elif required_re.search(stripped):
            section = "required"
        elif resp_re.search(stripped):
            section = "responsibilities"

        tokens = en_pattern.findall(stripped)
        zh_text = en_pattern.sub(" ", stripped)
        if jieba_mod is not None:
            zh_tokens = [t for t in jieba_mod.cut(zh_text) if t.strip()]
        else:
            zh_tokens = zh_pattern.findall(zh_text)
        tokens.extend(zh_tokens)

        for token in tokens:
            norm = normalize(token)
            if len(norm) < 2 or norm in SOFT_SKILLS or norm in STOPWORDS or norm.isdigit():
                continue
            canonical = synonym_map.get(norm, norm)
            if canonical not in seen:
                seen.add(canonical)
                keywords.append({
                    "keyword": token,
                    "canonical": canonical,
                    "section": section,
                    "weight": SECTION_WEIGHT.get(section, 1.0),
                    "occurrences": 1,
                })
            else:
                for kw in keywords:
                    if kw["canonical"] == canonical:
                        kw["weight"] += 0.5
                        kw["occurrences"] += 1
                        break
    return keywords


# ═══════════════════════════════════════════
# 简历能力提取
# ═══════════════════════════════════════════

def extract_resume_terms(resume: dict, synonym_map: dict[str, str]) -> dict[str, set[str]]:
    """从简历中提取关键词，按 section 分组。"""
    sections = {}

    def add(section: str, term: str):
        norm = normalize(term)
        if len(norm) < 2:
            return
        canonical = synonym_map.get(norm, norm)
        sections.setdefault(section, {}).setdefault(canonical, set()).add(term)

    for skill in resume.get("skills", []):
        for kw in skill.get("keywords", []):
            add("skills", kw)

    for proj in resume.get("projects", []):
        for tech in proj.get("tech", []):
            add("tech", tech)
        for h in proj.get("highlights", []):
            add("highlights", h)

    for work in resume.get("work", []):
        for h in work.get("highlights", []):
            add("highlights", h)

    for edu in resume.get("education", []):
        for c in edu.get("courses", []):
            add("courses", c)

    return sections


def get_all_resume_text(resume: dict) -> str:
    """获取简历全文（用于概念匹配的全文检索）。"""
    parts = []
    for skill in resume.get("skills", []):
        parts.extend(skill.get("keywords", []))
    for section in ("work", "projects", "research", "activities"):
        for entry in resume.get(section, []) or []:
            parts.extend(entry.get("highlights", []) or [])
            parts.append(entry.get("summary", "") or "")
    for edu in resume.get("education", []) or []:
        parts.extend(edu.get("courses", []) or [])
        parts.extend(edu.get("highlights", []) or [])
    return " ".join(parts)


def get_resume_work_years(resume: dict) -> float:
    """计算简历中的工作年限。"""
    from datetime import datetime
    total_months = 0
    now = datetime.now()
    for work in resume.get("work", []) or []:
        start = work.get("start", "")
        end = work.get("end", "")
        if not start:
            continue
        try:
            start_parts = re.split(r"[.\-年]", start)
            if len(start_parts) < 2:
                continue
            sy, sm = int(start_parts[0]), int(start_parts[1])
            if end and end != "至今":
                end_parts = re.split(r"[.\-年]", end)
                if len(end_parts) >= 2:
                    ey, em = int(end_parts[0]), int(end_parts[1])
                else:
                    continue
            else:
                ey, em = now.year, now.month
            months = (ey - sy) * 12 + (em - sm)
            total_months += max(0, months)
        except (ValueError, IndexError):
            continue
    return round(total_months / 12, 1)


def get_resume_degree_level(resume: dict) -> int:
    """获取简历最高学历等级。"""
    max_level = 0
    for edu in resume.get("education", []) or []:
        degree = edu.get("degree", "") or ""
        for d, level in DEGREE_MAP.items():
            if d in degree.lower():
                max_level = max(max_level, level)
    return max_level


def get_resume_concepts(resume: dict, concepts: list[dict]) -> set[str]:
    """检测简历中体现了哪些概念（基于全文检索）。"""
    full_text = get_all_resume_text(resume).lower()
    matched = set()
    for concept in concepts:
        concept_name = concept.get("concept", "")
        related = concept.get("related", [])
        # 检查概念名本身
        if concept_name.lower() in full_text:
            matched.add(concept_name)
            continue
        # 检查关联词
        for r in related:
            if isinstance(r, str) and r.lower() in full_text:
                matched.add(concept_name)
                break
    return matched


def get_resume_evidence(resume: dict) -> dict:
    """提取简历中的证据信息（用于证据匹配）。"""
    return {
        "work_years": get_resume_work_years(resume),
        "degree_level": get_resume_degree_level(resume),
        "concepts": get_resume_concepts(resume, load_concepts()),
        "has_github": any(
            "github" in (p.get("network", "") + p.get("url", "")).lower()
            for p in (resume.get("basics", {}).get("profiles", []) or [])
        ),
        "has_management": _check_management(resume),
        "has_quant_metrics": _check_quant_metrics(resume),
    }


def _check_management(resume: dict) -> bool:
    """检查是否有管理经验。"""
    mgmt_words = ["带领", "管理", "组长", "leader", "lead", "mentor", "指导", "团队", "人小组", "带队"]
    for section in ("work", "projects"):
        for entry in resume.get(section, []) or []:
            for h in entry.get("highlights", []) or []:
                if any(w in h.lower() for w in mgmt_words):
                    return True
    return False


def _check_quant_metrics(resume: dict) -> bool:
    """检查是否有量化指标。"""
    quant_re = re.compile(r"\d+[%万亿次]|QPS|TPS|DAU|MAU|UV|PV|GMV", re.IGNORECASE)
    for section in ("work", "projects"):
        for entry in resume.get(section, []) or []:
            for h in entry.get("highlights", []) or []:
                if quant_re.search(h):
                    return True
    return False


# ═══════════════════════════════════════════
# 三层匹配引擎
# ═══════════════════════════════════════════

def match_layer1_keywords(jd_keyword_canonical: str, resume_sections: dict[str, set[str]]) -> tuple[bool, list[str]]:
    """Layer 1: 关键词 + 同义词匹配。"""
    sources = []
    for section, terms in resume_sections.items():
        if jd_keyword_canonical in terms:
            sources.append(section)
    return (len(sources) > 0, sources)


def match_layer2_concepts(jd_keyword: str, resume_concepts: set[str]) -> bool:
    """Layer 2: 概念匹配。JD 关键词是否属于简历已体现的某个概念。"""
    return jd_keyword in resume_concepts


def match_layer3_evidence(req: dict, evidence: dict) -> tuple[bool, str]:
    """Layer 3: 证据匹配。检查年限/学历/管理等硬性要求。

    返回 (是否满足, 说明)。
    """
    if req["type"] == "experience":
        required_years = req.get("value", 0)
        actual_years = evidence.get("work_years", 0)
        if actual_years >= required_years:
            return True, f"工作年限 {actual_years} 年 >= 要求 {required_years} 年"
        return False, f"工作年限 {actual_years} 年 < 要求 {required_years} 年"

    if req["type"] == "education":
        required_level = req.get("value", 0)
        actual_level = evidence.get("degree_level", 0)
        if actual_level >= required_level:
            return True, f"学历达标（等级 {actual_level} >= {required_level}）"
        return False, f"学历等级 {actual_level} < 要求 {required_level}"

    if req["type"] == "soft_skill" and "团队" in req.get("raw", ""):
        if evidence.get("has_management"):
            return True, "简历中检测到团队管理经验"
        return False, "未检测到明确的团队管理经验"

    # 默认：无法用证据匹配
    return False, ""


# ═══════════════════════════════════════════
# Gap 分类
# ═══════════════════════════════════════════

def classify_gap(jd_kw: str, resume_sections: dict[str, set[str]], resume_full_text: str, evidence: dict) -> str:
    """对未匹配的 JD 需求进行 gap 分类。

    返回：evidence_gap / partial_gap / real_gap
    """
    # 检查是否有部分匹配（关键词的子串出现在简历中）
    for section, terms in resume_sections.items():
        for term in terms:
            if jd_kw in term or term in jd_kw:
                return "evidence_gap"
            # 检查简历全文中是否部分出现
            if jd_kw in resume_full_text.lower():
                return "evidence_gap"

    # 检查是否属于已有概念（说明有相关经验只是没写关键词）
    concepts = load_concepts()
    for concept in concepts:
        related = [normalize(r) if isinstance(r, str) else str(r).lower() for r in concept.get("related", [])]
        concept_name = concept.get("concept", "")
        if jd_kw in related or jd_kw == normalize(concept_name):
            if concept_name in evidence.get("concepts", set()):
                return "evidence_gap"

    return "real_gap"


# ═══════════════════════════════════════════
# 主匹配流程
# ═══════════════════════════════════════════

def run(resume_path: str, jd_path: str) -> dict:
    with open(resume_path, "r", encoding="utf-8") as f:
        resume = yaml.safe_load(f)
    with open(jd_path, "r", encoding="utf-8") as f:
        jd_text = f.read()

    synonym_map = load_synonyms()
    concepts = load_concepts()
    jieba_mod = try_jieba()

    # 解析 JD
    jd_keywords = extract_jd_keywords(jd_text, jieba_mod, synonym_map)
    resume_sections = extract_resume_terms(resume, synonym_map)
    resume_full_text = get_all_resume_text(resume).lower()
    evidence = get_resume_evidence(resume)
    # 重新加载 concepts（get_resume_concepts 内部已加载过，但 evidence 里已包含）
    resume_concepts = evidence.get("concepts", set())

    # 三层匹配
    covered = []
    missing = []

    for kw in jd_keywords:
        canonical = kw["canonical"]

        # Layer 1: 关键词 + 同义词
        l1_match, l1_sources = match_layer1_keywords(canonical, resume_sections)

        # Layer 2: 概念匹配
        l2_match = match_layer2_concepts(canonical, resume_concepts)
        # 也检查 JD 关键词是否是某个概念的关联词
        if not l2_match:
            for concept in concepts:
                related = concept.get("related", [])
                if canonical in [normalize(r) for r in related]:
                    if concept.get("concept", "") in resume_concepts:
                        l2_match = True
                        kw["matched_concept"] = concept.get("concept")
                        break

        if l1_match:
            kw["match_layer"] = 1
            kw["matched_in"] = l1_sources
            covered.append(kw)
        elif l2_match:
            kw["match_layer"] = 2
            kw["matched_in"] = ["concept"]
            covered.append(kw)
        else:
            # Layer 3 尝试（仅对非 skill 类型）
            if kw.get("type") in ("experience", "education", "soft_skill"):
                l3_match, l3_note = match_layer3_evidence(kw, evidence)
                if l3_match:
                    kw["match_layer"] = 3
                    kw["matched_note"] = l3_note
                    covered.append(kw)
                    continue
            kw["match_layer"] = 0
            # Gap 分类
            kw["gap_type"] = classify_gap(canonical, resume_sections, resume_full_text, evidence)
            missing.append(kw)

    missing.sort(key=lambda x: x["weight"], reverse=True)

    total = len(jd_keywords)
    coverage = len(covered) / total if total > 0 else 0

    # Gap 分类统计
    evidence_gaps = [m for m in missing if m.get("gap_type") == "evidence_gap"]
    partial_gaps = [m for m in missing if m.get("gap_type") == "partial_gap"]
    real_gaps = [m for m in missing if m.get("gap_type") == "real_gap"]

    # 维度得分
    skill_kws = [k for k in jd_keywords if k.get("type") != "experience" and k.get("type") != "education"]
    skill_covered = [k for k in skill_kws if k in covered]
    skill_score = round(len(skill_covered) / len(skill_kws) * 100, 1) if skill_kws else 100

    # 证据匹配维度
    evidence_checks = []
    for kw in jd_keywords:
        if kw.get("type") == "experience":
            ok, note = match_layer3_evidence(kw, evidence)
            evidence_checks.append(ok)
        if kw.get("type") == "education":
            ok, note = match_layer3_evidence(kw, evidence)
            evidence_checks.append(ok)
    evidence_score = round(sum(evidence_checks) / len(evidence_checks) * 100, 1) if evidence_checks else 100

    # 生成 evidence_gap 的改写建议
    rewrite_suggestions = []
    for gap in evidence_gaps:
        suggestion = {
            "keyword": gap["keyword"],
            "section": gap.get("section", ""),
            "suggestion": _make_suggestion(gap, resume_sections, resume_full_text),
        }
        rewrite_suggestions.append(suggestion)

    return {
        "overall_score": round(coverage * 100, 1),
        "dimension_scores": {
            "技术栈匹配": skill_score,
            "经验学历": evidence_score,
        },
        "total_keywords": total,
        "covered_count": len(covered),
        "missing_count": len(missing),
        "coverage_percent": round(coverage * 100, 1),
        "covered": covered,
        "missing": missing,
        "gap_summary": {
            "evidence_gap": len(evidence_gaps),
            "partial_gap": len(partial_gaps),
            "real_gap": len(real_gaps),
        },
        "evidence_gaps": evidence_gaps,
        "real_gaps": real_gaps,
        "rewrite_suggestions": rewrite_suggestions,
        "resume_evidence": {
            "work_years": evidence.get("work_years", 0),
            "degree_level": evidence.get("degree_level", 0),
            "has_github": evidence.get("has_github", False),
            "has_management": evidence.get("has_management", False),
            "has_quant_metrics": evidence.get("has_quant_metrics", False),
            "concepts_matched": list(resume_concepts),
        },
    }


def _make_suggestion(gap: dict, resume_sections: dict[str, set[str]], resume_full_text: str) -> str:
    """为 evidence_gap 生成具体改写建议。"""
    kw = gap["keyword"]
    canonical = gap.get("canonical", kw)

    # 在简历中找到可能相关的条目
    related_entries = []
    for section, terms in resume_sections.items():
        for term in terms:
            if canonical in term or term in canonical:
                related_entries.append(f"{section}: {term}")

    if related_entries:
        return f"简历中已有相关内容（{'; '.join(related_entries[:2])}），建议明确写出「{kw}」并补充使用场景和规模"
    else:
        return f"简历全文中可能涉及「{kw}」相关内容，建议在 highlights 中明确提及「{kw}」并补充量化结果"


def main():
    parser = argparse.ArgumentParser(description="JD 三层匹配分析")
    parser.add_argument("resume", help="resume.yaml 路径")
    parser.add_argument("--jd", required=True, help="JD 文本文件路径")
    args = parser.parse_args()

    if not Path(args.resume).exists():
        print(f"错误：简历文件不存在 {args.resume}", file=sys.stderr)
        sys.exit(1)
    if not Path(args.jd).exists():
        print(f"错误：JD 文件不存在 {args.jd}", file=sys.stderr)
        sys.exit(1)

    result = run(args.resume, args.jd)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
