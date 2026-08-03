"""类型定义模块。

定义简历优化器的核心数据结构。
"""

from typing import Any, Literal, Optional, TypedDict


class JDKeyword(TypedDict, total=False):
    """JD 关键词。"""
    keyword: str
    canonical: str
    category: str
    matched: bool
    matched_in: list[str]
    match_layer: int
    matched_concept: str


class MatchResult(TypedDict):
    """JD 匹配结果。"""
    jd_keywords: list[JDKeyword]
    covered: list[JDKeyword]
    missing: list[JDKeyword]
    evidence_gaps: list[JDKeyword]
    summary: dict[str, Any]


class Suggestion(TypedDict, total=False):
    """融入建议。"""
    keyword: str
    strategy: str
    strategy_description: str
    confidence: float
    suggested_text: str
    original_text: str
    target_section: str
    target_entry: str
    target_entry_index: int
    target_bullet_index: int


class IntegrationResult(TypedDict):
    """关键词融入结果。"""
    suggestions: list[Suggestion]
    keywords_processed: int
    keywords_total: int


class BulletIssue(TypedDict, total=False):
    """Bullet 问题。"""
    type: str
    severity: Literal["high", "medium", "low"]
    text: str
    suggestion: str
    category: str


class BulletDiagnosis(TypedDict):
    """Bullet 诊断结果。"""
    total_bullets: int
    issues_found: int
    issues: list[BulletIssue]


class ATSCheck(TypedDict, total=False):
    """ATS 检查结果。"""
    rule_id: str
    name: str
    status: Literal["pass", "fail", "warn"]
    severity: Literal["fatal", "warning", "info"]
    detail: str
    fix: str


class ATSResult(TypedDict):
    """ATS 检查汇总。"""
    total_checks: int
    passed: int
    warnings: int
    failed: int
    checks: list[ATSCheck]


class AppliedChange(TypedDict, total=False):
    """已应用的修改。"""
    type: str
    keyword: str
    section: str
    entry: str
    bullet_index: int
    before: str
    after: str
    confidence: float
    mode: Literal["auto", "interactive"]
    note: str
    user_note: str


class ConfirmationItem(TypedDict, total=False):
    """待确认项。"""
    keyword: str
    strategy: str
    strategy_description: str
    confidence: float
    risk: Literal["critical", "high", "medium", "low"]
    target_entry: str
    target_section: str
    bullet_text: str
    suggested_text: str
    question: str
    user_decision: str
    resolved: bool
    decision: str


class ExaggerationWarning(TypedDict, total=False):
    """夸大风险警告。"""
    word: str
    location: str
    section: str
    severity: Literal["high", "medium"]
    suggestion: str


class GenerateReport(TypedDict):
    """生成报告。"""
    summary: dict[str, Any]
    changes: list[AppliedChange]
    confirmations: list[ConfirmationItem]
    exaggeration_warnings: list[ExaggerationWarning]
    ats_checks: ATSResult


class OptimizeResult(TypedDict):
    """优化结果。"""
    general_resume: dict
    jd_resume: dict
    report: GenerateReport
    report_text: str
    confirmations: list[ConfirmationItem]


class SessionData(TypedDict, total=False):
    """会话数据。"""
    version: str
    created_at: float
    updated_at: float
    status: Literal["init", "in_progress", "completed", "paused"]
    resume_path: str
    jd_path: str
    out_dir: Optional[str]
    interactive: bool
    min_risk_level: str
    results: dict[str, Any]
    confirmations: list[ConfirmationItem]
    user_decisions: list[dict[str, Any]]


class DiffItem(TypedDict, total=False):
    """差异项。"""
    type: Literal["added", "removed", "modified"]
    path: str
    value: Any
    old: Any
    new: Any


class DiffReport(TypedDict):
    """差异报告。"""
    sections: list[dict]
    added: list[DiffItem]
    removed: list[DiffItem]
    modified: list[DiffItem]
    stats: dict[str, int]


# 风险级别
RiskLevel = Literal["critical", "high", "medium", "low"]

# 融入策略
IntegrationStrategy = Literal[
    "explicit",      # 明确同义词
    "tech_list",     # 技术列表
    "enrich",        # 丰富描述
    "summary",       # 摘要提及
    "new_context",   # 新增上下文
]