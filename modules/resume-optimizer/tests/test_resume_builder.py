"""测试 resume_builder 完整流程。"""

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from builder.resume_builder import ResumeBuilder
from profile.profile_manager import ProfileManager


def create_test_profile():
    """创建测试用信息库。"""
    return {
        "meta": {"source": "test"},
        "basics": {
            "name": "测试用户",
            "label": "前端工程师",
            "phone": "13800000000",
            "email": "test@test.com",
        },
        "education": [
            {
                "institution": "清华大学",
                "area": "计算机科学与技术",
                "degree": "本科",
                "gpa": "3.82/4.0",
                "start": "2022-09",
                "end": "2026-06",
                "courses": ["数据结构", "算法设计"],
                "descriptor": {"user_importance_rating": 10},
            }
        ],
        "work": [
            {
                "organization": "字节跳动",
                "position": "前端开发实习生",
                "start": "2025-06",
                "end": "2025-09",
                "tech": ["React", "TypeScript", "Docker"],
                "project_context": {
                    "name": "广告投放平台",
                    "scale": "日活500万+",
                },
                "personal_contribution": [
                    {
                        "action": "设计并实现",
                        "target": "Schema化改造",
                        "result": "代码量下降45%",
                    },
                    {
                        "action": "引入",
                        "target": "运行时校验框架",
                        "result": "线上问题减少60%",
                    },
                ],
                "descriptor": {"user_importance_rating": 9},
            },
            {
                "organization": "腾讯",
                "position": "前端开发实习生",
                "start": "2024-06",
                "end": "2024-09",
                "tech": ["Vue", "Next.js"],
                "project_context": {
                    "name": "小程序框架",
                    "scale": "万级日活",
                },
                "personal_contribution": [
                    {
                        "action": "优化",
                        "target": "SSR性能",
                        "result": "FCP从2.1s降至0.8s",
                    },
                ],
                "descriptor": {"user_importance_rating": 7},
            }
        ],
        "projects": [
            {
                "name": "MiniReact",
                "role": "独立作者",
                "tech": ["TypeScript"],
                "url": "https://github.com/test/mini-react",
                "project_context": {
                    "description": "简化版React",
                    "scale": "520+ star",
                },
                "personal_contribution": [
                    {
                        "action": "独立实现",
                        "target": "Fiber架构",
                        "result": "GitHub 520+ star",
                    },
                ],
                "descriptor": {"user_importance_rating": 8},
            }
        ],
        "skills": [
            {"name": "编程语言", "keywords": ["TypeScript", "JavaScript"]},
            {"name": "前端框架", "keywords": ["React", "Vue"]},
        ],
    }


def test_full_build_flow():
    """测试完整构建流程。"""
    print("🧪 测试：完整构建流程")

    with tempfile.TemporaryDirectory() as tmpdir:
        # 创建 builder
        config = {"profiles_dir": tmpdir}
        builder = ResumeBuilder(config)

        # 创建信息库
        profile = create_test_profile()
        builder.profile_manager.create_profile("test_user", profile)

        # 模拟 JD
        jd_text = """
        岗位：前端工程师
        
        职责：
        1. 负责产品前端开发，使用 React 和 TypeScript
        2. 优化前端性能
        3. 参与前端工程化建设
        
        要求：
        1. 本科及以上学历
        2. 1-3年前端经验，精通 React
        3. 熟悉 TypeScript、Webpack 等
        """

        # 构建简历
        result = builder.build_resume("test_user", jd_text)

        print(f"  📊 构建状态：{result['status']}")
        print(f"  📝 步骤数：{len(result['steps'])}")

        for step in result["steps"]:
            status_icon = "✅" if step["status"] == "success" else "❌"
            print(f"     {status_icon} {step['step']}: {step['status']}")
            if step.get("data"):
                for key, value in step["data"].items():
                    print(f"        - {key}: {value}")

        # 验证结果
        assert result["status"] == "success", f"构建失败：{result.get('errors')}"
        assert result["resume"] is not None, "应有简历输出"
        assert result["jd_analysis"] is not None, "应有 JD 分析"
        assert result["questions"] is not None, "应有问题集"

        resume = result["resume"]
        print(f"\n  📄 简历预览：")
        print(f"     - 教育背景：{len(resume.get('education', []))} 条")
        print(f"     - 工作经历：{len(resume.get('work', []))} 条")
        print(f"     - 项目经历：{len(resume.get('projects', []))} 条")
        print(f"     - 行数：{resume.get('line_count')}")
        print(f"     - 是否一页：{resume.get('fits_one_page')}")

        questions = result["questions"]
        print(f"\n  ❓ 问题统计：")
        print(f"     - 总问题数：{questions.get('total_count')}")
        print(f"     - 高优先级：{questions.get('high_priority_count')}")

    print("  🎉 测试通过！\n")


def test_save_and_load():
    """测试保存结果。"""
    print("🧪 测试：保存结果")

    with tempfile.TemporaryDirectory() as tmpdir:
        config = {"profiles_dir": str(Path(tmpdir) / "profiles")}
        builder = ResumeBuilder(config)

        # 创建信息库
        profile = create_test_profile()
        builder.profile_manager.create_profile("test_user", profile)

        # 构建简历
        jd_text = "前端开发岗位，要求 React 和 TypeScript"
        result = builder.build_resume("test_user", jd_text)

        # 保存结果
        output_dir = str(Path(tmpdir) / "output")
        saved_files = builder.save_result(
            result, output_dir, "test_user", "test_jd"
        )

        print(f"  💾 保存的文件：")
        for name, path in saved_files.items():
            exists = Path(path).exists()
            print(f"     - {name}: {'✅' if exists else '❌'} {path}")
            assert exists, f"文件不存在：{path}"

    print("  🎉 测试通过！\n")


def test_profile_update_from_answers():
    """测试根据回答更新信息库。"""
    print("🧪 测试：根据回答更新信息库")

    with tempfile.TemporaryDirectory() as tmpdir:
        config = {"profiles_dir": str(Path(tmpdir) / "profiles")}
        builder = ResumeBuilder(config)

        # 创建信息库
        profile = create_test_profile()
        builder.profile_manager.create_profile("test_user", profile)

        # 构建简历
        jd_text = "前端开发岗位，要求 React 和 TypeScript"
        result = builder.build_resume("test_user", jd_text)

        # 获取问题集
        questions = result["questions"]
        pending = builder.question_generator.get_pending_questions(questions)

        if pending:
            # 回答第一个问题
            first_q = pending[0]
            question_set = builder.question_generator.answer_question(
                questions, first_q["id"], "提升50%"
            )

            # 更新信息库
            updated_profile = builder.update_profile_from_answers(
                "test_user", question_set
            )

            print(f"  ✅ 信息库已更新")
            print(f"     - 工作经历数：{len(updated_profile.get('work', []))}")

    print("  🎉 测试通过！\n")


def test_list_and_delete_profiles():
    """测试列出和删除信息库。"""
    print("🧪 测试：列出和删除信息库")

    with tempfile.TemporaryDirectory() as tmpdir:
        config = {"profiles_dir": str(Path(tmpdir) / "profiles")}
        builder = ResumeBuilder(config)

        # 创建两个信息库
        profile1 = create_test_profile()
        builder.profile_manager.create_profile("user1", profile1)
        builder.profile_manager.create_profile("user2", profile1)

        # 列出
        users = builder.list_profiles()
        print(f"  👥 用户列表：{users}")
        assert len(users) == 2, f"应有 2 个用户，实际 {len(users)}"

        # 删除一个
        success = builder.delete_profile("user1", confirm=True)
        print(f"  🗑️ 删除 user1：{'成功' if success else '失败'}")
        assert success, "删除应成功"

        # 再次列出
        users = builder.list_profiles()
        print(f"  👥 剩余用户：{users}")
        assert len(users) == 1, f"应有 1 个用户，实际 {len(users)}"

    print("  🎉 测试通过！\n")


def test_interactive_workflow():
    """测试模拟交互式工作流。"""
    print("🧪 测试：模拟交互式工作流")

    with tempfile.TemporaryDirectory() as tmpdir:
        config = {"profiles_dir": str(Path(tmpdir) / "profiles")}
        builder = ResumeBuilder(config)

        # 模拟老用户流程
        print("  📋 场景：老用户创建简历")

        # 1. 加载信息库
        existing = builder.list_profiles()
        if not existing:
            print("     - 新用户，创建信息库")
            profile = create_test_profile()
            builder.profile_manager.create_profile("demo_user", profile)
        else:
            print("     - 老用户，加载信息库")

        # 2. 分析 JD
        jd_text = """
        字节跳动前端开发工程师
        
        岗位职责：
        - 负责核心产品前端开发
        - 推动前端工程化
        
        任职要求：
        - 本科及以上学历，计算机相关专业
        - 2年以上前端经验，精通 React
        - 熟悉 TypeScript、Webpack、Vite
        - 了解性能优化
        
        加分项：
        - 有开源项目贡献
        """

        print(f"     - JD 文本长度：{len(jd_text)} 字符")

        # 3. 构建简历
        result = builder.build_resume("demo_user", jd_text)

        if result["status"] == "success":
            resume = result["resume"]
            questions = result["questions"]

            print(f"  📄 生成的简历：")
            print(f"     - 页数：{resume.get('estimated_pages')}")
            print(f"     - 是否一页：{resume.get('fits_one_page')}")

            print(f"  ❓ 需要确认的问题：")
            print(f"     - 总数：{questions.get('total_count')}")
            print(f"     - 高优先级：{questions.get('high_priority_count')}")

            # 4. 模拟回答问题
            pending = builder.question_generator.get_pending_questions(questions)
            answered_count = 0

            for q in pending[:2]:  # 只回答前 2 个
                print(f"     - 回答：{q['question'][:50]}...")
                questions = builder.question_generator.answer_question(
                    questions, q["id"], "示例回答"
                )
                answered_count += 1

            print(f"     - 已回答：{answered_count} 个问题")

            # 5. 保存结果
            output_dir = str(Path(tmpdir) / "output")
            saved = builder.save_result(result, output_dir, "demo_user", "bytedance")
            print(f"  💾 保存文件：{len(saved)} 个")

    print("  🎉 测试通过！\n")


def run_all_tests():
    """运行所有测试。"""
    print("=" * 60)
    print("📋 Resume Builder 完整流程测试套件")
    print("=" * 60)
    print()

    tests = [
        test_full_build_flow,
        test_save_and_load,
        test_profile_update_from_answers,
        test_list_and_delete_profiles,
        test_interactive_workflow,
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