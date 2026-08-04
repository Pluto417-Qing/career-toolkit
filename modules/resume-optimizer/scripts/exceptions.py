"""自定义异常类。

提供清晰的错误类型，避免静默失败。
"""


class ResumeOptimizeError(Exception):
    """简历优化基础异常"""
    pass


class ScriptExecutionError(ResumeOptimizeError):
    """脚本执行失败"""

    def __init__(self, script_name: str, returncode: int, stderr: str):
        self.script_name = script_name
        self.returncode = returncode
        self.stderr = stderr
        super().__init__(f"脚本 {script_name} 执行失败（退出码 {returncode}）：{stderr}")


class ScriptTimeoutError(ResumeOptimizeError):
    """脚本执行超时"""

    def __init__(self, script_name: str, timeout: int):
        self.script_name = script_name
        self.timeout = timeout
        super().__init__(f"脚本 {script_name} 执行超时（{timeout} 秒）")


class ScriptRetryError(ResumeOptimizeError):
    """脚本重试后仍失败"""

    def __init__(self, script_name: str, attempts: int, last_error: Exception):
        self.script_name = script_name
        self.attempts = attempts
        self.last_error = last_error
        super().__init__(f"脚本 {script_name} 重试 {attempts} 次后仍失败：{last_error}")


class ValidationError(ResumeOptimizeError):
    """数据校验失败"""

    def __init__(self, field: str, reason: str):
        self.field = field
        self.reason = reason
        super().__init__(f"字段 {field} 校验失败：{reason}")


class FileNotFoundError(ResumeOptimizeError):
    """文件不存在"""

    def __init__(self, path: str, file_type: str = "文件"):
        self.path = path
        self.file_type = file_type
        super().__init__(f"{file_type}不存在：{path}")


class InvalidFormatError(ResumeOptimizeError):
    """格式错误"""

    def __init__(self, expected_format: str, actual: str):
        self.expected_format = expected_format
        self.actual = actual
        super().__init__(f"格式错误：期望 {expected_format}，实际得到 {actual}")


class JDMatchError(ResumeOptimizeError):
    """JD 匹配失败"""

    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(f"JD 匹配失败：{reason}")


class KeywordIntegrateError(ResumeOptimizeError):
    """关键词融入失败"""

    def __init__(self, keyword: str, reason: str):
        self.keyword = keyword
        self.reason = reason
        super().__init__(f"关键词「{keyword}」融入失败：{reason}")