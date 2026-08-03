"""内容精简器。

负责合并项目双视角、移除弱动词、控制一页纸。
"""

import re
from typing import Optional

from .condenser_types import CondensedEntry, CondensedResume, CondenseConfig, DEFAULT_CONDENSE_CONFIG


# 弱动词列表（应被移除或替换）
WEAK_VERBS = [
    "负责", "参与", "协助", "学习", "了解",
    "进行", "开展", "推进", "配合", "支持",
    "参与了", "负责了", "协助了",
]

# 强动词列表（用于替换弱动词）
STRONG_VERB_MAP = {
    "负责": "主导",
    "参与": "贡献",
    "协助": "支持",
    "学习": "掌握",
    "了解": "深入理解",
    "进行": "执行",
    "开展": "推动",
    "推进": "驱动",
    "配合": "协同",
    "支持": "赋能",
}


class ContentCondenser:
    """内容精简器。"""

    def __init__(self, config: Optional[CondenseConfig] = None):
        """初始化精简器。

        参数：
            config: 精简配置
        """
        self.config = config or DEFAULT_CONDENSE_CONFIG

    def condense_resume(self, profile: dict, selection_result: dict) -> CondensedResume:
        """精简简历。

        参数：
            profile: 用户信息库
            selection_result: 筛选结果（来自 experience_ranker）

        返回：
            精简后的简历
        """
        # 获取筛选后的条目
        selected_education = selection_result.get("education", [])
        selected_work = selection_result.get("work", [])
        selected_projects = selection_result.get("projects", [])

        # 精简各类条目
        condensed_education = []
        for entry in selected_education:
            raw = entry.get("_raw_entry", {})
            condensed = self._condense_education(raw)
            condensed_education.append(condensed)

        condensed_work = []
        for entry in selected_work:
            raw = entry.get("_raw_entry", {})
            condensed = self._condense_work_entry(raw)
            condensed_work.append(condensed)

        condensed_projects = []
        for entry in selected_projects:
            raw = entry.get("_raw_entry", {})
            condensed = self._condense_project_entry(raw)
            condensed_projects.append(condensed)

        # 构建精简简历
        condensed_resume = {
            "meta": {
                "condensed": True,
                "profile_id": profile.get("meta", {}).get("id", ""),
            },
            "basics": profile.get("basics", {}),
            "education": condensed_education,
            "work": condensed_work,
            "projects": condensed_projects,
            "skills": self._extract_skills(profile),
        }

        # 估算页数
        self._estimate_page(condensed_resume)

        # 如果超出一页纸，继续精简
        if not condensed_resume["fits_one_page"]:
            condensed_resume = self._further_condense(condensed_resume)

        return condensed_resume

    def _condense_education(self, entry: dict) -> CondensedEntry:
        """精简教育背景。"""
        condensed = {
            "id": entry.get("id", ""),
            "entry_type": "education",
            "title": entry.get("institution", ""),
            "subtitle": f"{entry.get('area', '')} · {entry.get('degree', '')}" if entry.get("area") else "",
            "period": f"{entry.get('start', '')} - {entry.get('end', '')}" if entry.get("start") else "",
            "highlights": [],
        }

        # 添加 GPA 和核心课程
        highlights = []
        if entry.get("gpa"):
            highlights.append(f"GPA: {entry['gpa']}")
        if entry.get("honors"):
            honors = entry["honors"]
            if isinstance(honors, list) and honors:
                highlights.append(f"荣誉：{', '.join(honors[:2])}")

        # 添加核心课程（从 descriptor 获取）
        descriptor = entry.get("descriptor", {})
        if descriptor.get("core_courses_confirmed"):
            courses = entry.get("courses", [])
            if courses:
                highlights.append(f"核心课程：{', '.join(courses[:4])}")

        condensed["highlights"] = highlights
        return condensed

    def _condense_work_entry(self, entry: dict) -> CondensedEntry:
        """精简工作经历。"""
        condensed = {
            "id": entry.get("id", ""),
            "entry_type": "work",
            "title": entry.get("organization", ""),
            "subtitle": entry.get("position", ""),
            "period": f"{entry.get('start', '')} - {entry.get('end', '')}" if entry.get("start") else "",
            "highlights": [],
            "tech_stack": entry.get("tech", []),
        }

        # 合并双视角（项目背景 + 个人贡献）
        if self.config["merge_dual_perspective"]:
            highlights = self._merge_dual_perspective(entry)
        else:
            # 仅使用个人贡献
            highlights = self._extract_contributions(entry)

        # 精简亮点
        highlights = self._trim_highlights(highlights)

        condensed["highlights"] = highlights
        return condensed

    def _condense_project_entry(self, entry: dict) -> CondensedEntry:
        """精简项目经历。"""
        condensed = {
            "id": entry.get("id", ""),
            "entry_type": "projects",
            "title": entry.get("name", ""),
            "subtitle": entry.get("role", ""),
            "period": "",
            "highlights": [],
            "tech_stack": entry.get("tech", []),
        }

        # 如果有 URL，添加到副标题
        if entry.get("url"):
            condensed["subtitle"] = f"{entry.get('role', '')} · {entry['url']}"

        # 合并双视角
        if self.config["merge_dual_perspective"]:
            highlights = self._merge_dual_perspective(entry)
        else:
            highlights = self._extract_contributions(entry)

        # 精简亮点
        highlights = self._trim_highlights(highlights)

        condensed["highlights"] = highlights
        return condensed

    def _merge_dual_perspective(self, entry: dict) -> list[str]:
        """合并项目双视角。

        格式：{action} {target}，{result}
        例如：主导 Schema 化改造，代码量下降 45%
        """
        highlights = []

        # 获取项目背景
        project_ctx = entry.get("project_context", {})
        project_name = project_ctx.get("name", "")
        project_scale = project_ctx.get("scale", "")
        project_desc = project_ctx.get("description", "")

        # 获取个人贡献
        contributions = entry.get("personal_contribution", [])

        if not contributions:
            # 没有个人贡献，使用旧格式 highlights
            old_highlights = entry.get("highlights", [])
            if old_highlights:
                return self._normalize_highlights(old_highlights)

            # 使用项目背景生成简要描述
            brief = project_name or project_desc
            if project_scale:
                brief += f"（{project_scale}）"
            if brief:
                return [brief]
            return []

        # 处理每个贡献
        for contrib in contributions:
            action = contrib.get("action", "")
            target = contrib.get("target", "")
            result = contrib.get("result", "")
            impact = contrib.get("impact", "")

            # 构建合并后的句子
            parts = []

            # 如果有项目背景且 target 是空，使用项目名
            effective_target = target
            if not effective_target and project_name:
                effective_target = project_name

            # action + target
            if action and effective_target:
                parts.append(f"{action} {effective_target}")
            elif action:
                parts.append(action)
            elif effective_target:
                parts.append(effective_target)

            # result
            if result:
                parts.append(result)

            # impact
            if impact and impact not in result:
                parts.append(impact)

            if parts:
                # 使用中文标点连接
                highlight = "，".join(parts)
                highlights.append(highlight)

        return highlights

    def _extract_contributions(self, entry: dict) -> list[str]:
        """仅提取个人贡献。"""
        highlights = []
        contributions = entry.get("personal_contribution", [])

        for contrib in contributions:
            text = contrib.get("text", "")
            if text:
                highlights.append(text)
            else:
                # 从 action/target/result 构建
                parts = []
                if contrib.get("action"):
                    parts.append(contrib["action"])
                if contrib.get("target"):
                    parts.append(contrib["target"])
                if contrib.get("result"):
                    parts.append(contrib["result"])
                if parts:
                    highlights.append("，".join(parts))

        return highlights

    def _normalize_highlights(self, highlights: list) -> list[str]:
        """标准化旧格式 highlights。"""
        normalized = []
        for hl in highlights:
            if isinstance(hl, str):
                normalized.append(hl)
            elif isinstance(hl, dict):
                text = hl.get("text", "")
                if text:
                    normalized.append(text)
        return normalized

    def _trim_highlights(self, highlights: list[str]) -> list[str]:
        """精简亮点列表。"""
        if not highlights:
            return []

        # 移除空字符串
        highlights = [h.strip() for h in highlights if h and h.strip()]

        # 移除弱动词开头的句子
        if self.config["remove_weak_verbs"]:
            filtered = []
            for h in highlights:
                # 检查是否以弱动词开头
                is_weak = False
                for weak_verb in WEAK_VERBS:
                    if h.startswith(weak_verb):
                        is_weak = True
                        break

                if is_weak:
                    # 尝试用强动词替换
                    replaced = self._replace_weak_verb(h)
                    if replaced and len(replaced.strip()) > 5:  # 替换后有实质内容
                        filtered.append(replaced)
                    # 否则跳过这条
                else:
                    filtered.append(h)
            highlights = filtered

        # 限制数量
        max_highlights = self.config["max_highlights_per_entry"]
        if len(highlights) > max_highlights:
            # 优先保留有量化数据的亮点
            scored = [(self._has_quantifiable_data(h), h) for h in highlights]
            scored.sort(key=lambda x: x[0], reverse=True)
            highlights = [h for _, h in scored[:max_highlights]]

        return highlights

    def _replace_weak_verb(self, text: str) -> str:
        """替换弱动词。"""
        for weak_verb, strong_verb in STRONG_VERB_MAP.items():
            if text.startswith(weak_verb):
                return strong_verb + text[len(weak_verb):]
        return text

    def _has_quantifiable_data(self, text: str) -> bool:
        """检查是否包含量化数据。"""
        quant_patterns = [
            r'\d+%', r'\d+倍', r'\d+万', r'\d+亿', r'\d+千',
            r'\d+star', r'\d+ stars', r'star',
            r'\d+QPS', r'\d+TPS',
            r'\d+MB', r'\d+GB', r'\d+KB',
            r'%\d+', r'降低\d+', r'提升\d+',
        ]
        for pattern in quant_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False

    def _extract_skills(self, profile: dict) -> list[dict]:
        """提取技能列表。"""
        skills = profile.get("skills", [])
        result = []

        for skill in skills:
            result.append({
                "id": skill.get("id", ""),
                "name": skill.get("name", ""),
                "keywords": skill.get("keywords", []),
            })

        return result

    def _estimate_page(self, resume: CondensedResume):
        """估算页数。"""
        # 计算行数
        line_count = 0

        # 基础信息：约 3 行
        line_count += 3

        # 教育背景
        for edu in resume.get("education", []):
            line_count += 2  # 标题行
            line_count += len(edu.get("highlights", []))

        # 工作经历
        for work in resume.get("work", []):
            line_count += 2  # 标题行
            line_count += len(work.get("highlights", []))

        # 项目经历
        for proj in resume.get("projects", []):
            line_count += 2  # 标题行
            line_count += len(proj.get("highlights", []))

        # 技能：约 3 行
        line_count += 3

        # 计算字数
        word_count = 0
        for section in ["education", "work", "projects"]:
            for entry in resume.get(section, []):
                word_count += len(entry.get("title", ""))
                word_count += len(entry.get("subtitle", ""))
                word_count += len(entry.get("highlights", [])) * 30  # 估算每个亮点 30 字

        resume["line_count"] = line_count
        resume["word_count"] = word_count
        resume["estimated_pages"] = round(line_count / self.config["page_line_limit"], 1)
        resume["fits_one_page"] = line_count <= self.config["page_line_limit"]

    def _further_condense(self, resume: CondensedResume) -> CondensedResume:
        """进一步精简以适应一页纸。"""
        print(f"  ⚠️ 超出一页纸，继续精简...")
        print(f"     当前行数：{resume['line_count']}，限制：{self.config['page_line_limit']}")

        # 策略 1：减少每个条目最多保留的亮点数
        original_max = self.config["max_highlights_per_entry"]

        for max_hl in [2, 1]:
            self.config["max_highlights_per_entry"] = max_hl

            # 重新精简
            for section in ["education", "work", "projects"]:
                for entry in resume.get(section, []):
                    entry["highlights"] = self._trim_highlights(
                        entry.get("highlights", [])
                    )

            # 重新估算
            self._estimate_page(resume)

            if resume["fits_one_page"]:
                print(f"  ✅ 精简到 {max_hl} 条亮点后适应一页纸")
                break

        # 如果还不行，减少条目数
        if not resume["fits_one_page"]:
            # 策略 2：减少工作经历
            while len(resume.get("work", [])) > 1 and not resume["fits_one_page"]:
                resume["work"] = resume["work"][:-1]
                self._estimate_page(resume)

            # 策略 3：减少项目经历
            while len(resume.get("projects", [])) > 1 and not resume["fits_one_page"]:
                resume["projects"] = resume["projects"][:-1]
                self._estimate_page(resume)

        # 恢复原始配置
        self.config["max_highlights_per_entry"] = original_max

        print(f"  📊 最终行数：{resume['line_count']}，页数：{resume['estimated_pages']}")
        return resume