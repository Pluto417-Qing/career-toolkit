"""A/B 对比视图生成器。

生成 HTML 对比报告，高亮显示通用版和 JD 版简历的差异。
"""

import json
from pathlib import Path
from typing import Any


def generate_diff(general: dict, jd: dict) -> dict:
    """生成两个简历版本的差异分析。

    返回差异报告，包含：
    - 新增的内容
    - 删除的内容
    - 修改的内容
    """
    diff = {
        "sections": [],
        "added": [],
        "removed": [],
        "modified": [],
        "stats": {"added": 0, "removed": 0, "modified": 0},
    }

    # 比较基础信息
    basics_diff = _compare_dict(
        general.get("basics", {}),
        jd.get("basics", {}),
        "基础信息"
    )
    _merge_diff_results(diff, basics_diff)

    # 比较各经历段落
    for section in ["education", "work", "projects", "research", "activities", "skills"]:
        general_section = general.get(section, []) or []
        jd_section = jd.get(section, []) or []

        if isinstance(general_section, list) and isinstance(jd_section, list):
            section_diff = _compare_list(
                general_section,
                jd_section,
                section
            )
            _merge_diff_results(diff, section_diff)

    return diff


def _compare_dict(old: dict, new: dict, path: str) -> list:
    """比较两个字典。"""
    changes = []

    # 查找新增和修改的字段
    for key, new_value in new.items():
        if key not in old:
            changes.append({
                "type": "added",
                "path": f"{path}.{key}",
                "value": new_value,
            })
        elif old[key] != new_value:
            changes.append({
                "type": "modified",
                "path": f"{path}.{key}",
                "old": old[key],
                "new": new_value,
            })

    # 查找删除的字段
    for key, old_value in old.items():
        if key not in new:
            changes.append({
                "type": "removed",
                "path": f"{path}.{key}",
                "value": old_value,
            })

    return changes


def _compare_list(old_list: list, new_list: list, path: str) -> list:
    """比较两个列表。"""
    changes = []

    # 按条目的 name/title 等标识匹配
    old_by_key = {}
    for i, item in enumerate(old_list):
        if isinstance(item, dict):
            key = item.get("name") or item.get("title") or item.get("organization") or f"__index_{i}"
            old_by_key[key] = (i, item)

    new_by_key = {}
    for i, item in enumerate(new_list):
        if isinstance(item, dict):
            key = item.get("name") or item.get("title") or item.get("organization") or f"__index_{i}"
            new_by_key[key] = (i, item)

    # 查找新增项
    for key, (idx, item) in new_by_key.items():
        if key not in old_by_key:
            changes.append({
                "type": "added",
                "path": f"{path}[{idx}]",
                "value": item,
            })

    # 查找删除项
    for key, (idx, item) in old_by_key.items():
        if key not in new_by_key:
            changes.append({
                "type": "removed",
                "path": f"{path}[{idx}]",
                "value": item,
            })

    # 查找修改项
    for key in set(old_by_key.keys()) & set(new_by_key.keys()):
        old_item = old_by_key[key][1]
        new_item = new_by_key[key][1]

        if old_item != new_item:
            # 比较 highlights
            old_highlights = old_item.get("highlights", [])
            new_highlights = new_item.get("highlights", [])

            hl_diff = _compare_highlights(old_highlights, new_highlights, f"{path}[{key}].highlights")
            changes.extend(hl_diff)

            # 比较其他字段
            for field in old_item:
                if field not in ("highlights", "keywords", "tech_stack"):
                    if old_item.get(field) != new_item.get(field):
                        changes.append({
                            "type": "modified",
                            "path": f"{path}[{key}].{field}",
                            "old": old_item.get(field),
                            "new": new_item.get(field),
                        })

            # 比较关键词/技术栈
            for field in ("keywords", "tech_stack"):
                old_kw = set(old_item.get(field, []) or [])
                new_kw = set(new_item.get(field, []) or [])

                if old_kw != new_kw:
                    added = new_kw - old_kw
                    removed = old_kw - new_kw
                    if added:
                        changes.append({
                            "type": "added",
                            "path": f"{path}[{key}].{field}",
                            "value": list(added),
                        })
                    if removed:
                        changes.append({
                            "type": "removed",
                            "path": f"{path}[{key}].{field}",
                            "value": list(removed),
                        })

    return changes


def _compare_highlights(old: list, new: list, path: str) -> list:
    """比较 highlights 列表。"""
    changes = []

    # 逐项比较
    max_len = max(len(old), len(new))
    for i in range(max_len):
        old_item = old[i] if i < len(old) else None
        new_item = new[i] if i < len(new) else None

        if old_item is None and new_item is not None:
            changes.append({
                "type": "added",
                "path": f"{path}[{i}]",
                "value": new_item,
            })
        elif old_item is not None and new_item is None:
            changes.append({
                "type": "removed",
                "path": f"{path}[{i}]",
                "value": old_item,
            })
        elif old_item != new_item:
            changes.append({
                "type": "modified",
                "path": f"{path}[{i}]",
                "old": old_item,
                "new": new_item,
            })

    return changes


def _merge_diff_results(diff: dict, changes: list):
    """合并差异结果。"""
    for change in changes:
        diff[change["type"]].append(change)
        diff["stats"][change["type"]] += 1


def generate_diff_html(diff: dict, output_path: str):
    """生成 HTML 对比报告。

    参数：
        diff: 差异报告（由 generate_diff 生成）
        output_path: 输出 HTML 文件路径
    """
    html = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>简历版本对比报告</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
            background: #f5f7fa;
            color: #2c3e50;
            line-height: 1.6;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        h1 {
            text-align: center;
            margin-bottom: 30px;
            color: #1a1a2e;
        }
        h2 {
            margin: 20px 0 15px;
            padding-bottom: 10px;
            border-bottom: 2px solid #e0e0e0;
        }
        .stats {
            display: flex;
            justify-content: center;
            gap: 30px;
            margin-bottom: 30px;
        }
        .stat-card {
            background: white;
            border-radius: 12px;
            padding: 20px 30px;
            box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
            text-align: center;
            min-width: 120px;
        }
        .stat-number {
            font-size: 36px;
            font-weight: 700;
        }
        .stat-label {
            font-size: 14px;
            color: #666;
            margin-top: 5px;
        }
        .stat-added .stat-number { color: #27ae60; }
        .stat-removed .stat-number { color: #e74c3c; }
        .stat-modified .stat-number { color: #f39c12; }

        .diff-section {
            background: white;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
        }
        .diff-type {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
            margin-bottom: 10px;
        }
        .type-added { background: #d4edda; color: #155724; }
        .type-removed { background: #f8d7da; color: #721c24; }
        .type-modified { background: #fff3cd; color: #856404; }

        .diff-item {
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 15px;
        }
        .diff-item.added { background: #d4edda; }
        .diff-item.removed { background: #f8d7da; }
        .diff-item.modified { background: #fff3cd; }

        .diff-path {
            font-family: monospace;
            font-size: 12px;
            color: #666;
            margin-bottom: 8px;
        }
        .diff-content {
            font-size: 14px;
        }
        .old-value, .new-value {
            margin: 5px 0;
            padding: 8px 12px;
            border-radius: 6px;
        }
        .old-value {
            background: rgba(231, 76, 60, 0.1);
            text-decoration: line-through;
        }
        .new-value {
            background: rgba(39, 174, 96, 0.1);
        }
        .label {
            font-size: 12px;
            font-weight: 600;
            margin-right: 8px;
        }
        .label-old { color: #e74c3c; }
        .label-new { color: #27ae60; }

        .empty-state {
            text-align: center;
            padding: 40px;
            color: #666;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 简历版本对比报告</h1>

        <div class="stats">
            <div class="stat-card stat-added">
                <div class="stat-number">""" + str(diff["stats"]["added"]) + """</div>
                <div class="stat-label">新增</div>
            </div>
            <div class="stat-card stat-modified">
                <div class="stat-number">""" + str(diff["stats"]["modified"]) + """</div>
                <div class="stat-label">修改</div>
            </div>
            <div class="stat-card stat-removed">
                <div class="stat-number">""" + str(diff["stats"]["removed"]) + """</div>
                <div class="stat-label">删除</div>
            </div>
        </div>
"""

    # 添加新增项
    if diff["added"]:
        html += """
        <div class="diff-section">
            <h2>🟢 新增内容</h2>
"""
        for item in diff["added"]:
            value_text = json.dumps(item["value"], ensure_ascii=False, indent=2)
            html += f"""
            <div class="diff-item added">
                <div class="diff-path">📁 {item['path']}</div>
                <div class="diff-content">
                    <div class="new-value">{value_text}</div>
                </div>
            </div>
"""
        html += "        </div>"

    # 添加修改项
    if diff["modified"]:
        html += """
        <div class="diff-section">
            <h2>🟡 修改内容</h2>
"""
        for item in diff["modified"]:
            old_text = json.dumps(item.get("old", ""), ensure_ascii=False, indent=2)
            new_text = json.dumps(item.get("new", ""), ensure_ascii=False, indent=2)
            html += f"""
            <div class="diff-item modified">
                <div class="diff-path">📝 {item['path']}</div>
                <div class="diff-content">
                    <div><span class="label label-old">修改前：</span><span class="old-value">{old_text}</span></div>
                    <div><span class="label label-new">修改后：</span><span class="new-value">{new_text}</span></div>
                </div>
            </div>
"""
        html += "        </div>"

    # 添加删除项
    if diff["removed"]:
        html += """
        <div class="diff-section">
            <h2>🔴 删除内容</h2>
"""
        for item in diff["removed"]:
            value_text = json.dumps(item["value"], ensure_ascii=False, indent=2)
            html += f"""
            <div class="diff-item removed">
                <div class="diff-path">📁 {item['path']}</div>
                <div class="diff-content">
                    <div class="old-value">{value_text}</div>
                </div>
            </div>
"""
        html += "        </div>"

    # 如果没有差异
    if not diff["added"] and not diff["modified"] and not diff["removed"]:
        html += """
        <div class="diff-section">
            <div class="empty-state">
                <h2>✅ 没有差异</h2>
                <p>两个版本的简历内容完全一致</p>
            </div>
        </div>
"""

    html += """
    </div>
</body>
</html>
"""

    # 写入文件
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    return str(output_path)


def generate_diff_report(general_path: str, jd_path: str, output_dir: str) -> str:
    """生成完整的对比报告。

    参数：
        general_path: 通用版简历路径
        jd_path: JD 版简历路径
        output_dir: 输出目录

    返回：
        生成的 HTML 报告路径
    """
    import yaml

    # 读取简历
    with open(general_path, "r", encoding="utf-8") as f:
        general = yaml.safe_load(f)

    with open(jd_path, "r", encoding="utf-8") as f:
        jd = yaml.safe_load(f)

    # 生成差异
    diff = generate_diff(general, jd)

    # 生成 HTML
    output_path = Path(output_dir) / "diff-report.html"
    return generate_diff_html(diff, str(output_path))