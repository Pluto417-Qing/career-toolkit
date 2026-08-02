---
name: resume-toolkit
description: 面向清华大学学生的中文简历专家。11 套主题简历渲染、PDF 导出；JD 三层匹配、关键词自然融入、ATS 检查、Bullet 量化改写。触发词：写简历、做简历、生成简历、简历模板、resume、CV、导出 PDF、预览简历、换主题、修改简历、发飞书、匹配 JD、JD 匹配、JD 融入、贴合 JD、ATS 检查、简历优化、量化改写、简历诊断。
author: 袁箐鸿
---

# Resume Toolkit

面向**清华大学学生**的简历专家：从「对话生成简历」到「JD 贴合优化」的完整链路。内置清华院系课程体系、经历类型模板、奖学金规范。

## 模块一览

| 模块 | 路径 | 定位 |
|---|---|---|
| **resume-builder** | [modules/resume-builder/MODULE.md](modules/resume-builder/MODULE.md) | 对话收集 → YAML 生成 → Schema 校验 → HTML/PDF/JSON 多端导出 |
| **resume-optimizer** | [modules/resume-optimizer/MODULE.md](modules/resume-optimizer/MODULE.md) | JD 三层匹配 → 关键词自然融入 → Bullet 量化改写 → 中文 ATS 检查 |

## 路由规则

根据用户意图选择加载哪个模块的完整文档：

### → resume-builder

触发词：写简历、做简历、生成简历、简历模板、resume、CV、导出 PDF、预览简历、换主题、修改简历、发飞书、简历发飞书、分享简历、发给导师、发给 HR

加载：[modules/resume-builder/MODULE.md](modules/resume-builder/MODULE.md)

### → resume-optimizer

触发词：匹配 JD、JD 匹配、关键词覆盖率、这个岗位合适吗、JD 融入、贴合 JD、把 JD 关键词融入简历、ATS 检查、简历体检、格式合规、量化改写、改 bullet、优化经历描述、简历诊断、简历优化

加载：[modules/resume-optimizer/MODULE.md](modules/resume-optimizer/MODULE.md)

### 联动场景

典型链路：
```
resume-builder 生成简历
  → resume-optimizer: JD 匹配（三层匹配 + gap 分类）
  → resume-optimizer: JD 融入（自然改写，不堆砌）
  → resume-optimizer: Bullet 诊断（量化改写）
  → resume-optimizer: ATS 检查（格式修复）
  → resume-builder: 更新 YAML → 重新渲染
```

## 模块间共享约定

- 用户工作目录结构：
  ```
  ./resume/resume.yaml           ← resume-builder 输入
  ./resume/out/resume.html|pdf   ← resume-builder 产出
  ```
- 脚本路径均相对于各自模块目录，调用时需 `cd` 或用绝对路径：
  - 校验：`python3 modules/resume-builder/scripts/validate.py <resume.yaml>`
  - 渲染：`python3 modules/resume-builder/scripts/render.py <resume.yaml> --out-dir ./resume/out --pdf`
  - JD 解析：`python3 modules/resume-optimizer/scripts/jd_parser.py <jd.txt>`
  - JD 匹配：`python3 modules/resume-optimizer/scripts/jd_match.py <resume.yaml> --jd <jd.txt>`
  - JD 融入：`python3 modules/resume-optimizer/scripts/jd_integrate.py <resume.yaml> --match <match.json>`
  - Bullet 诊断：`python3 modules/resume-optimizer/scripts/bullet_rewrite.py <resume.yaml>`
  - ATS 检查：`python3 modules/resume-optimizer/scripts/ats_check.py <resume.yaml>`

## 清华特色资产

| 资产 | 路径 | 用途 |
|---|---|---|
| 院系课程映射 | [modules/resume-builder/assets/tsinghua/departments.yaml](modules/resume-builder/assets/tsinghua/departments.yaml) | 收集教育背景时推荐核心课程 |
| 经历类型模板 | [modules/resume-builder/assets/tsinghua/experience_types.yaml](modules/resume-builder/assets/tsinghua/experience_types.yaml) | SRT/国创/挑战杯/实验室科研等写作模板 |
| 奖学金体系 | [modules/resume-builder/assets/tsinghua/scholarships.yaml](modules/resume-builder/assets/tsinghua/scholarships.yaml) | 奖学金命名规范与排序 |
| 示例简历 | [modules/resume-builder/assets/examples/thu-cs-grad.yaml](modules/resume-builder/assets/examples/thu-cs-grad.yaml) | 清华计算机系应届生完整示例 |
