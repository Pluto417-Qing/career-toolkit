"""JD 分析器类型定义。"""

from typing import TypedDict, Any


class Keyword(TypedDict, total=False):
    """关键词。"""
    keyword: str
    weight: int
    synonyms: list[str]
    category: str
    original_text: str


class ConceptMapping(TypedDict, total=False):
    """概念映射。"""
    concept: str
    related_keywords: list[str]


class Requirements(TypedDict, total=False):
    """JD 要求。"""
    experience: dict  # {level, years}
    education: dict  # {level, preferred}
    position_type: str
    industry: str


class JDAnalysis(TypedDict, total=False):
    """JD 分析结果。"""
    meta: dict
    keywords: dict  # {required: [...], preferred: [...]}
    soft_skills: list[Keyword]
    requirements: Requirements
    concept_mapping: list[ConceptMapping]
    raw_text: str
    quality_score: float  # JD 质量评分


class AnalyzedJD(TypedDict, total=False):
    """已分析的 JD，用于经历筛选。"""
    jd_id: str
    analysis: JDAnalysis
    matched_keywords: list[str]
    missing_keywords: list[str]
    concept_scores: dict[str, float]