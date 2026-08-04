"""ats_check.py 单元测试。

运行：python3 tests/test_ats_check.py
"""

import json
import sys
import tempfile
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from ats_check import (
    load_university_names,
    detect_date_format,
    check_time_order,
    check,
    run,
)


def test_load_university_names():
    """学校缩写表能正常加载。"""
    patterns = load_university_names()
    assert len(patterns) > 30, f"学校表太小：{len(patterns)} 条"
    # 北邮应该在表中
    found = any(p.search("北邮") for p, _ in patterns)
    assert found, "北邮 未在缩写表中"
    print("✅ test_load_university_names passed")


def test_detect_date_format():
    """日期格式检测正确。"""
    assert detect_date_format("2024.03") == "YYYY.MM"
    assert detect_date_format("2024-03") == "YYYY-MM"
    assert detect_date_format("2024年3月") == "YYYY年MM月"
    assert detect_date_format("2024/03") == "other"
    print("✅ test_detect_date_format passed")


def test_check_time_order():
    """时间倒序检测正确。"""
    # 倒序：2024 在 2023 之前
    entries_desc = [{"start": "2024.03"}, {"start": "2023.01"}]
    assert check_time_order(entries_desc) is True
    # 正序：2023 在 2024 之前 → 不是倒序
    entries_asc = [{"start": "2023.01"}, {"start": "2024.03"}]
    assert check_time_order(entries_asc) is False
    print("✅ test_check_time_order passed")


def test_check_helper():
    """check 辅助函数生成正确的报告项。"""
    r = check("1.1", "姓名", True, "fatal")
    assert r["status"] == "pass"
    r = check("1.2", "手机", False, "fatal")
    assert r["status"] == "fail"
    r = check("4.1", "敏感信息", False, "warn")
    assert r["status"] == "warn"
    print("✅ test_check_helper passed")


def test_run_abbreviation_detection():
    """ATS 检查能检测出学校缩写。"""
    resume_yaml = """
basics:
  name: 张三
  phone: "13800138000"
  email: zhangsan@test.com
education:
  - institution: 北邮
    degree: 本科
    start: "2020.09"
    end: "2024.06"
work:
  - organization: 字节跳动
    position: 前端实习生
    start: "2023.06"
    end: "2023.09"
    highlights:
      - 主导广告系统重构，CTR 提升 15%
"""
    with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False, encoding="utf-8") as f:
        f.write(resume_yaml)
        path = f.name
    try:
        result = run(path)
        # 应该检测到"北邮"缩写
        abbr_results = [r for r in result["results"] if r["rule_id"] == "1.6" and r["status"] != "pass"]
        assert len(abbr_results) > 0, "未检测到学校缩写"
        print("✅ test_run_abbreviation_detection passed")
    finally:
        Path(path).unlink(missing_ok=True)


def test_run_date_format_check():
    """ATS 检查能检测出日期格式不统一。"""
    resume_yaml = """
basics:
  name: 张三
education:
  - institution: 清华大学
    degree: 本科
    start: "2020年9月"
    end: "2024.06"
"""
    with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False, encoding="utf-8") as f:
        f.write(resume_yaml)
        path = f.name
    try:
        result = run(path)
        date_check = [r for r in result["results"] if r["rule_id"] == "2.1"]
        assert len(date_check) > 0, "未检测日期格式"
        assert date_check[0]["status"] == "fail", "日期格式不统一应该 fail"
        print("✅ test_run_date_format_check passed")
    finally:
        Path(path).unlink(missing_ok=True)


def test_run_sensitive_info():
    """ATS 检查能检测出敏感信息。"""
    resume_yaml = """
basics:
  name: 张三
  summary: 身份证号 110105200001011234
education:
  - institution: 清华大学
    degree: 本科
"""
    with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False, encoding="utf-8") as f:
        f.write(resume_yaml)
        path = f.name
    try:
        result = run(path)
        sensitive = [r for r in result["results"] if r["rule_id"] == "4.1"]
        assert len(sensitive) > 0 and sensitive[0]["status"] != "pass", "未检测到敏感信息"
        print("✅ test_run_sensitive_info passed")
    finally:
        Path(path).unlink(missing_ok=True)


if __name__ == "__main__":
    test_load_university_names()
    test_detect_date_format()
    test_check_time_order()
    test_check_helper()
    test_run_abbreviation_detection()
    test_run_date_format_check()
    test_run_sensitive_info()
    print("\n🎉 所有 ats_check 测试通过")
