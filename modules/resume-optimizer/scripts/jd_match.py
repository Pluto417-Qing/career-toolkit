"""JD 匹配分析脚本。

读取 resume.yaml 和 JD 文本，使用 jieba 分词 + 外置同义词库进行关键词提取与交叉匹配。
输出 JSON 报告。

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

SOFT_SKILLS = {
    "沟通", "协作", "团队合作", "抗压", "自驱", "主动", "责任心",
    "学习能力", "表达能力", "团队精神", "责任心强", "积极主动",
    "有耐心", "细心", "踏实", "勤奋", "乐观", "开朗",
}

STOPWORDS = {
    # 中文通用停用词
    "熟悉", "了解", "掌握", "精通", "熟练", "使用", "具备", "能够", "负责",
    "参与", "完成", "岗位要求", "任职资格", "工作职责", "职位描述", "加分项",
    "优先考虑", "工作内容", "基本要求", "技能要求", "必备条件", "有经验",
    "相关经验", "开发经验", "以上学历", "本科及以上", "硕士及以上",
    "年以上", "工作经验", "相关工作", "优先", "有较强", "有良好",
    # 通用动词/形容词
    "进行", "实现", "支持", "包括", "以及", "等", "及", "和", "与", "或",
    "具有", "拥有", "需要", "要求", "希望", "期望", "理想", "合适",
    # 常见无意义词
    "我们", "团队", "公司", "平台", "业务", "产品", "系统", "项目",
    "能力", "精神", "意识", "思维", "观念", "态度",
}

SECTION_WEIGHT = {
    "required": 2.0,
    "preferred": 1.0,
    "bonus": 0.5,
}


def normalize(text: str) -> str:
    return text.strip().lower()


def load_synonyms() -> dict[str, str]:
    """从外置 YAML 加载同义词库，返回 word → canonical 映射。"""
    if not SYNONYMS_PATH.exists():
        return {}
    with SYNONYMS_PATH.open("r", encoding="utf-8") as f:
        groups = yaml.safe_load(f) or []
    mapping = {}
    for group in groups:
        if not group:
            continue
        canonical = group[0]
        for word in group:
            mapping[normalize(word)] = normalize(canonical)
    return mapping


def try_jieba():
    """尝试加载 jieba 分词，失败则回退到正则分词。"""
    try:
        import jieba
        import jieba.analyse

        # 静默加载
        jieba.setLogLevel(60)
        # 加载自定义词典（同义词库中的规范名）
        if SYNONYMS_PATH.exists():
            with SYNONYMS_PATH.open("r", encoding="utf-8") as f:
                groups = yaml.safe_load(f) or []
            for group in groups:
                if not group:
                    continue
                for word in group:
                    if len(word) >= 2:
                        jieba.add_word(word)
        return jieba
    except ImportError:
        return None


def extract_jd_keywords(jd_text: str, jieba_mod, synonym_map: dict[str, str]) -> list[dict]:
    """从 JD 文本中提取关键词。优先使用 jieba，回退到正则。"""
    lines = jd_text.strip().splitlines()
    section = "required"
    keywords = []
    seen = set()

    bonus_patterns = re.compile(r"加分|优先|plus|preferred|bonus", re.IGNORECASE)
    required_patterns = re.compile(r"要求|资格|必备|must|required|任职", re.IGNORECASE)

    # 提取英文技术词的正则
    en_pattern = re.compile(r"[A-Za-z][A-Za-z0-9+#./_-]{1,}")
    # 提取中文词的正则（回退用）
    zh_pattern = re.compile(r"[\u4e00-\u9fff]{2,}")

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if bonus_patterns.search(stripped):
            section = "bonus"
        elif required_patterns.search(stripped):
            section = "required"

        tokens = []

        # 先提取英文词（jieba 会切坏英文）
        en_tokens = en_pattern.findall(stripped)
        tokens.extend(en_tokens)

        # 去掉英文部分后用 jieba 分词处理中文
        zh_text = en_pattern.sub(" ", stripped)
        if jieba_mod is not None:
            zh_tokens = [t for t in jieba_mod.cut(zh_text) if t.strip()]
        else:
            zh_tokens = zh_pattern.findall(zh_text)
        tokens.extend(zh_tokens)

        for token in tokens:
            norm = normalize(token)
            # 过滤：太短、停用词、软技能
            if len(norm) < 2:
                continue
            if norm in SOFT_SKILLS or norm in STOPWORDS:
                continue
            # 过滤纯数字
            if norm.isdigit():
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


def extract_resume_terms(resume: dict, synonym_map: dict[str, str]) -> dict[str, set[str]]:
    """从简历中提取关键词，按 section 分组，返回 canonical → set(original_terms)。"""
    sections = {}

    def add_term(section: str, term: str):
        norm = normalize(term)
        if len(norm) < 2:
            return
        canonical = synonym_map.get(norm, norm)
        sections.setdefault(section, {}).setdefault(canonical, set()).add(term)

    for skill in resume.get("skills", []):
        for kw in skill.get("keywords", []):
            add_term("skills", kw)

    for proj in resume.get("projects", []):
        for tech in proj.get("tech", []):
            add_term("tech", tech)
        for h in proj.get("highlights", []):
            add_term("highlights", h)

    for work in resume.get("work", []):
        for h in work.get("highlights", []):
            add_term("highlights", h)

    for edu in resume.get("education", []):
        for c in edu.get("courses", []):
            add_term("courses", c)

    return sections


def match_keyword(keyword_canonical: str, resume_sections: dict[str, set[str]]) -> tuple[bool, list[str]]:
    """检查关键词是否在简历中出现，返回 (是否匹配, 匹配来源列表)。"""
    sources = []
    for section, terms in resume_sections.items():
        if keyword_canonical in terms:
            sources.append(section)
    return (len(sources) > 0, sources)


def run(resume_path: str, jd_path: str) -> dict:
    with open(resume_path, "r", encoding="utf-8") as f:
        resume = yaml.safe_load(f)

    with open(jd_path, "r", encoding="utf-8") as f:
        jd_text = f.read()

    synonym_map = load_synonyms()
    jieba_mod = try_jieba()
    jd_keywords = extract_jd_keywords(jd_text, jieba_mod, synonym_map)
    resume_sections = extract_resume_terms(resume, synonym_map)

    covered = []
    missing = []

    for kw in jd_keywords:
        is_match, sources = match_keyword(kw["canonical"], resume_sections)
        if is_match:
            kw["matched_in"] = sources
            covered.append(kw)
        else:
            missing.append(kw)

    missing.sort(key=lambda x: x["weight"], reverse=True)

    total = len(jd_keywords)
    coverage = len(covered) / total if total > 0 else 0

    # 按重要度分组
    high_priority = [m for m in missing if m["weight"] >= 2.0]
    medium_priority = [m for m in missing if 1.0 <= m["weight"] < 2.0]
    low_priority = [m for m in missing if m["weight"] < 1.0]

    return {
        "total_keywords": total,
        "covered_count": len(covered),
        "missing_count": len(missing),
        "coverage_percent": round(coverage * 100, 1),
        "covered": covered,
        "missing": missing,
        "missing_by_priority": {
            "high": high_priority,
            "medium": medium_priority,
            "low": low_priority,
        },
    }


def main():
    parser = argparse.ArgumentParser(description="JD 关键词匹配分析（jieba + 同义词库）")
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
