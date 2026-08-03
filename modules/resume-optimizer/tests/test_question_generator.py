"""测试 question_generator。"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from question.question_generator import QuestionGenerator
from question.question_types import QuestionType, QuestionPriority


def create_test_profile():
    """创建测试用信息库。"""
    return {
        "basics": {"name": "测试用户"},
        "education": [
            {
                "id": "edu_001",
                "institution": "清华大学",
                "area": "计算机科学",
                "degree": "本科",
                "gpa": "3.8/4.0",
                "start": "2022-09",
                "end": "2026-06",
                "courses": ["数据结构", "算法设计"],
                "descriptor": {},  # 缺少 user_importance_rating
            }
        ],
        "work": [
            {
                "id": "work_001",
                "organization": "字节跳动",
                "position": "前端开发实习生",
                "start": "2025-06",
                "end": "2025-09",
                "tech": ["React", "TypeScript", "Docker"],
                "project_context": {
                    "name": "广告投放平台",
                    # 缺少 scale
                },
                "personal_contribution": [
                    {
                        "action": "负责",  # 弱动词
                        "target": "核心模块开发",
                        # 缺少量化数据
                    },
                    {
                        "action": "设计并实现",
                        "target": "Schema化改造",
                        "result": "代码量下降45%",
                    },
                ],
                "descriptor": {
                    # 缺少 user_importance_rating
                }
            },
            {
                "id": "work_002",
                "organization": "腾讯",
                "position": "前端开发实习生",
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
                "descriptor": {
                    "user_importance_rating": 7,
                }
            }
        ],
        "projects": [
            {
                "id": "proj_001",
                "name": "MiniReact",
                "role": "独立作者",
                "tech": ["TypeScript", "Rollup"],
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
                "descriptor": {
                    "user_importance_rating": 8,
                }
            }
        ],
        "skills": [],
    }


def create_test_jd_analysis():
    """创建测试用 JD 分析结果。"""
    return {
        "keywords": {
            "required": [
                {"keyword": "React", "weight": 10},
                {"keyword": "TypeScript", "weight": 10},
                {"keyword": "Docker", "weight": 5},
            ],
            "preferred": [
                {"keyword": "Next.js", "weight": 5},
            ]
        },
        "concept_mapping": [],
    }


def create_test_selection():
    """创建测试用筛选结果。"""
    return {
        "education": [
            {
                "id": "edu_001",
                "score": 0.9,
                "_raw_entry": create_test_profile()["education"][0],
            }
        ],
        "work": [
            {
                "id": "work_001",
                "score": 0.91,
                "_raw_entry": create_test_profile()["work"][0],
            },
            {
                "id": "work_002",
                "score": 0.78,
                "_raw_entry": create_test_profile()["work"][1],
            }
        ],
        "projects": [
            {
                "id": "proj_001",
                "score": 0.85,
                "_raw_entry": create_test_profile()["projects"][0],
            }
        ],
        "hidden_entries": [],
        "score_summary": {
            "avg_work_score": 0.85,
            "total_entries_selected": 4,
            "total_entries_available": 5,
        }
    }


def test_basic_generation():
    """测试基础问题生成。"""
    print("🧪 测试：基础问题生成")

    generator = QuestionGenerator(max_questions=20)
    profile = create_test_profile()
    jd_analysis = create_test_jd_analysis()
    selection = create_test_selection()

    result = generator.generate_questions(profile, jd_analysis, selection)

    print(f"  📊 生成问题统计：")
    print(f"     - 总问题数：{result['total_count']}")
    print(f"     - 高优先级：{result['high_priority_count']}")
    print(f"     - 中优先级：{result['medium_priority_count']}")
    print(f"     - 低优先级：{result['low_priority_count']}")

    print(f"\n  📝 问题列表：")
    for q in result["questions"]:
        print(f"     [{q['priority']}] {q['question'][:60]}...")

    assert result["total_count"] > 0, "应生成至少一个问题"
    print(f"  ✅ 基础问题生成成功")

    print("  🎉 测试通过！\n")


def test_missing_quantification_detection():
    """测试量化数据缺失检测。"""
    print("🧪 测试：量化数据缺失检测")

    generator = QuestionGenerator()
    profile = create_test_profile()
    jd_analysis = create_test_jd_analysis()
    selection = create_test_selection()

    result = generator.generate_questions(profile, jd_analysis, selection)

    # 查找量化数据缺失问题
    quant_questions = [
        q for q in result["questions"]
        if q["type"] == QuestionType.MISSING_QUANTIFICATION
    ]

    print(f"  量化数据缺失问题：{len(quant_questions)} 个")
    for q in quant_questions:
        print(f"    - {q['question'][:80]}")

    # work_001 的第一个贡献（"负责核心模块开发"）没有量化数据
    assert len(quant_questions) >= 1, "应检测到至少一个量化数据缺失"

    print(f"  ✅ 量化数据缺失检测正确")

    print("  🎉 测试通过！\n")


def test_clarification_detection():
    """测试歧义澄清检测。"""
    print("🧪 测试：歧义澄清检测")

    generator = QuestionGenerator()
    profile = create_test_profile()
    jd_analysis = create_test_jd_analysis()
    selection = create_test_selection()

    result = generator.generate_questions(profile, jd_analysis, selection)

    # 查找歧义澄清问题
    clarify_questions = [
        q for q in result["questions"]
        if q["type"] == QuestionType.CLARIFICATION
    ]

    print(f"  歧义澄清问题：{len(clarify_questions)} 个")
    for q in clarify_questions:
        print(f"    - {q['question'][:80]}")

    # work_001 有弱动词 "负责"
    assert len(clarify_questions) >= 1, "应检测到至少一个歧义表述"

    print(f"  ✅ 歧义澄清检测正确")

    print("  🎉 测试通过！\n")


def test_missing_descriptor_detection():
    """测试描述符缺失检测。"""
    print("🧪 测试：描述符缺失检测")

    generator = QuestionGenerator(max_questions=30)  # 增加限制以获取所有问题
    profile = create_test_profile()
    jd_analysis = create_test_jd_analysis()
    selection = create_test_selection()

    result = generator.generate_questions(profile, jd_analysis, selection)

    # 查找描述符缺失问题
    descriptor_questions = [
        q for q in result["questions"]
        if q["type"] == QuestionType.MISSING_DESCRIPTOR
    ]

    print(f"  描述符缺失问题：{len(descriptor_questions)} 个")
    for q in descriptor_questions:
        print(f"    - {q['question'][:80]}")

    # edu_001 和 work_001 都缺少 user_importance_rating
    assert len(descriptor_questions) >= 2, f"应检测到至少两个描述符缺失，实际 {len(descriptor_questions)}"

    print(f"  ✅ 描述符缺失检测正确")

    print("  🎉 测试通过！\n")


def test_answer_and_skip():
    """测试回答和跳过问题。"""
    print("🧪 测试：回答和跳过问题")

    generator = QuestionGenerator()
    profile = create_test_profile()
    jd_analysis = create_test_jd_analysis()
    selection = create_test_selection()

    result = generator.generate_questions(profile, jd_analysis, selection)

    # 获取第一个问题
    pending = generator.get_pending_questions(result)
    assert len(pending) > 0, "应有待回答的问题"

    first_q = pending[0]
    print(f"  回答前状态：{first_q['status']}")

    # 回答问题
    result = generator.answer_question(result, first_q["id"], "提升45%")
    updated_q = [q for q in result["questions"] if q["id"] == first_q["id"]][0]
    print(f"  回答后状态：{updated_q['status']}")
    print(f"  回答内容：{updated_q['user_answer']}")

    assert updated_q["status"] == "answered", "状态应为 answered"

    # 跳过第二个问题
    pending = generator.get_pending_questions(result)
    if pending:
        second_q = pending[0]
        result = generator.skip_question(result, second_q["id"])
        updated_q2 = [q for q in result["questions"] if q["id"] == second_q["id"]][0]
        print(f"  跳过后状态：{updated_q2['status']}")
        assert updated_q2["status"] == "skipped", "状态应为 skipped"

    # 验证统计
    answered = generator.get_answered_questions(result)
    print(f"  已回答问题数：{len(answered)}")

    print(f"  ✅ 回答和跳过功能正确")

    print("  🎉 测试通过！\n")


def test_question_grouping():
    """测试问题分组。"""
    print("🧪 测试：问题分组")

    generator = QuestionGenerator(max_questions=20)
    profile = create_test_profile()
    jd_analysis = create_test_jd_analysis()
    selection = create_test_selection()

    result = generator.generate_questions(profile, jd_analysis, selection)

    grouped = result["grouped_by_type"]
    print(f"  问题分组：")
    for q_type, questions in grouped.items():
        print(f"    {q_type}: {len(questions)} 个")

    assert "clarification" in grouped, "应有歧义澄清分组"
    print(f"  ✅ 问题分组正确")

    print("  🎉 测试通过！\n")


def test_max_questions_limit():
    """测试问题数量限制。"""
    print("🧪 测试：问题数量限制")

    generator = QuestionGenerator(max_questions=3)
    profile = create_test_profile()
    jd_analysis = create_test_jd_analysis()
    selection = create_test_selection()

    result = generator.generate_questions(profile, jd_analysis, selection)

    print(f"  最多生成 3 个问题，实际生成：{result['total_count']} 个")
    assert result["total_count"] <= 3, "不应超过最大数量限制"

    print(f"  ✅ 数量限制正确")

    print("  🎉 测试通过！\n")


def run_all_tests():
    """运行所有测试。"""
    print("=" * 60)
    print("📋 Question Generator 测试套件")
    print("=" * 60)
    print()

    tests = [
        test_basic_generation,
        test_missing_quantification_detection,
        test_clarification_detection,
        test_missing_descriptor_detection,
        test_answer_and_skip,
        test_question_grouping,
        test_max_questions_limit,
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