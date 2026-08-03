"""测试 experience_ranker。"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ranker.experience_ranker import ExperienceRanker


def create_test_profile():
    """创建测试用信息库。"""
    return {
        "basics": {"name": "测试用户"},
        "education": [
            {
                "id": "edu_001",
                "institution": "清华大学",
                "area": "计算机科学与技术",
                "degree": "本科",
                "gpa": "3.82/4.0",
                "start": "2022-09",
                "end": "2026-06",
                "courses": ["数据结构", "算法设计", "操作系统"],
                "descriptor": {
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
                        "action": "设计并实现",
                        "target": "Schema化改造方案",
                        "result": "代码量下降45%",
                        "impact": "全团队采用",
                        "tech_used": ["React", "TypeScript"],
                    },
                    {
                        "action": "引入",
                        "target": "运行时校验框架",
                        "result": "线上表单问题减少60%",
                        "tech_used": ["TypeScript"],
                    }
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
                        "action": "优化",
                        "target": "SSR渲染性能",
                        "result": "FCP从2.1s降至0.8s",
                    }
                ],
                "descriptor": {
                    "user_importance_rating": 7,
                }
            },
            {
                "id": "work_003",
                "organization": "小公司",
                "position": "后端开发实习生",
                "start": "2023-06",
                "end": "2023-09",
                "tech": ["Python", "Django"],
                "project_context": {
                    "name": "内部管理系统",
                },
                "personal_contribution": [
                    {
                        "action": "参与",
                        "target": "CRUD功能开发",
                    }
                ],
                "descriptor": {
                    "user_importance_rating": 3,
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
                        "action": "独立实现",
                        "target": "Fiber架构和Hooks",
                        "result": "GitHub 520+ star",
                    }
                ],
                "descriptor": {
                    "user_importance_rating": 8,
                }
            },
            {
                "id": "proj_002",
                "name": "数据分析工具",
                "role": "参与者",
                "tech": ["Python", "Pandas"],
                "project_context": {
                    "description": "股票数据分析",
                },
                "personal_contribution": [
                    {
                        "action": "编写",
                        "target": "数据清洗脚本",
                    }
                ],
                "descriptor": {
                    "user_importance_rating": 5,
                }
            }
        ],
    }


def create_test_jd_analysis():
    """创建测试用 JD 分析结果。"""
    return {
        "keywords": {
            "required": [
                {"keyword": "React", "weight": 10},
                {"keyword": "TypeScript", "weight": 10},
                {"keyword": "前端工程化", "weight": 8},
            ],
            "preferred": [
                {"keyword": "Next.js", "weight": 5},
                {"keyword": "性能优化", "weight": 5},
            ]
        },
        "soft_skills": [],
        "requirements": {
            "experience": {"level": "应届生", "years": 0},
            "education": {"level": "本科"},
            "position_type": "前端开发",
        },
        "concept_mapping": [
            {
                "concept": "前端工程化",
                "matched_keywords": ["React", "TypeScript"],
                "related_keywords": ["Webpack", "Vite", "Docker", "Jenkins", "CI/CD"],
            },
            {
                "concept": "前端框架",
                "matched_keywords": ["React"],
                "related_keywords": ["React", "Next.js", "Redux", "Vue"],
            },
            {
                "concept": "性能优化",
                "matched_keywords": [],
                "related_keywords": ["FCP", "LCP", "首屏加载", "QPS"],
            },
        ],
    }


def test_basic_ranking():
    """测试基础排名。"""
    print("🧪 测试：基础排名")

    ranker = ExperienceRanker()
    profile = create_test_profile()
    jd_analysis = create_test_jd_analysis()

    result = ranker.rank(profile, jd_analysis)

    print(f"  📊 分数汇总：")
    summary = result["score_summary"]
    print(f"     - 选中 {summary['total_entries_selected']}/{summary['total_entries_available']} 条经历")
    print(f"     - 工作经历平均分：{summary['avg_work_score']}")
    print(f"     - 项目经历平均分：{summary['avg_project_score']}")

    # 检查工作经历排序
    work_results = result["work"]
    print(f"\n  💼 工作经历排名（Top {len(work_results)}）：")
    for i, entry in enumerate(work_results):
        org = entry["_raw_entry"]["organization"]
        print(f"     {i+1}. {org} - 分数 {entry['score']}")
        print(f"        原因：{entry['reasons'][:2]}")

    # 验证排序正确（字节跳动应该排第一，因为它用了 React/TypeScript）
    if work_results:
        first_org = work_results[0]["_raw_entry"]["organization"]
        assert first_org == "字节跳动", f"字节跳动应排第一，实际第一是 {first_org}"
        print(f"\n  ✅ 排序正确：字节跳动（使用 React）排第一")

    print("  🎉 测试通过！\n")


def test_quantifiable_scoring():
    """测试量化成果评分。"""
    print("🧪 测试：量化成果评分")

    ranker = ExperienceRanker()

    # 测试条目 1：有量化成果
    entry_with_quant = {
        "personal_contribution": [
            {"result": "代码量下降45%"},
            {"result": "性能提升3倍"},
        ],
        "project_context": {"scale": "日活500万+"},
    }

    score1 = ranker._calculate_quant_score(entry_with_quant)
    print(f"  有量化成果的条目得分：{score1}")

    # 测试条目 2：无量化成果
    entry_without_quant = {
        "personal_contribution": [
            {"target": "功能开发"},
        ],
    }

    score2 = ranker._calculate_quant_score(entry_without_quant)
    print(f"  无量化成果的条目得分：{score2}")

    assert score1 > score2, "有量化成果的条目得分应更高"
    print(f"  ✅ 量化评分正确")

    print("  🎉 测试通过！\n")


def test_freshness_scoring():
    """测试时效性评分。"""
    print("🧪 测试：时效性评分")

    ranker = ExperienceRanker()

    # 近期经历
    recent_entry = {"end": "2025-09"}
    recent_score = ranker._calculate_freshness_score(recent_entry)
    print(f"  近期经历（2025-09）得分：{recent_score}")

    # 较早经历
    old_entry = {"end": "2020-06"}
    old_score = ranker._calculate_freshness_score(old_entry)
    print(f"  较早经历（2020-06）得分：{old_score}")

    # 未知日期
    unknown_entry = {}
    unknown_score = ranker._calculate_freshness_score(unknown_entry)
    print(f"  未知日期得分：{unknown_score}")

    assert recent_score > old_score, "近期经历得分应更高"
    print(f"  ✅ 时效性评分正确")

    print("  🎉 测试通过！\n")


def test_keyword_matching():
    """测试关键词匹配。"""
    print("🧪 测试：关键词匹配")

    ranker = ExperienceRanker()

    # 条目文本包含关键词
    entry_text = "负责 React 前端开发，使用 TypeScript 和 Webpack"
    entry_tech = ["React", "TypeScript"]
    jd_keywords = ["React", "TypeScript", "Docker"]

    score, matched = ranker._calculate_keyword_score(entry_text, entry_tech, jd_keywords)
    print(f"  匹配得分：{score}")
    print(f"  匹配关键词：{matched}")

    assert "React" in matched, "应匹配到 React"
    assert "TypeScript" in matched, "应匹配到 TypeScript"
    print(f"  ✅ 关键词匹配正确")

    print("  🎉 测试通过！\n")


def test_selection_limit():
    """测试筛选数量限制。"""
    print("🧪 测试：筛选数量限制")

    ranker = ExperienceRanker()
    profile = create_test_profile()
    jd_analysis = create_test_jd_analysis()

    # 修改配置，只保留 1 条工作经历
    ranker.config["max_work_entries"] = 1
    ranker.config["max_project_entries"] = 1

    result = ranker.rank(profile, jd_analysis)

    print(f"  工作经历（限制1条）：{len(result['work'])} 条")
    print(f"  项目经历（限制1条）：{len(result['projects'])} 条")

    assert len(result["work"]) <= 1, "工作经历应不超过1条"
    assert len(result["projects"]) <= 1, "项目经历应不超过1条"

    # 检查被隐藏的条目
    print(f"  被隐藏的条目：{len(result['hidden_entries'])} 条")
    for hidden in result["hidden_entries"]:
        print(f"     - {hidden['id']} (类型：{hidden['entry_type']}, 分数：{hidden['score']})")

    print(f"  ✅ 筛选限制正确")

    print("  🎉 测试通过！\n")


def test_suggestions_generation():
    """测试建议生成。"""
    print("🧪 测试：建议生成")

    ranker = ExperienceRanker()

    # 评分低的条目
    low_score_entry = {
        "personal_contribution": [
            {"action": "参与", "target": "一些开发"},
        ],
        "descriptor": {},
    }

    suggestions = ranker._generate_suggestions(low_score_entry, 0.2, 0.1, 0.0)
    print(f"  低评分条目建议：{suggestions}")

    assert len(suggestions) > 0, "应生成优化建议"
    print(f"  ✅ 建议生成正确")

    print("  🎉 测试通过！\n")


def test_manual_hidden_entry():
    """测试手动隐藏条目。"""
    print("🧪 测试：手动隐藏条目")

    ranker = ExperienceRanker()

    # 创建 profile，其中 work_003 被标记为 hidden
    profile = create_test_profile()
    profile["work"][2]["descriptor"]["hidden"] = True  # 小公司后端实习

    jd_analysis = create_test_jd_analysis()

    result = ranker.rank(profile, jd_analysis)

    selected_work_ids = [e["id"] for e in result["work"]]
    print(f"  选中的工作经历 ID：{selected_work_ids}")

    assert "work_003" not in selected_work_ids, "被标记为 hidden 的条目不应出现"
    print(f"  ✅ 手动隐藏功能正确")

    print("  🎉 测试通过！\n")


def run_all_tests():
    """运行所有测试。"""
    print("=" * 60)
    print("📋 Experience Ranker 测试套件")
    print("=" * 60)
    print()

    tests = [
        test_basic_ranking,
        test_quantifiable_scoring,
        test_freshness_scoring,
        test_keyword_matching,
        test_selection_limit,
        test_suggestions_generation,
        test_manual_hidden_entry,
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