---
name: resume-toolkit
description: 中文简历生成 + 求职优化专家。11 套主题简历渲染、PDF 导出；JD 关键词匹配、ATS 检查、Bullet 量化改写。触发词：写简历、做简历、生成简历、简历模板、resume、CV、导出 PDF、预览简历、换主题、修改简历、发飞书、匹配 JD、ATS 检查、简历优化、量化改写、简历诊断。
author: 袁箐鸿
---

# Resume Toolkit

专注中文简历领域的专家级工具包：从「对话生成简历」到「求职强化」的完整链路。

## 模块一览

| 模块 | 路径 | 定位 |
|---|---|---|
| **resume-builder** | [modules/resume-builder/MODULE.md](modules/resume-builder/MODULE.md) | 对话收集 → YAML 生成 → Schema 校验 → HTML/PDF/JSON 多端导出 |
| **resume-optimizer** | [modules/resume-optimizer/MODULE.md](modules/resume-optimizer/MODULE.md) | JD 匹配 → Bullet 量化改写 → 中文 ATS 检查 |

## 路由规则

根据用户意图选择加载哪个模块的完整文档：

### → resume-builder

触发词：写简历、做简历、生成简历、简历模板、resume、CV、导出 PDF、预览简历、换主题、修改简历、发飞书、简历发飞书、分享简历、发给导师、发给 HR

加载：[modules/resume-builder/MODULE.md](modules/resume-builder/MODULE.md)

### → resume-optimizer

触发词：匹配 JD、JD 匹配、关键词覆盖率、这个岗位合适吗、ATS 检查、简历体检、格式合规、量化改写、改 bullet、优化经历描述、简历诊断、简历优化

加载：[modules/resume-optimizer/MODULE.md](modules/resume-optimizer/MODULE.md)

### 联动场景

典型链路：`resume-builder 生成 → resume-optimizer 强化 → resume-builder 重渲染`。用户先通过对话生成简历，再用 optimizer 做 JD 匹配和 ATS 检查，修复后重新渲染。

## 模块间共享约定

- 用户工作目录结构：
  ```
  ./resume/resume.yaml           ← resume-builder 输入
  ./resume/out/resume.html|pdf   ← resume-builder 产出
  ```
- 脚本路径均相对于各自模块目录，调用时需 `cd` 或用绝对路径：
  - 校验：`python3 modules/resume-builder/scripts/validate.py <resume.yaml>`
  - 渲染：`python3 modules/resume-builder/scripts/render.py <resume.yaml> --out-dir ./resume/out --pdf`
  - JD 匹配：`python3 modules/resume-optimizer/scripts/jd_match.py <resume.yaml> --jd <jd.txt>`
  - Bullet 诊断：`python3 modules/resume-optimizer/scripts/bullet_rewrite.py <resume.yaml>`
  - ATS 检查：`python3 modules/resume-optimizer/scripts/ats_check.py <resume.yaml>`
