"""简历编排模块。

负责整合各子模块，协调数据流，产出 YAML 格式的简历。
"""

from .orchestrator import ResumeOrchestrator
from .template_system import TemplateManager, ResumeTemplate

# 向后兼容别名
ResumeBuilder = ResumeOrchestrator

__all__ = ["ResumeOrchestrator", "ResumeBuilder", "TemplateManager", "ResumeTemplate"]