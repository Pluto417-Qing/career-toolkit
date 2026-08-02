"""JD 优化编排脚本。

完整管道：
  resume.yaml + jd.txt
    → jd_match（三层匹配 + gap 分类）
    → jd_integrate（关键词自然融入建议）
    → bullet_rewrite（量化诊断）
    → 自动应用高置信度修改
    → 输出优化后 resume + 小报告

自动应用规则：
  - evidence_gap 且置信度 ≥ 0.7 → 自动融入
  - evidence_gap 且置信度 0.5-0.7 → 标记 [需确认]
  - bullet 有明确动词建议 → 自动补强
  - real_gap → 不修改，只在报告中提示

Usage:
    python3 scripts/jd_optimize.py <resume.yaml> --jd <jd.txt> [--out <optimized.yaml>]
"""

import argparse
import copy
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

SCRIPTS_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPTS_DIR.parent


def run_script(script_name: str, *args) -> dict:
    """运行一个 Python 脚本并返回 JSON 输出。"""
    cmd = [sys.executable, str(SCRIPTS_DIR / script_name)] + list(args)
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    if result.returncode != 0:
        print(f"⚠️ {script_name} 执行失败: {result.stderr}", file=sys.stderr)
        return {}
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return {}


# ═══════════════════════════════════════════
# 自动应用：JD 融入
# ═══════════════════════════════════════════

def apply_integration(resume: dict, integrate_result: dict) -> list[dict]:
    """把 JD 融入建议应用到简历上。

    返回应用记录列表。
    """
    applied = []
    suggestions = integrate_result.get("suggestions", [])

    for sug in suggestions:
        confidence = sug.get("confidence", 0)
        strategy = sug.get("strategy", "")
        keyword = sug.get("keyword", "")
        section = sug.get("target_section", "")
        entry_index = sug.get("target_entry_index", -1)
        bullet_index = sug.get("target_bullet_index", -1)
        suggested_text = sug.get("suggested_text", "")
        original_text = sug.get("original_text", "")

        # 获取目标 section 的条目列表
        entries = resume.get(section, [])
        if entry_index < 0 or entry_index >= len(entries):
            continue

        entry = entries[entry_index]
        highlights = entry.get("highlights", [])
        if bullet_index < 0 or bullet_index >= len(highlights):
            continue

        if confidence >= 0.7:
            # 高置信度：自动应用
            if strategy == "explicit":
                new_text = _apply_explicit(original_text, keyword)
            elif strategy == "tech_list":
                new_text = _apply_tech_list(original_text, keyword)
            elif strategy == "enrich":
                new_text = _apply_enrich(original_text, keyword)
            else:
                new_text = suggested_text

            # 如果没有实际变化，跳过
            if new_text == original_text:
                continue

            highlights[bullet_index] = new_text
            applied.append({
                "type": "auto_integrate",
                "keyword": keyword,
                "section": section,
                "entry": _get_entry_name(entry),
                "bullet_index": bullet_index,
                "before": original_text,
                "after": new_text,
                "confidence": confidence,
            })
        elif confidence >= 0.5:
            # 中置信度：标记需确认
            applied.append({
                "type": "needs_confirmation",
                "keyword": keyword,
                "section": section,
                "entry": _get_entry_name(entry),
                "bullet_index": bullet_index,
                "suggestion": suggested_text,
                "confidence": confidence,
            })

    return applied


def _get_entry_name(entry: dict) -> str:
    return entry.get("organization") or entry.get("name") or entry.get("title") or "unknown"


def _apply_explicit(original: str, keyword: str) -> str:
    """显式补写：在 bullet 末尾自然补充关键词。"""
    # 去掉句末标点，补充后加回
    stripped = original.rstrip("。；！.")
    return f"{stripped}（涉及 {keyword}）"


def _apply_tech_list(original: str, keyword: str) -> str:
    """技术栈补写：在描述中自然提及。"""
    # 如果关键词已经在文本中，不重复追加
    if keyword.lower() in original.lower():
        return original
    stripped = original.rstrip("。；！.")
    return f"{stripped}，基于 {keyword} 优化技术方案"


def _apply_enrich(original: str, keyword: str) -> str:
    """丰富描述：补充具体技术手段。"""
    stripped = original.rstrip("。；！.")
    return f"{stripped}，使用 {keyword} 实现核心模块"


# ═══════════════════════════════════════════
# 自动应用：Bullet 诊断
# ═══════════════════════════════════════════

# 动词库（按类别）
STRONG_VERBS = {
    "创造类": ["主导", "设计", "搭建", "构建", "创立", "发明", "提出"],
    "优化类": ["优化", "提升", "改进", "降低", "压缩", "加速", "重构"],
    "分析类": ["分析", "调研", "评估", "诊断", "排查", "定位"],
    "管理类": ["推动", "组织", "协调", "带领", "分配", "规划"],
    "技术类": ["实现", "开发", "封装", "部署", "集成", "迁移"],
}

def apply_bullet_fixes(resume: dict, bullet_result: dict) -> list[dict]:
    """对有问题的 bullet 进行自动补强。

    只处理 NO_VERB 类型（缺少动词），自动在句首补上合适的动词。
    NO_RESULT / NO_QUANT / TOO_SHORT / DUTY_LIST 只在报告中提示，不自动修改。
    """
    applied = []
    bullets = bullet_result.get("bullets", [])

    for bullet_info in bullets:
        issues = bullet_info.get("issues", [])
        section = bullet_info.get("section", "")
        entry_index = bullet_info.get("index", -1)
        bullet_index = bullet_info.get("bullet_index", -1)
        original = bullet_info.get("text", "")

        if entry_index < 0 or bullet_index < 0:
            continue

        entries = resume.get(section, [])
        if entry_index >= len(entries):
            continue
        entry = entries[entry_index]
        highlights = entry.get("highlights", [])
        if bullet_index >= len(highlights):
            continue

        # 只自动修复 NO_VERB（缺少动词）
        if "NO_VERB" in issues:
            verb = _pick_verb(original, entry)
            # 如果无法选出合适动词或 bullet 已有动词开头，跳过
            if not verb:
                continue
            new_text = f"{verb}{original}"
            # 如果修改后和原文一样（说明已有动词），跳过
            if new_text == original:
                continue
            highlights[bullet_index] = new_text
            applied.append({
                "type": "auto_bullet_fix",
                "problem": "NO_VERB",
                "section": section,
                "entry": _get_entry_name(entry),
                "bullet_index": bullet_index,
                "before": original,
                "after": new_text,
                "verb_added": verb,
            })

    return applied


def _pick_verb(text: str, entry: dict) -> str:
    """根据 bullet 上下文选择合适的动词。

    如果 bullet 已有动词开头，返回空字符串（不需要补）。
    """
    text_lower = text.lower()

    # 已有的常见动词开头（bullet_rewrite 可能误判）
    existing_verbs = [
        "主导", "独立完成", "设计", "落地", "推动", "优化", "沉淀",
        "实现", "开发", "封装", "部署", "集成", "迁移", "搭建", "构建",
        "使用", "基于", "引入", "负责", "参与", "产出", "编写", "主导",
        "重构", "分析", "调研", "组织", "协调", "带领",
    ]
    for v in existing_verbs:
        if text.startswith(v):
            return ""

    # 如果有论文/投稿 → 用「产出」
    if any(w in text_lower for w in ["论文", "投稿", "paper", "发表"]):
        return "产出"
    # 如果有搭建/构建 → 用「主导」
    if any(w in text_lower for w in ["搭建", "构建", "实现", "开发", "封装"]):
        return "主导"
    # 如果有优化/提升 → 用「优化」
    if any(w in text_lower for w in ["优化", "提升", "改进", "降低"]):
        return "推动"
    # 如果有编写/博客 → 用「沉淀」
    if any(w in text_lower for w in ["编写", "博客", "文档", "系列"]):
        return "沉淀"
    # 默认
    return "主导"


# ═══════════════════════════════════════════
# 生成报告
# ═══════════════════════════════════════════

def generate_report(match_result: dict, integrate_result: dict, bullet_result: dict,
                    applied_changes: list[dict], ats_result: dict | None) -> dict:
    """生成优化小报告。"""
    auto_changes = [c for c in applied_changes if c["type"].startswith("auto")]
    pending_changes = [c for c in applied_changes if c["type"] == "needs_confirmation"]

    # 汇总 gap 信息
    gap_summary = match_result.get("gap_summary", {})
    evidence_gaps = match_result.get("evidence_gaps", [])
    real_gaps = match_result.get("real_gaps", [])

    # 汇总 bullet 问题
    bullet_bullets = bullet_result.get("bullets", [])
    auto_fixed_bullets = [c for c in auto_changes if c["type"] == "auto_bullet_fix"]
    # 已自动修复 NO_VERB 的 bullet 文本集合
    fixed_texts = {c["before"] for c in auto_fixed_bullets}

    report = {
        "summary": {
            "overall_score_before": match_result.get("overall_score", 0),
            "coverage_before": match_result.get("coverage_percent", 0),
            "total_keywords": match_result.get("total_keywords", 0),
            "covered_before": match_result.get("covered_count", 0),
            "auto_applied": len(auto_changes),
            "needs_confirmation": len(pending_changes),
            "real_gaps_remaining": len(real_gaps),
            "bullet_issues_found": len(bullet_bullets),
            "bullet_auto_fixed": len(auto_fixed_bullets),
            "ats_status": "passed" if ats_result and ats_result.get("failed", []) == [] else "has_issues",
        },
        "auto_changes": auto_changes,
        "needs_confirmation": pending_changes,
        "real_gaps": [
            {
                "keyword": g.get("keyword", ""),
                "section": g.get("section", ""),
                "note": "简历中未找到相关经历，不建议虚构。如有相关经历请手动补充。",
            }
            for g in real_gaps
        ],
        "bullet_remaining_issues": [
            {
                "text": b.get("text", ""),
                "problems": [p for p in b.get("issues", []) if p != "NO_VERB"],
                "suggestion": b.get("rewrite_hint", ""),
                "entry": b.get("entry_name", ""),
                "section": b.get("section", ""),
            }
            for b in bullet_bullets
            if b.get("text", "") not in fixed_texts  # 跳过已自动修复 NO_VERB 的
            and any(p != "NO_VERB" for p in b.get("issues", []))  # 还有其他问题
        ],
        "principles": [
            "自动应用仅限高置信度（≥0.7）的 evidence_gap 改写",
            "缺少量化数据的 bullet 不自动虚构数字，需用户确认",
            "real_gap 不修改简历，只在报告中提示",
            "所有自动修改均可回溯（before/after 对照）",
        ],
    }

    if ats_result:
        report["ats"] = {
            "passed": len(ats_result.get("passed", [])),
            "warnings": len(ats_result.get("warnings", [])),
            "failed": len(ats_result.get("failed", [])),
            "issues": ats_result.get("failed", []) + ats_result.get("warnings", []),
        }

    return report


# ═══════════════════════════════════════════
# 格式化报告（人类可读）
# ═══════════════════════════════════════════

def format_report_text(report: dict) -> str:
    """把报告格式化为人类可读的文本。"""
    lines = []
    s = report["summary"]

    lines.append("═" * 60)
    lines.append("  简历 JD 优化报告")
    lines.append("═" * 60)
    lines.append("")

    # 概况
    lines.append("📊 优化概况")
    lines.append(f"   匹配前贴合度：{s['coverage_before']}%（{s['covered_before']}/{s['total_keywords']} 关键词）")
    lines.append(f"   自动应用修改：{s['auto_applied']} 处")
    lines.append(f"   待确认修改：  {s['needs_confirmation']} 处")
    lines.append(f"   无法填补 gap：{s['real_gaps_remaining']} 项（简历确实没有相关经历）")
    lines.append(f"   Bullet 诊断：  发现 {s['bullet_issues_found']} 条问题，自动修复 {s['bullet_auto_fixed']} 条")
    if s.get("ats_status") == "passed":
        lines.append("   ATS 检查：    ✅ 全部通过")
    else:
        lines.append("   ATS 检查：    ⚠️ 有问题需关注")
    lines.append("")

    # 自动应用的修改
    auto_changes = report.get("auto_changes", [])
    if auto_changes:
        lines.append("✅ 已自动应用的修改")
        for i, c in enumerate(auto_changes, 1):
            if c["type"] == "auto_integrate":
                lines.append(f"   {i}. 关键词「{c['keyword']}」→ {c['section']} / {c['entry']} bullet[{c['bullet_index']}]")
                lines.append(f"      修改前：{c['before']}")
                lines.append(f"      修改后：{c['after']}")
            elif c["type"] == "auto_bullet_fix":
                lines.append(f"   {i}. 补充动词「{c['verb_added']}」→ {c['section']} / {c['entry']} bullet[{c['bullet_index']}]")
                lines.append(f"      修改前：{c['before']}")
                lines.append(f"      修改后：{c['after']}")
        lines.append("")

    # 待确认
    pending = report.get("needs_confirmation", [])
    if pending:
        lines.append("🟡 建议确认后应用")
        for i, c in enumerate(pending, 1):
            lines.append(f"   {i}. 关键词「{c['keyword']}」→ {c['section']} / {c['entry']} bullet[{c['bullet_index']}]")
            lines.append(f"      建议改为：{c['suggestion']}")
            lines.append(f"      置信度：  {c['confidence']}")
        lines.append("")

    # 无法填补
    real_gaps = report.get("real_gaps", [])
    if real_gaps:
        lines.append("🔴 无法填补的 gap（简历确实没有相关经历）")
        for i, g in enumerate(real_gaps, 1):
            lines.append(f"   {i}. {g['keyword']} — {g['note']}")
        lines.append("")

    # Bullet 剩余问题
    bullet_issues = report.get("bullet_remaining_issues", [])
    if bullet_issues:
        lines.append("📝 Bullet 诊断（需手动改写）")
        for i, b in enumerate(bullet_issues, 1):
            problem_map = {
                "NO_RESULT": "缺少结果", "NO_QUANT": "缺少量化", "NO_VERB": "缺少动词",
                "TOO_SHORT": "过于简短", "DUTY_LIST": "流水账",
            }
            problems_str = " / ".join(problem_map.get(p, p) for p in b.get("problems", []))
            lines.append(f"   {i}. [{problems_str}] {b['text'][:60]}")
            lines.append(f"      建议：{b['suggestion']}")
        lines.append("")

    # ATS
    ats = report.get("ats")
    if ats and ats.get("issues"):
        lines.append("⚠️ ATS 检查问题")
        for issue in ats["issues"]:
            lines.append(f"   - [{issue.get('code', '')}] {issue.get('message', '')}")
        lines.append("")

    lines.append("─" * 60)
    lines.append("  原则：自动修改仅限高置信度内容，所有修改均有 before/after 记录")
    lines.append("─" * 60)

    return "\n".join(lines)


# ═══════════════════════════════════════════
# 主流程
# ═══════════════════════════════════════════

def run(resume_path: str, jd_path: str, out_path: str | None = None) -> dict:
    """完整优化管道。"""
    # 读取原始简历
    with open(resume_path, "r", encoding="utf-8") as f:
        resume = yaml.safe_load(f)

    # 深拷贝，避免修改原始数据
    optimized = copy.deepcopy(resume)

    # 创建临时文件用于中间结果传递
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as tmp:
        match_path = tmp.name

    try:
        # 1. JD 匹配
        match_result = run_script("jd_match.py", resume_path, "--jd", jd_path)
        if not match_result:
            return {"error": "JD 匹配失败"}
        # 保存匹配结果（供 jd_integrate 使用）
        with open(match_path, "w", encoding="utf-8") as f:
            json.dump(match_result, f, ensure_ascii=False)

        # 2. JD 融入
        integrate_result = run_script("jd_integrate.py", resume_path, "--match", match_path)

        # 3. Bullet 诊断
        bullet_result = run_script("bullet_rewrite.py", resume_path)

        # 4. ATS 检查
        ats_result = run_script("ats_check.py", resume_path)

        # 5. 自动应用修改
        all_applied = []
        all_applied.extend(apply_integration(optimized, integrate_result))
        all_applied.extend(apply_bullet_fixes(optimized, bullet_result))

        # 6. 生成报告
        report = generate_report(match_result, integrate_result, bullet_result, all_applied, ats_result)

        # 7. 输出优化后简历
        if out_path:
            with open(out_path, "w", encoding="utf-8") as f:
                yaml.dump(optimized, f, allow_unicode=True, sort_keys=False, default_flow_style=False)

        return {
            "optimized_resume": optimized,
            "report": report,
            "report_text": format_report_text(report),
        }
    finally:
        Path(match_path).unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description="JD 优化编排：匹配→融入→诊断→自动应用→输出优化简历+报告")
    parser.add_argument("resume", help="resume.yaml 路径")
    parser.add_argument("--jd", required=True, help="JD 文本文件路径")
    parser.add_argument("--out", default=None, help="优化后简历输出路径（默认打印到 stdout）")
    parser.add_argument("--report-only", action="store_true", help="只输出报告，不输出简历")
    args = parser.parse_args()

    if not Path(args.resume).exists():
        print(f"错误：简历文件不存在 {args.resume}", file=sys.stderr)
        sys.exit(1)
    if not Path(args.jd).exists():
        print(f"错误：JD 文件不存在 {args.jd}", file=sys.stderr)
        sys.exit(1)

    result = run(args.resume, args.jd, args.out if not args.report_only else None)

    if "error" in result:
        print(f"❌ {result['error']}", file=sys.stderr)
        sys.exit(1)

    # 打印报告
    print(result["report_text"])

    # 如果没有指定输出文件，打印优化后简历
    if not args.out and not args.report_only:
        print("\n" + "═" * 60)
        print("  优化后简历")
        print("═" * 60)
        print(yaml.dump(result["optimized_resume"], allow_unicode=True, sort_keys=False, default_flow_style=False))


if __name__ == "__main__":
    main()
