---
name: resume-builder
description: 用 YAML 编写、渲染并导出中文简历的完整工具链。能力：(1) 提供扩展自 JSON Resume 的中文语境 schema，让 Agent 用 YAML 结构化收集个人信息并做 schema 校验；(2) 通过内置 HTML 主题渲染出可在浏览器直接预览的简历页面；(3) 通过 WeasyPrint 一键导出印刷级 PDF；(4) 同时输出 JSON Resume 兼容的 resume.json，便于对接第三方主题/工具。适用场景：用户提到"写简历/做简历/生成简历/简历模板/resume/CV/导出 PDF/预览简历/JSON Resume/YAML 简历"，或需要为求职、实习、保研、留学、考公申请材料准备一份可维护的简历时使用。
author: 袁箐鸿
---

# Resume Builder

用 YAML 写简历，一处编写、多端导出（HTML 预览 / PDF 打印 / JSON Resume 数据）。

## 何时使用

用户想要：
- 生成、更新或美化一份简历（中文为主，也支持 zh-en 双语字段）
- 把散乱的经历整理成结构化数据，方便后续投递不同岗位时快速定制
- 在浏览器预览简历，或导出印刷级 PDF
- 需要一份符合 JSON Resume schema 的数据文件用来接第三方模板

不覆盖：`JD 匹配 / ATS 深度诊断 / bullet 量化改写`——那些交给 `resume-optimizer` skill；`职业方向规划 / 测评 / 路径推荐`交给 `career-planner` skill。

## 核心工作流

三步走：**收集 → 校验 → 渲染**。

### 1. 收集：把用户信息落到 `resume.yaml`

先把工作目录下（默认 `./resume/`）建 `resume.yaml`。字段结构参考 [schema.md](references/schema.md) 或直接看示例：
- 应届/在校生：从 [assets/examples/zh-fresh-grad.yaml](assets/examples/zh-fresh-grad.yaml) 复制起手。

**关键字段一览**（详细见 [schema.md](references/schema.md)）：

| 字段 | 说明 |
|---|---|
| `basics` | 姓名、联系方式、求职意向一句话（`label`）、社交主页 |
| `education[]` | 学校、专业、学位、GPA、排名、时间段 |
| `work[]` | 工作/实习经历，`type` 区分全职/实习/兼职 |
| `projects[]` | 项目经历，含技术栈 `tech` |
| `research[]` | 科研经历（学术向） |
| `skills[]` | 分类的技能与关键词 |
| `awards[]` / `publications[]` / `languages[]` / `activities[]` | 常规模块 |
| `custom_sections[]` | 自定义模块（考研目标、考公岗位规划、作品集等） |

**写作要点**（详细见 [writing-tips.md](references/writing-tips.md)）：
- `highlights` 每条一句话，动词开头 + 量化结果，避免形容词堆砌。
- 时间统一用 `YYYY-MM` 或 `YYYY`，"至今"直接省略 `end`。
- 空模块请直接不写，不要留空数组。

### 2. 校验：确保 schema 合法

```bash
cd <resume-builder skill dir>
python3 scripts/validate.py <path/to/resume.yaml>
```

校验失败会打印字段路径与错误原因；修完再进入渲染。

### 3. 渲染：生成 HTML / PDF / JSON

```bash
python3 scripts/render.py <path/to/resume.yaml> --out-dir <output_dir> --pdf
```

产出（在 `<output_dir>/`）：
- `resume.html`：在浏览器打开可预览
- `resume.pdf`：印刷级 PDF（WeasyPrint 生成，无需 headless Chromium）
- `resume.json`：JSON Resume 兼容超集，便于第三方对接

`--theme` 缺省会读取 `meta.theme`，否则用 `classic`。当前内置主题：
- `classic` — 单栏、传统中文简历风格，适配 A4 打印

要托管 HTML 让用户在线预览，可再走 `deploy` skill 部署 `resume.html`。

## 主题定制

- 主题目录：`assets/themes/<theme-name>/`，需包含 `template.html.j2` 和 `style.css`。
- 模板使用 Jinja2，数据入口变量为 `data`，字段结构与 schema 一致。
- 新增主题时把 `template.html.j2` 保持"数据即渲染"，样式差异全部放到 `style.css`。
- 特别注意：Jinja2 中读 dict 里名为 `items` 的键要用 `data['items']`，避免撞名 `.items()` 方法。

## 与其他 skill 的协作

- `career-planner` 生成规划后若用户需要简历，声明"使用 `resume-builder` skill 生成简历"，并把 `profile.yaml` 中的信息映射到 `resume.yaml`。
- `resume-optimizer`（后续）会在本 skill 产出的 `resume.json` 上做 JD 匹配、ATS 检查、bullet 量化。

## 目录导航

- [assets/schema/resume.schema.json](assets/schema/resume.schema.json) — JSON Schema（Draft 2020-12）
- [assets/themes/classic/](assets/themes/classic/) — 默认主题
- [assets/examples/zh-fresh-grad.yaml](assets/examples/zh-fresh-grad.yaml) — 应届生示例
- [references/schema.md](references/schema.md) — 字段详解与常见坑
- [references/writing-tips.md](references/writing-tips.md) — bullet 写作与量化建议
- [references/themes.md](references/themes.md) — 主题体系与定制指南
- [scripts/validate.py](scripts/validate.py) — YAML → schema 校验
- [scripts/render.py](scripts/render.py) — YAML → HTML/PDF/JSON
