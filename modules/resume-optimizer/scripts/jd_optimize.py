"""JD 适配版简历生成器。

定位：不是"修改工具"，而是"生成器"。
输入：通用版 resume.yaml + JD 文本
输出：
  1. resume-general.yaml  — 通用版（仅做 Bullet 诊断修复，不含 JD 适配）
  2. resume-jd.yaml       — JD 适配版（基于通用版 + JD 深度适配）
  3. 小报告 — 两版对比说明

两版区别：
  通用版：只修 Bullet（补动词/不虚构量化），不融入 JD 关键词
  JD 版：在通用版基础上，融入 JD 关键词 + 调整内容侧重 + 重排顺序

Usage:
    python3 scripts/jd_optimize.py <resume.yaml> --jd <jd.txt> --out-dir <output_dir>
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
# 通用版生成：只修 Bullet，不碰 JD
# ═══════════════════════════════════════════

STRONG_VERBS = {
    "创造类": ["主导", "设计", "搭建", "构建", "创立", "发明", "提出"],
    "优化类": ["优化", "提升", "改进", "降低", "压缩", "加速", "重构"],
    "分析类": ["分析", "调研", "评估", "诊断", "排查", "定位"],
    "管理类": ["推动", "组织", "协调", "带领", "分配", "规划"],
    "技术类": ["实现", "开发", "封装", "部署", "集成", "迁移"],
}

EXISTING_VERBS = [
    "主导", "独立完成", "设计", "落地", "推动", "优化", "沉淀",
    "实现", "开发", "封装", "部署", "集成", "迁移", "搭建", "构建",
    "使用", "基于", "引入", "负责", "参与", "产出", "编写",
    "重构", "分析", "调研", "组织", "协调", "带领",
]

# 弱动词：前置会读成"主导做了…"，应替换而非叠加
WEAK_VERBS = ["做了", "进行了", "完成了", "弄了", "搞了", "处理了"]


def build_general_version(resume: dict, bullet_result: dict) -> tuple[dict, list[dict]]:
    """生成通用版：只修 Bullet 的 NO_VERB 问题。

    返回 (通用版 resume, 修改记录)。
    """
    general = copy.deepcopy(resume)
    applied = []

    for bullet_info in bullet_result.get("bullets", []):
        issues = bullet_info.get("issues", [])
        if "NO_VERB" not in issues:
            continue

        section = bullet_info.get("section", "")
        entry_index = bullet_info.get("index", -1)
        bullet_index = bullet_info.get("bullet_index", -1)
        original = bullet_info.get("text", "")

        if entry_index < 0 or bullet_index < 0:
            continue

        entries = general.get(section, [])
        if entry_index >= len(entries):
            continue
        entry = entries[entry_index]
        highlights = entry.get("highlights", [])
        if bullet_index >= len(highlights):
            continue

        fix = _apply_verb_fix(original)
        if not fix:
            continue
        new_text, verb, mode = fix
        if new_text == original:
            continue

        highlights[bullet_index] = new_text
        entry_name = entry.get("organization") or entry.get("name") or entry.get("title") or "unknown"
        applied.append({
            "type": "bullet_fix",
            "section": section,
            "entry": entry_name,
            "bullet_index": bullet_index,
            "before": original,
            "after": new_text,
            "verb_added": verb,
            "mode": mode,
        })

    return general, applied


def _apply_verb_fix(text: str) -> tuple[str, str, str] | None:
    """为缺动词的 bullet 生成修复。

    返回 (新文本, 动词, 模式)，模式为 'replace'（替换弱动词）或 'prepend'（前置）。
    无需修复返回 None。
    """
    # 已有强动词开头
    for v in EXISTING_VERBS:
        if text.startswith(v):
            return None
    # 弱动词：替换
    for weak in WEAK_VERBS:
        if text.startswith(weak):
            strong = _pick_strong_verb(text)
            return strong + text[len(weak):], strong, "replace"
    # 无动词：前置
    verb = _pick_strong_verb(text)
    return verb + text, verb, "prepend"


def _pick_strong_verb(text: str) -> str:
    """根据 bullet 上下文选强动词。"""
    text_lower = text.lower()
    if any(w in text_lower for w in ["论文", "投稿", "paper", "发表"]):
        return "产出"
    if any(w in text_lower for w in ["搭建", "构建", "实现", "开发", "封装"]):
        return "主导"
    if any(w in text_lower for w in ["优化", "提升", "改进", "降低"]):
        return "推动"
    if any(w in text_lower for w in ["编写", "博客", "文档", "系列"]):
        return "沉淀"
    return "主导"


# ═══════════════════════════════════════════
# JD 适配版生成：通用版 + JD 深度适配
# ═══════════════════════════════════════════

# 融入分级阈值
# AUTO_THRESHOLD：confidence >= 此值 且策略为 explicit（仅补规范名）才自动应用
# 其余涉及动作声明的策略一律降级为「需候选人确认」
AUTO_THRESHOLD = 0.9


def build_jd_version(general: dict, match_result: dict, integrate_result: dict,
                      jd_keywords: list) -> tuple[dict, list[dict], list[dict]]:
    """在通用版基础上，融入 JD 关键词 + 调整内容侧重。

    返回 (JD 适配版 resume, 修改记录, 需候选人确认的清单)。

    分级原则（防止编造）：
      - 可自动应用：explicit 策略 + confidence >= 0.9
        （bullet 的 tech 列表已有同义词，只是补规范名，不改语义）
      - 需候选人确认：tech_list / enrich / summary 策略
        （涉及「基于 X 优化」「使用 X 实现」等动作声明，必须确认真实经历）
      - 禁止应用：new_context 策略
        （需新增一条 bullet，构成编造经历，归入确认清单提问）
    """
    jd_version = copy.deepcopy(general)
    applied = []
    confirmations = []

    # 1. 关键词融入（分级）
    suggestions = integrate_result.get("suggestions", [])
    for sug in suggestions:
        confidence = sug.get("confidence", 0)
        keyword = sug.get("keyword", "")
        section = sug.get("target_section", "")
        entry_index = sug.get("target_entry_index", -1)
        bullet_index = sug.get("target_bullet_index", -1)
        original = sug.get("original_text", "")
        strategy = sug.get("strategy", "")
        entry_name = sug.get("target_entry", "")

        # 自动应用：仅 explicit + 高置信度（补规范名，不改动作）
        if strategy == "explicit" and confidence >= AUTO_THRESHOLD:
            if entry_index < 0 or bullet_index < 0:
                continue
            entries = jd_version.get(section, [])
            if entry_index >= len(entries):
                continue
            entry = entries[entry_index]
            highlights = entry.get("highlights", [])
            if bullet_index >= len(highlights):
                continue
            new_text = _apply_explicit_neutral(original, keyword)
            if new_text != original:
                highlights[bullet_index] = new_text
                applied.append({
                    "type": "keyword_integrate",
                    "keyword": keyword,
                    "section": section,
                    "entry": entry_name,
                    "bullet_index": bullet_index,
                    "before": original,
                    "after": new_text,
                    "confidence": confidence,
                    "mode": "auto",
                    "note": "tech 列表已有同义词，仅补规范名，不改动作声明",
                })
            continue

        # 需确认：tech_list / enrich / summary / new_context
        confirmations.append({
            "keyword": keyword,
            "strategy": strategy,
            "strategy_description": sug.get("strategy_description", ""),
            "confidence": confidence,
            "target_entry": entry_name,
            "target_section": section,
            "bullet_text": original,
            "suggested_text": sug.get("suggested_text", ""),
            "question": _build_confirmation_question(keyword, strategy, entry_name, original),
            "risk": _strategy_risk(strategy),
        })

    # 2. label 调整（求职意向，不涉及编造，可自动）
    jd_title = _extract_jd_title(jd_keywords)
    if jd_title:
        basics = jd_version.get("basics", {})
        old_label = basics.get("label", "")
        if old_label and jd_title not in old_label:
            basics["label"] = f"{old_label}（目标：{jd_title}）"
        elif not old_label:
            basics["label"] = f"目标：{jd_title}"
        applied.append({
            "type": "label_adjust",
            "before": old_label,
            "after": basics.get("label", ""),
            "note": "根据 JD 标题调整求职意向",
        })

    # 3. skills 补充（概念匹配推断，非候选人自述，标注来源）
    covered_concepts = match_result.get("resume_evidence", {}).get("concepts_matched", [])
    if covered_concepts:
        skills = jd_version.get("skills", [])
        all_keywords = set()
        for skill_group in skills:
            for kw in skill_group.get("keywords", []):
                all_keywords.add(kw.lower())
        new_concepts = [c for c in covered_concepts if c.lower() not in all_keywords]
        if new_concepts:
            skills.append({
                "name": "领域经验（推断）",
                "keywords": new_concepts,
                "_note": "基于简历内容概念匹配推断，非候选人自述，建议人工核对",
            })
            applied.append({
                "type": "skill_enhance_inferred",
                "added_concepts": new_concepts,
                "note": "概念匹配推断，非候选人自述，需人工核对",
            })
            confirmations.append({
                "keyword": " / ".join(new_concepts),
                "strategy": "skill_infer",
                "target_entry": "skills.领域经验",
                "question": f"简历内容中匹配到以下概念：{', '.join(new_concepts)}。请确认是否确实具备这些领域的真实经验？若不属实将从 skills 中移除。",
                "risk": "medium",
            })

    return jd_version, applied, confirmations


def _build_confirmation_question(keyword: str, strategy: str, entry: str, bullet: str) -> str:
    """根据策略生成给候选人的提问。"""
    if strategy == "tech_list":
        return (f"在「{entry}」经历中，是否真实使用过「{keyword}」相关技术？"
                f"当前 bullet：「{bullet}」。若属实，建议如何自然地在该 bullet 中体现？")
    if strategy == "enrich":
        return (f"在「{entry}」经历中，是否使用「{keyword}」实现了某模块？"
                f"当前 bullet：「{bullet}」。若属实，请补充具体使用场景。")
    if strategy == "summary":
        return (f"在「{entry}」经历的 summary 中提到了「{keyword}」相关内容，"
                f"是否确实在 highlights 中展开过？请补充真实细节。")
    if strategy == "new_context":
        return (f"JD 要求「{keyword}」，但简历中未找到任何相关经历。"
                f"你是否有过相关经历？（若没有，不会编造，只在报告中标注为 gap）")
    return f"请确认是否具备「{keyword}」相关经历/技能。"


def _strategy_risk(strategy: str) -> str:
    """不同策略的编造风险等级。"""
    risk = {
        "explicit": "low",       # 仅补规范名
        "tech_list": "medium",   # 可能涉及动作声明
        "enrich": "high",        # 声明使用某技术实现
        "summary": "high",       # 新展开内容
        "new_context": "critical",  # 新增整条 bullet
        "skill_infer": "medium", # 概念推断
    }
    return risk.get(strategy, "unknown")


def _extract_jd_title(jd_keywords: list) -> str:
    """从 JD 关键词中推断岗位名称。"""
    title_keywords = [kw.get("keyword", "") for kw in jd_keywords[:5]]
    return " / ".join(title_keywords[:2]) if title_keywords else ""


def _apply_explicit_neutral(original: str, keyword: str) -> str:
    """explicit 策略：仅补规范名，措辞中性，不声明动作。"""
    if keyword.lower() in original.lower():
        return original
    stripped = original.rstrip("。；！.")
    return f"{stripped}（相关技术：{keyword}）"


# ═══════════════════════════════════════════
# 夸大风险检测
# ═══════════════════════════════════════════

# 夸大词：声明超出可验证范围的能力或规模
EXAGGERATION_WORDS = {
    "high": ["精通", "熟练掌握", "资深", "专家", "精通掌握", "深入研究", "深度精通"],
    "medium": ["千万级", "亿级", "百万级", "海量", "极致", "完美", "巨大", "显著提升"],
}


def detect_exaggeration(resume: dict) -> list[dict]:
    """扫描简历文本，检测可能夸大的措辞。

    返回夸大风险列表，每项含位置、原词、风险级别、建议。
    """
    warnings = []

    def scan(text: str, location: str):
        if not text:
            return
        for level, words in EXAGGERATION_WORDS.items():
            for w in words:
                if w in text:
                    warnings.append({
                        "location": location,
                        "word": w,
                        "risk": level,
                        "text": text,
                        "suggestion": _exaggeration_fix(w, level),
                    })

    # 扫描 summary / label
    basics = resume.get("basics", {}) or {}
    scan(basics.get("summary", ""), "basics.summary")
    scan(basics.get("label", ""), "basics.label")

    # 扫描各 section 的 highlights / summary
    for section in ("work", "projects", "research", "activities"):
        for i, entry in enumerate(resume.get(section, []) or []):
            name = entry.get("organization") or entry.get("name") or f"{section}[{i}]"
            scan(entry.get("summary", ""), f"{section}.{name}.summary")
            for j, hl in enumerate(entry.get("highlights", []) or []):
                scan(hl, f"{section}.{name}.highlights[{j}]")

    # 扫描 skills 关键词（"精通 X" 类声明）
    for i, group in enumerate(resume.get("skills", []) or []):
        for kw in group.get("keywords", []) or []:
            for level, words in EXAGGERATION_WORDS.items():
                for w in words:
                    if w in str(kw):
                        warnings.append({
                            "location": f"skills[{i}].{group.get('name', '')}",
                            "word": w,
                            "risk": level,
                            "text": kw,
                            "suggestion": _exaggeration_fix(w, level),
                        })

    return warnings


def _exaggeration_fix(word: str, level: str) -> str:
    """给出夸大词的改写建议。"""
    fixes = {
        "精通": "改为「熟悉」或「熟练使用」，并准备具体项目佐证",
        "熟练掌握": "改为「熟悉」或直接列出使用过的项目",
        "资深": "改为具体年限，如「3 年经验」",
        "专家": "改为「熟悉」或列出代表性产出",
        "深入研究": "改为「了解原理」或列出具体研究产出",
        "深度精通": "改为「熟悉」或列出具体应用",
        "千万级": "确认数字来源，如无据改为相对量化（如「提升 N 倍」）",
        "亿级": "确认数字来源，如无据改为相对量化",
        "百万级": "确认数字来源，如无据改为相对量化",
        "海量": "改为具体规模数字",
        "极致": "改为具体量化指标",
        "完美": "改为具体达成率",
        "巨大": "改为具体倍数或百分比",
        "显著提升": "补充具体提升幅度",
    }
    return fixes.get(word, f"「{word}」属于高风险措辞，建议改为可验证的表述")


# ═══════════════════════════════════════════
# 生成对比报告
# ═══════════════════════════════════════════

def generate_report(match_result: dict, bullet_result: dict,
                    general_changes: list[dict], jd_changes: list[dict],
                    confirmations: list[dict], exaggeration_warnings: list[dict],
                    ats_result: dict | None) -> dict:
    """生成两版对比报告。"""
    gap_summary = match_result.get("gap_summary", {})
    real_gaps = match_result.get("real_gaps", [])
    evidence_gaps = match_result.get("evidence_gaps", [])
    bullet_bullets = bullet_result.get("bullets", [])

    # 通用版修改中 bullet 修复数
    general_bullet_fixes = [c for c in general_changes if c["type"] == "bullet_fix"]
    # JD 版修改中关键词融入数
    jd_keyword_integrations = [c for c in jd_changes if c["type"] == "keyword_integrate"]
    jd_other_changes = [c for c in jd_changes if c["type"] != "keyword_integrate"]

    # bullet 剩余问题（通用版修复了 NO_VERB 后剩余的）
    fixed_texts = {c["before"] for c in general_bullet_fixes}
    remaining_bullet_issues = [
        {
            "text": b.get("text", ""),
            "problems": [p for p in b.get("issues", []) if p != "NO_VERB"],
            "suggestion": b.get("rewrite_hint", ""),
            "entry": b.get("entry_name", ""),
        }
        for b in bullet_bullets
        if b.get("text", "") not in fixed_texts
        and any(p != "NO_VERB" for p in b.get("issues", []))
    ]

    # 按风险级别分组确认清单
    critical_confirmations = [c for c in confirmations if c["risk"] == "critical"]
    high_confirmations = [c for c in confirmations if c["risk"] == "high"]
    medium_confirmations = [c for c in confirmations if c["risk"] == "medium"]

    return {
        "summary": {
            "coverage": match_result.get("coverage_percent", 0),
            "covered": match_result.get("covered_count", 0),
            "total_keywords": match_result.get("total_keywords", 0),
            "general_changes": len(general_changes),
            "jd_changes": len(jd_changes),
            "evidence_gaps": len(evidence_gaps),
            "real_gaps": len(real_gaps),
            "bullet_issues_found": len(bullet_bullets),
            "bullet_auto_fixed": len(general_bullet_fixes),
            "bullet_remaining": len(remaining_bullet_issues),
            "confirmations_needed": len(confirmations),
            "exaggeration_warnings": len(exaggeration_warnings),
            "ats_passed": ats_result is None or len(ats_result.get("failed", [])) == 0,
        },
        "general_version": {
            "changes": general_changes,
            "description": "通用版：仅修复 Bullet 基础问题（补动词），不针对特定 JD",
        },
        "jd_version": {
            "changes": jd_changes,
            "keyword_integrations": jd_keyword_integrations,
            "other_changes": jd_other_changes,
            "description": "JD 适配版：在通用版基础上融入 JD 关键词 + 调整内容侧重",
        },
        "confirmations_needed": {
            "critical": critical_confirmations,
            "high": high_confirmations,
            "medium": medium_confirmations,
            "description": "需候选人确认的经历/技能，确认前不会写入简历",
        },
        "exaggeration_warnings": exaggeration_warnings,
        "real_gaps": [
            {"keyword": g.get("keyword", ""), "note": "简历无相关经历，不建议虚构"}
            for g in real_gaps
        ],
        "bullet_remaining_issues": remaining_bullet_issues,
        "principles": [
            "通用版只修 Bullet 基础问题，不碰 JD 关键词",
            "JD 适配版在通用版基础上深度适配，保留通用版不变",
            "缺少量化数据的 bullet 不自动虚构数字",
            "real_gap 不修改简历，只在报告中提示",
            "涉及动作声明（基于 X 优化 / 使用 X 实现）的关键词一律需候选人确认",
            "新增 bullet（new_context）禁止自动生成，归入确认清单提问",
            "夸大措辞（精通/资深/千万级）在报告中标注，需候选人提供佐证",
            "两版均可独立渲染为 PDF",
        ],
    }


def format_report_text(report: dict) -> str:
    """格式化为人类可读文本。"""
    lines = []
    s = report["summary"]

    lines.append("═" * 60)
    lines.append("  简历生成报告：通用版 + JD 适配版")
    lines.append("═" * 60)
    lines.append("")

    # 概况
    lines.append("📊 生成概况")
    lines.append(f"   JD 关键词覆盖：{s['covered']}/{s['total_keywords']}（{s['coverage']}%）")
    lines.append(f"   通用版修改：   {s['general_changes']} 处（仅 Bullet 基础修复）")
    lines.append(f"   JD 版修改：    {s['jd_changes']} 处（关键词融入 + 内容侧重）")
    lines.append(f"   Bullet 诊断：  发现 {s['bullet_issues_found']} 条，自动修复 {s['bullet_auto_fixed']} 条，剩余 {s['bullet_remaining']} 条")
    lines.append(f"   需候选人确认： {s['confirmations_needed']} 项（未确认前不写入简历）")
    lines.append(f"   夸大风险提示： {s['exaggeration_warnings']} 项")
    if s["ats_passed"]:
        lines.append("   ATS 检查：     ✅ 通过")
    else:
        lines.append("   ATS 检查：     ⚠️ 有问题")
    lines.append("")

    # 通用版修改
    general_changes = report.get("general_version", {}).get("changes", [])
    if general_changes:
        lines.append("📄 通用版修改（仅 Bullet 修复）")
        for i, c in enumerate(general_changes, 1):
            if c["type"] == "bullet_fix":
                lines.append(f"   {i}. 补充动词「{c['verb_added']}」→ {c['section']} / {c['entry']}（{c.get('mode', 'prepend')}）")
                lines.append(f"      修改前：{c['before']}")
                lines.append(f"      修改后：{c['after']}")
        lines.append("")

    # JD 版修改
    jd_changes = report.get("jd_version", {}).get("changes", [])
    if jd_changes:
        lines.append("🎯 JD 适配版修改")
        for i, c in enumerate(jd_changes, 1):
            if c["type"] == "keyword_integrate":
                lines.append(f"   {i}. 融入关键词「{c['keyword']}」→ {c['section']} / {c['entry']}（自动，仅补规范名）")
                lines.append(f"      修改前：{c['before']}")
                lines.append(f"      修改后：{c['after']}")
            elif c["type"] == "label_adjust":
                lines.append(f"   {i}. 调整求职意向")
                lines.append(f"      修改前：{c['before']}")
                lines.append(f"      修改后：{c['after']}")
            elif c["type"] == "skill_enhance_inferred":
                lines.append(f"   {i}. 补充领域经验技能组（推断）：{', '.join(c.get('added_concepts', []))}")
                lines.append(f"      ⚠️ 概念匹配推断，非候选人自述，需人工核对")
        lines.append("")

    # 需候选人确认
    confirmations = report.get("confirmations_needed", {})
    critical_c = confirmations.get("critical", [])
    high_c = confirmations.get("high", [])
    medium_c = confirmations.get("medium", [])
    if critical_c or high_c or medium_c:
        lines.append("❓ 需候选人确认（未确认前不写入简历）")
        idx = 1
        if critical_c:
            lines.append(f"   ── 高风险（可能编造经历，禁止自动生成）")
            for c in critical_c:
                lines.append(f"   {idx}. [{c['keyword']}] {c['question']}")
                idx += 1
        if high_c:
            lines.append(f"   ── 较高风险（涉及动作声明）")
            for c in high_c:
                lines.append(f"   {idx}. [{c['keyword']}] {c['question']}")
                idx += 1
        if medium_c:
            lines.append(f"   ── 中等风险（概念推断）")
            for c in medium_c:
                lines.append(f"   {idx}. [{c['keyword']}] {c['question']}")
                idx += 1
        lines.append("")

    # 夸大风险提示
    exaggeration = report.get("exaggeration_warnings", [])
    if exaggeration:
        lines.append("⚠️ 夸大风险提示（原简历中检测到）")
        for i, w in enumerate(exaggeration, 1):
            lines.append(f"   {i}. [{w['risk']}] {w['word']} @ {w['location']}")
            lines.append(f"      原文：{w['text'][:60]}")
            lines.append(f"      建议：{w['suggestion']}")
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
        problem_map = {
            "NO_RESULT": "缺少结果", "NO_QUANT": "缺少量化", "NO_VERB": "缺少动词",
            "TOO_SHORT": "过于简短", "DUTY_LIST": "流水账",
        }
        for i, b in enumerate(bullet_issues, 1):
            problems_str = " / ".join(problem_map.get(p, p) for p in b.get("problems", []))
            lines.append(f"   {i}. [{problems_str}] {b['text'][:60]}")
            lines.append(f"      建议：{b['suggestion']}")
        lines.append("")

    lines.append("─" * 60)
    lines.append("  两份简历已生成，可分别渲染为 PDF")
    lines.append("  · 通用版适用于多岗位投递")
    lines.append("  · JD 适配版针对该岗位深度优化")
    lines.append("  · 需候选人确认的项未写入，请逐项确认后再补充")
    lines.append("─" * 60)

    return "\n".join(lines)


# ═══════════════════════════════════════════
# 主流程
# ═══════════════════════════════════════════

def run(resume_path: str, jd_path: str, out_dir: str | None = None) -> dict:
    """双版本生成管道。"""
    with open(resume_path, "r", encoding="utf-8") as f:
        resume = yaml.safe_load(f)

    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as tmp:
        match_path = tmp.name

    try:
        # 1. JD 匹配
        match_result = run_script("jd_match.py", resume_path, "--jd", jd_path)
        if not match_result:
            return {"error": "JD 匹配失败"}
        with open(match_path, "w", encoding="utf-8") as f:
            json.dump(match_result, f, ensure_ascii=False)

        # 2. JD 融入建议
        integrate_result = run_script("jd_integrate.py", resume_path, "--match", match_path)

        # 3. Bullet 诊断
        bullet_result = run_script("bullet_rewrite.py", resume_path)

        # 4. ATS 检查
        ats_result = run_script("ats_check.py", resume_path)

        # 5. 生成通用版（只修 Bullet）
        general_version, general_changes = build_general_version(resume, bullet_result)

        # 6. 生成 JD 适配版（通用版 + JD 深度适配）
        jd_keywords = match_result.get("covered", []) + match_result.get("missing", [])
        jd_version, jd_changes, confirmations = build_jd_version(
            general_version, match_result, integrate_result, jd_keywords
        )

        # 7. 夸大风险检测（对原简历 + JD 版）
        exaggeration_warnings = detect_exaggeration(resume)
        jd_exaggeration = detect_exaggeration(jd_version)
        # 去重（按 location + word）
        seen = {(w["location"], w["word"]) for w in exaggeration_warnings}
        for w in jd_exaggeration:
            key = (w["location"], w["word"])
            if key not in seen:
                exaggeration_warnings.append(w)
                seen.add(key)

        # 8. 生成报告
        report = generate_report(
            match_result, bullet_result, general_changes, jd_changes,
            confirmations, exaggeration_warnings, ats_result
        )

        # 8. 输出文件
        if out_dir:
            out_dir = Path(out_dir)
            out_dir.mkdir(parents=True, exist_ok=True)
            general_path = out_dir / "resume-general.yaml"
            jd_yaml_path = out_dir / "resume-jd.yaml"
            with open(general_path, "w", encoding="utf-8") as f:
                yaml.dump(general_version, f, allow_unicode=True, sort_keys=False, default_flow_style=False)
            with open(jd_yaml_path, "w", encoding="utf-8") as f:
                yaml.dump(jd_version, f, allow_unicode=True, sort_keys=False, default_flow_style=False)

        return {
            "general_resume": general_version,
            "jd_resume": jd_version,
            "report": report,
            "report_text": format_report_text(report),
        }
    finally:
        Path(match_path).unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description="双版本简历生成：通用版 + JD 适配版")
    parser.add_argument("resume", help="resume.yaml 路径")
    parser.add_argument("--jd", required=True, help="JD 文本文件路径")
    parser.add_argument("--out-dir", default=None, help="输出目录（生成 resume-general.yaml + resume-jd.yaml）")
    args = parser.parse_args()

    if not Path(args.resume).exists():
        print(f"错误：简历文件不存在 {args.resume}", file=sys.stderr)
        sys.exit(1)
    if not Path(args.jd).exists():
        print(f"错误：JD 文件不存在 {args.jd}", file=sys.stderr)
        sys.exit(1)

    result = run(args.resume, args.jd, args.out_dir)

    if "error" in result:
        print(f"❌ {result['error']}", file=sys.stderr)
        sys.exit(1)

    print(result["report_text"])

    if args.out_dir:
        print(f"\n📄 通用版已保存：{Path(args.out_dir) / 'resume-general.yaml'}")
        print(f"🎯 JD 适配版已保存：{Path(args.out_dir) / 'resume-jd.yaml'}")


if __name__ == "__main__":
    main()
