"""表达优化器。

负责简历文本的专业化、流畅度和影响力提升。
"""

import re
from pathlib import Path
from typing import Optional

import yaml


class ExpressionOptimizer:
    """表达优化器。"""

    def __init__(self,
                 verbs_config_path: Optional[str] = None,
                 terms_config_path: Optional[str] = None):
        """初始化优化器。

        参数：
            verbs_config_path: 动词配置路径
            terms_config_path: 行业术语配置路径
        """
        self.verbs_config = self._load_config(
            verbs_config_path or
            str(Path(__file__).parent.parent / "assets" / "enhanced_verbs.yaml")
        )
        self.terms_config = self._load_config(
            terms_config_path or
            str(Path(__file__).parent.parent / "assets" / "industry_terms.yaml")
        )

        # 加载弱动词映射
        self.weak_to_strong = self.verbs_config.get("weak_to_strong", {})

        # 加载行业术语映射
        self.industry_terms = self.verbs_config.get("industry_terms", {})

        # 加载强动词列表
        self.strong_verbs = self._extract_strong_verbs()

        # 加载模板
        self.templates = self.verbs_config.get("templates", {})

    def optimize_text(self, text: str, mode: str = "standard") -> str:
        """优化文本。

        参数：
            text: 原始文本
            mode: 优化模式 (standard/aggressive/conservative)

        返回：
            优化后的文本
        """
        if not text:
            return text

        # 1. 替换弱动词
        text = self._replace_weak_verbs(text, mode)

        # 2. 应用行业术语
        text = self._apply_industry_terms(text, mode)

        # 3. 增强表达影响力
        text = self._enhance_impact(text)

        # 4. 清理冗余表达
        text = self._clean_redundancy(text)

        return text

    def optimize_highlight(self, action: str, target: str,
                           result: str = "", impact: str = "") -> str:
        """优化亮点描述。

        参数：
            action: 动作
            target: 目标
            result: 结果
            impact: 影响

        返回：
            优化后的完整句子
        """
        # 优化动词
        optimized_action = self.optimize_text(action, mode="standard")

        # 优化目标和结果
        optimized_target = self._enhance_specificity(target)
        optimized_result = self._enhance_quantification(result)

        # 组合成完整句子
        parts = [optimized_action, optimized_target]

        if optimized_result:
            parts.append(optimized_result)

        if impact:
            parts.append(impact)

        # 使用中文逗号连接
        sentence = "，".join(parts)

        return sentence

    def suggest_improvements(self, text: str) -> list[dict]:
        """提供改进建议。

        参数：
            text: 原始文本

        返回：
            改进建议列表
        """
        suggestions = []

        # 1. 检查弱动词
        weak_verb_suggestions = self._check_weak_verbs(text)
        suggestions.extend(weak_verb_suggestions)

        # 2. 检查模糊表达
        vague_suggestions = self._check_vague_expressions(text)
        suggestions.extend(vague_suggestions)

        # 3. 检查缺少量化
        quant_suggestions = self._check_quantification(text)
        suggestions.extend(quant_suggestions)

        # 4. 检查行业术语使用
        term_suggestions = self._check_industry_terms(text)
        suggestions.extend(term_suggestions)

        return suggestions

    # ═══════════════════════════════════════════
    # 内部方法：文本优化
    # ═══════════════════════════════════════════

    def _replace_weak_verbs(self, text: str, mode: str) -> str:
        """替换弱动词。"""
        for weak, strong in self.weak_to_strong.items():
            # 根据模式决定替换力度
            if mode == "aggressive":
                # 激进模式：全部替换
                text = re.sub(
                    r'^' + weak,
                    strong,
                    text
                )
            elif mode == "standard":
                # 标准模式：只替换句首的弱动词
                if text.startswith(weak):
                    text = strong + text[len(weak):]
            # conservative: 保守模式不替换，只记录建议

        return text

    def _apply_industry_terms(self, text: str, mode: str) -> str:
        """应用行业术语。"""
        for informal, formal in self.industry_terms.items():
            # 只在模式为 aggressive 时替换
            if mode == "aggressive":
                text = text.replace(informal, formal)

        return text

    def _enhance_impact(self, text: str) -> str:
        """增强表达影响力。"""
        # 添加强调词（谨慎使用）
        impact_patterns = [
            (r'^(实现)([^，。]+)$', r'\1了\2'),
            (r'^(完成)([^，。]+)$', r'\1了\2'),
        ]

        for pattern, replacement in impact_patterns:
            text = re.sub(pattern, replacement, text)

        return text

    def _enhance_specificity(self, text: str) -> str:
        """增强具体性。"""
        # 替换模糊词为具体描述
        replacements = {
            "模块": "核心模块",
            "功能": "关键功能",
            "系统": "核心系统",
        }

        for old, new in replacements.items():
            if old in text and new not in text:
                text = text.replace(old, new, 1)

        return text

    def _enhance_quantification(self, text: str) -> str:
        """增强量化描述。"""
        # 如果已经有量化数据，直接返回
        quant_patterns = [r'\d+%', r'\d+倍', r'\d+万', r'star']
        if any(re.search(p, text, re.IGNORECASE) for p in quant_patterns):
            return text

        # 如果有提升、降低等词但缺少数据，添加占位符提示
        if any(w in text for w in ["提升", "降低", "减少", "增加"]):
            if not re.search(r'\d', text):
                # 不修改原文，只返回
                return text

        return text

    def _clean_redundancy(self, text: str) -> str:
        """清理冗余表达。"""
        # 移除重复词汇
        redundancy_patterns = [
            (r'的的', '的'),
            (r'了了', '了'),
            (r'进行实施', '实施'),
            (r'开展进行', '开展'),
        ]

        for pattern, replacement in redundancy_patterns:
            text = re.sub(pattern, replacement, text)

        return text

    # ═══════════════════════════════════════════
    # 内部方法：检查与建议
    # ═══════════════════════════════════════════

    def _check_weak_verbs(self, text: str) -> list[dict]:
        """检查弱动词使用。"""
        suggestions = []

        for weak_verb in self.weak_to_strong.keys():
            if weak_verb in text:
                strong_verb = self.weak_to_strong[weak_verb]
                suggestions.append({
                    "type": "weak_verb",
                    "issue": f"使用了弱动词「{weak_verb}」",
                    "suggestion": f"建议替换为「{strong_verb}」",
                    "example": text.replace(weak_verb, strong_verb, 1),
                    "priority": "high",
                })

        return suggestions

    def _check_vague_expressions(self, text: str) -> list[dict]:
        """检查模糊表达。"""
        suggestions = []

        vague_words = ["很多", "一些", "大量", "各种", "较好", "不错"]

        for word in vague_words:
            if word in text:
                suggestions.append({
                    "type": "vague_expression",
                    "issue": f"使用了模糊表达「{word}」",
                    "suggestion": "建议使用具体数字或描述",
                    "example": f"例如：将「{word}」替换为具体数量",
                    "priority": "medium",
                })

        return suggestions

    def _check_quantification(self, text: str) -> list[dict]:
        """检查量化数据。"""
        suggestions = []

        # 检查是否有"提升"、"降低"等词但缺少数据
        impact_words = ["提升", "降低", "减少", "增加", "优化", "改进"]
        has_quant = bool(re.search(r'\d+%|\d+倍|\d+万|star', text, re.IGNORECASE))

        if any(w in text for w in impact_words) and not has_quant:
            suggestions.append({
                "type": "missing_quantification",
                "issue": "描述了改进但缺少量化数据",
                "suggestion": "建议补充具体百分比或数值",
                "example": "例如：提升 45%、增加 3 倍、节省 100 万",
                "priority": "high",
            })

        return suggestions

    def _check_industry_terms(self, text: str) -> list[dict]:
        """检查行业术语使用。"""
        suggestions = []

        for informal, formal in self.industry_terms.items():
            if informal in text:
                suggestions.append({
                    "type": "industry_term",
                    "issue": f"使用了非专业术语「{informal}」",
                    "suggestion": f"建议使用专业术语「{formal}」",
                    "example": text.replace(informal, formal),
                    "priority": "low",
                })

        return suggestions

    def _extract_strong_verbs(self) -> list[str]:
        """提取所有强动词。"""
        strong_verbs = []

        for category, verbs in self.verbs_config.items():
            if category in ["technical", "impact", "collaboration", "innovation"]:
                for sub_category, verb_list in verbs.items():
                    if isinstance(verb_list, list):
                        strong_verbs.extend(verb_list)

        return list(set(strong_verbs))

    def _load_config(self, path: str) -> dict:
        """加载配置文件。"""
        try:
            with open(path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except FileNotFoundError:
            return {}

    # ═══════════════════════════════════════════
    # 公开方法：模板应用
    # ═══════════════════════════════════════════

    def apply_star_template(self, situation: str, task: str,
                            action: str, result: str) -> str:
        """应用 STAR 模板。

        参数：
            situation: 情境
            task: 任务
            action: 行动
            result: 结果

        返回：
            应用模板后的句子
        """
        template = self.templates.get("star", {})
        parts = []

        if situation:
            parts.append(template.get("situation", "在{context}场景下，").format(context=situation))
        if task:
            parts.append(template.get("task", "负责{task}，").format(task=task))
        if action:
            parts.append(template.get("action", "通过{action}，").format(action=action))
        if result:
            parts.append(template.get("result", "实现了{result}。").format(result=result))

        return "".join(parts)

    def apply_quantified_template(self, action: str, target: str,
                                  metric: str, value: str, unit: str = "%") -> str:
        """应用量化结果模板。

        参数：
            action: 动作
            target: 目标
            metric: 指标
            value: 数值
            unit: 单位

        返回：
            应用模板后的句子
        """
        templates = self.templates.get("quantified", [])
        if not templates:
            return f"{action}{target}，{metric}{value}{unit}"

        # 使用第一个模板
        template = templates[0]
        return template.format(
            action=action,
            target=target,
            metric=metric,
            value=value,
            unit=unit
        )