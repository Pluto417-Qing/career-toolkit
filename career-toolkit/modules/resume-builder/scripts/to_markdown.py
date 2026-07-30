#!/usr/bin/env python3
"""Convert resume.yaml to Markdown suitable for Feishu doc publishing.

Usage:
    python3 scripts/to_markdown.py <resume.yaml> [--out-dir ./out]

Output:
    <out-dir>/resume.md
"""

import argparse
import sys
from pathlib import Path

import yaml


def load_yaml(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _fmt_date_range(item: dict) -> str:
    start = item.get("start", "")
    end = item.get("end", "至今")
    if not start:
        return ""
    return f"{start} – {end}"


def _section_header(title: str) -> str:
    return f"\n## {title}\n"


def render_basics(data: dict) -> str:
    b = data.get("basics", {})
    if not b:
        return ""
    lines = [f"# {b.get('name', '')}"]
    if b.get("english_name"):
        lines[0] += f" ({b['english_name']})"
    if b.get("label"):
        lines.append(f"\n**{b['label']}**")

    contact_parts = []
    if b.get("phone"):
        contact_parts.append(f"📞 {b['phone']}")
    if b.get("email"):
        contact_parts.append(f"✉️ {b['email']}")
    if b.get("location"):
        contact_parts.append(f"📍 {b['location']}")
    if b.get("website"):
        contact_parts.append(f"🔗 {b['website']}")
    if contact_parts:
        lines.append("\n" + " | ".join(contact_parts))

    profiles = b.get("profiles", [])
    if profiles:
        profile_strs = [f"[{p.get('network', '')}]({p.get('url', '')})" for p in profiles]
        lines.append(" · ".join(profile_strs))

    if b.get("summary"):
        lines.append(f"\n> {b['summary']}")

    return "\n".join(lines)


def render_education(data: dict) -> str:
    items = data.get("education", [])
    if not items:
        return ""
    lines = [_section_header("教育经历")]
    for item in items:
        title = item.get("institution", "")
        if item.get("area"):
            title += f" · {item['area']}"
        if item.get("degree"):
            title += f" · {item['degree']}"
        date_str = _fmt_date_range(item)
        lines.append(f"### {title}")
        meta_parts = []
        if date_str:
            meta_parts.append(date_str)
        if item.get("gpa"):
            meta_parts.append(f"GPA {item['gpa']}")
        if item.get("rank"):
            meta_parts.append(f"排名 {item['rank']}")
        if meta_parts:
            lines.append(" | ".join(meta_parts))
        for h in item.get("highlights", []):
            lines.append(f"- {h}")
        lines.append("")
    return "\n".join(lines)


def render_work(data: dict) -> str:
    items = data.get("work", [])
    if not items:
        return ""
    lines = [_section_header("工作/实习经历")]
    for item in items:
        title = item.get("organization", "")
        if item.get("position"):
            title += f" · {item['position']}"
        lines.append(f"### {title}")
        meta_parts = []
        date_str = _fmt_date_range(item)
        if date_str:
            meta_parts.append(date_str)
        if item.get("type"):
            meta_parts.append(item["type"])
        if item.get("location"):
            meta_parts.append(item["location"])
        if meta_parts:
            lines.append(" | ".join(meta_parts))
        if item.get("summary"):
            lines.append(f"\n{item['summary']}")
        for h in item.get("highlights", []):
            lines.append(f"- {h}")
        lines.append("")
    return "\n".join(lines)


def render_projects(data: dict) -> str:
    items = data.get("projects", [])
    if not items:
        return ""
    lines = [_section_header("项目经历")]
    for item in items:
        title = item.get("name", "")
        if item.get("role"):
            title += f" · {item['role']}"
        lines.append(f"### {title}")
        meta_parts = []
        date_str = _fmt_date_range(item)
        if date_str:
            meta_parts.append(date_str)
        if item.get("tech"):
            meta_parts.append("技术栈: " + ", ".join(item["tech"]))
        if meta_parts:
            lines.append(" | ".join(meta_parts))
        if item.get("url"):
            lines.append(f"链接: {item['url']}")
        if item.get("summary"):
            lines.append(f"\n{item['summary']}")
        for h in item.get("highlights", []):
            lines.append(f"- {h}")
        lines.append("")
    return "\n".join(lines)


def render_research(data: dict) -> str:
    items = data.get("research", [])
    if not items:
        return ""
    lines = [_section_header("科研经历")]
    for item in items:
        title = item.get("institution", item.get("name", ""))
        if item.get("position"):
            title += f" · {item['position']}"
        lines.append(f"### {title}")
        date_str = _fmt_date_range(item)
        if date_str:
            lines.append(date_str)
        if item.get("summary"):
            lines.append(f"\n{item['summary']}")
        for h in item.get("highlights", []):
            lines.append(f"- {h}")
        lines.append("")
    return "\n".join(lines)


def render_skills(data: dict) -> str:
    items = data.get("skills", [])
    if not items:
        return ""
    lines = [_section_header("技能")]
    for item in items:
        name = item.get("name", "")
        keywords = item.get("keywords", [])
        lines.append(f"- **{name}**：{', '.join(keywords)}")
    lines.append("")
    return "\n".join(lines)


def render_awards(data: dict) -> str:
    items = data.get("awards", [])
    if not items:
        return ""
    lines = [_section_header("荣誉奖项")]
    for item in items:
        title = item.get("title", "")
        parts = [f"**{title}**"]
        if item.get("awarder"):
            parts.append(item["awarder"])
        if item.get("date"):
            parts.append(item["date"])
        lines.append(f"- {' · '.join(parts)}")
    lines.append("")
    return "\n".join(lines)


def render_publications(data: dict) -> str:
    items = data.get("publications", [])
    if not items:
        return ""
    lines = [_section_header("发表论文")]
    for item in items:
        title = item.get("name", item.get("title", ""))
        parts = [f"**{title}**"]
        if item.get("publisher"):
            parts.append(item["publisher"])
        if item.get("date"):
            parts.append(item["date"])
        lines.append(f"- {' · '.join(parts)}")
    lines.append("")
    return "\n".join(lines)


def render_languages(data: dict) -> str:
    items = data.get("languages", [])
    if not items:
        return ""
    lines = [_section_header("语言能力")]
    for item in items:
        lang = item.get("language", "")
        parts = [lang]
        if item.get("level"):
            parts.append(item["level"])
        if item.get("score"):
            parts.append(f"成绩 {item['score']}")
        lines.append(f"- {' · '.join(parts)}")
    lines.append("")
    return "\n".join(lines)


def render_activities(data: dict) -> str:
    items = data.get("activities", [])
    if not items:
        return ""
    lines = [_section_header("社会活动")]
    for item in items:
        title = item.get("organization", item.get("name", ""))
        if item.get("position"):
            title += f" · {item['position']}"
        lines.append(f"### {title}")
        date_str = _fmt_date_range(item)
        if date_str:
            lines.append(date_str)
        for h in item.get("highlights", []):
            lines.append(f"- {h}")
        lines.append("")
    return "\n".join(lines)


def render_custom_sections(data: dict) -> str:
    items = data.get("custom_sections", [])
    if not items:
        return ""
    lines = []
    for section in items:
        lines.append(_section_header(section.get("title", "其他")))
        for item in section.get("items", []):
            if item.get("heading"):
                lines.append(f"### {item['heading']}")
            if item.get("subheading"):
                lines.append(item["subheading"])
            if item.get("summary"):
                lines.append(item["summary"])
            for h in item.get("highlights", []):
                lines.append(f"- {h}")
        lines.append("")
    return "\n".join(lines)


def to_markdown(data: dict) -> str:
    sections = [
        render_basics(data),
        render_education(data),
        render_work(data),
        render_projects(data),
        render_research(data),
        render_skills(data),
        render_awards(data),
        render_publications(data),
        render_languages(data),
        render_activities(data),
        render_custom_sections(data),
    ]
    return "\n".join(s for s in sections if s).strip() + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("resume", help="path to resume.yaml")
    ap.add_argument("--out-dir", default="./out", help="output directory")
    args = ap.parse_args()

    resume_path = Path(args.resume).resolve()
    if not resume_path.exists():
        print(f"❌ resume file not found: {resume_path}", file=sys.stderr)
        return 2

    data = load_yaml(resume_path)
    out_dir = Path(args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    md_path = out_dir / "resume.md"
    md_path.write_text(to_markdown(data), encoding="utf-8")
    print(f"✅ Markdown written: {md_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
