#!/usr/bin/env python3
"""Generate PNG screenshots for all resume preview HTML files.

Usage:
    python3 scripts/generate_previews.py

Requires: playwright (pip install playwright && playwright install chromium)
"""

import sys
from pathlib import Path

PREVIEW_DIR = Path(__file__).resolve().parent.parent / "modules" / "resume-builder" / "out" / "preview"
VIEWPORT = {"width": 800, "height": 1130}
DEVICE_SCALE_FACTOR = 3


def main() -> int:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("❌ playwright not installed. Run: pip install playwright && playwright install chromium")
        return 1

    html_files = sorted(PREVIEW_DIR.glob("*/resume.html"))
    if not html_files:
        print("⚠️  No resume.html files found in", PREVIEW_DIR)
        return 0

    print(f"📸 Generating {len(html_files)} screenshots...")

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport=VIEWPORT, device_scale_factor=DEVICE_SCALE_FACTOR)

        for html_path in html_files:
            png_path = html_path.with_suffix(".png")
            file_url = f"file://{html_path}"
            page.goto(file_url, wait_until="networkidle")
            page.screenshot(path=str(png_path), full_page=False)
            print(f"  ✅ {png_path.relative_to(PREVIEW_DIR)}")

        browser.close()

    print(f"\n🎉 Done. {len(html_files)} screenshots saved.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
