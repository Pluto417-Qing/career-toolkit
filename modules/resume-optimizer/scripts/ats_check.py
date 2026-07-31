"""中文 ATS 合规检查脚本。

读取 resume.yaml，逐项检查 ATS 合规性，输出 JSON 报告。
"""

import argparse
import json
import re
import sys
from pathlib import Path

import yaml

PHONE_PATTERN = re.compile(r"^1[3-9]\d{9}$")
EMAIL_PATTERN = re.compile(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$")
DATE_YYYY_MM_DOT = re.compile(r"^\d{4}\.\d{2}$")
DATE_YYYY_MM_DASH = re.compile(r"^\d{4}-\d{2}$")
DATE_CHINESE = re.compile(r"\d{4}年\d{1,2}月")
SENSITIVE_FIELDS = {"身份证", "身份证号", "家庭住址", "家庭地址", "婚姻", "政治面貌"}
ABBREVIATION_PATTERNS = [
    (re.compile(r"北邮"), "北京邮电大学"),
    (re.compile(r"清华"), "清华大学"),
    (re.compile(r"北大"), "北京大学"),
    (re.compile(r"浙大"), "浙江大学"),
    (re.compile(r"上交"), "上海交通大学"),
    (re.compile(r"哈工大"), "哈尔滨工业大学"),
    (re.compile(r"华科"), "华中科技大学"),
    (re.compile(r"中科大"), "中国科学技术大学"),
    (re.compile(r"南大"), "南京大学"),
    (re.compile(r"武大"), "武汉大学"),
]


def check(rule_id: str, name: str, passed: bool, severity: str, detail: str = "", fix: str = "") -> dict:
    return {
        "rule_id": rule_id,
        "name": name,
        "status": "pass" if passed else ("fail" if severity == "fatal" else "warn"),
        "severity": severity,
        "detail": detail,
        "fix": fix,
    }


def collect_dates(resume: dict) -> list[tuple[str, str]]:
    dates = []
    for section in ("education", "work", "projects", "research", "activities"):
        for i, entry in enumerate(resume.get(section, []) or []):
            for field in ("start", "end"):
                val = entry.get(field)
                if val and val != "至今":
                    dates.append((f"{section}[{i}].{field}", val))
    return dates


def detect_date_format(date_str: str) -> str:
    if DATE_YYYY_MM_DOT.match(date_str):
        return "YYYY.MM"
    if DATE_YYYY_MM_DASH.match(date_str):
        return "YYYY-MM"
    if DATE_CHINESE.match(date_str):
        return "YYYY年MM月"
    return "other"


def check_time_order(entries: list[dict]) -> bool:
    starts = []
    for entry in entries:
        s = entry.get("start", "")
        if s:
            norm = s.replace(".", "").replace("-", "").replace("年", "").replace("月", "")
            starts.append(norm)
    for i in range(len(starts) - 1):
        if starts[i] < starts[i + 1]:
            return False
    return True


def run(resume_path: str) -> dict:
    with open(resume_path, "r", encoding="utf-8") as f:
        resume = yaml.safe_load(f)

    results = []
    basics = resume.get("basics", {})

    # 1.1 姓名
    results.append(check("1.1", "姓名字段", bool(basics.get("name")), "fatal",
                         "" if basics.get("name") else "basics.name 为空"))

    # 1.2 手机号
    phone = basics.get("phone", "")
    phone_clean = re.sub(r"[\s\-]", "", phone) if phone else ""
    results.append(check("1.2", "手机号格式", bool(PHONE_PATTERN.match(phone_clean)), "fatal",
                         f"当前值: {phone}" if phone else "未填写手机号",
                         "填写 11 位手机号，不含空格和横线"))

    # 1.3 邮箱
    email = basics.get("email", "")
    results.append(check("1.3", "邮箱格式", bool(EMAIL_PATTERN.match(email)) if email else False, "warn",
                         f"当前值: {email}" if email else "未填写邮箱"))

    # 1.4 求职意向
    results.append(check("1.4", "求职意向", bool(basics.get("label")), "warn",
                         "" if basics.get("label") else "basics.label 为空，建议填写目标岗位"))

    # 1.5 教育经历
    edu = resume.get("education", []) or []
    edu_valid = any(e.get("institution") and e.get("degree") for e in edu)
    results.append(check("1.5", "教育经历完整", edu_valid, "fatal",
                         "" if edu_valid else "缺少教育经历或缺少 institution/degree"))

    # 1.6 名称全称
    for section in ("education", "work"):
        for i, entry in enumerate(resume.get(section, []) or []):
            name_field = entry.get("institution") or entry.get("organization") or ""
            for pattern, full_name in ABBREVIATION_PATTERNS:
                if pattern.search(name_field) and full_name not in name_field:
                    results.append(check("1.6", "名称使用全称", False, "warn",
                                         f'{section}[{i}] "{name_field}" 疑似缩写',
                                         f"建议改为完整名称，如 {full_name}"))
                    break

    # 2.1 时间格式统一
    dates = collect_dates(resume)
    if dates:
        formats = set(detect_date_format(d[1]) for d in dates)
        unified = len(formats) <= 1
        results.append(check("2.1", "时间格式统一", unified, "fatal",
                             f"存在多种格式: {formats}" if not unified else "",
                             "统一使用 YYYY.MM 或 YYYY-MM"))

        # 2.2 推荐格式
        has_chinese_date = any(detect_date_format(d[1]) == "YYYY年MM月" for d in dates)
        results.append(check("2.2", "时间格式推荐", not has_chinese_date, "warn",
                             "使用了'年/月'汉字格式" if has_chinese_date else "",
                             "改用 YYYY.MM 格式，ATS 解析更稳定"))

    # 2.4 倒序排列
    for section in ("education", "work"):
        entries = resume.get(section, []) or []
        if len(entries) > 1:
            ordered = check_time_order(entries)
            results.append(check("2.4", f"{section} 倒序排列", ordered, "warn",
                                 f"{section} 未按时间倒序" if not ordered else ""))

    # 4.1 敏感信息
    full_text = json.dumps(resume, ensure_ascii=False)
    has_sensitive = any(s in full_text for s in SENSITIVE_FIELDS)
    id_card = bool(re.search(r"\d{17}[\dXx]", full_text))
    results.append(check("4.1", "无敏感信息", not (has_sensitive or id_card), "warn",
                         "检测到可能的敏感信息（身份证号/家庭地址/婚姻/政治面貌）" if (has_sensitive or id_card) else ""))

    # 4.3 技能等级
    for skill in resume.get("skills", []) or []:
        if skill.get("level") and "精通" in skill.get("level", ""):
            results.append(check("4.3", "技能等级用词", False, "warn",
                                 f'skills "{skill["name"]}" 使用了"精通"',
                                 '除非确实顶级水平，建议改为"熟练"'))

    # 4.4 highlights 非空
    for section in ("work", "projects"):
        for i, entry in enumerate(resume.get(section, []) or []):
            hl = entry.get("highlights", []) or []
            entry_name = entry.get("organization") or entry.get("name") or f"{section}[{i}]"
            if not hl:
                results.append(check("4.4", "经历有 highlights", False, "warn",
                                     f'{section}[{i}] "{entry_name}" 无 highlights',
                                     "至少添加 1-2 条成果描述"))

    # Summary
    total = len(results)
    pass_count = sum(1 for r in results if r["status"] == "pass")
    warn_count = sum(1 for r in results if r["status"] == "warn")
    fail_count = sum(1 for r in results if r["status"] == "fail")

    return {
        "total": total,
        "pass": pass_count,
        "warn": warn_count,
        "fail": fail_count,
        "results": results,
    }


def main():
    parser = argparse.ArgumentParser(description="中文 ATS 合规检查")
    parser.add_argument("resume", help="resume.yaml 路径")
    args = parser.parse_args()

    if not Path(args.resume).exists():
        print(f"错误：简历文件不存在 {args.resume}", file=sys.stderr)
        sys.exit(1)

    result = run(args.resume)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
