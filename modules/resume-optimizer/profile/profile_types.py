"""信息库数据类型定义。"""

from typing import Any, Optional, TypedDict


class MetaInfo(TypedDict, total=False):
    """元信息。"""
    version: str
    created_at: str
    updated_at: str
    source: str  # interactive | upload | migrated


class Basics(TypedDict, total=False):
    """基础信息。"""
    name: str
    label: str
    phone: str
    email: str
    profiles: list[dict]
    summary: str
    descriptor: dict[str, Any]


class EducationEntry(TypedDict, total=False):
    """教育背景条目。"""
    id: str
    institution: str
    area: str
    degree: str
    gpa: str
    start: str
    end: str
    courses: list[str]
    honors: list[str]
    descriptor: dict[str, Any]


class ProjectContext(TypedDict, total=False):
    """项目背景（项目做了什么）。"""
    name: str
    description: str
    business_value: str
    scale: str
    team_size: int
    tech_stack: list[str]


class PersonalContribution(TypedDict, total=False):
    """个人贡献（你做了什么）。"""
    id: str
    action: str
    target: str
    result: str
    impact: str
    tech_used: list[str]


class WorkEntry(TypedDict, total=False):
    """工作经历条目。"""
    id: str
    organization: str
    position: str
    department: str
    start: str
    end: str
    tech: list[str]
    project_context: ProjectContext
    personal_contribution: list[PersonalContribution]
    descriptor: dict[str, Any]


class ProjectEntry(TypedDict, total=False):
    """项目经历条目。"""
    id: str
    name: str
    role: str
    tech: list[str]
    url: str
    project_context: ProjectContext
    personal_contribution: list[PersonalContribution]
    descriptor: dict[str, Any]


class SkillEntry(TypedDict, total=False):
    """技能条目。"""
    id: str
    name: str
    keywords: list[str]
    descriptor: dict[str, Any]


class AwardEntry(TypedDict, total=False):
    """奖项条目。"""
    id: str
    title: str
    date: str
    awarder: str
    descriptor: dict[str, Any]


class Profile(TypedDict, total=False):
    """用户信息库。"""
    meta: MetaInfo
    basics: Basics
    education: list[EducationEntry]
    work: list[WorkEntry]
    projects: list[ProjectEntry]
    skills: list[SkillEntry]
    awards: list[AwardEntry]


class SelectionResult(TypedDict, total=False):
    """筛选结果。"""
    education: list[dict]  # {id, score, reason}
    work: list[dict]
    projects: list[dict]
    hidden_entries: list[dict]  # 被隐藏的条目


class PageConstraint(TypedDict, total=False):
    """一页纸约束。"""
    max_pages: int
    paper_size: str
    font_size_min: int
    max_education_entries: int
    max_work_entries: int
    max_project_entries: int
    max_highlights_per_work: int
    max_highlights_per_project: int


class CondensedResume(TypedDict, total=False):
    """精简后的简历。"""
    meta: dict
    basics: Basics
    education: list[dict]
    work: list[dict]
    projects: list[dict]
    skills: list[dict]
    word_count: int
    estimated_pages: float