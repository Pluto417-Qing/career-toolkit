"""简历模板系统。

对接 resume-builder 的 11 套 Jinja2 主题，提供模板对比和管理。
"""

from pathlib import Path
from typing import Optional
import json
import sys

# 定位 resume-builder 的 themes 目录
_CURRENT_DIR = Path(__file__).resolve().parent.parent.parent
_THEMES_DIR = _CURRENT_DIR / "resume-builder" / "assets" / "themes"


# 11 套主题的元信息（基于 resume-builder/assets/themes/）
THEME_META = {
    "classic": {
        "display_name": "经典",
        "description": "传统正式风格，适合银行、国企等传统行业",
        "category": "traditional",
    },
    "modern": {
        "display_name": "现代",
        "description": "简约专业风格，适合互联网、科技公司",
        "category": "modern",
    },
    "minimal": {
        "display_name": "极简",
        "description": "极简设计，突出内容本身",
        "category": "minimal",
    },
    "compact": {
        "display_name": "紧凑",
        "description": "高密度排版，适合一页纸控制",
        "category": "compact",
    },
    "elegant": {
        "display_name": "优雅",
        "description": "精致优雅，适合中高管岗位",
        "category": "traditional",
    },
    "academic": {
        "display_name": "学术",
        "description": "学术风格，适合科研、教育岗位",
        "category": "academic",
    },
    "infographic": {
        "display_name": "信息图",
        "description": "视觉化风格，适合设计、产品岗位",
        "category": "creative",
    },
    "creative": {
        "display_name": "创意",
        "description": "活力个性风格，适合创意类岗位",
        "category": "creative",
    },
    "executive": {
        "display_name": "高管",
        "description": "大气稳重，适合高管、资深岗位",
        "category": "traditional",
    },
    "metro": {
        "display_name": "都市",
        "description": "现代都市风格，适合时尚、媒体行业",
        "category": "modern",
    },
    "tech": {
        "display_name": "科技",
        "description": "科技感风格，适合技术研发岗位",
        "category": "modern",
    },
}

# 主题分类 → 推荐岗位映射
CATEGORY_RECOMMENDATIONS = {
    "traditional": ["银行", "国企", "政府", "事业单位", "公务员"],
    "modern": ["互联网", "科技", "IT", "软件", "工程师"],
    "minimal": ["任何岗位", "技术岗", "简约风格偏好"],
    "compact": ["内容较多", "一页纸需求", "多段经历"],
    "academic": ["科研", "教育", "学术", "高校", "实验室"],
    "creative": ["设计", "产品", "创意", "市场", "品牌"],
}


class ResumeTemplate:
    """简历模板（包装 resume-builder 的主题）。"""

    def __init__(self, name: str):
        """初始化模板。

        参数：
            name: 主题名称（对应 resume-builder 的主题目录）
        """
        self.name = name
        meta = THEME_META.get(name, {})
        self.display_name = meta.get("display_name", name)
        self.description = meta.get("description", "")
        self.category = meta.get("category", "modern")
        self.theme_dir = _THEMES_DIR / name

    def exists(self) -> bool:
        """检查主题是否存在于 resume-builder 中。"""
        return self.theme_dir.is_dir() and (self.theme_dir / "template.html.j2").exists()

    def render(self, resume_data: dict, output_format: str = "html") -> str:
        """渲染简历。

        参数：
            resume_data: 简历数据（resume.yaml 的结构）
            output_format: 输出格式 (html/markdown/json)

        返回：
            渲染结果
        """
        if output_format == "json":
            return json.dumps(resume_data, ensure_ascii=False, indent=2)

        if not self.exists():
            raise ValueError(f"主题不存在: {self.name} (目录: {self.theme_dir})")

        if output_format == "html":
            return self._render_via_builder(resume_data)
        elif output_format == "markdown":
            return self._render_markdown(resume_data)
        else:
            raise ValueError(f"不支持的输出格式：{output_format}")

    def _render_via_builder(self, resume_data: dict) -> str:
        """调用 resume-builder 的 Jinja2 渲染。"""
        try:
            from jinja2 import Environment, FileSystemLoader, select_autoescape
        except ImportError:
            raise ImportError("请先安装 jinja2: pip install Jinja2")

        env = Environment(
            loader=FileSystemLoader(str(self.theme_dir)),
            autoescape=select_autoescape(["html", "xml"]),
            trim_blocks=True,
            lstrip_blocks=True,
        )
        tmpl = env.get_template("template.html.j2")
        return tmpl.render(data=resume_data)

    def _render_markdown(self, resume_data: dict) -> str:
        """渲染 Markdown（与 resume-builder 保持一致）。"""
        basics = resume_data.get("basics", {})
        parts = [f"# {basics.get('name', '')}", ""]

        if basics.get("label"):
            parts.append(f"**{basics['label']}**")
        contact = []
        if basics.get("phone"):
            contact.append(f"📞 {basics['phone']}")
        if basics.get("email"):
            contact.append(f"✉️ {basics['email']}")
        if contact:
            parts.append(" | ".join(contact))
        parts.append("")

        for edu in resume_data.get("education", []):
            parts.append(f"## 📚 {edu.get('institution', edu.get('title', ''))}")
            parts.append(f"*{edu.get('subtitle', '')} | {edu.get('period', '')}*")
            for hl in edu.get("highlights", []):
                parts.append(f"- {hl}")
            parts.append("")

        for w in resume_data.get("work", []):
            parts.append(f"## 💼 {w.get('title', '')}")
            parts.append(f"*{w.get('subtitle', '')} | {w.get('period', '')}*")
            for hl in w.get("highlights", []):
                parts.append(f"- {hl}")
            parts.append("")

        for proj in resume_data.get("projects", []):
            parts.append(f"## 🚀 {proj.get('title', '')}")
            parts.append(f"*{proj.get('subtitle', '')}*")
            for hl in proj.get("highlights", []):
                parts.append(f"- {hl}")
            parts.append("")

        return "\n".join(parts)


class TemplateManager:
    """模板管理器（基于 resume-builder 的 11 套主题）。"""

    def __init__(self, themes_dir: Optional[str] = None):
        """初始化管理器。

        参数：
            themes_dir: 主题目录路径（默认自动定位 resume-builder/assets/themes）
        """
        if themes_dir:
            self.themes_dir = Path(themes_dir)
        else:
            self.themes_dir = _THEMES_DIR

        # 从目录扫描可用主题
        self._templates = {}
        if self.themes_dir.is_dir():
            for d in sorted(self.themes_dir.iterdir()):
                if d.is_dir() and (d / "template.html.j2").exists():
                    self._templates[d.name] = ResumeTemplate(d.name)

    def get_template(self, name: str) -> Optional[ResumeTemplate]:
        """获取模板。"""
        return self._templates.get(name)

    def list_templates(self) -> list[dict]:
        """列出所有可用主题。"""
        result = []
        for name, tmpl in sorted(self._templates.items()):
            meta = THEME_META.get(name, {})
            result.append({
                "name": name,
                "display_name": meta.get("display_name", name),
                "description": meta.get("description", tmpl.description),
                "category": meta.get("category", "modern"),
            })
        return result

    def list_by_category(self) -> dict[str, list[dict]]:
        """按分类列出主题。"""
        by_cat: dict[str, list[dict]] = {}
        for t in self.list_templates():
            cat = t.get("category", "other")
            by_cat.setdefault(cat, []).append(t)
        return by_cat

    def render_with_all_templates(self, resume_data: dict,
                                   output_format: str = "html") -> dict[str, str]:
        """用所有可用主题渲染简历。"""
        results = {}
        for name, tmpl in self._templates.items():
            try:
                results[name] = tmpl.render(resume_data, output_format)
            except Exception as e:
                results[name] = f"[渲染失败: {e}]"
        return results

    def compare_templates(self, resume_data: dict) -> dict:
        """对比所有主题并推荐。"""
        comparison = {
            "total_templates": len(self._templates),
            "templates": [],
            "recommendations": [],
        }

        for name, tmpl in sorted(self._templates.items()):
            meta = THEME_META.get(name, {})
            html_len = 0
            try:
                html_len = len(tmpl.render(resume_data, "html"))
            except Exception:
                pass

            comparison["templates"].append({
                "name": name,
                "display_name": meta.get("display_name", name),
                "description": meta.get("description", ""),
                "category": meta.get("category", "modern"),
                "html_length": html_len,
            })

        # 根据岗位标签推荐
        basics = resume_data.get("basics", {})
        label = (basics.get("label", "") or "").lower()

        matched_cats = set()
        for cat, keywords in CATEGORY_RECOMMENDATIONS.items():
            if any(kw in label for kw in keywords):
                matched_cats.add(cat)

        if matched_cats:
            comparison["recommendations"].append({
                "categories": list(matched_cats),
                "reason": f"岗位标签「{basics.get('label', '')}」匹配这些分类",
                "templates": [
                    t["name"] for t in comparison["templates"]
                    if t["category"] in matched_cats
                ],
            })
        else:
            comparison["recommendations"].append({
                "categories": ["modern"],
                "reason": "默认推荐现代风格，适合大多数岗位",
                "templates": ["modern", "minimal", "compact"],
            })

        return comparison