# Career Toolkit — Skill Pack

> 职业规划 + 简历生成，完全本地运行，无需服务器。


## 安装

给 Agent 说一句话即可：

```
帮我安装这个 skill: https://github.com/<your-username>/career-toolkit
```

Agent 会自动完成 clone + 依赖安装 + 验证。

> 依赖：Python 3.8+、PyYAML、Jinja2、jsonschema（Agent 自动 pip install）

---

## 包含模块

### Career Planner — 职业规划智能体

引导式对话收集用户画像 → Holland RIASEC 测评 → 多路径可行性对比 → 3-6-12 个月行动规划。

**适用场景：**
- 不知道自己适合什么方向
- 考研 / 就业 / 考公 / 留学的抉择
- 需要一份可执行的阶段性行动清单

**产出：** `profile.yaml` + `career_plan.md`（含时间线 + RIASEC 雷达图）

---

### Resume Builder — 简历生成器

对话式信息收集 → YAML 结构化简历 → Schema 校验 → 多主题渲染。

**7 套主题：** classic / modern / academic / minimal / compact / elegant / infographic

**导出格式：** HTML 预览 · PDF 打印 · JSON Resume 标准 · Markdown

**产出：** `resume.yaml` + `resume.html` + `resume.pdf`

---

## 使用

安装后直接对话触发：

| 你说的话 | 触发模块 |
|---|---|
| "我是大三的，不知道该考研还是找工作" | Career Planner |
| "帮我做个简历" | Resume Builder |
| "帮我匹配这个 JD" | Resume Optimizer（附赠） |

---

## 系统要求

| 项目 | 要求 |
|---|---|
| Python | 3.8+ |
| 磁盘空间 | ~5MB |
| 网络 | **不需要**（核心功能离线可用） |
| 操作系统 | macOS / Linux / Windows (WSL) |
| PDF 导出 | 可选，需额外安装 WeasyPrint |

---

## 文件结构

```
career-toolkit/
├── SKILL.md              # Skill 入口（Agent 自动识别）
├── manifest.json         # 依赖声明（Agent 读取后自动安装）
├── demo/                 # 演示 GIF
└── modules/
    ├── career-planner/   # 职业规划（测评 + Playbook + 可视化）
    ├── resume-builder/   # 简历生成（7 主题 + Schema + 渲染）
    └── resume-optimizer/ # 求职强化（JD 匹配 + ATS 检查）
```

---

## 许可

MIT
