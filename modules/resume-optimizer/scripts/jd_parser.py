"""JD 解析器：把原始 JD 文本清洗 + 结构化为标准格式。

管道：
  原始文本 → 噪音清洗 → 段落识别 → 需求拆解 → 需求分类 → 重要度标注 → 质量评分

输出结构化 JD JSON，供 jd_match.py 消费。

Usage:
    python3 scripts/jd_parser.py <jd.txt>
"""

import argparse
import json
import re
import sys
from pathlib import Path

import yaml

SKILL_DIR = Path(__file__).resolve().parent.parent
CONCEPTS_PATH = SKILL_DIR / "assets" / "concepts.yaml"
SYNONYMS_PATH = SKILL_DIR / "assets" / "synonyms.yaml"

# ─── 段落识别正则 ───
SECTION_PATTERNS = {
    "responsibilities": re.compile(
        r"岗位职责|工作职责|工作内容|职位描述|职责描述|你需要做|你将负责|What you.*do",
        re.IGNORECASE
    ),
    "requirements": re.compile(
        r"任职要求|岗位要求|任职资格|必备条件|任职条件|职位要求|我们希望你|要求.*|Required|Requirements|Must have",
        re.IGNORECASE
    ),
    "bonus": re.compile(
        r"加分项|优先考虑|加分条件|Nice to have|Preferred|Bonus|Plus|优先",
        re.IGNORECASE
    ),
    "salary": re.compile(
        r"薪资|薪酬|待遇|福利|上班时间|工作时间|休假|补贴|五险一金|住房公积金|stock|equity|compensation",
        re.IGNORECASE
    ),
    "company_intro": re.compile(
        r"公司介绍|关于我们|公司简介|我们是谁|公司概况|About us|Who we are",
        re.IGNORECASE
    ),
}

# 噪音行模式（要过滤掉的）
NOISE_PATTERNS = [
    re.compile(r"^(投递|简历|欢迎|期待|加入|点击|联系|邮箱|电话|微信|QQ|地址|交通|地铁|公交)"),
    re.compile(r"^(http|https|www\.|mailto:)"),
    re.compile(r"^\s*$"),  # 空行
    re.compile(r"^\s*[-—–]+\s*$"),  # 分隔线
    re.compile(r"^\s*[📌📍🏢💰📈🎉🚀💡⭐✨🔥]\s*"),  # emoji 开头
]

# ─── 需求分类规则 ───
EXPERIENCE_PATTERN = re.compile(r"(\d+)\s*年|年以上|经验|工作经历")
EDUCATION_PATTERN = re.compile(r"本科|硕士|博士|学历|学位|Bachelor|Master|PhD|本科及以上|硕士及以上")
CERTIFICATION_PATTERN = re.compile(r"PMP|CPA|CFA|CCIE|HCIE|RHCE|AWS|Azure|认证|证书|资格证")

# 学历映射
DEGREE_MAP = {
    "大专": 1, "专科": 1, "大专及以上": 1,
    "本科": 2, "本科及以上": 2, "bachelor": 2,
    "硕士": 3, "硕士及以上": 3, "master": 3,
    "博士": 4, "phd": 4, "博士及以上": 4,
}


def load_concepts() -> list[dict]:
    """加载概念映射库。"""
    if not CONCEPTS_PATH.exists():
        return []
    with CONCEPTS_PATH.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or []


def load_synonyms() -> dict[str, str]:
    """加载同义词库。"""
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


def clean_noise(lines: list[str]) -> list[str]:
    """过滤噪音行。"""
    cleaned = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        is_noise = any(p.search(stripped) for p in NOISE_PATTERNS)
        if not is_noise:
            cleaned.append(stripped)
    return cleaned


def detect_section(line: str) -> str | None:
    """检测行属于哪个段落。"""
    for section, pattern in SECTION_PATTERNS.items():
        if pattern.search(line):
            return section
    return None


def split_into_sections(lines: list[str]) -> dict[str, list[str]]:
    """把 JD 文本按段落分组。"""
    sections = {"unclassified": []}
    current = "unclassified"

    for line in lines:
        detected = detect_section(line)
        if detected:
            current = detected
            sections.setdefault(current, [])
            # 如果这一行除了段落标题还有内容，也加入
            remainder = SECTION_PATTERNS[current].sub("", line).strip()
            if remainder and len(remainder) > 3:
                sections[current].append(remainder)
        else:
            sections.setdefault(current, [])
            sections[current].append(line)

    return sections


def split_requirements(section_lines: list[str]) -> list[str]:
    """把段落内容拆成独立需求条目。

    支持：数字编号、bullet 符号、分号分隔、换行分隔。
    """
    items = []
    current_item = ""

    for line in section_lines:
        # 去掉行首编号和 bullet 符号
        stripped = re.sub(r"^[\d]+[.、)\]]\s*", "", line)
        stripped = re.sub(r"^[•·\-\*●▪◦]\s*", "", stripped)

        # 如果是独立短行（编号项），作为新条目
        if len(stripped) < 80 and not stripped.endswith("，"):
            if current_item:
                items.append(current_item.strip())
            current_item = stripped
        else:
            # 长行或以逗号结尾的行，追加到当前条目
            current_item = (current_item + " " + stripped).strip() if current_item else stripped

        # 分号分隔
        if "；" in current_item or ";" in current_item:
            parts = re.split(r"[；;]", current_item)
            items.extend(p.strip() for p in parts if p.strip())
            current_item = ""

    if current_item:
        items.append(current_item.strip())

    # 过滤太短的
    return [item for item in items if len(item) >= 3]


def classify_requirement(text: str) -> dict:
    """对单个需求条目进行分类。

    返回 {type, value, raw}：
    - type: skill / experience / education / certification / soft_skill / other
    - value: 提取的具体值（年限/学历等级等）
    - raw: 原始文本
    """
    text_lower = text.lower()

    # 经验年限
    exp_match = EXPERIENCE_PATTERN.search(text)
    if exp_match and "年" in text:
        years = 0
        num_match = re.search(r"(\d+)\s*年", text)
        if num_match:
            years = int(num_match.group(1))
        return {"type": "experience", "value": years, "raw": text}

    # 学历
    if EDUCATION_PATTERN.search(text):
        degree_level = 0
        for degree, level in DEGREE_MAP.items():
            if degree.lower() in text_lower:
                degree_level = max(degree_level, level)
        return {"type": "education", "value": degree_level, "raw": text}

    # 证书
    if CERTIFICATION_PATTERN.search(text):
        cert_match = re.search(r"(PMP|CPA|CFA|CCIE|HCIE|RHCE|AWS[^ ]*|Azure[^ ]*)", text, re.IGNORECASE)
        cert = cert_match.group(1) if cert_match else "certification"
        return {"type": "certification", "value": cert, "raw": text}

    # 软技能（关键词检测）
    soft_keywords = ["沟通", "协作", "团队", "抗压", "自驱", "主动", "责任心", "学习能力", "表达能力"]
    if any(kw in text for kw in soft_keywords) and not re.search(r"[A-Za-z]{3,}", text):
        return {"type": "soft_skill", "value": text, "raw": text}

    # 默认：技能/领域知识
    return {"type": "skill", "value": text, "raw": text}


def determine_importance(section: str, text: str, occurrence_count: int = 1) -> str:
    """确定需求重要度。

    返回：must_have / nice_to_have / implicit
    """
    if section == "bonus":
        return "nice_to_have"
    if section == "requirements":
        return "must_have"
    if section == "unclassified":
        # 未分类的，根据是否有"优先"等词判断
        if re.search(r"优先|加分|preferred|plus|bonus", text, re.IGNORECASE):
            return "nice_to_have"
        return "must_have"
    # 职责描述中的隐含要求
    return "implicit"


def extract_keywords_from_text(text: str, synonym_map: dict[str, str]) -> list[str]:
    """从需求条目中提取关键词（用于后续匹配）。"""
    en_pattern = re.compile(r"[A-Za-z][A-Za-z0-9+#./_-]{1,}")
    zh_pattern = re.compile(r"[\u4e00-\u9fff]{2,}")

    keywords = []
    keywords.extend(en_pattern.findall(text))
    keywords.extend(zh_pattern.findall(text))

    # 归并同义词
    canonicals = []
    for kw in keywords:
        norm = kw.strip().lower()
        canonical = synonym_map.get(norm, norm)
        if canonical not in canonicals and len(canonical) >= 2:
            canonicals.append(canonical)

    return canonicals


def check_concept_match(text: str, concepts: list[dict]) -> list[str]:
    """检查需求条目中是否包含概念词，返回匹配的概念列表。"""
    matched = []
    for concept in concepts:
        concept_name = concept.get("concept", "")
        related = concept.get("related", [])
        # 检查概念名本身
        if concept_name in text:
            matched.append(concept_name)
            continue
        # 检查关联词
        for r in related:
            if isinstance(r, str) and r.lower() in text.lower():
                matched.append(concept_name)
                break
    return matched


def score_jd_quality(parsed: dict) -> dict:
    """给解析后的 JD 打质量分。"""
    issues = []
    score = 100

    requirements = parsed.get("requirements", [])
    total_reqs = len(requirements)

    # 检查项数
    if total_reqs < 3:
        issues.append("要求条目过少（<3），JD 可能不完整")
        score -= 20
    elif total_reqs < 5:
        issues.append("要求条目偏少（<5），可能有遗漏")
        score -= 10

    # 检查是否有技术要求
    skill_reqs = [r for r in requirements if r["type"] == "skill"]
    if len(skill_reqs) == 0:
        issues.append("未检测到明确的技术技能要求")
        score -= 15

    # 检查是否有经验要求
    exp_reqs = [r for r in requirements if r["type"] == "experience"]
    if len(exp_reqs) == 0:
        issues.append("未检测到年限要求")
        score -= 5

    # 检查模糊要求占比
    vague_words = ["熟悉", "了解", "掌握", "精通", "良好", "较强"]
    vague_count = sum(1 for r in requirements if any(v in r["raw"] for v in vague_words))
    if total_reqs > 0 and vague_count / total_reqs > 0.7:
        issues.append(f"模糊要求占比过高（{vague_count}/{total_reqs}），JD 质量偏低")
        score -= 15

    score = max(0, score)
    return {"score": score, "issues": issues, "total_requirements": total_reqs}


def parse_jd(jd_text: str) -> dict:
    """完整 JD 解析管道。"""
    synonym_map = load_synonyms()
    concepts = load_concepts()

    # ① 噪音清洗
    lines = jd_text.strip().splitlines()
    cleaned = clean_noise(lines)

    # ② 段落识别
    sections = split_into_sections(cleaned)

    # ③④⑤ 需求拆解 + 分类 + 重要度
    all_requirements = []
    for section_name, section_lines in sections.items():
        if section_name in ("salary", "company_intro"):
            continue
        items = split_requirements(section_lines)
        for item in items:
            classified = classify_requirement(item)
            importance = determine_importance(section_name, item)
            keywords = extract_keywords_from_text(item, synonym_map)
            concept_matches = check_concept_match(item, concepts)
            all_requirements.append({
                "raw": item,
                "section": section_name,
                "type": classified["type"],
                "value": classified["value"],
                "importance": importance,
                "keywords": keywords,
                "concepts": concept_matches,
            })

    # 提取职位信息
    title = ""
    company = ""
    for line in cleaned[:5]:
        if not title and re.search(r"工程师|开发|架构师|产品经理|设计师|分析师|经理|总监|实习|算法|前端|后端|全栈|运营", line):
            title = line[:50]

    # ⑥ 质量评分
    quality = score_jd_quality({"requirements": all_requirements})

    return {
        "title": title,
        "company": company,
        "sections": {k: v for k, v in sections.items() if k not in ("salary", "company_intro")},
        "requirements": all_requirements,
        "quality": quality,
        "stats": {
            "total": len(all_requirements),
            "by_type": _count_by(all_requirements, "type"),
            "by_importance": _count_by(all_requirements, "importance"),
        },
    }


def _count_by(items: list[dict], key: str) -> dict:
    counts = {}
    for item in items:
        val = item.get(key, "unknown")
        counts[val] = counts.get(val, 0) + 1
    return counts


def main():
    parser = argparse.ArgumentParser(description="JD 解析器：清洗 + 结构化 + 质量评分")
    parser.add_argument("jd", help="JD 文本文件路径")
    parser.add_argument("--out", default=None, help="输出 JSON 路径（默认打印到 stdout）")
    args = parser.parse_args()

    jd_path = Path(args.jd)
    if not jd_path.exists():
        print(f"错误：JD 文件不存在 {jd_path}", file=sys.stderr)
        sys.exit(1)

    jd_text = jd_path.read_text(encoding="utf-8")
    result = parse_jd(jd_text)

    if args.out:
        Path(args.out).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"✅ JD 解析结果已保存：{args.out}")
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
