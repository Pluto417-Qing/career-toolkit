"""经历筛选器。

根据 JD 分析结果，对用户信息库中的经历进行评分和筛选。
"""

import re
from datetime import datetime
from typing import Optional

from .ranker_types import (
    RankedEntry,
    SelectionConfig,
    SelectionResult,
    ScoreDetail,
    DEFAULT_CONFIG,
)


class ExperienceRanker:
    """经历筛选器。"""

    def __init__(self, config: Optional[SelectionConfig] = None):
        """初始化筛选器。

        参数：
            config: 筛选配置，默认使用 DEFAULT_CONFIG
        """
        self.config = config or DEFAULT_CONFIG

    def rank(self, profile: dict, jd_analysis: dict) -> SelectionResult:
        """对信息库中的经历进行评分和筛选。

        参数：
            profile: 用户信息库
            jd_analysis: JD 分析结果

        返回：
            筛选结果
        """
        # 提取 JD 关键词和概念
        jd_keywords = self._extract_all_keywords(jd_analysis)
        jd_concepts = jd_analysis.get("concept_mapping", [])

        # 评分各类经历
        education_ranked = []
        for edu in profile.get("education", []):
            ranked = self._score_entry(edu, "education", jd_keywords, jd_concepts)
            education_ranked.append(ranked)

        work_ranked = []
        for work in profile.get("work", []):
            ranked = self._score_entry(work, "work", jd_keywords, jd_concepts)
            work_ranked.append(ranked)

        projects_ranked = []
        for proj in profile.get("projects", []):
            ranked = self._score_entry(proj, "projects", jd_keywords, jd_concepts)
            projects_ranked.append(ranked)

        # 按分数排序
        education_ranked.sort(key=lambda x: x["score"], reverse=True)
        work_ranked.sort(key=lambda x: x["score"], reverse=True)
        projects_ranked.sort(key=lambda x: x["score"], reverse=True)

        # 筛选（取 Top N，且超过阈值）
        result = self._select_top_entries(
            education_ranked, work_ranked, projects_ranked
        )

        return result

    def _score_entry(self, entry: dict, entry_type: str,
                     jd_keywords: list[str], jd_concepts: list[dict]) -> RankedEntry:
        """对单个条目进行评分。

        参数：
            entry: 条目数据
            entry_type: 条目类型
            jd_keywords: JD 关键词列表
            jd_concepts: JD 概念映射

        返回：
            评分后的条目
        """
        # 获取条目中的所有文本
        entry_text = self._get_entry_text(entry)
        entry_tech = self._get_entry_tech(entry)

        # 1. 关键词匹配得分
        keyword_score, matched_keywords = self._calculate_keyword_score(
            entry_text, entry_tech, jd_keywords
        )

        # 2. 概念关联得分
        concept_score, matched_concepts = self._calculate_concept_score(
            entry_text, entry_tech, jd_concepts
        )

        # 3. 量化成果得分
        quant_score = self._calculate_quant_score(entry)

        # 4. 用户重要性得分
        importance_score = self._calculate_importance_score(entry)

        # 5. 时效性得分
        freshness_score = self._calculate_freshness_score(entry)

        # 加权求和
        total_score = (
            self.config["keyword_weight"] * keyword_score
            + self.config["concept_weight"] * concept_score
            + self.config["quant_weight"] * quant_score
            + self.config["importance_weight"] * importance_score
            + self.config["freshness_weight"] * freshness_score
        )

        # 生成原因说明
        reasons = self._generate_reasons(
            matched_keywords, matched_concepts, quant_score, importance_score
        )

        # 生成优化建议
        suggestions = self._generate_suggestions(
            entry, keyword_score, concept_score, quant_score
        )

        return {
            "id": entry.get("id", ""),
            "entry_type": entry_type,
            "score": round(total_score, 2),
            "score_detail": {
                "keyword_score": round(keyword_score, 2),
                "concept_score": round(concept_score, 2),
                "quant_score": round(quant_score, 2),
                "importance_score": round(importance_score, 2),
                "freshness_score": round(freshness_score, 2),
                "total_score": round(total_score, 2),
            },
            "reasons": reasons,
            "suggestions": suggestions,
            "_raw_entry": entry,  # 保留原始数据
        }

    def _get_entry_text(self, entry: dict) -> str:
        """获取条目文本内容。"""
        texts = []

        # 基础信息
        for key in ["organization", "position", "department", "institution",
                     "name", "role", "description", "summary"]:
            if entry.get(key):
                texts.append(str(entry[key]))

        # 项目背景
        if entry.get("project_context"):
            ctx = entry["project_context"]
            for key in ["name", "description", "business_value", "scale"]:
                if ctx.get(key):
                    texts.append(str(ctx[key]))

        # 个人贡献
        if entry.get("personal_contribution"):
            for contrib in entry["personal_contribution"]:
                for key in ["text", "action", "target", "result", "impact"]:
                    if contrib.get(key):
                        texts.append(str(contrib[key]))

        # 旧格式 highlights
        if entry.get("highlights"):
            for hl in entry["highlights"]:
                texts.append(str(hl))

        # 描述符
        if entry.get("descriptor"):
            desc = entry["descriptor"]
            for key in ["career_goal", "core_courses_confirmed",
                         "quantifiable_results_verified"]:
                if desc.get(key):
                    texts.append(str(desc[key]))

        return " ".join(texts)

    def _get_entry_tech(self, entry: dict) -> list[str]:
        """获取条目技术栈。"""
        tech = []
        if entry.get("tech"):
            tech.extend(entry["tech"])
        if entry.get("project_context", {}).get("tech_stack"):
            tech.extend(entry["project_context"]["tech_stack"])
        if entry.get("personal_contribution"):
            for contrib in entry["personal_contribution"]:
                if contrib.get("tech_used"):
                    tech.extend(contrib["tech_used"])
        return list(set(tech))

    def _calculate_keyword_score(self, entry_text: str, entry_tech: list[str],
                                 jd_keywords: list[str]) -> tuple[float, list[str]]:
        """计算关键词匹配得分。"""
        if not jd_keywords:
            return 0.0, []

        matched = []
        total_weight = 0
        matched_weight = 0

        for kw in jd_keywords:
            total_weight += 1
            kw_lower = kw.lower()

            # 检查技术栈
            if any(kw_lower == t.lower() for t in entry_tech):
                matched.append(kw)
                matched_weight += 1
                continue

            # 检查文本（不区分大小写）
            if kw_lower in entry_text.lower():
                matched.append(kw)
                matched_weight += 0.8  # 文本匹配权重略低

        score = matched_weight / max(total_weight, 1)
        return min(score, 1.0), matched

    def _calculate_concept_score(self, entry_text: str, entry_tech: list[str],
                                  jd_concepts: list[dict]) -> tuple[float, list[str]]:
        """计算概念关联得分。"""
        if not jd_concepts:
            return 0.0, []

        matched_concepts = []
        total_score = 0

        for concept in jd_concepts:
            concept_keywords = concept.get("related_keywords", [])
            if not concept_keywords:
                continue

            concept_matched = False
            for ck in concept_keywords:
                ck_lower = ck.lower()
                # 检查技术栈
                if any(ck_lower == t.lower() for t in entry_tech):
                    concept_matched = True
                    break
                # 检查文本
                if ck_lower in entry_text.lower():
                    concept_matched = True
                    break

            if concept_matched:
                matched_concepts.append(concept["concept"])
                total_score += 1

        score = total_score / max(len(jd_concepts), 1)
        return min(score, 1.0), matched_concepts

    def _calculate_quant_score(self, entry: dict) -> float:
        """计算量化成果得分。"""
        quant_indicators = [
            "%", "倍", "万", "亿", "千", "百万", "千万",
            "star", "stars", "starred", "天", "小时", "分钟",
            "QPS", "qps", "TPS", "tps", "FCP", "LCP", "TTI",
            "MB", "GB", "KB", "kb", "mb", "gb",
            "次", "万次", "千次",
        ]

        # 检查个人贡献
        quant_count = 0
        if entry.get("personal_contribution"):
            for contrib in entry["personal_contribution"]:
                text = " ".join(str(v) for v in contrib.values() if isinstance(v, str))
                for indicator in quant_indicators:
                    if indicator.lower() in text.lower():
                        quant_count += 1
                        break

        # 检查旧格式 highlights
        if entry.get("highlights"):
            for hl in entry["highlights"]:
                for indicator in quant_indicators:
                    if indicator.lower() in str(hl).lower():
                        quant_count += 1
                        break

        # 检查项目背景
        if entry.get("project_context"):
            ctx = entry["project_context"]
            scale = str(ctx.get("scale", ""))
            for indicator in quant_indicators:
                if indicator.lower() in scale.lower():
                    quant_count += 1
                    break

        # 归一化（最多 3 个量化项得满分）
        score = min(quant_count / 3, 1.0)
        return score

    def _calculate_importance_score(self, entry: dict) -> float:
        """计算用户重要性得分。"""
        descriptor = entry.get("descriptor", {})
        rating = descriptor.get("user_importance_rating", 5)
        if isinstance(rating, (int, float)):
            return min(rating / 10, 1.0)
        return 0.5  # 默认中等

    def _calculate_freshness_score(self, entry: dict) -> float:
        """计算时效性得分。"""
        end_date = entry.get("end", "")
        if not end_date:
            return 0.5  # 未知日期，默认中等

        # 解析日期
        try:
            if len(end_date) == 7:  # 格式：2025-09
                end_dt = datetime.strptime(end_date, "%Y-%m")
            elif len(end_date) == 10:  # 格式：2025-09-30
                end_dt = datetime.strptime(end_date, "%Y-%m-%d")
            else:
                return 0.5
        except ValueError:
            return 0.5

        # 计算月份差
        now = datetime.now()
        months_diff = (now.year - end_dt.year) * 12 + (now.month - end_dt.month)

        # 越新得分越高
        if months_diff <= 3:
            return 1.0
        elif months_diff <= 6:
            return 0.85
        elif months_diff <= 12:
            return 0.7
        elif months_diff <= 24:
            return 0.5
        else:
            return 0.3

    def _generate_reasons(self, matched_keywords: list[str],
                          matched_concepts: list[str],
                          quant_score: float,
                          importance_score: float) -> list[str]:
        """生成得分原因说明。"""
        reasons = []

        if matched_keywords:
            reasons.append(f"匹配关键词：{', '.join(matched_keywords[:5])}")

        if matched_concepts:
            reasons.append(f"关联概念：{', '.join(matched_concepts[:3])}")

        if quant_score > 0:
            reasons.append("包含量化成果")

        if importance_score >= 0.8:
            reasons.append("用户评价重要性高")

        return reasons

    def _generate_suggestions(self, entry: dict, keyword_score: float,
                               concept_score: float, quant_score: float) -> list[str]:
        """生成优化建议。"""
        suggestions = []

        if keyword_score < 0.3:
            suggestions.append("关键词匹配度较低，建议补充相关技术栈或项目描述")

        if concept_score < 0.3:
            suggestions.append("概念关联度较低，建议从更高层次描述项目价值")

        if quant_score < 0.3:
            suggestions.append("缺少量化成果，建议补充具体数据（如百分比、倍数、数量等）")

        if not entry.get("descriptor", {}).get("user_importance_rating"):
            suggestions.append("建议为该经历标注重要性评分（1-10）")

        return suggestions

    def _select_top_entries(self, education: list[RankedEntry],
                            work: list[RankedEntry],
                            projects: list[RankedEntry]) -> SelectionResult:
        """选择 Top N 条目。"""
        min_score = self.config["min_score_threshold"]

        # 筛选工作经历
        selected_work = [e for e in work
                         if e["score"] >= min_score and not e["_raw_entry"].get("descriptor", {}).get("hidden", False)]
        selected_work = selected_work[:self.config["max_work_entries"]]

        # 筛选项目经历
        selected_projects = [e for e in projects
                             if e["score"] >= min_score and not e["_raw_entry"].get("descriptor", {}).get("hidden", False)]
        selected_projects = selected_projects[:self.config["max_project_entries"]]

        # 筛选教育经历（通常只取最高分）
        selected_education = [e for e in education
                              if e["score"] >= min_score]
        selected_education = selected_education[:self.config["max_education_entries"]]

        # 被隐藏的条目
        all_selected_ids = set()
        for lst in [selected_work, selected_projects, selected_education]:
            for e in lst:
                all_selected_ids.add(e["id"])

        hidden_entries = []
        for lst, type_name in [(work, "work"), (projects, "projects"), (education, "education")]:
            for e in lst:
                if e["id"] not in all_selected_ids:
                    hidden_entries.append(e)

        # 计算分数汇总
        score_summary = {
            "avg_work_score": self._safe_avg([e["score"] for e in selected_work]),
            "avg_project_score": self._safe_avg([e["score"] for e in selected_projects]),
            "avg_education_score": self._safe_avg([e["score"] for e in selected_education]),
            "total_entries_selected": len(selected_work) + len(selected_projects) + len(selected_education),
            "total_entries_available": len(work) + len(projects) + len(education),
        }

        return {
            "education": selected_education,
            "work": selected_work,
            "projects": selected_projects,
            "hidden_entries": hidden_entries,
            "score_summary": score_summary,
        }

    def _safe_avg(self, values: list[float]) -> float:
        """安全计算平均值。"""
        if not values:
            return 0.0
        return round(sum(values) / len(values), 2)

    def get_jd_keywords_from_analysis(self, jd_analysis: dict) -> list[str]:
        """从 JD 分析结果中提取所有关键词。"""
        keywords = []
        for kw in jd_analysis.get("keywords", {}).get("required", []):
            keywords.append(kw["keyword"])
        for kw in jd_analysis.get("keywords", {}).get("preferred", []):
            keywords.append(kw["keyword"])
        return keywords

    def _extract_all_keywords(self, jd_analysis: dict) -> list[str]:
        """[alias] 从 JD 分析结果中提取所有关键词。"""
        return self.get_jd_keywords_from_analysis(jd_analysis)