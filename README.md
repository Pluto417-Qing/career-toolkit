# Career Toolkit

> 一个 Agent Skill：用对话代替表单，把「想不清楚 → 写不出来 → 投不精准」这条路走通。

![type](https://img.shields.io/badge/type-Agent%20Skill-purple)
![python](https://img.shields.io/badge/python-3.8+-blue)
![license](https://img.shields.io/badge/license-MIT-green)

---

## 用起来是什么感觉

```
你：我想做个简历，但不太确定该往哪个方向写
AI：好，咱先花几分钟聊聊你的情况。你现在是在校还是已经工作了？
你：大三，计算机
AI：实习过吗？或者有没有拿得出手的项目？
你：做过一个校园二手交易平台，后端是我写的
AI：日活大概多少？技术栈是什么？
你：Spring Boot + MySQL，峰值大概 500 人同时在线
AI：不错，这个能量化。我先帮你生成一版看看——
    ✅ resume.yaml 已生成
    ✅ 渲染完成 → resume.html (classic 主题)
    要换风格还是继续补充内容？
```

没有表单要你填，没有模板让你挑完自己写。它追着问，问够了直接出活。

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

三个模块各自独立，也能串联：规划产出的画像直接灌进简历字段，简历直接喂给优化器做 JD 匹配。

---

## 模块细节

### ① Career Planner — 想清楚要什么

适合还没想明白方向的人。通过引导式提问收集背景，跑 Holland RIASEC 测评，生成考研/就业/考公的多路径对比，最后给出 3-6-12 个月行动规划。

**产出文件：** `profile.yaml` · `career_plan.md`（含雷达图 + 时间线）

### ② Resume Builder — 把经历变成一页纸

核心模块。对话挖掘经历 → 结构化为 YAML → JSON Schema 校验 → 选主题渲染。

**导出格式：** HTML 预览 · PDF 打印 · JSON Resume 标准 · Markdown（可直接推飞书文档）

### ③ Resume Optimizer — 投得更准

给它一段 JD，它会：提取关键词算覆盖率、检查 ATS 格式合规性、逐条诊断 Bullet 并给改写建议。

**产出文件：** 匹配度评分 + 逐条改写方案

---

## 主题画廊

11 套主题，每套有头像/无头像两版。选完还能口头微调（「标题大一号」「项目放前面」）。

<table>
<tr>
<td align="center"><img src="modules/resume-builder/out/preview/classic-avatar/resume.png" width="180"/><br/><b>Classic</b></td>
<td align="center"><img src="modules/resume-builder/out/preview/modern-avatar/resume.png" width="180"/><br/><b>Modern</b></td>
<td align="center"><img src="modules/resume-builder/out/preview/minimal-avatar/resume.png" width="180"/><br/><b>Minimal</b></td>
<td align="center"><img src="modules/resume-builder/out/preview/elegant-avatar/resume.png" width="180"/><br/><b>Elegant</b></td>
</tr>
<tr>
<td align="center"><img src="modules/resume-builder/out/preview/compact-avatar/resume.png" width="180"/><br/><b>Compact</b></td>
<td align="center"><img src="modules/resume-builder/out/preview/academic-avatar/resume.png" width="180"/><br/><b>Academic</b></td>
<td align="center"><img src="modules/resume-builder/out/preview/infographic-avatar/resume.png" width="180"/><br/><b>Infographic</b></td>
<td align="center"><img src="modules/resume-builder/out/preview/creative-avatar/resume.png" width="180"/><br/><b>Creative</b></td>
</tr>
<tr>
<td align="center"><img src="modules/resume-builder/out/preview/executive-avatar/resume.png" width="180"/><br/><b>Executive</b></td>
<td align="center"><img src="modules/resume-builder/out/preview/metro-avatar/resume.png" width="180"/><br/><b>Metro</b></td>
<td align="center"><img src="modules/resume-builder/out/preview/tech-avatar/resume.png" width="180"/><br/><b>Tech</b></td>
<td></td>
</tr>
</table>

---

## 安装

跟你的 Agent 说一句：

```
帮我安装这个 skill: https://github.com/<your-username>/career-toolkit
```

Agent 会自动完成 clone、依赖安装和验证。

<details>
<summary>偏好手动操作？</summary>

```bash
git clone https://github.com/<your-username>/career-toolkit.git ~/.trae/skills/career-toolkit
pip install pyyaml jinja2 jsonschema
# PDF 导出需要额外装 weasyprint（依赖系统 cairo/pango）
pip install weasyprint
```
</details>

---

## 技术实现

| 层 | 做什么 | 技术选型 |
|---|---|---|
| 数据层 | 简历内容存储 | YAML + JSON Schema 校验 |
| 渲染层 | 多主题 HTML 生成 | Jinja2 模板 + 纯 CSS |
| 导出层 | PDF / Markdown / JSON Resume | WeasyPrint · 自研转换 |
| 测评层 | Holland RIASEC 评分 | Python 脚本 + YAML 题库 |
| 优化层 | JD 匹配 + ATS 检查 | 关键词提取 + 规则引擎 |

**设计原则：**
- 全离线运行，不依赖外部 API
- Schema 严格校验，渲染前自动修复数据问题
- 模块间通过文件（YAML/Markdown）解耦，可单独使用

---

## 文件结构

```
career-toolkit/
├── SKILL.md              # Agent 入口，负责意图路由
├── manifest.json         # 依赖声明
├── scripts/              # 工具脚本（预览图生成等）
└── modules/
    ├── career-planner/   # 职业规划模块
    │   ├── MODULE.md
    │   ├── scripts/
    │   ├── assets/assessments/
    │   └── references/
    ├── resume-builder/   # 简历生成模块
    │   ├── MODULE.md
    │   ├── scripts/
    │   ├── assets/themes/
    │   ├── assets/schema/
    │   └── out/preview/
    └── resume-optimizer/ # 求职优化模块
        ├── MODULE.md
        ├── scripts/
        └── references/
```

---

## 环境要求

- Python 3.8+
- 必装：`pyyaml` · `jinja2` · `jsonschema`
- 可选：`weasyprint`（PDF 导出，需系统级 cairo/pango）
- 网络：**不需要**

---

## Roadmap

- [ ] 行业专属主题（设计/金融/学术）
- [ ] 中英双语简历
- [ ] 面试准备模块
- [ ] 分岗位的经历深挖策略

---

## License

MIT
