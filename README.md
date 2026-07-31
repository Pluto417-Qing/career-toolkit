<div align="center">

# Career Toolkit

---

**把 AI 变成你的职业教练，从方向规划到简历落地，一条对话搞定。**

不是丢给你一堆模板自己填，而是有人陪你想清楚方向、挖出经历、排进一页纸。

![type](https://img.shields.io/badge/type-Agent%20Skill-purple)
![output](https://img.shields.io/badge/output-HTML%20→%20PDF-gray)
![python](https://img.shields.io/badge/python-3.8+-blue)
![license](https://img.shields.io/badge/license-MIT-green)

---

</div>

## 你大概遇到过这些

| 你说的话 | 常见 AI 工具 | Career Toolkit |
|---|---|---|
| 「帮我做个简历」 | 要你先整理好内容再粘贴 | 追着你问，每个问题带选项 |
| 「我不知道该考研还是工作」 | 给你一篇鸡汤文 | Holland 测评 + 多路径对比 + 行动清单 |
| 「帮我投这个岗位」 | 让你自己对照 JD 改 | 自动提取关键词、匹配度打分、逐条改写 |
| 「换个风格」 | 重新生成一份面目全非的 | 换套主题，3 秒重新渲染 |
| 「我要分享给别人看」 | 导出个 PDF 自己传 | 一键发飞书文档，直接甩链接 |

## 十一套主题

选完只是起点，每个细节都还能聊着改。

| Classic | Modern | Academic | Minimal |
|---|---|---|---|
| ![classic](modules/resume-builder/out/preview/classic-avatar/resume.png) | ![modern](modules/resume-builder/out/preview/modern-avatar/resume.png) | ![academic](modules/resume-builder/out/preview/academic-avatar/resume.png) | ![minimal](modules/resume-builder/out/preview/minimal-avatar/resume.png) |

| Compact | Elegant | Infographic | Creative |
|---|---|---|---|
| ![compact](modules/resume-builder/out/preview/compact-avatar/resume.png) | ![elegant](modules/resume-builder/out/preview/elegant-avatar/resume.png) | ![infographic](modules/resume-builder/out/preview/infographic-avatar/resume.png) | ![creative](modules/resume-builder/out/preview/creative-avatar/resume.png) |

| Executive | Metro | Tech |
|---|---|---|
| ![executive](modules/resume-builder/out/preview/executive-avatar/resume.png) | ![metro](modules/resume-builder/out/preview/metro-avatar/resume.png) | ![tech](modules/resume-builder/out/preview/tech-avatar/resume.png) |

每套主题提供**有头像 / 无头像**两个版本，适配不同场景。

## 三十秒装好

把这句话甩给你的 Agent：

```
帮我安装这个 skill: https://github.com/<your-username>/career-toolkit
```

完事。Agent 会自动 clone + 安装依赖 + 验证。然后跟它说「帮我做个简历」或「帮我规划一下方向」。

<details>
<summary>手动安装</summary>

```bash
git clone https://github.com/<your-username>/career-toolkit.git ~/.trae/skills/career-toolkit
pip install pyyaml jinja2 jsonschema
# 可选：PDF 导出
pip install weasyprint
```
</details>

## 三个模块，一条链路

```
方向不清楚？         有经历了？           要投岗位了？
     ↓                  ↓                   ↓
┌────────────┐   ┌────────────────┐   ┌────────────────┐
│  Career    │──→│    Resume      │──→│    Resume      │
│  Planner   │   │    Builder     │   │   Optimizer    │
└────────────┘   └────────────────┘   └────────────────┘
  职业规划           简历生成              求职优化
```

每个模块独立可用，也能串联成完整流程。

### Career Planner — 想清楚方向

引导式对话收集画像 → Holland RIASEC 测评 → 考研/就业/考公多路径对比 → 输出 3-6-12 个月行动规划。

**产出：** `profile.yaml` + `career_plan.md`（含 RIASEC 雷达图 + 时间线）

### Resume Builder — 写出简历

对话式挖经历 → 结构化为 YAML → JSON Schema 校验 → 11 套主题渲染。

**四种导出：** HTML 预览 · PDF 打印 · JSON Resume 标准 · Markdown（飞书文档）

**产出：** `resume.yaml` + `resume.html` + `resume.pdf`

### Resume Optimizer — 投准岗位

JD 关键词匹配 → ATS 格式合规检查 → Bullet 量化改写建议。

**产出：** 匹配度报告 + 逐条改写建议

## 它凭什么不一样

### 对话驱动，不是表单填写

你不用先整理好内容再粘贴进模板。它会追着你问「这个项目你具体做了什么」「有没有数字可以量化」，凑够信息就先渲染给你看，边聊边改。

### 方向 → 简历 → 投递，一站打通

Career Planner 产出的用户画像自动映射到 Resume Builder 的字段，不用重复输入。优化模块直接读已生成的简历做 JD 匹配。

### 你说人话，它改排版

「这行太挤了」「标题再大一号」「把项目经历放前面」——说完重新渲染，3 秒出结果。

### Schema 兜底，不会出格式错误

所有简历数据经过 JSON Schema 严格校验。缺字段、格式错，Agent 自行修复后再渲染，不会把半成品丢给你。

### 飞书生态集成

Markdown 导出 → 飞书文档一键创建 → 群聊直接分享链接。适合团队内互相 review。

## 三种典型用法

| 场景 | 它会做什么 |
|---|---|
| **从零开始** | 先问方向（可跳过）→ 访谈式挖经历 → 选主题 → 渲染 HTML → 确认后导出 PDF |
| **改旧简历** | 读取已有 YAML/PDF → 分析结构 → 逐段优化 → 重新渲染 |
| **投特定岗位** | 读 JD → 关键词匹配 → 建议调整顺序和措辞 → 生成定制版本 |

## 里面装了什么

```
career-toolkit/
├── SKILL.md                        # 入口（Agent 自动识别 + 路由）
├── manifest.json                   # 依赖声明（Agent 自动安装）
├── modules/
│   ├── career-planner/
│   │   ├── MODULE.md               # 规划工作流
│   │   ├── scripts/                # 测评评分 + 可视化
│   │   ├── assets/assessments/     # Holland / MBTI 题库
│   │   └── references/             # 考研/就业/考公 Playbook
│   ├── resume-builder/
│   │   ├── MODULE.md               # 简历工作流
│   │   ├── scripts/                # 渲染 + 校验 + Markdown 导出
│   │   ├── assets/themes/          # 11 套主题（Jinja2 + CSS）
│   │   ├── assets/schema/          # JSON Schema 定义
│   │   └── out/preview/            # 主题预览画廊
│   └── resume-optimizer/
│       ├── MODULE.md               # 优化工作流
│       ├── scripts/                # JD 匹配 + ATS 检查 + Bullet 改写
│       └── references/             # 优化策略文档
└── README.md
```

## 系统要求

| 项目 | 要求 |
|---|---|
| Python | 3.8+ |
| 必装依赖 | PyYAML · Jinja2 · jsonschema |
| 可选依赖 | WeasyPrint（PDF 导出，需系统 cairo/pango） |
| 网络 | **不需要**（核心功能完全离线） |
| 操作系统 | macOS / Linux / Windows (WSL) |

## 后续计划

- [ ] 更多行业专属主题（设计/金融/学术）
- [ ] 分岗位的经历深挖策略
- [ ] 多语言简历支持（中英双版）
- [ ] 面试准备模块

## 许可

MIT

---

**如果它帮到了你，给个 ⭐️ 是对开源最大的鼓励。**
