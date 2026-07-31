"""JD 匹配分析脚本。

读取 resume.yaml 和 JD 文本，提取关键词并交叉匹配，输出 JSON 报告。
"""

import argparse
import json
import re
import sys
from pathlib import Path

import yaml

SYNONYMS = [
    {"JS", "JavaScript", "ECMAScript"},
    {"TS", "TypeScript"},
    {"K8s", "Kubernetes"},
    {"Docker", "容器", "容器化"},
    {"MySQL", "关系型数据库", "RDBMS"},
    {"Redis", "缓存", "内存数据库"},
    {"React", "React.js", "ReactJS"},
    {"Vue", "Vue.js", "VueJS"},
    {"机器学习", "ML", "Machine Learning"},
    {"深度学习", "DL", "Deep Learning"},
    {"CI/CD", "持续集成", "持续部署"},
    {"微服务", "Microservice", "Microservices"},
    {"Go", "Golang"},
    {"Python", "Python3"},
    {"C++", "CPP"},
    {"PostgreSQL", "PG", "Postgres"},
    {"MongoDB", "Mongo"},
    {"Elasticsearch", "ES"},
    {"RabbitMQ", "MQ", "消息队列", "Kafka"},
    {"Nginx", "反向代理", "负载均衡"},
]

SOFT_SKILLS = {"沟通", "协作", "团队合作", "抗压", "自驱", "主动", "责任心", "学习能力", "表达能力"}

STOPWORDS = {
    "熟悉", "了解", "掌握", "精通", "熟练", "使用", "具备", "能够", "负责",
    "参与", "完成", "岗位要求", "任职资格", "工作职责", "职位描述", "加分项",
    "优先考虑", "工作内容", "基本要求", "技能要求", "必备条件", "有经验",
    "相关经验", "开发经验", "以上学历", "本科及以上", "硕士及以上",
    "年以上", "工作经验", "相关工作", "优先", "有较强", "有良好",
}

SECTION_WEIGHT = {
    "required": 2.0,
    "preferred": 1.0,
    "bonus": 0.5,
}


def normalize(text: str) -> str:
    return text.strip().lower()


def build_synonym_map() -> dict[str, str]:
    mapping = {}
    for group in SYNONYMS:
        canonical = sorted(group, key=len, reverse=True)[0]
        for word in group:
            mapping[normalize(word)] = normalize(canonical)
    return mapping


def extract_jd_keywords(jd_text: str) -> list[dict]:
    lines = jd_text.strip().splitlines()
    section = "required"
    keywords = []
    seen = set()

    bonus_patterns = re.compile(r"加分|优先|plus|preferred|bonus", re.IGNORECASE)
    required_patterns = re.compile(r"要求|资格|必备|must|required|任职", re.IGNORECASE)

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if bonus_patterns.search(stripped):
            section = "bonus"
        elif required_patterns.search(stripped):
            section = "required"

        tokens = re.findall(r"[A-Za-z][A-Za-z0-9+#/.]*|[\u4e00-\u9fff]{2,}", stripped)
        for token in tokens:
            norm = normalize(token)
            if norm in SOFT_SKILLS or norm in STOPWORDS or len(norm) < 2:
                continue
            if norm not in seen:
                seen.add(norm)
                keywords.append({
                    "keyword": token,
                    "section": section,
                    "weight": SECTION_WEIGHT.get(section, 1.0),
                })
            else:
                for kw in keywords:
                    if normalize(kw["keyword"]) == norm:
                        kw["weight"] += 0.5
                        break

    return keywords


def extract_resume_terms(resume: dict) -> set[str]:
    terms = set()

    for skill in resume.get("skills", []):
        for kw in skill.get("keywords", []):
            terms.add(normalize(kw))

    for proj in resume.get("projects", []):
        for tech in proj.get("tech", []):
            terms.add(normalize(tech))
        for h in proj.get("highlights", []):
            terms.add(normalize(h))

    for work in resume.get("work", []):
        for h in work.get("highlights", []):
            terms.add(normalize(h))

    for edu in resume.get("education", []):
        for c in edu.get("courses", []):
            terms.add(normalize(c))

    return terms


def match_keyword(keyword: str, resume_terms: set[str], synonym_map: dict[str, str]) -> bool:
    norm = normalize(keyword)
    canonical = synonym_map.get(norm, norm)

    for term in resume_terms:
        term_canonical = synonym_map.get(term, term)
        if canonical == term_canonical:
            return True
        if canonical in term or term in canonical:
            return True

    return False


def run(resume_path: str, jd_path: str) -> dict:
    with open(resume_path, "r", encoding="utf-8") as f:
        resume = yaml.safe_load(f)

    with open(jd_path, "r", encoding="utf-8") as f:
        jd_text = f.read()

    synonym_map = build_synonym_map()
    jd_keywords = extract_jd_keywords(jd_text)
    resume_terms = extract_resume_terms(resume)

    covered = []
    missing = []

    for kw in jd_keywords:
        if match_keyword(kw["keyword"], resume_terms, synonym_map):
            covered.append(kw)
        else:
            missing.append(kw)

    missing.sort(key=lambda x: x["weight"], reverse=True)

    total = len(jd_keywords)
    coverage = len(covered) / total if total > 0 else 0

    return {
        "total_keywords": total,
        "covered_count": len(covered),
        "missing_count": len(missing),
        "coverage_percent": round(coverage * 100, 1),
        "covered": covered,
        "missing": missing,
    }


def main():
    parser = argparse.ArgumentParser(description="JD 关键词匹配分析")
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
