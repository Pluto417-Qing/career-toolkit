"""信息库管理器。

负责用户信息库的创建、读取、更新、版本控制。
"""

import copy
import time
import uuid
from pathlib import Path
from typing import Any, Optional

import yaml

from .profile_types import (
    Basics,
    EducationEntry,
    Profile,
    ProjectEntry,
    SkillEntry,
    WorkEntry,
    AwardEntry,
)


class ProfileManager:
    """信息库管理器。"""

    def __init__(self, storage_dir: str = "profiles"):
        """初始化管理器。

        参数：
            storage_dir: 信息库存储目录
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def create_profile(self, user_id: str, profile: Profile) -> Path:
        """创建新的信息库。

        参数：
            user_id: 用户 ID
            profile: 信息库数据

        返回：
            保存的文件路径
        """
        user_dir = self.storage_dir / user_id
        user_dir.mkdir(parents=True, exist_ok=True)

        # 设置元信息
        profile.setdefault("meta", {})
        profile["meta"].update({
            "version": "2.0",
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "updated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "source": profile["meta"].get("source", "interactive"),
        })

        # 为每个条目生成 ID（如果没有）
        profile = self._ensure_ids(profile)

        # 保存当前版本
        profile_path = user_dir / "profile.yaml"
        self._save_yaml(profile_path, profile)

        return profile_path

    def load_profile(self, user_id: str) -> Optional[Profile]:
        """加载信息库。

        参数：
            user_id: 用户 ID

        返回：
            信息库数据，如果不存在返回 None
        """
        profile_path = self.storage_dir / user_id / "profile.yaml"
        if not profile_path.exists():
            return None

        return self._load_yaml(profile_path)

    def update_profile(self, user_id: str, updates: dict) -> Profile:
        """更新信息库。

        参数：
            user_id: 用户 ID
            updates: 更新内容（支持嵌套更新）

        返回：
            更新后的信息库
        """
        profile = self.load_profile(user_id)
        if not profile:
            raise FileNotFoundError(f"用户 {user_id} 的信息库不存在")

        # 保存历史版本
        self._archive_profile(user_id, profile)

        # 应用更新（深度合并）
        profile = self._deep_merge(profile, updates)

        # 更新时间戳
        profile["meta"]["updated_at"] = time.strftime("%Y-%m-%d %H:%M:%S")

        # 保存
        profile_path = self.storage_dir / user_id / "profile.yaml"
        self._save_yaml(profile_path, profile)

        return profile

    def add_entry(self, user_id: str, entry_type: str, entry: dict) -> Profile:
        """添加新条目（工作/项目/教育等）。

        参数：
            user_id: 用户 ID
            entry_type: 条目类型（work/projects/education/skills/awards）
            entry: 条目数据

        返回：
            更新后的信息库
        """
        profile = self.load_profile(user_id)
        if not profile:
            raise FileNotFoundError(f"用户 {user_id} 的信息库不存在")

        # 归档当前版本
        self._archive_profile(user_id, profile)

        # 确保 ID
        if "id" not in entry:
            entry["id"] = f"{entry_type[:4]}_{uuid.uuid4().hex[:6]}"

        # 确保 descriptor 存在
        if "descriptor" not in entry:
            entry["descriptor"] = {}

        # 添加到对应列表
        key = self._get_plural_key(entry_type)
        if key not in profile:
            profile[key] = []

        profile[key].append(entry)

        # 更新时间戳并保存
        profile["meta"]["updated_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
        profile_path = self.storage_dir / user_id / "profile.yaml"
        self._save_yaml(profile_path, profile)

        return profile

    def update_entry(self, user_id: str, entry_type: str, entry_id: str,
                      updates: dict) -> Profile:
        """更新指定条目。

        参数：
            user_id: 用户 ID
            entry_type: 条目类型
            entry_id: 条目 ID
            updates: 更新内容

        返回：
            更新后的信息库
        """
        profile = self.load_profile(user_id)
        if not profile:
            raise FileNotFoundError(f"用户 {user_id} 的信息库不存在")

        # 归档当前版本
        self._archive_profile(user_id, profile)

        key = self._get_plural_key(entry_type)
        entries = profile.get(key, [])

        for i, entry in enumerate(entries):
            if entry.get("id") == entry_id:
                entries[i] = self._deep_merge(entry, updates)
                break
        else:
            raise ValueError(f"条目 {entry_id} 不存在于 {entry_type}")

        # 更新时间戳并保存
        profile["meta"]["updated_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
        profile_path = self.storage_dir / user_id / "profile.yaml"
        self._save_yaml(profile_path, profile)

        return profile

    def add_descriptor(self, user_id: str, entry_type: str, entry_id: str,
                       key: str, value: Any) -> Profile:
        """添加/更新 descriptor 字段。

        参数：
            user_id: 用户 ID
            entry_type: 条目类型
            entry_id: 条目 ID
            key: descriptor 键
            value: descriptor 值

        返回：
            更新后的信息库
        """
        return self.update_entry(
            user_id, entry_type, entry_id,
            {"descriptor": {key: value}}
        )

    def delete_entry(self, user_id: str, entry_type: str, entry_id: str) -> Profile:
        """删除指定条目。

        参数：
            user_id: 用户 ID
            entry_type: 条目类型
            entry_id: 条目 ID

        返回：
            更新后的信息库
        """
        profile = self.load_profile(user_id)
        if not profile:
            raise FileNotFoundError(f"用户 {user_id} 的信息库不存在")

        # 归档当前版本
        self._archive_profile(user_id, profile)

        key = self._get_plural_key(entry_type)
        entries = profile.get(key, [])

        original_len = len(entries)
        entries = [e for e in entries if e.get("id") != entry_id]

        if len(entries) == original_len:
            raise ValueError(f"条目 {entry_id} 不存在于 {entry_type}")

        profile[key] = entries

        # 更新时间戳并保存
        profile["meta"]["updated_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
        profile_path = self.storage_dir / user_id / "profile.yaml"
        self._save_yaml(profile_path, profile)

        return profile

    def get_entry(self, user_id: str, entry_type: str,
                  entry_id: str) -> Optional[dict]:
        """获取指定条目。

        参数：
            user_id: 用户 ID
            entry_type: 条目类型
            entry_id: 条目 ID

        返回：
            条目数据，如果不存在返回 None
        """
        profile = self.load_profile(user_id)
        if not profile:
            return None

        key = self._get_plural_key(entry_type)
        entries = profile.get(key, [])

        for entry in entries:
            if entry.get("id") == entry_id:
                return entry

        return None

    def list_entries(self, user_id: str, entry_type: str) -> list[dict]:
        """列出指定类型的所有条目。

        参数：
            user_id: 用户 ID
            entry_type: 条目类型

        返回：
            条目列表
        """
        profile = self.load_profile(user_id)
        if not profile:
            return []

        key = self._get_plural_key(entry_type)
        return profile.get(key, [])

    def list_users(self) -> list[str]:
        """列出所有用户 ID。

        返回：
            用户 ID 列表
        """
        users = []
        for d in self.storage_dir.iterdir():
            if d.is_dir() and (d / "profile.yaml").exists():
                users.append(d.name)
        return users

    def delete_profile(self, user_id: str, confirm: bool = False) -> bool:
        """删除信息库。

        参数：
            user_id: 用户 ID
            confirm: 是否确认删除

        返回：
            是否删除成功
        """
        if not confirm:
            raise ValueError("请设置 confirm=True 以确认删除")

        user_dir = self.storage_dir / user_id
        if not user_dir.exists():
            return False

        import shutil
        shutil.rmtree(user_dir)
        return True

    def get_history(self, user_id: str) -> list[dict]:
        """获取历史版本列表。

        参数：
            user_id: 用户 ID

        返回：
            历史版本列表
        """
        user_dir = self.storage_dir / user_id
        if not user_dir.exists():
            return []

        history_dir = user_dir / "history"
        if not history_dir.exists():
            return []

        history = []
        for f in sorted(history_dir.glob("profile_*.yaml")):
            history.append({
                "file": str(f),
                "timestamp": f.stem.replace("profile_", ""),
            })

        return history

    def restore_version(self, user_id: str, timestamp: str) -> Profile:
        """恢复到指定历史版本。

        参数：
            user_id: 用户 ID
            timestamp: 时间戳（如 20260801_153000_123）

        返回：
            恢复后的信息库
        """
        user_dir = self.storage_dir / user_id
        if not user_dir.exists():
            raise FileNotFoundError(f"用户 {user_id} 的信息库不存在")

        version_path = user_dir / "history" / f"profile_{timestamp}.yaml"
        if not version_path.exists():
            raise FileNotFoundError(f"历史版本 {timestamp} 不存在")

        # 读取历史版本
        profile = self._load_yaml(version_path)

        # 保存为当前版本
        profile["meta"]["updated_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
        profile["meta"]["restored_from"] = timestamp

        self._save_yaml(user_dir / "profile.yaml", profile)

        return profile

    # ═══════════════════════════════════════════
    # 内部方法
    # ═══════════════════════════════════════════

    def _ensure_ids(self, profile: Profile) -> Profile:
        """确保所有条目都有 ID。"""
        for key in ["education", "work", "projects", "skills", "awards"]:
            for entry in profile.get(key, []):
                if "id" not in entry:
                    entry["id"] = f"{key[:4]}_{uuid.uuid4().hex[:6]}"
                if "descriptor" not in entry:
                    entry["descriptor"] = {}
        return profile

    def _archive_profile(self, user_id: str, profile: Profile):
        """归档当前版本为历史。"""
        user_dir = self.storage_dir / user_id
        history_dir = user_dir / "history"
        history_dir.mkdir(parents=True, exist_ok=True)

        # 使用毫秒级时间戳 + 随机后缀，避免同一秒内覆盖
        timestamp = time.strftime("%Y%m%d_%H%M%S") + f"_{int(time.time() * 1000) % 1000:03d}"
        archive_path = history_dir / f"profile_{timestamp}.yaml"

        # 限制历史版本数量（保留最近 30 个）
        histories = sorted(history_dir.glob("profile_*.yaml"))
        if len(histories) >= 30:
            # 删除最旧的
            for old_file in histories[:-29]:
                old_file.unlink()

        self._save_yaml(archive_path, profile)

    def _deep_merge(self, base: dict, updates: dict) -> dict:
        """深度合并两个字典。"""
        result = copy.deepcopy(base)

        for key, value in updates.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            elif key in result and isinstance(result[key], list) and isinstance(value, list):
                result[key] = value  # 列表直接替换
            else:
                result[key] = copy.deepcopy(value)

        return result

    def _get_plural_key(self, entry_type: str) -> str:
        """获取复数键名。"""
        mapping = {
            "education": "education",
            "edu": "education",
            "work": "work",
            "project": "projects",
            "projects": "projects",
            "skill": "skills",
            "skills": "skills",
            "award": "awards",
            "awards": "awards",
        }
        return mapping.get(entry_type, f"{entry_type}s")

    def _save_yaml(self, path: Path, data: dict):
        """保存 YAML 文件。"""
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, allow_unicode=True, sort_keys=False, default_flow_style=False)

    def _load_yaml(self, path: Path) -> dict:
        """加载 YAML 文件。"""
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}


def create_profile_from_resume(resume_path: str, output_dir: str = "profiles") -> Profile:
    """从旧版简历文件创建信息库（迁移）。

    参数：
        resume_path: 旧版 resume.yaml 路径
        output_dir: 输出目录

    返回：
        迁移后的 Profile 数据
    """
    with open(resume_path, "r", encoding="utf-8") as f:
        old_resume = yaml.safe_load(f) or {}

    profile = Profile()

    # 元信息
    profile["meta"] = {
        "version": "2.0",
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "updated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "source": "migrated",
        "migrated_from": str(resume_path),
    }

    # 基础信息
    profile["basics"] = old_resume.get("basics", {})
    if "descriptor" not in profile["basics"]:
        profile["basics"]["descriptor"] = {}

    # 教育背景
    profile["education"] = []
    for edu in old_resume.get("education", []):
        entry = {
            "id": f"edu_{uuid.uuid4().hex[:6]}",
            **edu,
            "descriptor": {
                "migrated_from": "resume_v1",
                "user_importance_rating": 5,
            }
        }
        profile["education"].append(entry)

    # 工作经历
    profile["work"] = []
    for work in old_resume.get("work", []):
        # 尝试拆分 highlights 为 personal_contribution
        highlights = work.get("highlights", [])
        contributions = []
        for i, hl in enumerate(highlights):
            contributions.append({
                "id": f"contrib_{uuid.uuid4().hex[:6]}",
                "text": hl,
            })

        entry = {
            "id": f"work_{uuid.uuid4().hex[:6]}",
            "organization": work.get("organization", ""),
            "position": work.get("position", ""),
            "department": work.get("department", ""),
            "start": work.get("start", ""),
            "end": work.get("end", ""),
            "tech": work.get("tech", []),
            "project_context": {
                "name": work.get("department", ""),
                "description": "",
                "business_value": "",
            },
            "personal_contribution": contributions,
            "descriptor": {
                "migrated_from": "resume_v1",
                "user_importance_rating": 5,
                "need_supplement": True,
            }
        }
        profile["work"].append(entry)

    # 项目经历
    profile["projects"] = []
    for proj in old_resume.get("projects", []):
        highlights = proj.get("highlights", [])
        contributions = []
        for i, hl in enumerate(highlights):
            contributions.append({
                "id": f"contrib_{uuid.uuid4().hex[:6]}",
                "text": hl,
            })

        entry = {
            "id": f"proj_{uuid.uuid4().hex[:6]}",
            "name": proj.get("name", ""),
            "role": proj.get("role", ""),
            "tech": proj.get("tech", []),
            "url": proj.get("url", ""),
            "project_context": {
                "description": proj.get("name", ""),
                "scale": "",
            },
            "personal_contribution": contributions,
            "descriptor": {
                "migrated_from": "resume_v1",
                "user_importance_rating": 5,
                "need_supplement": True,
            }
        }
        profile["projects"].append(entry)

    # 技能
    profile["skills"] = []
    for skill in old_resume.get("skills", []):
        entry = {
            "id": f"skill_{uuid.uuid4().hex[:6]}",
            **skill,
            "descriptor": {
                "migrated_from": "resume_v1",
                "proficiency": {},
            }
        }
        profile["skills"].append(entry)

    # 奖项
    profile["awards"] = []
    for award in old_resume.get("awards", []):
        entry = {
            "id": f"award_{uuid.uuid4().hex[:6]}",
            **award,
            "descriptor": {
                "migrated_from": "resume_v1",
            }
        }
        profile["awards"].append(entry)

    return profile