---
name: career-toolkit
description: 职业规划 + 简历生成 + 求职优化。Holland 测评与行动规划；7 套主题简历渲染、PDF 导出；JD 关键词匹配、ATS 检查、Bullet 量化改写。触发词：职业规划、生涯规划、考研就业、写简历、生成简历、导出 PDF、匹配 JD、ATS 检查、简历优化、量化改写、毕业迷茫。
author: 袁箐鸿
---

# Career Toolkit

一站式职业发展工具包，覆盖从「方向规划」到「简历产出」的完整链路。

## 模块一览

| 模块 | 路径 | 定位 |
|---|---|---|
| **career-planner** | [modules/career-planner/MODULE.md](modules/career-planner/MODULE.md) | 画像收集 → Holland 测评 → 路径规划 → 行动报告 |
| **resume-builder** | [modules/resume-builder/MODULE.md](modules/resume-builder/MODULE.md) | YAML 简历 → Schema 校验 → HTML/PDF/JSON 多端导出 |
| **resume-optimizer** | [modules/resume-optimizer/MODULE.md](modules/resume-optimizer/MODULE.md) | JD 匹配 → Bullet 量化改写 → 中文 ATS 检查 |

## 路由规则

根据用户意图选择加载哪个模块的完整文档：

### → career-planner

触发词：职业规划、生涯规划、我该做什么工作、考研还是就业、考公规划、留学规划、Holland 测评、毕业迷茫、未来方向、行动计划

加载：[modules/career-planner/MODULE.md](modules/career-planner/MODULE.md)

### → resume-builder

触发词：写简历、做简历、生成简历、简历模板、resume、CV、导出 PDF、预览简历、换主题、修改简历、发飞书、简历发飞书、分享简历、发给导师、发给 HR

加载：[modules/resume-builder/MODULE.md](modules/resume-builder/MODULE.md)

### → resume-optimizer

触发词：匹配 JD、JD 匹配、关键词覆盖率、这个岗位合适吗、ATS 检查、简历体检、格式合规、量化改写、改 bullet、优化经历描述、简历诊断、简历优化

加载：[modules/resume-optimizer/MODULE.md](modules/resume-optimizer/MODULE.md)

### 联动场景

当用户在做规划时说"顺便帮我做个简历"，由 career-planner 完成画像后，自动将 `profile.yaml` 字段映射到 `resume.yaml`，然后切换到 resume-builder 模块执行渲染。

## 模块间共享约定

- 用户工作目录结构：
  ```
  ./career/profile.yaml          ← career-planner 产出
  ./career/career_plan.md        ← career-planner 产出
  ./resume/resume.yaml           ← resume-builder 输入
  ./resume/out/resume.html|pdf   ← resume-builder 产出
  ```
- `career-planner` 的 `profile.yaml → resume.yaml` 字段映射关系见 career-planner MODULE.md 尾部。
- 脚本路径均相对于各自模块目录，调用时需 `cd` 或用绝对路径：
  - 校验：`python3 modules/resume-builder/scripts/validate.py <resume.yaml>`
  - 渲染：`python3 modules/resume-builder/scripts/render.py <resume.yaml> --out-dir ./resume/out --pdf`
  - Holland 评分：`python3 modules/career-planner/scripts/score_holland.py <answers.yaml>`
  - JD 匹配：`python3 modules/resume-optimizer/scripts/jd_match.py <resume.yaml> --jd <jd.txt>`
  - Bullet 诊断：`python3 modules/resume-optimizer/scripts/bullet_rewrite.py <resume.yaml>`
  - ATS 检查：`python3 modules/resume-optimizer/scripts/ats_check.py <resume.yaml>`
