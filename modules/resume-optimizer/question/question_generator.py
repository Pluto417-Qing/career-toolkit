"""提问生成器。

检测信息缺失，生成针对性问题。
"""

import re
import uuid
from typing import Optional

from .question_types import Question, QuestionType, QuestionPriority, QuestionSet


class QuestionGenerator:
    """提问生成器。"""

    # 弱动词模式
    WEAK_VERB_PATTERNS = [
        (r'负责(.+)', '负责 {target}，具体做了什么？有什么量化成果？'),
        (r'参与(.+)', '参与 {target}，在其中具体承担什么角色？'),
        (r'协助(.+)', '协助 {target}，具体贡献了什么？'),
        (r'学习(.+)', '学习了 {target}，是否有实际应用成果？'),
        (r'了解(.+)', '了解 {target}，是否在项目中使用过？'),
    ]

    # 模糊表述模式
    VAGUE_PATTERNS = [
        (r'性能优化', '性能优化：具体提升了多少？有哪些指标？'),
        (r'优化了', '优化了：具体做了什么优化？效果如何？'),
        (r'重构了', '重构了：重构的原因是什么？带来了什么改善？'),
        (r'设计了', '设计了：设计的思路是什么？解决了什么问题？'),
        (r'实现了', '实现了：实现的难点是什么？有什么创新？'),
        (r'开发了', '开发了：开发过程中遇到了什么挑战？'),
    ]

    def __init__(self, max_questions: int = 10):
        """初始化提问生成器。

        参数：
            max_questions: 最多生成的问题数量
        """
        self.max_questions = max_questions

    def generate_questions(self, profile: dict, jd_analysis: dict,
                            selection_result: dict) -> QuestionSet:
        """生成针对性问题。

        参数：
            profile: 用户信息库
            jd_analysis: JD 分析结果
            selection_result: 筛选结果

        返回：
            问题集合
        """
        questions = []

        # 1. 检测量化数据缺失
        questions.extend(
            self._detect_missing_quantification(profile, selection_result)
        )

        # 2. 检测相关性确认
        questions.extend(
            self._detect_relevance_issues(profile, jd_analysis, selection_result)
        )

        # 3. 检测歧义表述
        questions.extend(
            self._detect_clarification_needs(profile, selection_result)
        )

        # 4. 检测缺失描述符信息
        questions.extend(
            self._detect_missing_descriptors(profile, selection_result)
        )

        # 5. 一页纸裁剪确认
        questions.extend(
            self._detect_page_constraint_issues(selection_result)
        )

        # 6. 确认筛选结果
        questions.extend(
            self._generate_selection_confirmation(selection_result)
        )

        # 按优先级排序
        priority_order = {
            QuestionPriority.HIGH: 0,
            QuestionPriority.MEDIUM: 1,
            QuestionPriority.LOW: 2,
        }
        questions.sort(key=lambda q: priority_order.get(q["priority"], 3))

        # 限制数量
        questions = questions[:self.max_questions]

        # 构建问题集合
        question_set = {
            "questions": questions,
            "total_count": len(questions),
            "high_priority_count": sum(1 for q in questions if q["priority"] == QuestionPriority.HIGH),
            "medium_priority_count": sum(1 for q in questions if q["priority"] == QuestionPriority.MEDIUM),
            "low_priority_count": sum(1 for q in questions if q["priority"] == QuestionPriority.LOW),
            "grouped_by_type": self._group_by_type(questions),
        }

        return question_set

    def _detect_missing_quantification(self, profile: dict,
                                        selection_result: dict) -> list[Question]:
        """检测缺少量化数据的条目。"""
        questions = []
        quant_patterns = [r'\d+%', r'\d+倍', r'\d+万', r'\d+star', r'QPS', r'TPS']

        for section, entry_type in [("work", "work"), ("projects", "projects")]:
            for ranked_entry in selection_result.get(section, []):
                raw_entry = ranked_entry.get("_raw_entry", {})
                highlights = self._get_all_highlights(raw_entry)

                # 检查每个亮点是否有量化数据
                for hl in highlights:
                    has_quant = any(re.search(p, hl, re.IGNORECASE) for p in quant_patterns)
                    if not has_quant:
                        questions.append({
                            "id": f"q_{uuid.uuid4().hex[:8]}",
                            "type": QuestionType.MISSING_QUANTIFICATION,
                            "priority": QuestionPriority.HIGH,
                            "target_entry_id": raw_entry.get("id", ""),
                            "target_entry_type": entry_type,
                            "question": f"这段经历的「{hl[:30]}...」是否可以补充量化数据？例如百分比、倍数、数量等。",
                            "context": f"{raw_entry.get('organization', '')} - {raw_entry.get('position', '')}",
                            "suggested_answer": "格式：具体的数字 + 单位，如「提升45%」、「3倍」",
                            "status": "pending",
                        })

                        # 每个条目最多一个量化问题
                        break

        return questions

    def _detect_relevance_issues(self, profile: dict, jd_analysis: dict,
                                  selection_result: dict) -> list[Question]:
        """检测相关性问题。"""
        questions = []
        jd_keywords = self._extract_jd_keywords(jd_analysis)

        for section, entry_type in [("work", "work"), ("projects", "projects")]:
            for ranked_entry in selection_result.get(section, []):
                raw_entry = ranked_entry.get("_raw_entry", {})
                entry_tech = raw_entry.get("tech", [])

                # 检查 JD 要求的技能是否在条目中出现
                for kw in jd_keywords:
                    if kw.lower() in [t.lower() for t in entry_tech]:
                        # 检查是否有实际使用的证据
                        contributions = raw_entry.get("personal_contribution", [])
                        has_evidence = any(
                            kw.lower() in str(c).lower()
                            for c in contributions
                        )

                        if not has_evidence and contributions:
                            questions.append({
                                "id": f"q_{uuid.uuid4().hex[:8]}",
                                "type": QuestionType.RELEVANCE_CHECK,
                                "priority": QuestionPriority.HIGH,
                                "target_entry_id": raw_entry.get("id", ""),
                                "target_entry_type": entry_type,
                                "question": f"「{kw}」在「{raw_entry.get('organization', raw_entry.get('name', ''))}」中是否实际使用过？如果是，能否补充具体使用场景？",
                                "context": f"技术栈中包含 {kw}，但在具体贡献中未找到使用证据",
                                "suggested_answer": "描述具体使用场景和成果",
                                "status": "pending",
                            })

        return questions

    def _detect_clarification_needs(self, profile: dict,
                                     selection_result: dict) -> list[Question]:
        """检测需要歧义澄清的条目。"""
        questions = []

        for section, entry_type in [("work", "work"), ("projects", "projects")]:
            for ranked_entry in selection_result.get(section, []):
                raw_entry = ranked_entry.get("_raw_entry", {})
                highlights = self._get_all_highlights(raw_entry)

                for hl in highlights:
                    # 检查模糊表述
                    for pattern, question_template in self.WEAK_VERB_PATTERNS:
                        match = re.match(pattern, hl)
                        if match:
                            target = match.group(1).strip()
                            questions.append({
                                "id": f"q_{uuid.uuid4().hex[:8]}",
                                "type": QuestionType.CLARIFICATION,
                                "priority": QuestionPriority.MEDIUM,
                                "target_entry_id": raw_entry.get("id", ""),
                                "target_entry_type": entry_type,
                                "question": question_template.format(target=target),
                                "context": f"原描述：「{hl[:50]}...」",
                                "suggested_answer": "具体描述做了什么、结果如何",
                                "status": "pending",
                            })
                            break

        return questions

    def _detect_missing_descriptors(self, profile: dict,
                                     selection_result: dict) -> list[Question]:
        """检测缺失的描述符信息。"""
        questions = []
        seen_entries = set()  # 避免重复

        for section, entry_type in [("work", "work"), ("projects", "projects"), ("education", "education")]:
            for ranked_entry in selection_result.get(section, []):
                raw_entry = ranked_entry.get("_raw_entry", {})
                entry_id = raw_entry.get("id", "")
                
                # 避免重复检测
                if entry_id in seen_entries:
                    continue
                seen_entries.add(entry_id)
                
                descriptor = raw_entry.get("descriptor", {})

                # 检查是否有重要性评分
                if "user_importance_rating" not in descriptor:
                    entry_name = raw_entry.get("organization", 
                                  raw_entry.get("name",
                                  raw_entry.get("institution", entry_id)))
                    questions.append({
                        "id": f"q_{uuid.uuid4().hex[:8]}",
                        "type": QuestionType.MISSING_DESCRIPTOR,
                        "priority": QuestionPriority.LOW,
                        "target_entry_id": entry_id,
                        "target_entry_type": entry_type,
                        "question": f"请为「{entry_name}」的经历打分（1-10分），帮助我们更好地筛选内容。",
                        "context": "用于简历筛选排序",
                        "options": [
                            {"value": "10", "label": "非常重要"},
                            {"value": "8", "label": "重要"},
                            {"value": "5", "label": "一般"},
                            {"value": "3", "label": "不太重要"},
                        ],
                        "status": "pending",
                    })

                # 检查项目背景是否完整
                if entry_type == "work":
                    project_ctx = raw_entry.get("project_context", {})
                    if not project_ctx.get("scale"):
                        questions.append({
                            "id": f"q_{uuid.uuid4().hex[:8]}",
                            "type": QuestionType.MISSING_DESCRIPTOR,
                            "priority": QuestionPriority.MEDIUM,
                            "target_entry_id": raw_entry.get("id", ""),
                            "target_entry_type": entry_type,
                            "question": f"「{raw_entry.get('organization', '')}」实习的项目规模如何？例如用户量、日活等。",
                            "context": "补充项目背景，有助于简历筛选",
                            "suggested_answer": "例如：日活500万+、用户量100万+",
                            "status": "pending",
                        })

        return questions

    def _detect_page_constraint_issues(self, selection_result: dict) -> list[Question]:
        """检测一页纸约束问题。"""
        questions = []
        summary = selection_result.get("score_summary", {})

        total_selected = summary.get("total_entries_selected", 0)
        total_available = summary.get("total_entries_available", 0)

        # 如果筛选掉了一些条目，询问确认
        hidden = selection_result.get("hidden_entries", [])
        if hidden:
            hidden_by_type = {}
            for h in hidden:
                t = h["entry_type"]
                if t not in hidden_by_type:
                    hidden_by_type[t] = []
                hidden_by_type[t].append(h)

            for entry_type, entries in hidden_by_type.items():
                entry_names = []
                for e in entries:
                    raw = e.get("_raw_entry", {})
                    name = raw.get("organization", raw.get("name", e["id"]))
                    entry_names.append(f"{name} (分数 {e['score']})")

                type_label = {"work": "工作经历", "projects": "项目经历", "education": "教育背景"}.get(entry_type, entry_type)

                questions.append({
                    "id": f"q_{uuid.uuid4().hex[:8]}",
                    "type": QuestionType.PAGE_CONSTRAINT,
                    "priority": QuestionPriority.MEDIUM,
                    "target_entry_id": "",
                    "target_entry_type": entry_type,
                    "question": f"一页纸简历建议隐藏以下{type_label}：{', '.join(entry_names)}。是否同意？",
                    "context": f"由于一页纸限制，共隐藏 {len(entries)} 条{type_label}",
                    "options": [
                        {"value": "agree", "label": "同意隐藏"},
                        {"value": "keep", "label": "保留（可能超出一页）"},
                        {"value": "adjust", "label": "调整优先级"},
                    ],
                    "status": "pending",
                })

        return questions

    def _generate_selection_confirmation(self, selection_result: dict) -> list[Question]:
        """生成筛选结果确认问题。"""
        questions = []

        for section, label in [("work", "工作经历"), ("projects", "项目经历")]:
            selected = selection_result.get(section, [])
            if selected:
                entry_names = []
                for e in selected:
                    raw = e.get("_raw_entry", {})
                    name = raw.get("organization", raw.get("name", ""))
                    entry_names.append(f"{name} (分数 {e['score']})")

                questions.append({
                    "id": f"q_{uuid.uuid4().hex[:8]}",
                    "type": QuestionType.CONFIRM_SELECTION,
                    "priority": QuestionPriority.LOW,
                    "target_entry_id": "",
                    "target_entry_type": section,
                    "question": f"为该岗位推荐的{label}（按相关性排序）：{', '.join(entry_names)}。是否需要调整顺序或增减？",
                    "context": "可以调整、删除或添加经历",
                    "options": [
                        {"value": "ok", "label": "没问题"},
                        {"value": "reorder", "label": "调整顺序"},
                        {"value": "remove", "label": "删除某些"},
                        {"value": "add", "label": "添加被隐藏的"},
                    ],
                    "status": "pending",
                })

        return questions

    def _get_all_highlights(self, entry: dict) -> list[str]:
        """获取条目的所有亮点文本。"""
        highlights = []

        # 个人贡献
        for contrib in entry.get("personal_contribution", []):
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

        # 旧格式 highlights
        for hl in entry.get("highlights", []):
            if isinstance(hl, str):
                highlights.append(hl)
            elif isinstance(hl, dict) and hl.get("text"):
                highlights.append(hl["text"])

        return highlights

    def _extract_jd_keywords(self, jd_analysis: dict) -> list[str]:
        """从 JD 分析中提取关键词。"""
        keywords = []
        for kw in jd_analysis.get("keywords", {}).get("required", []):
            keywords.append(kw["keyword"])
        for kw in jd_analysis.get("keywords", {}).get("preferred", []):
            keywords.append(kw["keyword"])
        return keywords

    def _group_by_type(self, questions: list[Question]) -> dict[str, list[Question]]:
        """按类型分组问题。"""
        grouped = {}
        for q in questions:
            q_type = q["type"]
            if q_type not in grouped:
                grouped[q_type] = []
            grouped[q_type].append(q)
        return grouped

    def answer_question(self, question_set: QuestionSet, question_id: str,
                         answer: str) -> QuestionSet:
        """回答问题。

        参数：
            question_set: 问题集合
            question_id: 问题 ID
            answer: 用户回答

        返回：
            更新后的问题集合
        """
        for q in question_set["questions"]:
            if q["id"] == question_id:
                q["status"] = "answered"
                q["user_answer"] = answer
                break

        return question_set

    def skip_question(self, question_set: QuestionSet, question_id: str) -> QuestionSet:
        """跳过问题。

        参数：
            question_set: 问题集合
            question_id: 问题 ID

        返回：
            更新后的问题集合
        """
        for q in question_set["questions"]:
            if q["id"] == question_id:
                q["status"] = "skipped"
                break

        return question_set

    def get_pending_questions(self, question_set: QuestionSet) -> list[Question]:
        """获取待回答的问题。"""
        return [q for q in question_set["questions"] if q["status"] == "pending"]

    def get_answered_questions(self, question_set: QuestionSet) -> list[Question]:
        """获取已回答的问题。"""
        return [q for q in question_set["questions"] if q["status"] == "answered"]