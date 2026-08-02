"""jd_parser.py 单元测试。

运行：python3 tests/test_jd_parser.py
"""

import json
import sys
import tempfile
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from jd_parser import (
    clean_noise,
    detect_section,
    split_into_sections,
    split_requirements,
    classify_requirement,
    determine_importance,
    parse_jd,
    score_jd_quality,
)


def test_clean_noise():
    """噪音清洗能过滤投递/URL/空行/分隔线。"""
    lines = [
        "岗位职责：",
        "1. 负责前端开发",
        "投递简历至 hr@test.com",
        "https://www.test.com",
        "",
        "———",
        "2. 负责后端开发",
    ]
    cleaned = clean_noise(lines)
    assert "投递简历至 hr@test.com" not in cleaned
    assert "https://www.test.com" not in cleaned
    assert "" not in cleaned
    assert "1. 负责前端开发" in cleaned
    print("✅ test_clean_noise passed")


def test_detect_section():
    """段落识别正确。"""
    assert detect_section("任职要求：") == "requirements"
    assert detect_section("加分项：") == "bonus"
    assert detect_section("岗位职责：") == "responsibilities"
    assert detect_section("薪资：20k-40k") == "salary"
    assert detect_section("随便一行") is None
    print("✅ test_detect_section passed")


def test_split_into_sections():
    """段落分组正确。"""
    lines = [
        "岗位职责：",
        "1. 负责前端开发",
        "2. 负责后端开发",
        "任职要求：",
        "1. 熟悉 React",
        "2. 3年以上经验",
        "加分项：",
        "1. 了解 Docker",
    ]
    sections = split_into_sections(lines)
    assert "responsibilities" in sections
    assert "requirements" in sections
    assert "bonus" in sections
    print("✅ test_split_into_sections passed")


def test_split_requirements():
    """需求拆解正确。"""
    lines = [
        "1. 熟悉 React 和 TypeScript",
        "2. 3年以上前端开发经验",
        "3. 了解 Docker 和 K8s",
    ]
    items = split_requirements(lines)
    assert len(items) == 3
    assert "React" in items[0]
    print("✅ test_split_requirements passed")


def test_classify_requirement():
    """需求分类正确。"""
    # 经验
    req = classify_requirement("3年以上开发经验")
    assert req["type"] == "experience"
    assert req["value"] == 3

    # 学历
    req = classify_requirement("本科及以上学历")
    assert req["type"] == "education"
    assert req["value"] == 2

    # 技能
    req = classify_requirement("熟悉 React 框架")
    assert req["type"] == "skill"

    print("✅ test_classify_requirement passed")


def test_determine_importance():
    """重要度标注正确。"""
    assert determine_importance("bonus", "了解 Docker") == "nice_to_have"
    assert determine_importance("requirements", "熟悉 React") == "must_have"
    assert determine_importance("unclassified", "优先有大数据经验") == "nice_to_have"
    print("✅ test_determine_importance passed")


def test_parse_jd_full():
    """端到端 JD 解析。"""
    jd_text = """
    岗位职责：
    1. 负责公司核心业务的前端开发
    2. 参与技术方案设计

    任职要求：
    1. 熟悉 React 和 TypeScript
    2. 3年以上前端开发经验
    3. 本科及以上学历
    4. 熟悉高并发架构

    加分项：
    1. 了解 Docker 和 K8s
    2. 有开源贡献者优先

    薪资：20k-40k，五险一金
    """
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as f:
        f.write(jd_text)
        path = f.name
    try:
        result = parse_jd(open(path, encoding="utf-8").read())
        assert result["stats"]["total"] >= 5, f"需求条目太少: {result['stats']}"
        # 应该有 experience 类型
        types = result["stats"]["by_type"]
        assert "experience" in types, f"缺少 experience 类型: {types}"
        assert "education" in types, f"缺少 education 类型: {types}"
        # 质量分应该 > 50
        assert result["quality"]["score"] > 50, f"质量分太低: {result['quality']}"
        print(f"✅ test_parse_jd_full passed (需求 {result['stats']['total']} 条, 质量 {result['quality']['score']} 分)")
    finally:
        Path(path).unlink(missing_ok=True)


if __name__ == "__main__":
    test_clean_noise()
    test_detect_section()
    test_split_into_sections()
    test_split_requirements()
    test_classify_requirement()
    test_determine_importance()
    test_parse_jd_full()
    print("\n🎉 所有 jd_parser 测试通过")
