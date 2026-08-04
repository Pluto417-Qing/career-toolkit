"""信息库管理模块。"""

from .profile_manager import ProfileManager, create_profile_from_resume
from .profile_types import (
    Profile,
    Basics,
    EducationEntry,
    WorkEntry,
    ProjectEntry,
    SkillEntry,
    AwardEntry,
    ProjectContext,
    PersonalContribution,
    SelectionResult,
    PageConstraint,
    CondensedResume,
)

__all__ = [
    "ProfileManager",
    "create_profile_from_resume",
    "Profile",
    "Basics",
    "EducationEntry",
    "WorkEntry",
    "ProjectEntry",
    "SkillEntry",
    "AwardEntry",
    "ProjectContext",
    "PersonalContribution",
    "SelectionResult",
    "PageConstraint",
    "CondensedResume",
]