"""简历模板系统。

支持多模板生成、模板对比、自定义主题。
"""

from pathlib import Path
from typing import Optional
import json


class ResumeTemplate:
    """简历模板。"""

    def __init__(self, name: str, config: dict):
        """初始化模板。

        参数：
            name: 模板名称
            config: 模板配置
        """
        self.name = name
        self.config = config

        # 基础配置
        self.display_name = config.get("display_name", name)
        self.description = config.get("description", "")
        self.layout = config.get("layout", "single_column")
        self.style = config.get("style", {})

    def render(self, resume_data: dict, output_format: str = "html") -> str:
        """渲染简历。

        参数：
            resume_data: 简历数据
            output_format: 输出格式 (html/markdown/json)

        返回：
            渲染结果
        """
        if output_format == "html":
            return self._render_html(resume_data)
        elif output_format == "markdown":
            return self._render_markdown(resume_data)
        elif output_format == "json":
            return json.dumps(resume_data, ensure_ascii=False, indent=2)
        else:
            raise ValueError(f"不支持的输出格式：{output_format}")

    def _render_html(self, resume_data: dict) -> str:
        """渲染 HTML。"""
        # 基础样式
        styles = self._get_base_styles()

        # 构建 HTML
        html_parts = [
            "<!DOCTYPE html>",
            "<html>",
            "<head>",
            '<meta charset="UTF-8">',
            f"<title>{resume_data.get('basics', {}).get('name', 'Resume')}</title>",
            "<style>",
            styles,
            "</style>",
            "</head>",
            "<body>",
            self._render_header(resume_data.get("basics", {})),
            self._render_education(resume_data.get("education", [])),
            self._render_work(resume_data.get("work", [])),
            self._render_projects(resume_data.get("projects", [])),
            self._render_skills(resume_data.get("skills", [])),
            "</body>",
            "</html>",
        ]

        return "\n".join(html_parts)

    def _render_markdown(self, resume_data: dict) -> str:
        """渲染 Markdown。"""
        md_parts = []

        basics = resume_data.get("basics", {})
        md_parts.append(f"# {basics.get('name', '')}")
        md_parts.append("")

        if basics.get("label"):
            md_parts.append(f"**{basics['label']}**")
        if basics.get("phone"):
            md_parts.append(f"📞 {basics['phone']}")
        if basics.get("email"):
            md_parts.append(f"✉️ {basics['email']}")
        md_parts.append("")

        # 教育背景
        for edu in resume_data.get("education", []):
            md_parts.append(f"## 📚 {edu.get('institution', '')}")
            md_parts.append(f"*{edu.get('subtitle', '')} | {edu.get('period', '')}*")
            for hl in edu.get("highlights", []):
                md_parts.append(f"- {hl}")
            md_parts.append("")

        # 工作经历
        for work in resume_data.get("work", []):
            md_parts.append(f"## 💼 {work.get('title', '')}")
            md_parts.append(f"*{work.get('subtitle', '')} | {work.get('period', '')}*")
            for hl in work.get("highlights", []):
                md_parts.append(f"- {hl}")
            md_parts.append("")

        # 项目经历
        for proj in resume_data.get("projects", []):
            md_parts.append(f"## 🚀 {proj.get('title', '')}")
            md_parts.append(f"*{proj.get('subtitle', '')}*")
            for hl in proj.get("highlights", []):
                md_parts.append(f"- {hl}")
            md_parts.append("")

        return "\n".join(md_parts)

    def _get_base_styles(self) -> str:
        """获取基础样式。"""
        # 从模板配置获取样式，或使用默认
        font_family = self.style.get("font_family", "'Segoe UI', 'Microsoft YaHei', sans-serif")
        primary_color = self.style.get("primary_color", "#2563eb")
        bg_color = self.style.get("bg_color", "#ffffff")
        text_color = self.style.get("text_color", "#1f2937")

        return f"""
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{
                font-family: {font_family};
                font-size: 10pt;
                line-height: 1.5;
                color: {text_color};
                background: {bg_color};
                max-width: 210mm;
                margin: 0 auto;
                padding: 10mm;
            }}
            header {{
                text-align: center;
                border-bottom: 2px solid {primary_color};
                padding-bottom: 10px;
                margin-bottom: 15px;
            }}
            header h1 {{
                font-size: 24pt;
                color: {primary_color};
                margin-bottom: 5px;
            }}
            header .contact {{
                font-size: 9pt;
                color: #6b7280;
            }}
            section {{
                margin-bottom: 15px;
            }}
            section h2 {{
                font-size: 12pt;
                color: {primary_color};
                border-bottom: 1px solid #e5e7eb;
                padding-bottom: 3px;
                margin-bottom: 8px;
            }}
            .entry {{
                margin-bottom: 12px;
            }}
            .entry-title {{
                font-weight: 600;
                font-size: 11pt;
            }}
            .entry-subtitle {{
                color: #6b7280;
                font-size: 10pt;
            }}
            .entry-period {{
                color: #9ca3af;
                font-size: 9pt;
            }}
            .highlights {{
                margin-top: 5px;
                padding-left: 15px;
            }}
            .highlights li {{
                margin-bottom: 3px;
            }}
            .quant {{
                color: {primary_color};
                font-weight: 600;
            }}
            .impact {{
                color: #059669;
                font-weight: 600;
            }}
            .tech {{
                background: #eff6ff;
                padding: 1px 4px;
                border-radius: 3px;
                font-family: monospace;
            }}
            @media print {{
                body {{ padding: 0; }}
            }}
        """

    def _render_header(self, basics: dict) -> str:
        """渲染头部。"""
        name = basics.get("name", "")
        label = basics.get("label", "")
        phone = basics.get("phone", "")
        email = basics.get("email", "")

        return f"""
            <header>
                <h1>{name}</h1>
                <div class="contact">
                    {label} | {phone} | {email}
                </div>
            </header>
        """

    def _render_education(self, education: list) -> str:
        """渲染教育背景。"""
        if not education:
            return ""

        parts = ["<section>", "<h2>📚 教育背景</h2>"]

        for edu in education:
            parts.append(f"""
                <div class="entry">
                    <div class="entry-title">{edu.get('title', '')}</div>
                    <div class="entry-subtitle">{edu.get('subtitle', '')}</div>
                    <div class="entry-period">{edu.get('period', '')}</div>
                    <ul class="highlights">
                        {''.join(f'<li>{hl}</li>' for hl in edu.get('highlights', []))}
                    </ul>
                </div>
            """)

        parts.append("</section>")
        return "\n".join(parts)

    def _render_work(self, work: list) -> str:
        """渲染工作经历。"""
        if not work:
            return ""

        parts = ["<section>", "<h2>💼 工作经历</h2>"]

        for w in work:
            parts.append(f"""
                <div class="entry">
                    <div class="entry-title">{w.get('title', '')}</div>
                    <div class="entry-subtitle">{w.get('subtitle', '')}</div>
                    <div class="entry-period">{w.get('period', '')}</div>
                    <ul class="highlights">
                        {''.join(f'<li>{hl}</li>' for hl in w.get('highlights', []))}
                    </ul>
                </div>
            """)

        parts.append("</section>")
        return "\n".join(parts)

    def _render_projects(self, projects: list) -> str:
        """渲染项目经历。"""
        if not projects:
            return ""

        parts = ["<section>", "<h2>🚀 项目经历</h2>"]

        for proj in projects:
            parts.append(f"""
                <div class="entry">
                    <div class="entry-title">{proj.get('title', '')}</div>
                    <div class="entry-subtitle">{proj.get('subtitle', '')}</div>
                    <ul class="highlights">
                        {''.join(f'<li>{hl}</li>' for hl in proj.get('highlights', []))}
                    </ul>
                </div>
            """)

        parts.append("</section>")
        return "\n".join(parts)

    def _render_skills(self, skills: list) -> str:
        """渲染技能。"""
        if not skills:
            return ""

        parts = ["<section>", "<h2>🛠️ 技能</h2>", '<ul class="highlights">']

        for skill in skills:
            name = skill.get("name", "")
            keywords = skill.get("keywords", [])
            if keywords:
                parts.append(f"<li><strong>{name}:</strong> {', '.join(keywords)}</li>")

        parts.extend(["</ul>", "</section>"])
        return "\n".join(parts)


# ═══════════════════════════════════════════════════════════
# 预设模板
# ═══════════════════════════════════════════════════════════

# 经典模板：传统、正式
CLASSIC_TEMPLATE = ResumeTemplate("classic", {
    "display_name": "经典风格",
    "description": "传统正式风格，适合银行、国企等传统行业",
    "layout": "single_column",
    "style": {
        "font_family": "'SimSun', 'STSong', serif",
        "primary_color": "#000000",
        "bg_color": "#ffffff",
        "text_color": "#333333",
    }
})

# 现代模板：简约、专业
MODERN_TEMPLATE = ResumeTemplate("modern", {
    "display_name": "现代风格",
    "description": "简约专业风格，适合互联网、科技公司",
    "layout": "single_column",
    "style": {
        "font_family": "'Segoe UI', 'Microsoft YaHei', sans-serif",
        "primary_color": "#2563eb",
        "bg_color": "#ffffff",
        "text_color": "#1f2937",
    }
})

# 极简模板：简洁、聚焦
MINIMAL_TEMPLATE = ResumeTemplate("minimal", {
    "display_name": "极简风格",
    "description": "极简设计，突出内容本身",
    "layout": "single_column",
    "style": {
        "font_family": "'Helvetica Neue', Arial, sans-serif",
        "primary_color": "#374151",
        "bg_color": "#ffffff",
        "text_color": "#111827",
    }
})

# 创意模板：活力、个性
CREATIVE_TEMPLATE = ResumeTemplate("creative", {
    "display_name": "创意风格",
    "description": "活力个性风格，适合设计、产品岗位",
    "layout": "single_column",
    "style": {
        "font_family": "'PingFang SC', 'Microsoft YaHei', sans-serif",
        "primary_color": "#6366f1",
        "bg_color": "#fafafa",
        "text_color": "#1f2937",
    }
})


# ═══════════════════════════════════════════════════════════
# 模板管理器
# ═══════════════════════════════════════════════════════════

class TemplateManager:
    """模板管理器。"""

    def __init__(self):
        """初始化管理器。"""
        self.templates = {
            "classic": CLASSIC_TEMPLATE,
            "modern": MODERN_TEMPLATE,
            "minimal": MINIMAL_TEMPLATE,
            "creative": CREATIVE_TEMPLATE,
        }

    def get_template(self, name: str) -> Optional[ResumeTemplate]:
        """获取模板。

        参数：
            name: 模板名称

        返回：
            模板对象，如果不存在返回 None
        """
        return self.templates.get(name)

    def list_templates(self) -> list[dict]:
        """列出所有模板。"""
        return [
            {
                "name": name,
                "display_name": tmpl.display_name,
                "description": tmpl.description,
            }
            for name, tmpl in self.templates.items()
        ]

    def render_with_all_templates(self, resume_data: dict,
                                   output_format: str = "html") -> dict[str, str]:
        """用所有模板渲染简历。

        参数：
            resume_data: 简历数据
            output_format: 输出格式

        返回：
            模板名称 -> 渲染结果
        """
        results = {}

        for name, template in self.templates.items():
            results[name] = template.render(resume_data, output_format)

        return results

    def compare_templates(self, resume_data: dict) -> dict:
        """对比所有模板。

        参数：
            resume_data: 简历数据

        返回：
            对比结果
        """
        comparison = {
            "templates": [],
            "recommendations": [],
        }

        # 收集各模板信息
        for name, template in self.templates.items():
            html = template.render(resume_data, "html")
            comparison["templates"].append({
                "name": name,
                "display_name": template.display_name,
                "description": template.description,
                "html_length": len(html),
                "style": template.style,
            })

        # 生成推荐
        # 根据简历内容推荐合适的模板
        basics = resume_data.get("basics", {})
        label = basics.get("label", "").lower()

        if any(kw in label for kw in ["银行", "国企", "政府", "事业单位"]):
            comparison["recommendations"].append({
                "template": "classic",
                "reason": "传统行业适合经典正式风格",
            })
        elif any(kw in label for kw in ["设计", "产品", "创意"]):
            comparison["recommendations"].append({
                "template": "creative",
                "reason": "创意类岗位适合活力个性风格",
            })
        else:
            comparison["recommendations"].append({
                "template": "modern",
                "reason": "互联网科技岗位适合简约专业风格",
            })

        return comparison