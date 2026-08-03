"""测试 profile_manager。"""

import os
import sys
import tempfile
from pathlib import Path

# 添加模块路径
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from profile.profile_manager import ProfileManager, create_profile_from_resume
from profile.profile_types import Profile


def test_create_and_load_profile():
    """测试创建和加载信息库。"""
    print("🧪 测试：创建和加载信息库")

    with tempfile.TemporaryDirectory() as tmpdir:
        manager = ProfileManager(tmpdir)

        # 创建测试信息库
        profile = {
            "meta": {"source": "test"},
            "basics": {
                "name": "测试用户",
                "label": "测试工程师",
                "phone": "13800000000",
                "email": "test@test.com",
            },
            "education": [
                {
                    "institution": "清华大学",
                    "area": "计算机科学",
                    "degree": "本科",
                    "gpa": "3.8/4.0",
                    "start": "2022-09",
                    "end": "2026-06",
                }
            ],
            "work": [
                {
                    "organization": "测试公司",
                    "position": "测试实习生",
                    "start": "2025-06",
                    "end": "2025-09",
                    "tech": ["Python", "Java"],
                    "personal_contribution": [
                        {"text": "完成了测试任务"},
                    ],
                }
            ],
        }

        path = manager.create_profile("test_user", profile)
        print(f"  ✅ 创建成功：{path}")

        # 加载
        loaded = manager.load_profile("test_user")
        assert loaded is not None, "加载失败"
        assert loaded["basics"]["name"] == "测试用户"
        assert len(loaded["education"]) == 1
        assert len(loaded["work"]) == 1
        assert "id" in loaded["education"][0]  # 检查 ID 已生成
        assert "descriptor" in loaded["education"][0]  # 检查 descriptor 已生成
        print(f"  ✅ 加载成功：{loaded['basics']['name']}")

    print("  🎉 测试通过！\n")


def test_update_profile():
    """测试更新信息库。"""
    print("🧪 测试：更新信息库")

    with tempfile.TemporaryDirectory() as tmpdir:
        manager = ProfileManager(tmpdir)

        # 创建
        manager.create_profile("test_user", {
            "basics": {"name": "测试用户"},
            "education": [],
            "work": [],
        })

        # 更新基础信息
        updated = manager.update_profile("test_user", {
            "basics": {"label": "高级工程师"},
        })

        assert updated["basics"]["label"] == "高级工程师"
        print(f"  ✅ 基础信息更新成功")

    print("  🎉 测试通过！\n")


def test_add_and_get_entry():
    """测试添加和获取条目。"""
    print("🧪 测试：添加和获取条目")

    with tempfile.TemporaryDirectory() as tmpdir:
        manager = ProfileManager(tmpdir)

        manager.create_profile("test_user", {
            "basics": {"name": "测试用户"},
            "education": [],
            "work": [],
            "projects": [],
        })

        # 添加工作经历
        entry = {
            "organization": "新公司",
            "position": "新实习生",
            "tech": ["Go"],
            "personal_contribution": [{"text": "新贡献"}],
        }
        updated = manager.add_entry("test_user", "work", entry)

        assert len(updated["work"]) == 1
        entry_id = updated["work"][0]["id"]
        print(f"  ✅ 添加条目成功：{entry_id}")

        # 获取
        fetched = manager.get_entry("test_user", "work", entry_id)
        assert fetched is not None
        assert fetched["organization"] == "新公司"
        print(f"  ✅ 获取条目成功")

        # 添加 descriptor
        manager.add_descriptor("test_user", "work", entry_id, "user_importance_rating", 9)
        fetched = manager.get_entry("test_user", "work", entry_id)
        assert fetched["descriptor"]["user_importance_rating"] == 9
        print(f"  ✅ 添加 descriptor 成功")

    print("  🎉 测试通过！\n")


def test_delete_entry():
    """测试删除条目。"""
    print("🧪 测试：删除条目")

    with tempfile.TemporaryDirectory() as tmpdir:
        manager = ProfileManager(tmpdir)

        manager.create_profile("test_user", {
            "basics": {"name": "测试用户"},
            "education": [],
            "work": [
                {"id": "work_001", "organization": "公司A"},
                {"id": "work_002", "organization": "公司B"},
            ],
        })

        # 删除
        updated = manager.delete_entry("test_user", "work", "work_001")
        assert len(updated["work"]) == 1
        assert updated["work"][0]["id"] == "work_002"
        print(f"  ✅ 删除成功，剩余 {len(updated['work'])} 条")

    print("  🎉 测试通过！\n")


def test_version_control():
    """测试版本控制。"""
    print("🧪 测试：版本控制")

    with tempfile.TemporaryDirectory() as tmpdir:
        manager = ProfileManager(tmpdir)

        # 创建
        manager.create_profile("test_user", {
            "basics": {"name": "版本测试"},
            "education": [],
        })

        # 多次更新（触发历史归档）
        for i in range(3):
            manager.update_profile("test_user", {
                "basics": {"label": f"更新_{i}"}
            })

        # 检查历史
        history = manager.get_history("test_user")
        print(f"  📚 历史版本数：{len(history)}")
        assert len(history) >= 2  # 至少有 2 个历史版本

        # 列出用户
        users = manager.list_users()
        assert "test_user" in users
        print(f"  👥 用户列表：{users}")

    print("  🎉 测试通过！\n")


def test_migration():
    """测试从旧版简历迁移。"""
    print("🧪 测试：旧版简历迁移")

    # 创建临时旧版简历
    with tempfile.TemporaryDirectory() as tmpdir:
        resume_path = Path(tmpdir) / "old_resume.yaml"
        resume_path.write_text("""
basics:
  name: 迁移测试
  label: 前端工程师
  email: migrate@test.com

education:
  - institution: 北京大学
    area: 软件工程
    degree: 硕士
    gpa: 3.9/4.0
    start: "2023-09"
    end: "2026-06"

work:
  - organization: 阿里
    position: 前端实习生
    start: "2025-03"
    end: "2025-09"
    tech: [React, TypeScript]
    highlights:
      - 主导组件库建设，覆盖 20+ 业务场景
      - 性能优化，首屏加载时间降低 40%

projects:
  - name: TestProject
    role: 参与者
    tech: [Vue]
    highlights:
      - 完成核心功能开发

skills:
  - name: 前端框架
    keywords: [React, Vue, Angular]
""")

        # 迁移
        profile = create_profile_from_resume(str(resume_path), tmpdir)

        assert profile["basics"]["name"] == "迁移测试"
        assert profile["meta"]["source"] == "migrated"
        assert len(profile["work"]) == 1
        assert profile["work"][0]["descriptor"]["need_supplement"] == True
        print(f"  ✅ 迁移成功：{len(profile.get('work', []))} 段实习")
        print(f"     - 标记了 need_supplement，等待后续补充")

    print("  🎉 测试通过！\n")


def run_all_tests():
    """运行所有测试。"""
    print("=" * 60)
    print("📋 Profile Manager 测试套件")
    print("=" * 60)
    print()

    tests = [
        test_create_and_load_profile,
        test_update_profile,
        test_add_and_get_entry,
        test_delete_entry,
        test_version_control,
        test_migration,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"❌ 测试失败：{e}")
            failed += 1
            import traceback
            traceback.print_exc()

    print("=" * 60)
    print(f"📊 测试结果：{passed} 通过，{failed} 失败")
    print("=" * 60)


if __name__ == "__main__":
    run_all_tests()