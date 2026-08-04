"""测试 content_condenser。"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from condenser.content_condenser import ContentCondenser


def create_test_profile():
    """创建测试用信息库。"""
    return {
        "meta": {"id": "test_001"},
        "basics": {
            "name": "测试用户",
            "label": "前端工程师",
            "phone": "13800000000",
            "email": "test@test.com",
        },
        "education": [
            {
                "id": "edu_001",
                "institution": "清华大学",
                "area": "计算机科学与技术",
                "degree": "本科",
                "gpa": "3.82/4.0",
                "start": "2022-09",
                "end": "2026-06",
                "courses": ["数据结构", "算法设计", "操作系统", "计算机网络", "编译原理"],
                "honors": ["国家奖学金", "优秀学生干部"],
                "descriptor": {
                    "core_courses_confirmed": True,
                    "user_importance_rating": 10,
                }
            }
        ],
        "work": [
            {
                "id": "work_001",
                "organization": "字节跳动",
                "position": "前端开发实习生",
                "start": "2025-06",
                "end": "2025-09",
                "tech": ["React", "TypeScript", "Docker", "Jenkins"],
                "project_context": {
                    "name": "广告投放平台",
                    "business_value": "支持30+广告场景",
                    "scale": "日活500万+",
                },
                "personal_contribution": [
                    {
                        "id": "contrib_001",
                        "action": "设计并实现",
                        "target": "Schema化改造方案",
                        "result": "代码量下降45%",
                        "impact": "全团队采用",
                        "tech_used": ["React", "TypeScript"],
                    },
                    {
                        "id": "contrib_002",
                        "action": "引入",
                        "target": "运行时校验框架",
                        "result": "线上表单问题减少60%",
                        "tech_used": ["TypeScript"],
                    },
                    {
                        "id": "contrib_003",
                        "action": "搭建",
                        "target": "Docker + Jenkins 自动化流水线",
                        "result": "构建效率提升3倍",
                    },
                    {
                        "id": "contrib_004",
                        "action": "负责",  # 弱动词，应被替换
                        "target": "一些边缘功能",
                        "result": "",
                    },
                ],
                "descriptor": {
                    "user_importance_rating": 9,
                }
            },
            {
                "id": "work_002",
                "organization": "腾讯",
                "position": "前端开发实习生",
                "start": "2024-06",
                "end": "2024-09",
                "tech": ["Vue", "Next.js", "Node.js"],
                "project_context": {
                    "name": "微信小程序框架",
                    "scale": "支持万级日活",
                },
                "personal_contribution": [
                    {
                        "id": "contrib_005",
                        "action": "优化",
                        "target": "SSR渲染性能",
                        "result": "FCP从2.1s降至0.8s",
                    },
                    {
                        "id": "contrib_006",
                        "action": "封装",
                        "target": "12个可视化组件",
                        "result": "复用率提升至85%",
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
                "url": "https://github.com/test/mini-react",
                "project_context": {
                    "description": "简化版React，实现Fiber架构",
                    "scale": "520+ star",
                },
                "personal_contribution": [
                    {
                        "id": "contrib_p1",
                        "action": "独立实现",
                        "target": "Fiber架构和Hooks",
                        "result": "GitHub 520+ star",
                    },
                    {
                        "id": "contrib_p2",
                        "action": "撰写",
                        "target": "8篇技术博客",
                        "result": "月访问量2000+",
                    },
                ],
                "descriptor": {
                    "user_importance_rating": 8,
                }
            }
        ],
        "skills": [
            {"id": "skill_001", "name": "编程语言", "keywords": ["TypeScript", "JavaScript"]},
            {"id": "skill_002", "name": "前端框架", "keywords": ["React", "Vue", "Next.js"]},
        ],
    }


def create_test_selection():
    """创建测试用筛选结果。"""
    return {
        "education": [
            {
                "id": "edu_001",
                "score": 0.95,
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
            },
        ],
        "projects": [
            {
                "id": "proj_001",
                "score": 0.85,
                "_raw_entry": create_test_profile()["projects"][0],
            }
        ],
        "hidden_entries": [],
        "score_summary": {},
    }


def test_basic_condense():
    """测试基础精简。"""
    print("🧪 测试：基础精简")

    condenser = ContentCondenser()
    profile = create_test_profile()
    selection = create_test_selection()

    result = condenser.condense_resume(profile, selection)

    print(f"  📊 精简结果：")
    print(f"     - 教育背景：{len(result['education'])} 条")
    print(f"     - 工作经历：{len(result['work'])} 条")
    print(f"     - 项目经历：{len(result['projects'])} 条")
    print(f"     - 行数：{result['line_count']}")
    print(f"     - 页数：{result['estimated_pages']}")
    print(f"     - 是否一页：{result['fits_one_page']}")

    # 检查工作经历亮点
    for work in result["work"]:
        print(f"\n  💼 {work['title']} - {work['subtitle']}")
        print(f"     亮点 ({len(work['highlights'])} 条)：")
        for hl in work["highlights"]:
            print(f"     - {hl}")

    # 验证合并双视角
    work1 = result["work"][0]
    assert work1["highlights"], "应有亮点"
    print(f"\n  ✅ 基础精简成功")

    print("  🎉 测试通过！\n")


def test_dual_perspective_merge():
    """测试双视角合并。"""
    print("🧪 测试：双视角合并")

    condenser = ContentCondenser()

    # 测试合并
    entry = {
        "project_context": {
            "name": "广告投放平台",
            "scale": "日活500万+",
        },
        "personal_contribution": [
            {
                "action": "设计并实现",
                "target": "Schema化改造方案",
                "result": "代码量下降45%",
            },
            {
                "action": "引入",
                "target": "运行时校验框架",
                "result": "线上问题减少60%",
            },
        ],
    }

    highlights = condenser._merge_dual_perspective(entry)
    print(f"  合并亮点：")
    for hl in highlights:
        print(f"    - {hl}")

    # 验证格式
    assert highlights, "应有亮点"
    # 检查是否合并了 action + target + result
    assert any("设计并实现" in hl and "代码量下降45%" in hl for hl in highlights), \
        "应合并 action + target + result"

    print(f"  ✅ 双视角合并正确")

    print("  🎉 测试通过！\n")


def test_weak_verb_removal():
    """测试弱动词移除。"""
    print("🧪 测试：弱动词移除")

    condenser = ContentCondenser()

    # 测试弱动词替换
    test_highlights = [
        "负责核心模块开发",
        "参与系统设计",
        "设计并实现新架构",
        "优化页面性能",
    ]

    condensed = condenser._trim_highlights(test_highlights)
    print(f"  原始：{test_highlights}")
    print(f"  精简后：{condensed}")

    # 弱动词"负责"应被替换为"主导"
    assert any("主导" in hl for hl in condensed), "弱动词'负责'应被替换为'主导'"

    print(f"  ✅ 弱动词移除正确")

    print("  🎉 测试通过！\n")


def test_page_estimation():
    """测试一页纸估算。"""
    print("🧪 测试：一页纸估算")

    condenser = ContentCondenser()

    # 模拟精简简历
    resume = {
        "education": [
            {"highlights": ["GPA: 3.82", "核心课程：数据结构, 算法设计"]}
        ],
        "work": [
            {"highlights": ["设计并实现XXX，提升45%", "引入XXX，减少60%问题"]},
            {"highlights": ["优化XXX，FCP从2.1s降至0.8s"]},
        ],
        "projects": [
            {"highlights": ["独立实现XXX，520+ star", "撰写博客，月访问2000+"]},
        ],
    }

    condenser._estimate_page(resume)

    print(f"  行数：{resume['line_count']}")
    print(f"  字数：{resume['word_count']}")
    print(f"  估算页数：{resume['estimated_pages']}")
    print(f"  是否一页：{resume['fits_one_page']}")

    assert "line_count" in resume, "应包含行数"
    assert "fits_one_page" in resume, "应包含一页纸判断"

    print(f"  ✅ 一页纸估算正确")

    print("  🎉 测试通过！\n")


def test_further_condense():
    """测试进一步精简。"""
    print("🧪 测试：进一步精简")

    condenser = ContentCondenser()

    # 创建一个超长简历
    resume = {
        "meta": {},
        "basics": {"name": "测试"},
        "education": [
            {
                "title": "学校",
                "subtitle": "专业",
                "highlights": [f"亮点{i}" for i in range(10)],
            }
        ],
        "work": [
            {
                "title": "公司1",
                "subtitle": "职位",
                "highlights": [f"亮点{i}" for i in range(5)],
            },
            {
                "title": "公司2",
                "subtitle": "职位",
                "highlights": [f"亮点{i}" for i in range(5)],
            },
            {
                "title": "公司3",
                "subtitle": "职位",
                "highlights": [f"亮点{i}" for i in range(5)],
            },
        ],
        "projects": [
            {
                "title": "项目1",
                "subtitle": "角色",
                "highlights": [f"亮点{i}" for i in range(5)],
            },
            {
                "title": "项目2",
                "subtitle": "角色",
                "highlights": [f"亮点{i}" for i in range(5)],
            },
        ],
        "skills": [],
    }

    condenser._estimate_page(resume)
    print(f"  精简前行数：{resume['line_count']}")
    print(f"  精简前是否一页：{resume['fits_one_page']}")

    # 强制进一步精简
    result = condenser._further_condense(resume)

    print(f"  精简后行数：{result['line_count']}")
    print(f"  精简后是否一页：{result['fits_one_page']}")

    # 精简后应适应一页
    assert result["fits_one_page"], "精简后应适应一页纸"

    print(f"  ✅ 进一步精简正确")

    print("  🎉 测试通过！\n")


def test_quantifiable_detection():
    """测试量化数据检测。"""
    print("🧪 测试：量化数据检测")

    condenser = ContentCondenser()

    test_cases = [
        ("代码量下降45%", True),
        ("性能提升3倍", True),
        ("日活500万+", True),
        ("GitHub 520+ star", True),
        ("完成功能开发", False),
        ("参与了一些工作", False),
    ]

    for text, expected in test_cases:
        result = condenser._has_quantifiable_data(text)
        status = "✅" if result == expected else "❌"
        print(f"  {status} '{text}' -> 有量化数据：{result}")

    print("  🎉 测试通过！\n")


def run_all_tests():
    """运行所有测试。"""
    print("=" * 60)
    print("📋 Content Condenser 测试套件")
    print("=" * 60)
    print()

    tests = [
        test_basic_condense,
        test_dual_perspective_merge,
        test_weak_verb_removal,
        test_page_estimation,
        test_further_condense,
        test_quantifiable_detection,
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