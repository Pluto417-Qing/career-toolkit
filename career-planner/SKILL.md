---
name: career-planner
description: 面向学生和职场新人的职业规划智能体。能力：(1) 引导式收集用户画像（教育、经历、技能、兴趣、约束）并落到结构化 profile.yaml；(2) 通过 Holland RIASEC 简版量表做兴趣测评并计算得分；(3) 基于测评结果与用户约束，给出「就业 / 读研 / 考研 / 保研 / 留学 / 考公」多路径可行性对比与个性化建议；(4) 输出 3-6-12 个月里程碑与关键节点日历的行动规划报告 career_plan.md；(5) 需要制作简历时声明式调用 resume-builder skill。适用场景：用户提到"职业规划、生涯规划、我该做什么工作、大学生迷茫、就业还是考研、考公规划、留学规划、Holland 测评、MBTI、找工作方向、毕业选择"或对未来方向感到迷茫时使用。
author: 袁箐鸿
---

# Career Planner

面向学生 / 职场新人的职业规划智能体。三步：**画像 → 测评 → 路径**，最终产出一份可执行的 12 个月规划报告。

## 何时使用

用户表达：
- "我不知道自己适合做什么 / 毕业该干什么"
- "帮我规划一下大学生涯 / 求职方向"
- "考研还是就业 / 大厂还是考公 / 国内还是留学"
- "帮我做个职业测评"
- 需要一份阶段性行动清单（3/6/12 个月）

不覆盖：
- 简历本身的生成与排版 → 声明式调用 `resume-builder` skill
- 岗位 JD 匹配、ATS 检查、bullet 量化 → 声明式调用 `resume-optimizer` skill（后续）

## 核心工作流

### Step 1：收集画像

在工作目录建 `./career/profile.yaml`（示例：[assets/examples/profile.yaml](assets/examples/profile.yaml)）。

**关键原则：分轮问，不要一次问 20 题**。详细策略见 [references/collect-profile.md](references/collect-profile.md)。

第一轮只问三件事：**当前身份 / 学校专业 / 大致想探索的方向**。有这些就能启动，后续再补齐。

### Step 2：测评

引导用户做 Holland RIASEC 简版（60 题，可拆成 3 组 20 题）：

1. 把题库读出来给用户看：[assets/assessments/holland-riasec.yaml](assets/assessments/holland-riasec.yaml)
2. 让用户以「题号: 分数（1-5）」形式回答，收集到 `./career/holland_answers.yaml`：
   ```yaml
   answers:
     1: 4
     2: 3
     ...
   ```
3. 打分：
   ```bash
   python3 scripts/score_holland.py ./career/holland_answers.yaml > ./career/holland_result.json
   ```
   输出结构：每维度 0-100 分、Holland Code（前 3 高维度）、建议方向。
4. 把 Code 回填到 `profile.yaml` 的 `assessment.holland`。

Holland Code 是**参考锚点，不是判决**——需要结合用户已有经历、约束与偏好综合解读。

### Step 3：路径规划

根据用户的 `goals.primary`（就业 / 读研 / 考公 / 出国），选择对应 playbook：

| 目标 | 参考文档 |
|---|---|
| 就业（校招 / 实习） | [references/path-playbooks/employment.md](references/path-playbooks/employment.md) |
| 读研（保研 / 考研 / 留学 / 直博） | [references/path-playbooks/graduate-school.md](references/path-playbooks/graduate-school.md) |
| 考公 / 事业单位 | [references/path-playbooks/civil-service.md](references/path-playbooks/civil-service.md) |

如果用户还未想清楚，一次给 **2-3 条路径的可行性对比**（不要 4 条以上，选项过多反而无法决策）。

对每条路径给出：
- 可行性评估（结合画像 + 测评 + 约束）
- 关键节点时间线
- 3-6-12 个月里程碑
- 需要立即启动的 2-3 个行动

产出：`./career/career_plan.md`。若用户明确要求"帮我生成飞书文档 / 报告"，用 `lark-doc` skill 把 markdown 发布成飞书文档。

### Step 4（可选）：生成简历

若用户希望"顺便做个简历"，声明式调用 `resume-builder` skill，把 `profile.yaml` 中的对应字段映射到 `resume.yaml`（映射对照见 SKILL 尾部）。

## 与其他 skill 的协作

- **`resume-builder`**：需要生成简历时使用；不要在本 skill 里重复实现 HTML/PDF 渲染。
- **`lark-doc`**：用户要发布规划报告为飞书文档时使用。
- **`lark-htmlbox`**：想在飞书报告里画路径对比图（雷达图 / 时间线）时使用。

## profile.yaml → resume.yaml 字段映射

| profile.yaml | resume.yaml |
|---|---|
| `basic.name` | `basics.name` |
| `basic.city` | `basics.location` |
| `education[]` | `education[]`（字段名基本一致） |
| `experiences[type=实习]` | `work[]`（type 保留） |
| `experiences[type=项目]` | `projects[]` |
| `experiences[type=科研]` | `research[]` |
| `skills.hard` | `skills[].keywords` |
| `skills.languages` | `languages[]` |
| `goals.primary/targets` | `basics.label` 或 `custom_sections[title=求职意向]` |

## 目录导航

- [assets/assessments/holland-riasec.yaml](assets/assessments/holland-riasec.yaml) — Holland 60 题
- [assets/examples/profile.yaml](assets/examples/profile.yaml) — profile 示例
- [references/collect-profile.md](references/collect-profile.md) — 画像收集策略
- [references/path-playbooks/](references/path-playbooks/) — 各路径 playbook
- [scripts/score_holland.py](scripts/score_holland.py) — Holland 打分脚本
