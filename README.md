<h1 align="center">Career Toolkit</h1>
<p align="center">Agent Skill — 用对话代替表单，从职业规划到简历生成一步到位。</p>

<p align="center">
  <img src="https://img.shields.io/badge/type-Agent%20Skill-purple"/>
  <img src="https://img.shields.io/badge/python-3.8+-blue"/>
  <img src="https://img.shields.io/badge/license-MIT-green"/>
</p>

## 主题画廊

11 套主题，每套有头像/无头像两版，支持口头微调。

<table>
<tr>
<td align="center"><img src="https://raw.githubusercontent.com/Pluto417-Qing/career-toolkit/gh-pages/classic-avatar/resume.png" width="320"/><br/><b>Classic</b></td>
<td align="center"><img src="https://raw.githubusercontent.com/Pluto417-Qing/career-toolkit/gh-pages/modern-avatar/resume.png" width="320"/><br/><b>Modern</b></td>
<td align="center"><img src="https://raw.githubusercontent.com/Pluto417-Qing/career-toolkit/gh-pages/minimal-avatar/resume.png" width="320"/><br/><b>Minimal</b></td>
</tr>
<tr>
<td align="center"><img src="https://raw.githubusercontent.com/Pluto417-Qing/career-toolkit/gh-pages/elegant-avatar/resume.png" width="320"/><br/><b>Elegant</b></td>
<td align="center"><img src="https://raw.githubusercontent.com/Pluto417-Qing/career-toolkit/gh-pages/compact-avatar/resume.png" width="320"/><br/><b>Compact</b></td>
<td align="center"><img src="https://raw.githubusercontent.com/Pluto417-Qing/career-toolkit/gh-pages/academic-avatar/resume.png" width="320"/><br/><b>Academic</b></td>
</tr>
<tr>
<td align="center"><img src="https://raw.githubusercontent.com/Pluto417-Qing/career-toolkit/gh-pages/infographic-avatar/resume.png" width="320"/><br/><b>Infographic</b></td>
<td align="center"><img src="https://raw.githubusercontent.com/Pluto417-Qing/career-toolkit/gh-pages/creative-avatar/resume.png" width="320"/><br/><b>Creative</b></td>
<td align="center"><img src="https://raw.githubusercontent.com/Pluto417-Qing/career-toolkit/gh-pages/executive-avatar/resume.png" width="320"/><br/><b>Executive</b></td>
</tr>
<tr>
<td align="center"><img src="https://raw.githubusercontent.com/Pluto417-Qing/career-toolkit/gh-pages/metro-avatar/resume.png" width="320"/><br/><b>Metro</b></td>
<td align="center"><img src="https://raw.githubusercontent.com/Pluto417-Qing/career-toolkit/gh-pages/tech-avatar/resume.png" width="320"/><br/><b>Tech</b></td>
<td></td>
</tr>
</table>

---

## 工作原理

```
       ┌─────────────────────────────────────────────────┐
       │              Career Toolkit                      │
       │                                                 │
       │   ① Planner    ② Builder      ③ Optimizer      │
       │   ┌────────┐   ┌──────────┐   ┌────────────┐   │
       │   │ 画像   │   │ 对话挖掘 │   │ JD 关键词  │   │
       │   │ 测评   │──→│ YAML生成 │──→│ ATS 检查   │   │
       │   │ 规划   │   │ 主题渲染 │   │ Bullet改写 │   │
       │   └────────┘   └──────────┘   └────────────┘   │
       │                                                 │
       │   profile.yaml → resume.yaml → 匹配报告         │
       └─────────────────────────────────────────────────┘
```

- **Career Planner** — 引导式提问 + Holland 测评，产出职业规划和行动时间线
- **Resume Builder** — 对话挖掘经历 → YAML → 选主题渲染（HTML/PDF/Markdown/JSON Resume）
- **Resume Optimizer** — 给 JD 算覆盖率、ATS 合规检查、逐条 Bullet 改写

---

## 安装

在你使用的 Agent 中直接发送：

```
帮我安装这个 skill: https://github.com/Pluto417-Qing/resume-skill
```

### 手动安装

```bash
git clone https://github.com/Pluto417-Qing/resume-skill.git
cd resume-skill
pip install PyYAML Jinja2 jsonschema
pip install weasyprint  # 可选，PDF 导出
```

### 各 Agent / IDE 接入方式

| Agent / IDE | 接入方法 |
|---|---|
| Trae | 克隆到 `~/.trae/skills/career-toolkit` |
| Cursor | 克隆到 `~/.cursor/skills/career-toolkit`，或在 `.cursor/rules/` 中引用 |
| Windsurf | 克隆到 `~/.windsurf/skills/career-toolkit` |
| Claude Code | 将仓库路径加入项目 `AGENTS.md` 或 `~/.claude/settings.json` 的 skills 列表 |
| Codex (OpenAI) | 在 `codex.yaml` 中注册为 tool，或放入 `~/.codex/skills/` |
| OpenClaw | 在 `.openclaw/config.yaml` 的 `skills` 字段添加本地路径或远程 URL |
| Hermes | 在 `hermes.config.json` 的 `plugins` 中添加仓库路径 |
| 通用 | 克隆到任意目录，在你的 Agent 配置中指向该路径即可 |

---

## 技术实现

| 层 | 技术选型 |
|---|---|
| 数据层 | YAML + JSON Schema 校验 |
| 渲染层 | Jinja2 模板 + 纯 CSS |
| 导出层 | WeasyPrint / Markdown / JSON Resume |
| 测评层 | Python + YAML 题库 |
| 优化层 | 关键词提取 + 规则引擎 |

全离线，不依赖外部 API。模块间通过文件解耦，可单独使用。

---

## License

MIT
