"""jd_match.py 单元测试。

运行：python3 tests/test_jd_match.py
"""

import json
import sys
import tempfile
from pathlib import Path

# 把 scripts 目录加入 path
SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from jd_match import (
    load_synonyms,
    extract_jd_keywords,
    extract_resume_terms,
    match_keyword,
    normalize,
)


def test_load_synonyms():
    """同义词库能正常加载，且包含已知同义词组。"""
    smap = load_synonyms()
    assert len(smap) > 50, f"同义词库太小：{len(smap)} 组"
    # JS → JavaScript
    assert smap.get("js") == "javascript"
    # K8s → Kubernetes
    assert smap.get("k8s") == "kubernetes"
    # 容器 → Docker
    assert smap.get("容器") == "docker"
    print("✅ test_load_synonyms passed")


def test_extract_jd_keywords_basic():
    """从 JD 文本中能提取出关键词，同义词被正确归并。"""
    smap = load_synonyms()
    jd_text = """
    岗位要求：
    1. 熟悉 JavaScript / TypeScript
    2. 熟练使用 React 框架
    3. 了解 K8s 部署
    加分项：
    1. 有大数据经验，熟悉 Spark
    """
    kws = extract_jd_keywords(jd_text, jieba_mod=None, synonym_map=smap)

    # 应该包含 React
    canonicals = [k["canonical"] for k in kws]
    assert "react" in canonicals, f"React 未被提取: {canonicals}"
    # JS 和 JavaScript 应该被归并
    js_kws = [k for k in kws if k["canonical"] == "javascript"]
    assert len(js_kws) == 1, f"JS/JavaScript 未被归并: {js_kws}"
    print("✅ test_extract_jd_keywords_basic passed")


def test_extract_jd_keywords_section_weights():
    """JD 中 required 段的权重应该高于 bonus 段。"""
    smap = load_synonyms()
    jd_text = """
    任职要求：
    熟悉 Python
    加分项：
    了解 Rust
    """
    kws = extract_jd_keywords(jd_text, jieba_mod=None, synonym_map=smap)
    python_kw = next(k for k in kws if k["canonical"] == "python")
    rust_kw = next(k for k in kws if k["canonical"] == "rust")
    assert python_kw["weight"] > rust_kw["weight"], \
        f"Python 权重 {python_kw['weight']} 应大于 Rust {rust_kw['weight']}"
    print("✅ test_extract_jd_keywords_section_weights passed")


def test_match_keyword_synonym():
    """简历中写 'JS'，JD 中要求 'JavaScript'，应该匹配。"""
    smap = load_synonyms()
    resume = {
        "skills": [{"name": "前端", "keywords": ["JS", "React"]}],
        "projects": [{"name": "p1", "tech": ["TypeScript"]}],
    }
    resume_sections = extract_resume_terms(resume, smap)
    is_match, sources = match_keyword("javascript", resume_sections)
    assert is_match, "JS → JavaScript 未匹配"
    is_match2, _ = match_keyword("react", resume_sections)
    assert is_match2, "React 未匹配"
    print("✅ test_match_keyword_synonym passed")


def test_resume_terms_extraction():
    """从简历中提取的技术词应正确归并到各 section。"""
    smap = load_synonyms()
    resume = {
        "skills": [{"keywords": ["MySQL", "Redis"]}],
        "projects": [{"tech": ["Docker"], "highlights": ["使用 K8s 部署"]}],
    }
    sections = extract_resume_terms(resume, smap)
    assert "mysql" in sections.get("skills", {})
    assert "docker" in sections.get("tech", {})
    print("✅ test_resume_terms_extraction passed")


def test_full_run():
    """端到端：从简历文件 + JD 文件生成完整报告。"""
    resume_yaml = """
basics:
  name: 张三
skills:
  - name: 前端
    keywords: [React, TypeScript, Vue]
projects:
  - name: 项目A
    tech: [Webpack, Sass]
    highlights: [主导前端架构重构，代码量减少 40%]
"""
    jd_text = """
    岗位要求：
    熟悉 React 和 TypeScript
    了解 Docker 和 K8s
    加分项：
    有 Node.js 经验
    """

    with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False, encoding="utf-8") as rf:
        rf.write(resume_yaml)
        resume_path = rf.name
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as jf:
        jf.write(jd_text)
        jd_path = jf.name

    try:
        sys.path.insert(0, str(SCRIPTS_DIR))
        from jd_match import run
        result = run(resume_path, jd_path)
        assert result["total_keywords"] > 0
        assert result["covered_count"] >= 1, "至少 React 应该匹配"
        assert result["coverage_percent"] > 0
        print(f"✅ test_full_run passed (覆盖率 {result['coverage_percent']}%)")
    finally:
        Path(resume_path).unlink(missing_ok=True)
        Path(jd_path).unlink(missing_ok=True)


if __name__ == "__main__":
    test_load_synonyms()
    test_extract_jd_keywords_basic()
    test_extract_jd_keywords_section_weights()
    test_match_keyword_synonym()
    test_resume_terms_extraction()
    test_full_run()
    print("\n🎉 所有 jd_match 测试通过")
