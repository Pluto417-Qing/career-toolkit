"""bullet_rewrite.py 单元测试。

运行：python3 tests/test_bullet_rewrite.py
"""

import sys
import tempfile
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from bullet_rewrite import (
    diagnose_bullet,
    extract_highlights,
    starts_with_verb,
    get_verb_category,
    run,
    ALL_VERBS,
)


def test_starts_with_verb():
    """动词检测正确。"""
    assert starts_with_verb("主导了系统重构") is True
    assert starts_with_verb("参与了开发") is True
    assert starts_with_verb("需要做很多事情") is False
    print("✅ test_starts_with_verb passed")


def test_get_verb_category():
    """动词分类正确。"""
    assert get_verb_category("主导广告系统重构") == "create"
    assert get_verb_category("优化了查询性能") == "optimize"
    assert get_verb_category("分析用户行为数据") == "analyze"
    assert get_verb_category("带领5人团队") == "manage"
    assert get_verb_category("部署了K8s集群") == "technical"
    assert get_verb_category("没有动词开头") is None
    print("✅ test_get_verb_category passed")


def test_diagnose_good_bullet():
    """质量好的 bullet 不应该有问题。"""
    diag = diagnose_bullet("主导广告系统重构，覆盖 30+ 场景，CTR 提升 15%")
    assert len(diag["issues"]) == 0, f"好 bullet 不应有问题: {diag['issues']}"
    assert diag["verb_category"] == "create"
    print("✅ test_diagnose_good_bullet passed")


def test_diagnose_no_quant():
    """缺少量化的 bullet 应该报 NO_QUANT。"""
    diag = diagnose_bullet("主导了系统重构，提升了性能")
    # 「提升了性能」包含 RESULT 关键词但缺少量化数据
    assert "NO_QUANT" in diag["issues"], "应检测到缺少量化数据"
    print("✅ test_diagnose_no_quant passed")


def test_diagnose_vague():
    """模糊描述应该报 VAGUE。"""
    diag = diagnose_bullet("参与了一些相关工作，负责相关的事情")
    assert "VAGUE" in diag["issues"], f"应检测到模糊词: {diag['issues']}"
    print("✅ test_diagnose_vague passed")


def test_diagnose_duty_list():
    """职责式描述应该报 DUTY_LIST。"""
    diag = diagnose_bullet("负责日常维护工作")
    assert "DUTY_LIST" in diag["issues"], f"应检测到职责式: {diag['issues']}"
    print("✅ test_diagnose_duty_list passed")


def test_diagnose_too_short():
    """过短描述应该报 TOO_SHORT。"""
    diag = diagnose_bullet("写了代码")
    assert "TOO_SHORT" in diag["issues"]
    print("✅ test_diagnose_too_short passed")


def test_diagnose_too_long():
    """过长描述应该报 TOO_LONG。"""
    long_text = "主导了一个非常非常非常非常非常非常非常非常非常非常非常非常非常非常非常非常非常非常长的项目描述" * 2
    diag = diagnose_bullet(long_text)
    assert "TOO_LONG" in diag["issues"]
    print("✅ test_diagnose_too_long passed")


def test_extract_highlights():
    """从简历中正确提取 highlights。"""
    resume = {
        "work": [
            {
                "organization": "字节跳动",
                "highlights": ["主导系统重构，QPS 提升 50%", "参与了一些相关工作"],
            }
        ],
        "projects": [
            {
                "name": "项目A",
                "highlights": ["负责日常维护"],
            }
        ],
    }
    bullets = extract_highlights(resume)
    assert len(bullets) == 3
    assert bullets[0]["entry_name"] == "字节跳动"
    assert bullets[2]["section"] == "projects"
    print("✅ test_extract_highlights passed")


def test_run_full():
    """端到端测试。"""
    resume_yaml = """
basics:
  name: 张三
work:
  - organization: 字节跳动
    position: 前端实习生
    highlights:
      - "主导广告系统重构，覆盖 30+ 场景，CTR 提升 15%"
      - "参与了一些相关工作"
      - "负责日常维护"
projects:
  - name: 个人项目
    tech: [React]
    highlights:
      - "设计并实现了用户画像系统"
"""
    with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False, encoding="utf-8") as f:
        f.write(resume_yaml)
        path = f.name
    try:
        result = run(path)
        assert result["total_bullets"] == 4
        # bullet 1 好，bullet 2/3 有多个问题，bullet 4 缺量化
        assert result["problematic_count"] == 3, f"应有 3 条问题 bullet: {result['problematic_count']}"
        assert result["healthy_count"] == 1
        assert "VAGUE" in result["issue_distribution"] or "DUTY_LIST" in result["issue_distribution"]
        print(f"✅ test_run_full passed (总 {result['total_bullets']} 条，问题 {result['problematic_count']} 条)")
    finally:
        Path(path).unlink(missing_ok=True)


if __name__ == "__main__":
    test_starts_with_verb()
    test_get_verb_category()
    test_diagnose_good_bullet()
    test_diagnose_no_quant()
    test_diagnose_vague()
    test_diagnose_duty_list()
    test_diagnose_too_short()
    test_diagnose_too_long()
    test_extract_highlights()
    test_run_full()
    print("\n🎉 所有 bullet_rewrite 测试通过")
