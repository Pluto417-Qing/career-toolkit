"""内容精简器类型定义。"""

from typing import TypedDict


class CondensedEntry(TypedDict, total=False):
    """精简后的条目。"""
    id: str
    entry_type: str
    title: str  # 条目标题
    subtitle: str  # 副标题（如职位、学历等）
    period: str  # 时间范围
    highlights: list[str]  # 精简后的亮点
    tech_stack: list[str]  # 技术栈


class CondensedResume(TypedDict, total=False):
    """精简后的简历。"""
    meta: dict
    basics: dict
    education: list[CondensedEntry]
    work: list[CondensedEntry]
    projects: list[CondensedEntry]
    skills: list[dict]
    word_count: int
    line_count: int
    estimated_pages: float
    fits_one_page: bool


class CondenseConfig(TypedDict, total=False):
    """精简配置。"""
    max_highlights_per_entry: int  # 每个条目最多保留亮点数
    max_work_entries: int  # 最多保留工作经历数
    max_project_entries: int  # 最多保留项目数
    page_char_limit: int  # 一页纸字符限制（约 600-800 字）
    page_line_limit: int  # 一页纸行数限制（约 30-35 行）
    remove_weak_verbs: bool  # 是否移除弱动词
    merge_dual_perspective: bool  # 是否合并双视角


DEFAULT_CONDENSE_CONFIG: CondenseConfig = {
    "max_highlights_per_entry": 3,
    "max_work_entries": 3,
    "max_project_entries": 3,
    "page_char_limit": 800,
    "page_line_limit": 35,
    "remove_weak_verbs": True,
    "merge_dual_perspective": True,
}