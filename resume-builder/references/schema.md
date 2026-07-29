# Resume Schema 详解

`assets/schema/resume.schema.json` 是权威定义（JSON Schema Draft 2020-12），本文档只做人类可读的解释与常见坑。

## 顶层字段

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `meta` | object | 否 | 元信息（语言、主题、更新时间） |
| `basics` | object | 是 | 个人基础信息 |
| `education` | array | 否 | 教育经历 |
| `work` | array | 否 | 工作/实习经历 |
| `projects` | array | 否 | 项目经历 |
| `research` | array | 否 | 科研经历 |
| `publications` | array | 否 | 论文/出版 |
| `awards` | array | 否 | 获奖/荣誉 |
| `skills` | array | 否 | 技能 |
| `languages` | array | 否 | 语言能力 |
| `activities` | array | 否 | 社团 / 志愿 |
| `interests` | array | 否 | 兴趣 |
| `references` | array | 否 | 推荐人 |
| `custom_sections` | array | 否 | 自定义模块（考研目标 / 考公规划 / 作品集…） |

## `meta`

```yaml
meta:
  language: zh   # zh | en | zh-en
  theme: classic # 主题目录名
  updated_at: 2026-07
```

## `basics`

必填 `name`；其余可选。`profiles` 用于 GitHub/LinkedIn 等社交主页：

```yaml
basics:
  name: 张三
  english_name: Zhang San
  label: 前端工程师 · 应届生      # 一句话定位/求职意向
  gender: 男
  birth: 2003-05
  phone: "138 xxxx 8888"
  email: san@example.com
  location: 北京
  website: https://example.com
  avatar: ./avatar.jpg           # 可选，本地路径或 URL
  summary: 简介一段
  profiles:
    - {network: GitHub, username: san, url: https://github.com/san}
```

## `education[]`

必填 `institution`。示例：

```yaml
education:
  - institution: 某某大学
    area: 计算机科学与技术        # 专业
    degree: 本科                  # 本科/硕士/博士
    gpa: 3.7/4.0
    rank: 15/120
    start: 2022-09
    end: 2026-06
    courses: [数据结构, 操作系统]
    highlights:
      - 校级一等奖学金 * 3
```

## `work[]`

必填 `organization`。`type` 建议：`全职 / 实习 / 兼职 / 顾问`。

## `projects[]`

必填 `name`。`tech` 是关键词数组，模板会用 `·` 拼接展示。

## `custom_sections[]`

用于所有"标准字段之外"的模块。每个 section 有 `title` 和 `items[]`，item 支持 `heading / subheading / date / summary / highlights`。

```yaml
custom_sections:
  - title: 考研规划
    items:
      - heading: 目标院校：清华大学计算机系
        subheading: 学硕（学术型硕士）
        highlights:
          - 一志愿方向：系统软件
          - 参考分数线：380+
```

## 常见坑

1. **时间字段是字符串**：`2025-06` 会被 YAML 解析成 `datetime.date`，会导致 schema 校验失败。**用引号或写 `2025-06-01`，或使用 `"2025-06"`**。
2. **placeholder 字符串要加引号**：形如 `<xxx>` 的值必须写成 `"<xxx>"`，避免被 YAML 当作特殊 token。
3. **`custom_sections[].items` 键名**：Jinja2 模板中不能写 `cs.items`（会撞名 `dict.items()` 方法），必须写 `cs['items']`。schema 层没有限制，但如果你在自定义主题里访问，请注意。
4. **空数组不要写**：`education: []` 会被渲染为空 section，不美观；直接删掉字段。
5. **highlights 每条控制在一句话内**：模板会以 `<li>` 渲染，多句话会挤在同一 bullet 中。
