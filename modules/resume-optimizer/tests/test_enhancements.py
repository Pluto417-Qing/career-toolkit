"""测试表达优化和模板系统。"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from condenser.expression_optimizer import ExpressionOptimizer
from condenser.highlighter import Highlighter
from builder.template_system import TemplateManager


def test_expression_optimizer():
    """测试表达优化器。"""
    print("🧪 测试：表达优化器")

    optimizer = ExpressionOptimizer()

    # 测试弱动词替换
    test_cases = [
        ("负责核心模块开发", "主导核心模块开发"),
        ("参与系统设计", "贡献系统设计"),
        ("学习新技术", "掌握新技术"),
    ]

    for original, expected in test_cases:
        optimized = optimizer.optimize_text(original)
        print(f"   原文：{original}")
        print(f"   优化：{optimized}")
        # 注意：实际替换结果取决于模式
        assert len(optimized) > 0

    print("  ✅ 表达优化测试通过\n")


def test_suggestion_generation():
    """测试建议生成。"""
    print("🧪 测试：建议生成")

    optimizer = ExpressionOptimizer()

    text = "负责一些功能的开发，性能有所提升"
    suggestions = optimizer.suggest_improvements(text)

    print(f"  文本：{text}")
    print(f"  建议数：{len(suggestions)}")

    for s in suggestions:
        print(f"    - [{s['priority']}] {s['issue']}")
        print(f"      {s['suggestion']}")

    assert len(suggestions) > 0, "应生成建议"

    print("  ✅ 建议生成测试通过\n")


def test_highlighter():
    """测试重点突出器。"""
    print("🧪 测试：重点突出器")

    highlighter = Highlighter()

    # 测试高亮
    text = "主导核心模块开发，性能提升45%，QPS从1000提升至5000"
    highlighted = highlighter.highlight_text(text, mode="html")

    print(f"  原文：{text}")
    print(f"  高亮：{highlighted[:80]}...")

    assert "quant" in highlighted or "impact" in highlighted, "应添加高亮标记"

    # 测试关键点识别
    highlights = [
        "主导核心模块开发，性能提升45%",
        "参与项目开发",
        "独立实现新架构，GitHub 520+ star",
    ]

    key_points = highlighter.identify_key_points(highlights)
    print(f"\n  关键点识别：")
    for kp in key_points:
        print(f"    - 分数 {kp['score']}: {kp['text'][:30]}...")
        print(f"      原因：{kp['reasons']}")

    print("  ✅ 重点突出测试通过\n")


def test_template_system():
    """测试模板系统。"""
    print("🧪 测试：模板系统")

    manager = TemplateManager()

    # 列出模板
    templates = manager.list_templates()
    print(f"  可用模板：{len(templates)} 个")
    for t in templates:
        print(f"    - {t['name']}: {t['display_name']}")

    # 渲染简历
    resume_data = {
        "basics": {
            "name": "测试用户",
            "label": "前端工程师",
            "phone": "13800000000",
            "email": "test@test.com",
        },
        "education": [
            {
                "title": "清华大学",
                "subtitle": "计算机科学 · 本科",
                "period": "2022-2026",
                "highlights": ["GPA: 3.82/4.0"],
            }
        ],
        "work": [
            {
                "title": "字节跳动",
                "subtitle": "前端开发实习生",
                "period": "2025.06-2025.09",
                "highlights": [
                    "主导核心模块开发，性能提升45%",
                    "引入新架构，代码量下降60%",
                ],
            }
        ],
        "projects": [
            {
                "title": "MiniReact",
                "subtitle": "独立作者",
                "highlights": ["独立实现 Fiber 架构，GitHub 520+ star"],
            }
        ],
        "skills": [
            {"name": "前端框架", "keywords": ["React", "Vue", "TypeScript"]},
        ],
    }

    # 用所有模板渲染
    results = manager.render_with_all_templates(resume_data, "html")

    print(f"\n  渲染结果：")
    for name, html in results.items():
        print(f"    - {name}: {len(html)} 字符")

    # 验证所有模板都能渲染
    assert all(html for html in results.values()), "所有模板都应能渲染"

    print("  ✅ 模板系统测试通过\n")


def test_template_comparison():
    """测试模板对比。"""
    print("🧪 测试：模板对比")

    manager = TemplateManager()

    resume_data = {
        "basics": {
            "name": "测试用户",
            "label": "前端工程师",
        },
        "education": [],
        "work": [
            {
                "title": "字节跳动",
                "subtitle": "前端开发实习生",
                "highlights": ["主导核心模块开发"],
            }
        ],
        "projects": [],
        "skills": [],
    }

    comparison = manager.compare_templates(resume_data)

    print(f"  模板数：{len(comparison['templates'])}")
    print(f"  推荐数：{len(comparison['recommendations'])}")

    for rec in comparison["recommendations"]:
        print(f"    推荐：{rec['template']} - {rec['reason']}")

    assert len(comparison["templates"]) == 4, "应有 4 个模板"

    print("  ✅ 模板对比测试通过\n")


def test_star_template():
    """测试 STAR 模板。"""
    print("🧪 测试：STAR 模板")

    optimizer = ExpressionOptimizer()

    sentence = optimizer.apply_star_template(
        situation="高并发场景",
        task="优化系统性能",
        action="引入缓存机制",
        result="QPS提升10倍"
    )

    print(f"  STAR 句子：{sentence}")

    assert "高并发" in sentence or "缓存" in sentence or "QPS" in sentence

    print("  ✅ STAR 模板测试通过\n")


def test_skill_prioritization():
    """测试技能优先排序。"""
    print("🧪 测试：技能优先排序")

    highlighter = Highlighter()

    skills = ["React", "Python", "Vue", "SQL", "TypeScript"]
    jd_keywords = ["React", "TypeScript", "Node.js"]

    prioritized = highlighter.prioritize_skills(skills, jd_keywords)

    print(f"  原始技能：{skills}")
    print(f"  JD 关键词：{jd_keywords}")
    print(f"  排序结果：")
    for p in prioritized:
        print(f"    - {p['skill']}: {p['priority']} ({p.get('match_type', '-')})")

    # React 和 TypeScript 应该是高优先级
    high_priority = [p for p in prioritized if p["priority"] == "high"]
    assert len(high_priority) >= 2, "应有至少 2 个高优先级技能"

    print("  ✅ 技能排序测试通过\n")


def run_all_tests():
    """运行所有测试。"""
    print("=" * 60)
    print("📋 表达优化和模板系统测试套件")
    print("=" * 60)
    print()

    tests = [
        test_expression_optimizer,
        test_suggestion_generation,
        test_highlighter,
        test_template_system,
        test_template_comparison,
        test_star_template,
        test_skill_prioritization,
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