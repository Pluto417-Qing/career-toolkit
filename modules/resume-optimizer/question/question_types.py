"""提问生成类型定义。"""

from typing import TypedDict
from enum import Enum


class QuestionType(str, Enum):
    """问题类型。"""
    MISSING_QUANTIFICATION = "missing_quantification"  # 缺少量化数据
    RELEVANCE_CHECK = "relevance_check"  # 相关性确认
    CLARIFICATION = "clarification"  # 歧义澄清
    PAGE_CONSTRAINT = "page_constraint"  # 一页纸裁剪确认
    MISSING_DESCRIPTOR = "missing_descriptor"  # 缺少描述信息
    CONFIRM_SELECTION = "confirm_selection"  # 确认筛选结果


class QuestionPriority(str, Enum):
    """问题优先级。"""
    HIGH = "high"  # 高优先级：影响简历质量
    MEDIUM = "medium"  # 中优先级：优化内容
    LOW = "low"  # 低优先级：锦上添花


class Question(TypedDict, total=False):
    """问题定义。"""
    id: str
    type: QuestionType
    priority: QuestionPriority
    target_entry_id: str  # 目标条目 ID
    target_entry_type: str  # 目标条目类型
    question: str  # 问题文本
    context: str  # 问题上下文
    options: list[dict]  # 可选答案
    suggested_answer: str  # 建议答案格式
    status: str  # pending | answered | skipped
    user_answer: str  # 用户回答


class QuestionSet(TypedDict, total=False):
    """问题集合。"""
    questions: list[Question]
    total_count: int
    high_priority_count: int
    medium_priority_count: int
    low_priority_count: int
    grouped_by_type: dict[str, list[Question]]