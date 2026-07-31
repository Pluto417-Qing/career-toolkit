# Resume Builder

用自然对话生成一份专业简历——用户只需聊天，Agent 负责收集、组织、校验、渲染。

## 核心原则

> **用户不需要知道 YAML、Schema、字段名。**
> Agent 通过对话主动提问、归纳、确认，最终产出结构化简历并渲染为 HTML/PDF。

禁止：把字段列表或 YAML 模板甩给用户让他们自己填。
正确做法：逐步引导，一次只问一两个问题，按「基础信息 → 教育 → 经历 → 技能 → 补充」的节奏推进。

## 何时使用

用户想要：
- 生成、更新或美化一份简历
- 把散乱的经历整理成结构化数据
- 在浏览器预览简历，或导出印刷级 PDF
- 需要一份 JSON Resume 兼容数据用来接第三方模板

不覆盖：JD 匹配 / ATS 深度诊断 / bullet 量化改写（交给 `resume-optimizer`）；职业方向规划（交给 `career-planner`）。

## 工作流：对话驱动，三阶段自动推进

### 阶段 1：对话收集

Agent 主动引导对话，分轮次收集以下信息（不必一次问完，自然穿插即可）：

1. **破冰 & 定位**：你目前是学生还是在职？大概投什么方向？有没有现成简历/经历文档可以参考？
2. **基础信息**：姓名、联系方式、求职意向一句话、社交主页（GitHub/LinkedIn 等）
3. **教育背景**：学校、专业、学位、GPA/排名（可选）、毕业时间
4. **核心经历**：工作/实习/项目/科研——每段问清楚：做了什么、用了什么技术、成果如何量化
5. **技能 & 补充**：技术栈分类、获奖、语言能力、自定义模块（考研目标、作品集等）

6. **模板选择**：信息收集接近完成时，向用户展示可选主题并询问偏好：
   - `classic`：单栏传统中文简历，适合大多数场景
   - `modern`：双栏现代风格，视觉层次分明
   - `academic`：学术长 CV，适合科研/留学申请
   - `minimal`：极简留白，适合设计/创意方向
   - `compact`：紧凑高密度，内容多时一页塞下
   - `elegant`：衬线标题铜棕色调，正式商务风
   - `infographic`：技能进度条+时间线可视化，适合技术岗展示

   用户未明确选择时默认 `classic`。选择结果写入 `meta.theme` 字段。

**收集技巧**：
- 用户给出模糊描述时，追问量化数据（"提升了多少？""服务了多少用户？"）
- 用户一次性粘贴大段文字时，Agent 主动提炼结构化要点并回复确认
- 信息够用时主动说"我这边信息差不多了，帮你生成初稿？"

收集完成后，Agent 在用户工作目录（默认 `./resume/`）生成 `resume.yaml`。字段结构遵循 [schema.md](references/schema.md)，写作规范见 [writing-tips.md](references/writing-tips.md)。

### 阶段 2：校验

```bash
cd <resume-builder module dir>
python3 scripts/validate.py <path/to/resume.yaml>
```

校验失败时 Agent 自行修复并重试，不要把 schema 错误暴露给用户。

### 阶段 3：渲染

```bash
python3 scripts/render.py <path/to/resume.yaml> --out-dir <output_dir> --pdf
```

产出（在 `<output_dir>/`）：
- `resume.html`：浏览器可预览
- `resume.pdf`：印刷级 PDF（WeasyPrint）
- `resume.json`：JSON Resume 兼容超集

渲染完成后主动告知用户产出路径，并询问是否需要调整内容或换主题。

`--theme` 缺省读 `meta.theme`，否则用 `classic`。内置主题见 [themes.md](references/themes.md)。

### 阶段 4（可选）：发飞书

当用户说"发飞书/分享简历给XX review"时：

1. 生成 Markdown：`python3 scripts/to_markdown.py <resume.yaml> --out-dir <output_dir>`
2. 用 `lark-doc` skill 创建飞书文档，标题格式 `简历 - {姓名} - {日期}`
3. 若指定了接收人，用 `lark-im` skill 发送文档链接

> 需要用户已完成 lark-cli 登录。未认证时提示走 `lark-shared` skill。

## 迭代修改

用户后续说"把实习那段改一下""加个项目""换个主题"时：
- Agent 直接修改 `resume.yaml` 对应部分
- 重新校验 + 渲染
- 告知用户已更新，无需重新走完整收集流程

## 主题定制

- 主题目录：`assets/themes/<theme-name>/`，含 `template.html.j2` + `style.css`
- 模板用 Jinja2，数据入口变量为 `data`，结构与 schema 一致
- Jinja2 中读 dict 里名为 `items` 的键要用 `data['items']`，避免撞名 `.items()` 方法

## 与其他模块的协作

- `career-planner` 完成画像后可自动映射 `profile.yaml → resume.yaml`，无缝衔接本模块
- `resume-optimizer`（后续）在本模块产出的 `resume.json` 上做 JD 匹配与 ATS 检查
- `lark-doc` / `lark-im` / `lark-shared`：飞书发布链路

## 目录导航

- [assets/schema/resume.schema.json](assets/schema/resume.schema.json) — JSON Schema
- [assets/themes/](assets/themes/) — 内置主题集
- [assets/examples/zh-fresh-grad.yaml](assets/examples/zh-fresh-grad.yaml) — 应届生示例
- [references/schema.md](references/schema.md) — 字段详解（Agent 内部参考）
- [references/writing-tips.md](references/writing-tips.md) — bullet 写作规范
- [references/themes.md](references/themes.md) — 主题体系与定制指南
- [scripts/validate.py](scripts/validate.py) — schema 校验
- [scripts/render.py](scripts/render.py) — 渲染 HTML/PDF/JSON/Markdown
- [scripts/to_markdown.py](scripts/to_markdown.py) — Markdown 导出（飞书用）
