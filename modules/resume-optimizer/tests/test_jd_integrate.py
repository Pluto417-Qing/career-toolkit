"""jd_integrate.py 单元测试。

运行：python3 tests/test_jd_integrate.py
"""

import json
import sys
import tempfile
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from jd_integrate import (
    extract_all_bullets,
    score_relevance,
    find_best_bullet,
    determine_strategy,
    detect_stuffing,
    generate_rewrite_suggestion,
    run,
    load_synonyms,
)


def test_extract_all_bullets():
    """从简历中正确提取所有 bullet。"""
    resume = {
        "work": [
            {"organization": "字节跳动", "highlights": ["主导重构", "优化性能"]},
        ],
        "projects": [
            {"name": "项目A", "tech": ["React"], "highlights": ["从零搭建"]},
        ],
    }
    bullets = extract_all_bullets(resume)
    assert len(bullets) == 3
    assert bullets[0]["entry_name"] == "字节跳动"
    assert bullets[0]["section"] == "work"
    assert bullets[2]["section"] == "projects"
    print("✅ test_extract_all_bullets passed")


def test_score_relevance_high():
    """相关度评分：bullet 的 tech 列表有同义词时分数最高。"""
    smap = load_synonyms()
    bullet = {
        "tech": ["Docker"],
        "text": "使用容器化部署",
        "text_lower": "使用容器化部署",
        "summary": "",
    }
    score = score_relevance("Kubernetes", bullet, smap)
    # Docker 和 Kubernetes 都是「容器化」概念的关联词
    assert score >= 0.8, f"Docker 应与 Kubernetes 高相关: {score}"
    print(f"✅ test_score_relevance_high passed (score={score})")


def test_score_relevance_zero():
    """相关度评分：无关联时分数为 0。"""
    smap = load_synonyms()
    bullet = {
        "tech": ["React"],
        "text": "前端开发",
        "text_lower": "前端开发",
        "summary": "",
    }
    score = score_relevance("Kafka", bullet, smap)
    assert score == 0.0, f"Kafka 与 React 无关联，分数应为 0: {score}"
    print("✅ test_score_relevance_zero passed")


def test_find_best_bullet():
    """找到最佳融入 bullet。"""
    smap = load_synonyms()
    bullets = [
        {"tech": ["React"], "text": "前端开发", "text_lower": "前端开发", "summary": "", "section": "work", "entry_name": "A", "entry_index": 0, "bullet_index": 0},
        {"tech": ["Docker"], "text": "容器化部署", "text_lower": "容器化部署", "summary": "", "section": "work", "entry_name": "B", "entry_index": 1, "bullet_index": 0},
    ]
    gap = {"keyword": "Kubernetes"}
    result = find_best_bullet(gap, bullets, smap)
    assert result is not None
    assert result["bullet"]["entry_name"] == "B"
    assert result["relevance_score"] >= 0.8
    print("✅ test_find_best_bullet passed")


def test_find_best_bullet_no_match():
    """无匹配时返回 None。"""
    smap = load_synonyms()
    bullets = [
        {"tech": ["React"], "text": "前端开发", "text_lower": "前端开发", "summary": "", "section": "work", "entry_name": "A", "entry_index": 0, "bullet_index": 0},
    ]
    gap = {"keyword": "Kafka"}
    result = find_best_bullet(gap, bullets, smap)
    assert result is None
    print("✅ test_find_best_bullet_no_match passed")


def test_determine_strategy():
    """策略判断正确。"""
    assert determine_strategy("x", {}, 1.0, {}) == "explicit"
    assert determine_strategy("x", {}, 0.8, {}) == "tech_list"
    assert determine_strategy("x", {}, 0.6, {}) == "enrich"
    assert determine_strategy("x", {}, 0.4, {}) == "summary"
    assert determine_strategy("x", {}, 0.2, {}) == "new_context"
    print("✅ test_determine_strategy passed")


def test_detect_stuffing():
    """堆砌检测：同一 bullet 被多个关键词塞入时报警告。"""
    suggestions = [
        {"target_section": "work", "target_entry": 0, "target_bullet_index": 0, "keyword": "K8s"},
        {"target_section": "work", "target_entry": 0, "target_bullet_index": 0, "keyword": "微服务"},
        {"target_section": "work", "target_entry": 1, "target_bullet_index": 0, "keyword": "Redis"},
    ]
    warnings = detect_stuffing(suggestions)
    assert len(warnings) == 1
    assert len(warnings[0]["keywords"]) == 2
    print("✅ test_detect_stuffing passed")


def test_full_run():
    """端到端：简历 + 匹配结果 → 融入建议。"""
    resume_yaml = """
basics:
  name: 李明
skills:
  - name: 前端
    keywords: [React, TypeScript]
projects:
  - name: 电商系统
    tech: [Docker, Webpack]
    highlights:
      - 主导前端架构重构，QPS 从 500 提升到 5000
work:
  - organization: 字节跳动
    position: 前端实习生
    start: "2023.06"
    end: "2023.12"
    highlights:
      - 优化了广告投放系统，CTR 提升 15%
"""
    match_json = json.dumps({
        "evidence_gaps": [
            {"keyword": "Kubernetes", "canonical": "kubernetes", "gap_type": "evidence_gap"},
        ],
        "real_gaps": [
            {"keyword": "Kafka", "canonical": "kafka", "gap_type": "real_gap"},
        ],
    })

    with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False, encoding="utf-8") as rf:
        rf.write(resume_yaml)
        resume_path = rf.name
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as mf:
        mf.write(match_json)
        match_path = mf.name

    try:
        result = run(resume_path, match_path)
        assert result["total_gaps"] == 1
        assert result["processable"] == 1
        assert len(result["suggestions"]) == 1
        s = result["suggestions"][0]
        assert s["keyword"] == "Kubernetes"
        assert s["confidence"] >= 0.7
        assert s["strategy"] in ("explicit", "tech_list", "enrich")
        assert "principles" in result
        print(f"✅ test_full_run passed (策略={s['strategy']}, 置信度={s['confidence']})")
    finally:
        Path(resume_path).unlink(missing_ok=True)
        Path(match_path).unlink(missing_ok=True)


if __name__ == "__main__":
    test_extract_all_bullets()
    test_score_relevance_high()
    test_score_relevance_zero()
    test_find_best_bullet()
    test_find_best_bullet_no_match()
    test_determine_strategy()
    test_detect_stuffing()
    test_full_run()
    print("\n🎉 所有 jd_integrate 测试通过")
