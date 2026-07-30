# Career Toolkit — Skill Pack

> 职业规划 + 简历生成，一键安装到 TRAE，完全本地运行。

<!-- 将 demo/overview.gif 替换为实际录制的演示 GIF -->
![Demo](demo/overview.gif)

---

## 包含模块

### 🎯 Career Planner — 职业规划智能体

引导式对话收集用户画像 → Holland RIASEC 测评 → 多路径可行性对比 → 3-6-12 个月行动规划。

**适用场景：**
- 不知道自己适合什么方向
- 考研 / 就业 / 考公 / 留学的抉择
- 需要一份可执行的阶段性行动清单

**产出：**
- `profile.yaml` — 结构化用户画像
- `career_plan.md` — 规划报告（含时间线 + RIASEC 雷达图）

---

### 📄 Resume Builder — 简历生成器

对话式信息收集 → YAML 结构化简历 → Schema 校验 → 多主题渲染。

**7 套主题：** classic / modern / academic / minimal / compact / elegant / infographic

**导出格式：** HTML 预览 · PDF 打印 · JSON Resume 标准 · Markdown（飞书兼容）

**产出：**
- `resume.yaml` — 结构化简历数据
- `resume.html` — HTML 预览
- `resume.pdf` — PDF 导出（需 WeasyPrint）

---

## 快速开始

```bash
# 1. 克隆或拷贝到 TRAE user_skills 目录
cp -r career-toolkit ~/Desktop/user_skills/

# 2. 运行安装脚本
cd ~/Desktop/user_skills/career-toolkit
bash setup.sh
```

安装完成后在 TRAE 对话中直接说：

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
| 磁盘空间 | ~5MB（不含 WeasyPrint） |
| 网络 | **不需要**（核心功能离线可用） |
| 操作系统 | macOS / Linux / Windows (WSL) |

---

## 详细安装指引

→ 见 [INSTALL.md](INSTALL.md)

---

## 文件结构

```
career-toolkit/
├── SKILL.md                    # Skill 入口定义（TRAE 自动识别）
├── setup.sh                    # 一键安装脚本
├── INSTALL.md                  # 详细安装指引
├── demo/                       # 演示 GIF 资源
│   └── PLACEHOLDER.md
└── modules/
    ├── career-planner/         # 职业规划智能体
    │   ├── MODULE.md
    │   ├── scripts/            # Holland/MBTI 评分 + 可视化
    │   ├── assets/             # 题库 + 示例
    │   └── references/         # Playbook（就业/考研/考公）
    └── resume-builder/         # 简历生成器
        ├── MODULE.md
        ├── scripts/            # 校验 + 渲染 + Markdown 转换
        ├── assets/             # Schema + 7 套主题 + 示例
        └── references/         # 字段说明 + 写作指南
```

---

## 许可

MIT
