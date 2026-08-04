"""经历筛选类型定义。"""

from typing import TypedDict, Any


class ScoreDetail(TypedDict, total=False):
    """评分详情。"""
    keyword_score: float  # 关键词匹配得分
    concept_score: float  # 概念关联得分
    quant_score: float  # 量化成果得分
    importance_score: float  # 用户重要性得分
    freshness_score: float  # 时效性得分
    total_score: float  # 总得分


class RankedEntry(TypedDict, total=False):
    """排序后的条目。"""
    id: str
    entry_type: str  # work/project/education
    score: float
    score_detail: ScoreDetail
    reasons: list[str]  # 得分原因
    suggestions: list[str]  # 优化建议


class SelectionConfig(TypedDict, total=False):
    """筛选配置。"""
    max_work_entries: int  # 最大保留工作经历数
    max_project_entries: int  # 最大保留项目数
    max_education_entries: int  # 最大保留教育经历数
    min_score_threshold: float  # 最低分数阈值
    keyword_weight: float  # 关键词权重
    concept_weight: float  # 概念权重
    quant_weight: float  # 量化成果权重
    importance_weight: float  # 用户重要性权重
    freshness_weight: float  # 时效性权重


class SelectionResult(TypedDict, total=False):
    """筛选结果。"""
    education: list[RankedEntry]
    work: list[RankedEntry]
    projects: list[RankedEntry]
    hidden_entries: list[RankedEntry]  # 被隐藏的条目
    score_summary: dict  # 分数汇总


DEFAULT_CONFIG: SelectionConfig = {
    "max_work_entries": 3,
    "max_project_entries": 3,
    "max_education_entries": 1,
    "min_score_threshold": 0.3,
    "keyword_weight": 0.35,
    "concept_weight": 0.25,
    "quant_weight": 0.20,
    "importance_weight": 0.10,
    "freshness_weight": 0.10,
}