#!/usr/bin/env python3
"""Render career plan as a consultant-style HTML with RIASEC radar + 12-month timeline.

Usage:
    python3 scripts/render_plan_visual.py <career_plan.yaml> [--out <output.html>]

Input: career_plan.yaml containing:
    meta:       name, goal, target, holland_code, generated
    riasec:     R/I/A/S/E/C scores (0-100)
    milestones: list of {month, label, category, details}

Output: Self-contained HTML suitable for lark-htmlbox embedding or browser viewing.
"""

import argparse
import html
import json
import sys
from pathlib import Path

import yaml

CATEGORY_COLORS = {
    "prep": "#3B82F6",
    "action": "#F59E0B",
    "decision": "#10B981",
    "growth": "#8B5CF6",
    "academic": "#6B7280",
}

CATEGORY_LABELS = {
    "prep": "准备",
    "action": "行动",
    "decision": "决策",
    "growth": "成长",
    "academic": "学业",
}

RIASEC_LABELS = {
    "R": "现实型 Realistic",
    "I": "研究型 Investigative",
    "A": "艺术型 Artistic",
    "S": "社会型 Social",
    "E": "企业型 Enterprising",
    "C": "常规型 Conventional",
}


def build_html(plan: dict) -> str:
    meta = plan["meta"]
    riasec = plan["riasec"]
    milestones = plan["milestones"]

    dims = ["R", "I", "A", "S", "E", "C"]
    radar_labels = json.dumps([RIASEC_LABELS[d] for d in dims], ensure_ascii=False)
    radar_data = json.dumps([riasec.get(d, 0) for d in dims])

    timeline_html = _build_timeline(milestones)
    legend_html = _build_legend()

    name = html.escape(str(meta.get("name", "")))
    goal = html.escape(str(meta.get("goal", "")))
    target = html.escape(str(meta.get("target", "")))
    code = html.escape(str(meta.get("holland_code", "")))
    date = html.escape(str(meta.get("generated", "")))

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>职业规划报告 - {name}</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans SC", sans-serif;
  background: #f8fafc;
  color: #1e293b;
  line-height: 1.6;
  padding: 40px 20px;
}}
.container {{
  max-width: 900px;
  margin: 0 auto;
  background: #fff;
  border-radius: 16px;
  box-shadow: 0 4px 24px rgba(0,0,0,0.06);
  overflow: hidden;
}}
.header {{
  background: linear-gradient(135deg, #1e40af 0%, #7c3aed 100%);
  color: #fff;
  padding: 40px 48px;
}}
.header h1 {{
  font-size: 28px;
  font-weight: 700;
  margin-bottom: 8px;
}}
.header .subtitle {{
  font-size: 15px;
  opacity: 0.85;
}}
.header .meta-row {{
  display: flex;
  gap: 24px;
  margin-top: 16px;
  font-size: 13px;
  opacity: 0.75;
}}
.content {{
  padding: 48px;
}}
.section-title {{
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 24px;
  padding-left: 12px;
  border-left: 4px solid #7c3aed;
}}
.radar-section {{
  display: flex;
  align-items: center;
  gap: 40px;
  margin-bottom: 56px;
}}
.radar-chart {{
  flex: 0 0 340px;
  height: 300px;
}}
.radar-insight {{
  flex: 1;
}}
.radar-insight .code-badge {{
  display: inline-block;
  background: linear-gradient(135deg, #7c3aed, #3b82f6);
  color: #fff;
  padding: 6px 16px;
  border-radius: 20px;
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 16px;
}}
.radar-insight p {{
  font-size: 14px;
  color: #475569;
  margin-bottom: 8px;
}}
.timeline-section {{
  margin-top: 16px;
}}
.timeline {{
  position: relative;
  padding: 20px 0;
}}
.timeline::before {{
  content: "";
  position: absolute;
  left: 28px;
  top: 0;
  bottom: 0;
  width: 3px;
  background: #e2e8f0;
  border-radius: 2px;
}}
.tl-item {{
  position: relative;
  padding-left: 64px;
  margin-bottom: 28px;
}}
.tl-item:last-child {{ margin-bottom: 0; }}
.tl-dot {{
  position: absolute;
  left: 20px;
  top: 4px;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  border: 3px solid #fff;
  box-shadow: 0 0 0 3px currentColor;
  background: currentColor;
}}
.tl-month {{
  font-size: 12px;
  font-weight: 700;
  color: #94a3b8;
  text-transform: uppercase;
  margin-bottom: 2px;
}}
.tl-label {{
  font-size: 15px;
  font-weight: 600;
  color: #1e293b;
  margin-bottom: 4px;
}}
.tl-details {{
  font-size: 13px;
  color: #64748b;
}}
.legend {{
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
  margin-bottom: 24px;
}}
.legend-item {{
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #64748b;
}}
.legend-dot {{
  width: 10px;
  height: 10px;
  border-radius: 50%;
}}
.footer {{
  text-align: center;
  padding: 24px 48px;
  font-size: 12px;
  color: #94a3b8;
  border-top: 1px solid #f1f5f9;
}}
@media (max-width: 700px) {{
  .radar-section {{ flex-direction: column; }}
  .radar-chart {{ flex: none; width: 100%; height: 260px; }}
  .content {{ padding: 24px; }}
  .header {{ padding: 24px; }}
}}
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <h1>职业规划报告</h1>
    <div class="subtitle">{name} · {target}</div>
    <div class="meta-row">
      <span>目标：{goal}</span>
      <span>Holland Code：{code}</span>
      <span>生成日期：{date}</span>
    </div>
  </div>
  <div class="content">
    <h2 class="section-title">兴趣画像 · RIASEC 六维雷达</h2>
    <div class="radar-section">
      <div class="radar-chart">
        <canvas id="radarChart"></canvas>
      </div>
      <div class="radar-insight">
        <div class="code-badge">Holland Code: {code}</div>
        <p>你的兴趣倾向集中在 <strong>{code}</strong> 三个维度。这意味着你偏好需要逻辑分析、动手实践和系统化思维的工作环境。</p>
        <p>高分维度适合的方向：技术研发、数据分析、工程管理等需要深度思考与结构化输出的岗位。</p>
      </div>
    </div>

    <h2 class="section-title">12 个月行动路线图</h2>
    {legend_html}
    <div class="timeline-section">
      <div class="timeline">
{timeline_html}
      </div>
    </div>
  </div>
  <div class="footer">
    由 Career Toolkit 生成 · 仅供参考，具体路径需结合个人情况动态调整
  </div>
</div>

<script>
const ctx = document.getElementById('radarChart').getContext('2d');
new Chart(ctx, {{
  type: 'radar',
  data: {{
    labels: {radar_labels},
    datasets: [{{
      label: 'RIASEC',
      data: {radar_data},
      backgroundColor: 'rgba(124, 58, 237, 0.15)',
      borderColor: 'rgba(124, 58, 237, 0.8)',
      borderWidth: 2,
      pointBackgroundColor: 'rgba(124, 58, 237, 1)',
      pointRadius: 4,
      pointHoverRadius: 6,
    }}]
  }},
  options: {{
    responsive: true,
    maintainAspectRatio: false,
    plugins: {{
      legend: {{ display: false }},
    }},
    scales: {{
      r: {{
        beginAtZero: true,
        max: 100,
        ticks: {{
          stepSize: 25,
          font: {{ size: 10 }},
          backdropColor: 'transparent',
        }},
        pointLabels: {{
          font: {{ size: 11 }},
          color: '#475569',
        }},
        grid: {{
          color: 'rgba(148, 163, 184, 0.3)',
        }},
        angleLines: {{
          color: 'rgba(148, 163, 184, 0.3)',
        }},
      }},
    }},
  }},
}});
</script>
</body>
</html>"""


def _build_timeline(milestones: list) -> str:
    lines = []
    for m in milestones:
        cat = m.get("category", "prep")
        color = CATEGORY_COLORS.get(cat, "#6B7280")
        month = m.get("month", "?")
        label = html.escape(m.get("label", ""))
        details = html.escape(m.get("details", ""))
        lines.append(f"""        <div class="tl-item">
          <div class="tl-dot" style="color: {color};"></div>
          <div class="tl-month">Month {month}</div>
          <div class="tl-label">{label}</div>
          <div class="tl-details">{details}</div>
        </div>""")
    return "\n".join(lines)


def _build_legend() -> str:
    items = []
    for cat, color in CATEGORY_COLORS.items():
        label = CATEGORY_LABELS.get(cat, cat)
        items.append(
            f'<div class="legend-item">'
            f'<div class="legend-dot" style="background:{color};"></div>'
            f'{label}</div>'
        )
    return f'<div class="legend">{"".join(items)}</div>'


def main() -> int:
    parser = argparse.ArgumentParser(description="Render career plan visual (HTML)")
    parser.add_argument("plan_yaml", help="Path to career_plan.yaml")
    parser.add_argument("--out", "-o", default=None, help="Output HTML path (default: <plan>_visual.html)")
    args = parser.parse_args()

    plan_path = Path(args.plan_yaml).resolve()
    if not plan_path.exists():
        print(f"❌ File not found: {plan_path}", file=sys.stderr)
        return 2

    with plan_path.open("r", encoding="utf-8") as f:
        plan = yaml.safe_load(f)

    for key in ("meta", "riasec", "milestones"):
        if key not in plan:
            print(f"❌ Missing required key: {key}", file=sys.stderr)
            return 2

    out_path = Path(args.out) if args.out else plan_path.with_name(plan_path.stem + "_visual.html")
    out_path.write_text(build_html(plan), encoding="utf-8")
    print(f"✅ Generated: {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
