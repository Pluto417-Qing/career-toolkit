"""重点突出器。

负责识别和强调关键成果、核心技能。
"""

import re
from typing import Optional


class Highlighter:
    """重点突出器。"""

    # 量化指标关键词（用于识别重点）
    QUANT_KEYWORDS = [
        "%", "倍", "万", "亿", "千", "star", "QPS", "TPS",
        "FCP", "LCP", "TTI", "DAU", "MAU", "GMV",
    ]

    # 影响力关键词
    IMPACT_KEYWORDS = [
        "主导", "引领", "推动", "驱动", "牵头",
        "影响", "促进", "赋能", "开创", "突破",
    ]

    # 核心技术关键词
    TECH_KEYWORDS = [
        "React", "Vue", "Angular", "TypeScript", "JavaScript",
        "Node.js", "Python", "Java", "Go",
        "Docker", "K8s", "AWS", "GCP",
    ]

    def __init__(self, config: Optional[dict] = None):
        """初始化突出器。

        参数：
            config: 配置字典
        """
        self.config = config or {}

    def highlight_text(self, text: str, mode: str = "html") -> str:
        """高亮文本中的重点内容。

        参数：
            text: 原始文本
            mode: 高亮模式 (html/markdown/plain)

        返回：
            高亮后的文本
        """
        if not text:
            return text

        highlighted = text

        # 1. 高亮量化指标
        highlighted = self._highlight_quantification(highlighted, mode)

        # 2. 高亮影响力动词
        highlighted = self._highlight_impact_verbs(highlighted, mode)

        # 3. 高亮核心技术
        highlighted = self._highlight_tech_keywords(highlighted, mode)

        return highlighted

    def identify_key_points(self, highlights: list[str]) -> list[dict]:
        """识别亮点中的关键点。

        参数：
            highlights: 亮点列表

        返回：
            关键点列表，每个包含分数和原因
        """
        key_points = []

        for hl in highlights:
            score = 0.0
            reasons = []

            # 检查量化指标
            has_quant, quant_count = self._count_quantification(hl)
            if has_quant:
                score += quant_count * 0.3
                reasons.append(f"包含 {quant_count} 个量化指标")

            # 检查影响力动词
            has_impact, impact_count = self._count_impact_verbs(hl)
            if has_impact:
                score += impact_count * 0.2
                reasons.append(f"使用 {impact_count} 个影响力动词")

            # 检查技术关键词
            has_tech, tech_count = self._count_tech_keywords(hl)
            if has_tech:
                score += tech_count * 0.1
                reasons.append(f"涉及 {tech_count} 个核心技术")

            key_points.append({
                "text": hl,
                "score": min(score, 1.0),
                "reasons": reasons,
                "has_quantification": has_quant,
                "has_impact": has_impact,
                "tech_count": tech_count,
            })

        # 按分数排序
        key_points.sort(key=lambda x: x["score"], reverse=True)

        return key_points

    def prioritize_skills(self, skills: list[str],
                          jd_keywords: list[str]) -> list[dict]:
        """优先排序技能。

        参数：
            skills: 技能列表
            jd_keywords: JD 关键词

        返回：
            排序后的技能，包含优先级信息
        """
        prioritized = []

        for skill in skills:
            priority = "normal"
            match_type = None

            # 检查是否与 JD 关键词匹配
            for kw in jd_keywords:
                if kw.lower() in skill.lower():
                    priority = "high"
                    match_type = "jd_match"
                    break

            # 检查是否为核心技术
            if any(t.lower() in skill.lower() for t in self.TECH_KEYWORDS):
                if priority != "high":
                    priority = "medium"
                    match_type = "core_tech"

            prioritized.append({
                "skill": skill,
                "priority": priority,
                "match_type": match_type,
            })

        # 排序：high > medium > normal
        priority_order = {"high": 0, "medium": 1, "normal": 2}
        prioritized.sort(key=lambda x: priority_order.get(x["priority"], 2))

        return prioritized

    # ═══════════════════════════════════════════
    # 内部方法：高亮实现
    # ═══════════════════════════════════════════

    def _highlight_quantification(self, text: str, mode: str) -> str:
        """高亮量化指标。"""
        for kw in self.QUANT_KEYWORDS:
            pattern = rf'(\d+{re.escape(kw)}|\d+\s*{re.escape(kw)}|\d+%\s*{re.escape(kw)})'

            if mode == "html":
                replacement = r'<span class="quant">\1</span>'
            elif mode == "markdown":
                replacement = r'**\1**'
            else:
                replacement = r'\1'

            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)

        return text

    def _highlight_impact_verbs(self, text: str, mode: str) -> str:
        """高亮影响力动词。"""
        for verb in self.IMPACT_KEYWORDS:
            if mode == "html":
                replacement = f'<span class="impact">{verb}</span>'
            elif mode == "markdown":
                replacement = f'**{verb}**'
            else:
                replacement = verb

            text = text.replace(verb, replacement)

        return text

    def _highlight_tech_keywords(self, text: str, mode: str) -> str:
        """高亮技术关键词。"""
        for tech in self.TECH_KEYWORDS:
            if mode == "html":
                replacement = f'<span class="tech">{tech}</span>'
            elif mode == "markdown":
                replacement = f'`{tech}`'
            else:
                replacement = tech

            text = text.replace(tech, replacement)

        return text

    def _count_quantification(self, text: str) -> tuple[bool, int]:
        """计算量化指标数量。"""
        count = 0
        for kw in self.QUANT_KEYWORDS:
            if kw.lower() in text.lower():
                count += text.lower().count(kw.lower())
        return count > 0, count

    def _count_impact_verbs(self, text: str) -> tuple[bool, int]:
        """计算影响力动词数量。"""
        count = 0
        for verb in self.IMPACT_KEYWORDS:
            if verb in text:
                count += text.count(verb)
        return count > 0, count

    def _count_tech_keywords(self, text: str) -> tuple[bool, int]:
        """计算技术关键词数量。"""
        count = 0
        for tech in self.TECH_KEYWORDS:
            if tech.lower() in text.lower():
                count += 1
        return count > 0, count

    # ═══════════════════════════════════════════
    # 公开方法：生成报告
    # ═══════════════════════════════════════════

    def generate_highlight_report(self, highlights: list[str]) -> dict:
        """生成重点报告。

        参数：
            highlights: 亮点列表

        返回：
            重点报告
        """
        key_points = self.identify_key_points(highlights)

        # 统计
        total_quant = sum(1 for kp in key_points if kp["has_quantification"])
        total_impact = sum(1 for kp in key_points if kp["has_impact"])
        avg_score = sum(kp["score"] for kp in key_points) / max(len(key_points), 1)

        # 分类
        strong_points = [kp for kp in key_points if kp["score"] >= 0.5]
        weak_points = [kp for kp in key_points if kp["score"] < 0.3]

        return {
            "total_highlights": len(highlights),
            "strong_points_count": len(strong_points),
            "weak_points_count": len(weak_points),
            "avg_score": round(avg_score, 2),
            "quantification_coverage": round(total_quant / max(len(highlights), 1), 2),
            "impact_coverage": round(total_impact / max(len(highlights), 1), 2),
            "strong_points": strong_points,
            "weak_points": weak_points,
            "suggestions": self._generate_suggestions(key_points),
        }

    def _generate_suggestions(self, key_points: list[dict]) -> list[str]:
        """生成优化建议。"""
        suggestions = []

        # 检查量化覆盖
        no_quant = [kp for kp in key_points if not kp["has_quantification"]]
        if no_quant:
            suggestions.append(
                f"有 {len(no_quant)} 条亮点缺少量化数据，建议补充具体数字"
            )

        # 检查影响力动词
        no_impact = [kp for kp in key_points if not kp["has_impact"]]
        if no_impact:
            suggestions.append(
                f"有 {len(no_impact)} 条亮点使用弱动词，建议替换为影响力动词"
            )

        return suggestions