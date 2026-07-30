#!/usr/bin/env python3
"""Render resume.yaml into HTML (and optionally PDF).

Usage:
    python3 scripts/render.py <resume.yaml> [--theme classic] [--out-dir ./out] [--pdf]

Outputs:
    <out-dir>/resume.html
    <out-dir>/resume.pdf   (only if --pdf)
    <out-dir>/resume.json  (JSON Resume compatible mirror)
"""

import argparse
import json
import sys
from pathlib import Path

import yaml
from jinja2 import Environment, FileSystemLoader, select_autoescape

SKILL_DIR = Path(__file__).resolve().parent.parent
THEMES_DIR = SKILL_DIR / "assets" / "themes"


def load_yaml(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def render_html(data: dict, theme: str) -> str:
    theme_dir = THEMES_DIR / theme
    if not (theme_dir / "template.html.j2").exists():
        raise SystemExit(f"❌ Theme not found: {theme_dir}")
    env = Environment(
        loader=FileSystemLoader(str(theme_dir)),
        autoescape=select_autoescape(["html", "xml"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    tmpl = env.get_template("template.html.j2")
    return tmpl.render(data=data)


def to_pdf(html: str, out_path: Path, base_url: Path) -> None:
    try:
        from weasyprint import HTML
    except ImportError as e:
        raise SystemExit("❌ weasyprint not installed. Run: pip install weasyprint") from e
    HTML(string=html, base_url=str(base_url)).write_pdf(str(out_path))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("resume", help="path to resume.yaml")
    ap.add_argument("--theme", default=None, help="theme name (default: from data.meta.theme or 'classic')")
    ap.add_argument("--out-dir", default="./out", help="output directory")
    ap.add_argument("--pdf", action="store_true", help="also render PDF via WeasyPrint")
    ap.add_argument("--markdown", action="store_true", help="also render Markdown (for Feishu doc publishing)")
    args = ap.parse_args()

    resume_path = Path(args.resume).resolve()
    if not resume_path.exists():
        print(f"❌ resume file not found: {resume_path}", file=sys.stderr)
        return 2

    data = load_yaml(resume_path)
    theme = args.theme or (data.get("meta") or {}).get("theme") or "classic"

    out_dir = Path(args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    html = render_html(data, theme)
    html_path = out_dir / "resume.html"
    html_path.write_text(html, encoding="utf-8")
    print(f"✅ HTML written: {html_path}")

    # Also mirror data as JSON (JSON Resume-compatible superset)
    json_path = out_dir / "resume.json"
    json_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✅ JSON written: {json_path}")

    if args.pdf:
        pdf_path = out_dir / "resume.pdf"
        to_pdf(html, pdf_path, base_url=THEMES_DIR / theme)
        print(f"✅ PDF written:  {pdf_path}")

    if args.markdown:
        from to_markdown import to_markdown
        md_path = out_dir / "resume.md"
        md_path.write_text(to_markdown(data), encoding="utf-8")
        print(f"✅ Markdown written: {md_path}")

    print(f"\n👉 在浏览器打开预览：file://{html_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
