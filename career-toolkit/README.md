# Career Toolkit

一站式职业发展工具包，覆盖从「方向规划」到「简历产出」的完整链路。

## 功能模块

### Career Planner — 职业规划智能体

引导式收集用户画像，结合 Holland RIASEC 测评，输出多路径可行性对比和 3-6-12 个月行动规划。

适用场景：
- 不知道自己适合做什么工作
- 考研 vs 就业 vs 考公 vs 留学的抉择
- 需要一份阶段性行动清单

### Resume Builder — 简历生成器

YAML 结构化数据驱动，一处编写、多端导出。

- 7 套 HTML 主题：classic / modern / academic / minimal / compact / elegant / infographic
- WeasyPrint PDF 导出
- JSON Resume 兼容输出

## 快速开始

### 职业规划

与 AI 对话，说出你的困惑即可启动：

> "我是大三计算机专业的，不知道毕业该考研还是找工作"

产出文件：
```
./career/profile.yaml       # 用户画像
./career/career_plan.md     # 规划报告
```

### 简历生成

告诉 AI 你想做简历，按引导填写信息：

> "帮我写一份简历" / "生成简历"

产出文件：
```
./resume/resume.yaml        # 结构化简历数据
./resume/out/resume.html    # HTML 预览
./resume/out/resume.pdf     # PDF 导出
```

## 命令行工具

```bash
# Holland 测评评分
python3 modules/career-planner/scripts/score_holland.py <answers.yaml>

# 简历 Schema 校验
python3 modules/resume-builder/scripts/validate.py <resume.yaml>

# 简历渲染（HTML + PDF）
python3 modules/resume-builder/scripts/render.py <resume.yaml> --out-dir ./resume/out --pdf
```

## 项目结构

```
career-toolkit/
├── SKILL.md                          # Skill 入口与路由规则
├── modules/
│   ├── career-planner/
│   │   ├── MODULE.md                 # 模块完整文档
│   │   ├── scripts/
│   │   │   └── score_holland.py      # Holland 评分脚本
│   │   ├── assets/
│   │   │   ├── assessments/          # Holland RIASEC 题库
│   │   │   └── examples/             # profile.yaml 示例
│   │   └── references/
│   │       ├── collect-profile.md    # 画像收集策略
│   │       └── path-playbooks/       # 路径 Playbook（就业/考公/考研）
│   └── resume-builder/
│       ├── MODULE.md                 # 模块完整文档
│       ├── scripts/
│       │   ├── validate.py           # Schema 校验
│       │   ├── render.py            # Jinja2 渲染 + PDF 导出
│       │   └── to_markdown.py       # YAML → Markdown（飞书发布用）
│       ├── assets/
│       │   ├── schema/               # JSON Schema
│       │   ├── themes/               # 7 套 HTML 主题模板
│       │   └── examples/             # 简历 YAML 示例
│       └── references/
│           ├── schema.md             # 字段说明
│           ├── themes.md             # 主题预览与选择指南
│           └── writing-tips.md       # 简历写作要点
```

## 依赖

- Python 3.8+
- PyYAML
- Jinja2
- jsonschema
- WeasyPrint（PDF 导出需要）