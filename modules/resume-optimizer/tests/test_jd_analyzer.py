"""测试 jd_analyzer。"""

import sys
from pathlib import Path

# 添加模块路径
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from jd.jd_analyzer import JDAnalyzer


def test_basic_analysis():
    """测试基础 JD 分析。"""
    print("🧪 测试：基础 JD 分析")

    analyzer = JDAnalyzer()

    jd_text = """
    岗位：前端工程师
    
    岗位职责：
    1. 负责公司产品的前端开发，使用 React 和 TypeScript
    2. 优化前端性能，提升用户体验
    3. 参与前端工程化建设，包括 CI/CD 流水线
    
    任职要求：
    1. 本科及以上学历，计算机相关专业
    2. 2年以上前端开发经验，精通 React
    3. 熟悉 TypeScript、Webpack、Vite 等技术
    4. 有性能优化经验，了解 FCP、LCP 等指标
    5. 具备良好的团队协作和沟通能力
    
    加分项：
    1. 有开源项目贡献者
    2. 熟悉 Next.js、Node.js
    """

    result = analyzer.analyze(jd_text)

    print(f"  📊 JD 质量评分：{result['quality_score']}")
    
    # 检查关键词提取
    required_kw = result["keywords"]["required"]
    preferred_kw = result["keywords"]["preferred"]
    
    print(f"  🔴 必备关键词 ({len(required_kw)} 个)：")
    for kw in required_kw[:5]:
        print(f"     - {kw['keyword']} (权重 {kw['weight']})")
    
    print(f"  🟡 加分关键词 ({len(preferred_kw)} 个)：")
    for kw in preferred_kw[:5]:
        print(f"     - {kw['keyword']} (权重 {kw['weight']})")

    # 检查要求提取
    req = result["requirements"]
    print(f"  📋 经验要求：{req.get('experience')}")
    print(f"  📋 学历要求：{req.get('education')}")
    print(f"  📋 岗位类型：{req.get('position_type')}")

    # 检查概念映射
    concepts = result["concept_mapping"]
    print(f"  🧩 概念映射 ({len(concepts)} 个)：")
    for concept in concepts:
        print(f"     - {concept['concept']}: {concept.get('matched_keywords', [])}")

    # 验证核心关键词被提取
    all_keywords = [kw["keyword"] for kw in required_kw + preferred_kw]
    assert "React" in all_keywords or "TypeScript" in all_keywords, "未提取到 React/TypeScript"
    print(f"  ✅ 核心关键词提取成功")

    # 验证概念映射
    concept_names = [c["concept"] for c in concepts]
    assert len(concept_names) > 0, "概念映射为空"
    print(f"  ✅ 概念映射成功")

    print("  🎉 测试通过！\n")


def test_requirements_extraction():
    """测试要求提取。"""
    print("🧪 测试：要求提取")

    analyzer = JDAnalyzer()

    test_cases = [
        {
            "text": "招聘应届毕业生，本科及以上学历",
            "expected_exp": {"level": "应届生", "years": 0},
            "expected_edu": {"level": "本科"},
        },
        {
            "text": "要求3-5年工作经验，硕士学历",
            "expected_exp": {"level": "高级", "years": 3},
            "expected_edu": {"level": "硕士"},
        },
        {
            "text": "5年以上经验，博士优先",
            "expected_exp": {"level": "专家", "years": 5},
            "expected_edu": {"level": "博士"},
        },
    ]

    for i, case in enumerate(test_cases):
        result = analyzer._extract_requirements(case["text"])
        
        exp = result["experience"]
        edu = result["education"]
        
        # 验证
        assert exp.get("level") == case["expected_exp"]["level"], \
            f"Case {i}: 经验级别不匹配，期望 {case['expected_exp']['level']}，实际 {exp.get('level')}"
        assert edu.get("level") == case["expected_edu"]["level"], \
            f"Case {i}: 学历级别不匹配"
        
        print(f"  ✅ Case {i}: 经验={exp.get('level')}, 学历={edu.get('level')}")

    print("  🎉 测试通过！\n")


def test_concept_mapping():
    """测试概念映射。"""
    print("🧪 测试：概念映射")

    analyzer = JDAnalyzer()

    # 模拟关键词列表
    keywords = [
        {"keyword": "React", "weight": 10},
        {"keyword": "TypeScript", "weight": 10},
        {"keyword": "Webpack", "weight": 8},
        {"keyword": "Docker", "weight": 5},
    ]

    mappings = analyzer._build_concept_mapping(keywords)

    # 应该找到至少 2 个概念
    assert len(mappings) >= 2, f"概念映射过少：{len(mappings)}"

    print(f"  🧩 概念映射结果 ({len(mappings)} 个概念)：")
    for m in mappings:
        print(f"     - {m['concept']}")
        print(f"       匹配关键词：{m.get('matched_keywords', [])}")
        print(f"       相关关键词（前5个）：{m.get('related_keywords', [])[:5]}")

    # 测试获取相关关键词
    related = analyzer.get_related_keywords("React")
    print(f"  🔗 React 的相关词 ({len(related)} 个)：{related[:10]}")

    # 测试获取关键词所属概念
    concepts = analyzer.get_concepts_for_keyword("Webpack")
    print(f"  📂 Webpack 所属概念：{concepts}")

    print("  🎉 测试通过！\n")


def test_quality_scoring():
    """测试 JD 质量评分。"""
    print("🧪 测试：JD 质量评分")

    analyzer = JDAnalyzer()

    # 高质量 JD
    high_quality_jd = """
    岗位职责：
    1. 负责产品核心模块的前端开发，使用 React 和 TypeScript
    2. 推动前端工程化建设，包括 CI/CD、自动化测试
    3. 优化页面性能，提升 FCP、LCP 等核心指标

    任职要求：
    1. 本科及以上学历，计算机相关专业
    2. 3年以上前端经验，精通 React、TypeScript
    3. 熟悉 Webpack、Vite 等构建工具
    4. 了解性能优化原理，有实际优化经验
    5. 具备良好的团队协作和沟通能力

    加分项：
    1. 有开源项目贡献
    2. 熟悉 Node.js、Next.js
    3. 了解微前端架构
    """

    high_score = analyzer.analyze(high_quality_jd)["quality_score"]

    # 低质量 JD
    low_quality_jd = """
    招前端，会写代码就行。
    """

    low_score = analyzer.analyze(low_quality_jd)["quality_score"]

    print(f"  高质量 JD 评分：{high_score}")
    print(f"  低质量 JD 评分：{low_score}")
    assert high_score > low_score, "高质量 JD 评分应更高"

    print("  🎉 测试通过！\n")


def test_save_and_load():
    """测试保存分析结果。"""
    print("🧪 测试：保存分析结果")

    import tempfile
    from pathlib import Path
    import yaml

    analyzer = JDAnalyzer()
    result = analyzer.analyze("招前端工程师，要求 React、TypeScript")

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "jd_analysis.yaml"
        analyzer.save_analysis(result, str(output_path))

        assert output_path.exists(), "文件未保存"
        
        # 验证可以重新加载
        with open(output_path, "r", encoding="utf-8") as f:
            loaded = yaml.safe_load(f)
        assert "keywords" in loaded
        print(f"  ✅ 保存成功：{output_path}")
        print(f"  ✅ 加载验证成功")

    print("  🎉 测试通过！\n")


def run_all_tests():
    """运行所有测试。"""
    import yaml

    print("=" * 60)
    print("📋 JD Analyzer 测试套件")
    print("=" * 60)
    print()

    tests = [
        test_basic_analysis,
        test_requirements_extraction,
        test_concept_mapping,
        test_quality_scoring,
        test_save_and_load,
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