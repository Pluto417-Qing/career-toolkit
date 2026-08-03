<h1 align="center">Resume Toolkit</h1>
<p align="center">Agent Skill — 面向中文简历的信息库驱动生成与优化系统</p>

<p align="center">
  <img src="https://img.shields.io/badge/type-Agent%20Skill-purple"/>
  <img src="https://img.shields.io/badge/python-3.8+-blue"/>
  <img src="https://img.shields.io/badge/license-MIT-green"/>
</p>

**Resume Toolkit** 是一个全离线、信息库驱动的中文简历系统。核心理念：

> 先建立「个人信息库」存储完整履历，再面向特定 JD 从信息库中筛选、裁剪、润色、交互生成两份简历——**通用版（海投）** 与 **JD 适配版（定向）**。

---

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

## 架构总览

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Resume Toolkit                              │
│                                                                     │
│  ┌─────────────────────────── 信息库驱动 ──────────────────────────┐ │
│  │                                                                 │ │
│  │  ① ProfileManager         ② JDAnalyzer                        │ │
│  │  ┌──────────────────┐     ┌────────────────────────────┐       │ │
│  │  │ 个人信息库管理    │     │ JD 关键词提取 · 概念映射   │       │ │
│  │  │ 完整履历 · 双视角 │     │ 必备/加分关键词分级        │       │ │
│  │  └──────────────────┘     └────────────────────────────┘       │ │
│  │           │                         │                           │ │
│  │           ▼                         ▼                           │ │
│  │  ③ ExperienceRanker       ④ ContentCondenser                   │ │
│  │  ┌──────────────────┐     ┌────────────────────────────┐       │ │
│  │  │ 5 维相关性评分    │     │ 双视角合并 · 弱动词替换    │       │ │
│  │  │ 关键词/概念/量化  │     │ 一页纸控制 · 表达优化      │       │ │
│  │  └──────────────────┘     └────────────────────────────┘       │ │
│  │           │                         │                           │ │
│  │           ▼                         ▼                           │ │
│  │  ⑤ QuestionGenerator      ⑥ ResumeBuilder                     │ │
│  │  ┌──────────────────┐     ┌────────────────────────────┐       │ │
│  │  │ 缺失/模糊检测    │     │ 整合所有模块               │       │ │
│  │  │ 交互式追问       │     │ 4 模板对比 · 多格式导出    │       │ │
│  │  └──────────────────┘     └────────────────────────────┘       │ │
│  │                                                                 │ │
│  └─────────────────────────────────────────────────────────────────┘ │
│                                                                     │
│  附加模块：ExpressionOptimizer · Highlighter · TemplateManager      │
└─────────────────────────────────────────────────────────────────────┘
```

### 核心特性

| 能力 | 说明 |
|------|------|
| **信息库驱动** | 一次采集完整履历（工作/项目/教育双视角），多次复用生成不同简历 |
| **双视角采集** | 每条经历同时记录「项目做了什么」和「你做了什么」，构建真实贡献 |
| **5 维经历筛选** | 关键词匹配、概念关联、量化程度、重要性、时效性加权评分 |
| **双版本生成** | 通用版（海投）+ JD 适配版（定向），不编造经历 |
| **交互式追问** | 自动识别缺失量化、模糊描述、与 JD 不匹配的条目并追问用户 |
| **一页纸控制** | 默认输出 A4 一页，自动裁剪弱相关内容 |
| **表达优化** | 弱动词→强动词替换、行业术语专业化、STAR 模板应用 |
| **重点突出** | 量化指标/影响力动词/技术关键词高亮与优先级排序 |
| **模板对比** | 4 套风格（经典/现代/极简/创意）一键对比预览 |

---

## 模块详解

### 🔖 Resume Builder（简历生成）

对话式采集 → YAML → 选主题渲染（HTML/PDF/Markdown/JSON Resume）。

```bash
# 从信息库生成简历
python3 modules/resume-optimizer/scripts/resume_cli.py build <user_id> --jd jd.txt
```

### 🔍 Resume Optimizer（求职优化）

面向 JD 的完整优化链路：

| 原子 Skill | 说明 |
|---|---|
| **JD 匹配** | 三层关键词覆盖率分析，输出 gap 分类与改写建议 |
| **关键词融入** | 不堆砌、不编造，5 种融入策略 + 置信度分级 |
| **Bullet 改写** | 诊断形容词式/职责式/模糊式描述，生成改写对照 |
| **ATS 检查** | 中文字段合规、时间格式、夸大词检测 |
| **双版本生成** | 一键产出通用版 + JD 适配版 |

```bash
# 一键优化
python3 modules/resume-optimizer/scripts/jd_optimize.py resume.yaml --jd jd.txt
# 匹配分析
python3 modules/resume-optimizer/scripts/jd_match.py resume.yaml --jd jd.txt
```

### ⚙️ 模块化子系统

`modules/resume-optimizer/` 下按职责拆分的 6 个子模块：

| 模块 | 路径 | 核心职责 |
|------|------|----------|
| **profile** | `profile/` | 信息库 CRUD、版本控制、描述符系统 |
| **jd** | `jd/` | JD 关键词提取、概念映射、质量评分 |
| **ranker** | `ranker/` | 5 维相关性评分、经历排序与 Top-N 选择 |
| **condenser** | `condenser/` | 内容精简、表达优化、重点高亮 |
| **question** | `question/` | 问题生成、优先级排序、交互管理 |
| **builder** | `builder/` | 整合编排、模板渲染、多格式导出 |

---

## CLI 使用

```bash
# 构建简历（核心命令）
python3 scripts/resume_cli.py build <user_id> --jd jd.txt [--template modern] [--interactive]

# 分析 JD
python3 scripts/resume_cli.py analyze-jd jd.txt

# 信息库管理
python3 scripts/resume_cli.py profile list
python3 scripts/resume_cli.py profile show --user-id demo
python3 scripts/resume_cli.py profile migrate --user-id demo --resume old.yaml

# 优化文本
python3 scripts/resume_cli.py optimize "负责核心模块开发，性能有所提升"

# 列出 / 对比模板
python3 scripts/resume_cli.py templates
python3 scripts/resume_cli.py compare <user_id> --jd jd.txt
```

---

## 安装

在 Agent 中直接发送：

```
帮我安装这个 skill: https://github.com/Pluto417-Qing/resume-skill
```

### 手动安装

```bash
git clone https://github.com/Pluto417-Qing/resume-skill.git
cd resume-skill
pip install PyYAML Jinja2 jsonschema jieba
pip install weasyprint  # 可选，PDF 导出
```

### Agent / IDE 接入

| Agent | 接入方法 |
|---|---|
| Trae | 克隆到 `~/.trae/skills/resume-toolkit` |
| Cursor | 克隆到 `~/.cursor/skills/resume-toolkit` |
| Windsurf | 克隆到 `~/.windsurf/skills/resume-toolkit` |
| Claude Code | 加入 skills 列表或 `AGENTS.md` |
| 通用 | 克隆到任意目录，配置指向该路径 |

---

## 技术实现

| 层 | 技术选型 |
|---|---|
| 数据层 | YAML + JSON Schema 校验 + 版本化信息库 |
| 分词/匹配 | jieba 分词 + TF-IDF + 概念映射库 |
| 经历筛选 | 5 维加权评分算法（关键词/概念/量化/重要性/时效） |
| 内容优化 | 弱动词替换规则引擎 + 同义词库 + 行业术语库 |
| 渲染层 | Jinja2 模板 + 纯 CSS（11 主题） |
| 导出层 | WeasyPrint / Markdown / JSON Resume |
| 交互层 | 问题优先级排序 + 多轮问答管理 |

**全离线运行**，不依赖外部 API。模块间通过文件解耦，可单独使用。

---

## 目录结构

```
modules/
├── resume-builder/          # 对话采集 + 渲染
│   ├── assets/themes/       # 11 套主题
│   ├── assets/tsinghua/     # 清华院系/奖学金/经历类型
│   └── scripts/             # render / validate / to_markdown
└── resume-optimizer/        # 求职优化
    ├── profile/             # 信息库管理
    ├── jd/                  # JD 分析
    ├── ranker/              # 经历筛选
    ├── condenser/           # 内容精简 + 表达优化 + 重点突出
    ├── question/            # 交互提问生成
    ├── builder/             # 整合构建 + 模板系统
    ├── assets/              # 动词/术语/概念/同义词库
    └── scripts/             # CLI + 5 个原子 Skill 脚本
```

---

## License

MIT