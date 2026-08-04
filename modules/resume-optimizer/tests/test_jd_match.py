"""jd_match.py 单元测试（三层匹配引擎版）。

运行：python3 tests/test_jd_match.py
"""

import json
import sys
import tempfile
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from jd_match import (
    load_synonyms,
    load_concepts,
    extract_jd_keywords,
    extract_resume_terms,
    match_layer1_keywords,
    match_layer2_concepts,
    match_layer3_evidence,
    classify_gap,
    get_resume_work_years,
    get_resume_degree_level,
    get_resume_evidence,
    run,
    normalize,
)


# ═══════════════════════════════════════════
# Layer 1 测试
# ═══════════════════════════════════════════

def test_load_synonyms():
    """同义词库能正常加载。"""
    smap = load_synonyms()
    assert len(smap) > 50, f"同义词库太小：{len(smap)} 组"
    assert smap.get("js") == "javascript"
    assert smap.get("k8s") == "kubernetes"
    print("✅ test_load_synonyms passed")


def test_load_concepts():
    """概念库能正常加载。"""
    concepts = load_concepts()
    assert len(concepts) >= 20, f"概念库太小：{len(concepts)} 组"
    concept_names = [c["concept"] for c in concepts]
    assert "高并发" in concept_names
    assert "分布式" in concept_names
    assert "团队管理" in concept_names
    print("✅ test_load_concepts passed")


def test_layer1_keyword_match():
    """Layer 1: 关键词 + 同义词匹配。"""
    smap = load_synonyms()
    resume_sections = {
        "skills": {"javascript": {"JS"}, "react": {"React"}},
        "tech": {"typescript": {"TypeScript"}},
    }
    ok, sources = match_layer1_keywords("javascript", resume_sections)
    assert ok and "skills" in sources
    ok, sources = match_layer1_keywords("react", resume_sections)
    assert ok
    ok, _ = match_layer1_keywords("rust", resume_sections)
    assert not ok
    print("✅ test_layer1_keyword_match passed")


def test_layer1_synonym():
    """同义词归并：简历写 JS，JD 要求 JavaScript。"""
    smap = load_synonyms()
    resume = {
        "skills": [{"keywords": ["JS", "React"]}],
        "projects": [{"tech": ["TypeScript"]}],
    }
    sections = extract_resume_terms(resume, smap)
    ok, _ = match_layer1_keywords("javascript", sections)
    assert ok, "JS → JavaScript 未匹配"
    print("✅ test_layer1_synonym passed")


# ═══════════════════════════════════════════
# Layer 2 测试
# ═══════════════════════════════════════════

def test_layer2_concept_match():
    """Layer 2: 概念匹配。JD 要'高并发'，简历有'QPS'。"""
    smap = load_synonyms()
    resume = {
        "skills": [{"keywords": ["React"]}],
        "work": [{"highlights": ["优化了系统性能，QPS 提升 50%"]}],
    }
    evidence = get_resume_evidence(resume)
    concepts = evidence.get("concepts", set())
    assert "高并发" in concepts, f"高并发概念未匹配: {concepts}"
    ok = match_layer2_concepts("高并发", concepts)
    assert ok
    print("✅ test_layer2_concept_match passed")


def test_layer2_distributed():
    """概念匹配：简历有微服务，JD 要分布式。"""
    resume = {
        "projects": [{"tech": ["Spring Cloud"], "highlights": ["搭建了微服务架构"]}],
    }
    evidence = get_resume_evidence(resume)
    assert "分布式" in evidence.get("concepts", set()) or "微服务架构" in evidence.get("concepts", set())
    print("✅ test_layer2_distributed passed")


# ═══════════════════════════════════════════
# Layer 3 测试
# ═══════════════════════════════════════════

def test_layer3_experience():
    """Layer 3: 经验年限匹配。"""
    evidence = {"work_years": 3.5, "degree_level": 2}
    ok, note = match_layer3_evidence({"type": "experience", "value": 3}, evidence)
    assert ok, "3.5年 >= 3年应该匹配"
    ok, note = match_layer3_evidence({"type": "experience", "value": 5}, evidence)
    assert not ok, "3.5年 < 5年不应该匹配"
    print("✅ test_layer3_experience passed")


def test_layer3_education():
    """Layer 3: 学历匹配。"""
    evidence = {"work_years": 0, "degree_level": 3}  # 硕士
    ok, _ = match_layer3_evidence({"type": "education", "value": 2}, evidence)
    assert ok, "硕士 >= 本科应该匹配"
    ok, _ = match_layer3_evidence({"type": "education", "value": 4}, evidence)
    assert not ok, "硕士 < 博士不应该匹配"
    print("✅ test_layer3_education passed")


def test_resume_work_years():
    """工作年限计算正确。"""
    resume = {
        "work": [
            {"start": "2022.06", "end": "2023.06"},  # 1 年
            {"start": "2023.07", "end": "至今"},       # ~1 年
        ]
    }
    years = get_resume_work_years(resume)
    # 2022.06-2023.06 = 1年 + 2023.07-至今（~3年），总共 ~4年
    assert years >= 3.0, f"年限计算异常: {years}"
    print(f"✅ test_resume_work_years passed (计算 {years} 年)")


def test_resume_degree():
    """学历等级提取正确。"""
    resume = {"education": [{"degree": "硕士"}]}
    assert get_resume_degree_level(resume) == 3
    resume = {"education": [{"degree": "本科"}]}
    assert get_resume_degree_level(resume) == 2
    print("✅ test_resume_degree passed")


# ═══════════════════════════════════════════
# Gap 分类测试
# ═══════════════════════════════════════════

def test_classify_gap_evidence():
    """Gap 分类：有相关内容但没写关键词 → evidence_gap。"""
    smap = load_synonyms()
    resume_sections = {"tech": {"docker": {"Docker"}}}
    resume_full_text = "使用了 Docker 容器化部署".lower()
    evidence = {"concepts": {"容器化"}}
    # Kubernetes 缺失，但简历有 Docker（属于「容器化」概念）
    gap_type = classify_gap("kubernetes", resume_sections, resume_full_text, evidence)
    assert gap_type == "evidence_gap", f"应为 evidence_gap: {gap_type}"
    print("✅ test_classify_gap_evidence passed")


def test_classify_gap_real():
    """Gap 分类：完全没有相关经验 → real_gap。"""
    resume_sections = {"skills": {"react": {"React"}}}
    resume_full_text = "前端开发 React".lower()
    evidence = {"concepts": set()}
    gap_type = classify_gap("kafka", resume_sections, resume_full_text, evidence)
    assert gap_type == "real_gap", f"应为 real_gap: {gap_type}"
    print("✅ test_classify_gap_real passed")


# ═══════════════════════════════════════════
# 端到端测试
# ═══════════════════════════════════════════

def test_full_run_with_concepts():
    """端到端：三层匹配 + gap 分类。"""
    resume_yaml = """
basics:
  name: 张三
  profiles:
    - network: GitHub
      url: https://github.com/zhangsan
skills:
  - name: 前端
    keywords: [React, TypeScript, Vue]
projects:
  - name: 电商系统
    tech: [Webpack, Docker]
    highlights:
      - 主导前端架构重构，QPS 从 500 提升到 5000，覆盖 30+ 场景
work:
  - organization: 字节跳动
    position: 前端实习生
    start: "2023.06"
    end: "2023.12"
    highlights:
      - 优化了广告投放系统，CTR 提升 15%
education:
  - institution: 清华大学
    degree: 本科
    start: "2020.09"
    end: "2024.06"
"""
    jd_text = """
    任职要求：
    1. 熟悉 React 和 TypeScript
    2. 2年以上前端开发经验
    3. 本科及以上学历
    4. 有高并发系统经验

    加分项：
    1. 了解 Docker 和 K8s
    2. 有 GitHub 开源贡献
    """
    with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False, encoding="utf-8") as rf:
        rf.write(resume_yaml)
        resume_path = rf.name
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as jf:
        jf.write(jd_text)
        jd_path = jf.name

    try:
        result = run(resume_path, jd_path)
        # 应该有覆盖
        assert result["total_keywords"] > 0
        assert result["covered_count"] >= 1
        # 应该有 dimension_scores
        assert "技术栈匹配" in result["dimension_scores"]
        # 应该有 gap_summary
        assert "evidence_gap" in result["gap_summary"]
        assert "real_gap" in result["gap_summary"]
        # 应该有 resume_evidence
        ev = result["resume_evidence"]
        assert ev["degree_level"] == 2  # 本科
        assert ev["has_github"] is True
        assert ev["has_quant_metrics"] is True
        # 高并发概念应该被匹配到
        assert "高并发" in ev["concepts_matched"]
        print(f"✅ test_full_run_with_concepts passed (覆盖率 {result['coverage_percent']}%, "
              f"evidence_gap {result['gap_summary']['evidence_gap']}, "
              f"real_gap {result['gap_summary']['real_gap']})")
    finally:
        Path(resume_path).unlink(missing_ok=True)
        Path(jd_path).unlink(missing_ok=True)


if __name__ == "__main__":
    test_load_synonyms()
    test_load_concepts()
    test_layer1_keyword_match()
    test_layer1_synonym()
    test_layer2_concept_match()
    test_layer2_distributed()
    test_layer3_experience()
    test_layer3_education()
    test_resume_work_years()
    test_resume_degree()
    test_classify_gap_evidence()
    test_classify_gap_real()
    test_full_run_with_concepts()
    print("\n🎉 所有 jd_match 测试通过")
