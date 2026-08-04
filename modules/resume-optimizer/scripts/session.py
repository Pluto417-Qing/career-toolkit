"""会话管理器。

支持保存和恢复交互会话，允许用户分步完成简历优化。
"""

import json
import time
from pathlib import Path
from typing import Any, Optional


class SessionManager:
    """管理交互会话的保存和恢复。"""

    def __init__(self, session_path: Optional[str] = None):
        """初始化会话管理器。

        参数：
            session_path: 会话文件路径（可选）
        """
        self.session_path = Path(session_path) if session_path else None
        self.data = {
            "version": "1.0",
            "created_at": time.time(),
            "updated_at": time.time(),
            "status": "init",  # init / in_progress / completed / paused
            "resume_path": None,
            "jd_path": None,
            "out_dir": None,
            "interactive": True,
            "min_risk_level": "medium",
            "results": {},
            "confirmations": [],
            "user_decisions": [],
        }

    def set_config(self, resume_path: str, jd_path: str, out_dir: Optional[str] = None,
                   interactive: bool = True, min_risk_level: str = "medium"):
        """设置会话配置。"""
        self.data.update({
            "resume_path": resume_path,
            "jd_path": jd_path,
            "out_dir": out_dir,
            "interactive": interactive,
            "min_risk_level": min_risk_level,
            "status": "in_progress",
        })
        self._touch()

    def add_result(self, key: str, value: Any):
        """添加中间结果。"""
        self.data["results"][key] = value
        self._touch()

    def add_decision(self, decision: dict):
        """添加用户决策。"""
        decision["timestamp"] = time.time()
        self.data["user_decisions"].append(decision)
        self._touch()

    def add_confirmation(self, item: dict):
        """添加待确认项。"""
        self.data["confirmations"].append(item)
        self._touch()

    def get_results(self, key: str) -> Any:
        """获取中间结果。"""
        return self.data["results"].get(key)

    def get_pending_confirmations(self) -> list:
        """获取待确认项列表。"""
        return [c for c in self.data["confirmations"]
                if not c.get("resolved", False)]

    def mark_confirmation_resolved(self, index: int, decision: str, note: str = ""):
        """标记确认项已解决。"""
        if 0 <= index < len(self.data["confirmations"]):
            self.data["confirmations"][index]["resolved"] = True
            self.data["confirmations"][index]["decision"] = decision
            self.data["confirmations"][index]["note"] = note
            self._touch()

    def complete(self):
        """标记会话完成。"""
        self.data["status"] = "completed"
        self._touch()

    def pause(self):
        """标记会话暂停。"""
        self.data["status"] = "paused"
        self._touch()

    def is_completed(self) -> bool:
        """检查会话是否完成。"""
        return self.data["status"] == "completed"

    def _touch(self):
        """更新最后修改时间。"""
        self.data["updated_at"] = time.time()

    def save(self, path: Optional[str] = None):
        """保存会话到文件。"""
        save_path = Path(path) if path else self.session_path
        if not save_path:
            raise ValueError("未指定会话保存路径")

        save_path.parent.mkdir(parents=True, exist_ok=True)
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)

    @classmethod
    def load(cls, path: str) -> "SessionManager":
        """从文件加载会话。"""
        load_path = Path(path)
        if not load_path.exists():
            raise FileNotFoundError(f"会话文件不存在：{path}")

        with open(load_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        manager = cls()
        manager.data = data
        return manager

    def get_summary(self) -> dict:
        """获取会话摘要。"""
        pending = self.get_pending_confirmations()
        return {
            "status": self.data["status"],
            "resume_path": self.data["resume_path"],
            "jd_path": self.data["jd_path"],
            "created_at": self.data["created_at"],
            "updated_at": self.data["updated_at"],
            "pending_count": len(pending),
            "total_decisions": len(self.data["user_decisions"]),
        }


def list_sessions(session_dir: str) -> list[dict]:
    """列出指定目录下的所有会话文件。

    返回会话摘要列表，按更新时间倒序。
    """
    dir_path = Path(session_dir)
    if not dir_path.exists():
        return []

    sessions = []
    for f in dir_path.glob("*.session.json"):
        try:
            with open(f, "r", encoding="utf-8") as fp:
                data = json.load(fp)
            sessions.append({
                "file": str(f),
                "name": f.stem.replace(".session", ""),
                "status": data.get("status", "unknown"),
                "resume": data.get("resume_path", ""),
                "jd": data.get("jd_path", ""),
                "updated_at": data.get("updated_at", 0),
                "pending_count": len([c for c in data.get("confirmations", [])
                                       if not c.get("resolved", False)]),
            })
        except (json.JSONDecodeError, KeyError):
            continue

    # 按更新时间倒序
    sessions.sort(key=lambda x: x["updated_at"], reverse=True)
    return sessions


def format_session_time(timestamp: float) -> str:
    """格式化时间戳。"""
    if timestamp:
        return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp))
    return "N/A"