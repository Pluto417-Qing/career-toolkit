# Resume Toolkit Skill 功能与改动报告

> 对比基线：commit `5d21ec6`（聚焦简历领域重构）
> 报告生成时间：2026-08-03

---

## 一、当前功能全景

### 整体定位

面向**清华大学学生**的中文简历专家，覆盖「对话生成 → JD 贴合优化 → 双版本产出」完整链路。

### 两个模块

| 模块 | 路径 | 职责 |
|---|---|---|
| resume-builder | `modules/resume-builder/MODULE.md` | 对话收集 → YAML → Schema 校验 → 11 套主题 HTML/PDF/JSON 导出 |
| resume-optimizer | `modules/resume-optimizer/MODULE.md` | JD 解析 → 三层匹配 → 关键词融入 → Bullet 改写 → ATS 检查 → 双版本生成 |

### resume-builder 功能

- **11 套主题**：academic / classic / compact / creative / elegant / executive / infographic / metro / minimal / modern / tech
- **多端导出**：HTML、PDF、Markdown、JSON
- **清华特色资产**（新增）：
  - `assets/tsinghua/departments.yaml` — 院系核心课程映射
  - `assets/tsinghua/experience_types.yaml` — SRT/国创/挑战杯/实验室科研等写作模板
  - `assets/tsinghua/scholarships.yaml` — 奖学金命名规范与排序
  - `assets/examples/thu-cs-grad.yaml` — 清华计算机系应届生完整示例
- **Schema 校验**：`assets/schema/resume.schema.json`

### resume-optimizer 六项原子能力

| # | 脚本 | 功能 | 触发词 |
|---|---|---|---|
| 0 | `scripts/jd_optimize.py` | **双版本生成**（通用版 + JD 适配版） | 一键优化、贴合 JD |
| 1 | `scripts/jd_parser.py` | JD 解析：去噪、分段、拆需求、分类、质量评分 | 解析 JD |
| 2 | `scripts/jd_match.py` | **三层匹配**：关键词+同义词 / 概念 / 证据 | 匹配 JD、覆盖率 |
| 3 | `scripts/jd_integrate.py` | **关键词自然融入**：5 种策略 + 置信度 + 堆砌检测 | JD 融入 |
| 4 | `scripts/bullet_rewrite.py` | Bullet 诊断：NO_VERB/NO_QUANT/TOO_SHORT/DUTY_LIST + 改写建议 | 量化改写 |
| 5 | `scripts/ats_check.py` | 中文 ATS：学校缩写、日期格式、必填字段等 | ATS 检查 |

### 核心场景：双版本生成

```
resume.yaml + jd.txt
  → jd_match（三层匹配 + gap 分类）
  → jd_integrate（融入建议 + 置信度）
  → bullet_rewrite（Bullet 诊断）
  → ats_check（ATS 检查）
  → build_general_version（通用版：只修 Bullet）
  → build_jd_version（JD 版：通用版 + 关键词融入 + label/skill 调整）
  → detect_exaggeration（夸大风险检测）
  → 输出：resume-general.yaml + resume-jd.yaml + 对比报告
```

**两版差异**：

| 版本 | 文件 | 处理 | 适用 |
|---|---|---|---|
| 通用版 | resume-general.yaml | 仅修 Bullet（补动词，弱动词替换而非叠加） | 海投 |
| JD 适配版 | resume-jd.yaml | 通用版 + 关键词分级融入 + label 调整 + 推断技能组 | 精投 |

### 不编造原则（核心约束）

关键词融入按编造风险**分级**：

| 级别 | 策略 | 处理 | 原因 |
|---|---|---|---|
| 可自动 | explicit + confidence≥0.9 | 仅补规范名 `（相关技术：X）` | tech 列表已有同义词，不改语义 |
| 需确认 | tech_list / enrich / summary | 生成提问清单，**不写入简历** | 涉及「基于 X 优化」「使用 X 实现」等动作声明 |
| 禁止 | new_context | 归入提问清单 | 需新增整条 bullet，构成编造经历 |

**夸大风险检测**：扫描「精通/资深/千万级/海量」等措辞，报告中标注位置+改写建议，不自动修改，需候选人佐证。

### 测试覆盖

45 个单元测试全部通过：

| 测试文件 | 用例数 |
|---|---|
| `tests/test_jd_parser.py` | 7 |
| `tests/test_jd_match.py` | 13 |
| `tests/test_jd_integrate.py` | 8 |
| `tests/test_bullet_rewrite.py` | 10 |
| `tests/test_ats_check.py` | 7 |

---

## 二、与一版的改动对比

分界点：commit `5d21ec6`（refactor: 聚焦简历领域）。此前为"一版"，此后为本轮迭代。

### 1. 模块结构改动

| 一版（career-toolkit） | 当前（resume-toolkit） |
|---|---|
| 3 个模块：career-planner + resume-builder + resume-optimizer | 2 个模块：resume-builder + resume-optimizer |
| 定位「一站式职业发展」 | 定位「清华简历专家」 |

**删除**：整个 `career-planner` 模块（-1518 行）
- Holland 测评、MBTI 测评
- 路径规划（就业/考研/考公/留学）
- profile.yaml 画像收集
- 行动报告可视化

### 2. resume-optimizer 改动（核心）

#### 新增脚本（4 个）

| 脚本 | 行数 | 功能 |
|---|---|---|
| `scripts/jd_parser.py` | ~396 | JD 解析器：去噪、分段、拆需求、分类、质量评分 |
| `scripts/jd_integrate.py` | ~400 | 关键词自然融入：5 种策略（explicit/tech_list/enrich/summary/new_context）+ 置信度 + 堆砌检测 |
| `scripts/jd_optimize.py` | ~700 | 双版本生成编排：通用版 + JD 适配版 + 对比报告 + 夸大检测 |
| `tests/` | 5 个文件 | 45 个单元测试 |

#### 新增资产（3 个）

| 文件 | 内容 |
|---|---|
| `assets/synonyms.yaml` | 200+ 组同义词（react↔React.js 等） |
| `assets/concepts.yaml` | 概念映射（高并发↔QPS、分布式↔微服务） |
| `assets/university_names.yaml` | 70+ 所高校缩写表（ATS 用） |

#### 升级脚本

| 脚本 | 一版 | 当前 |
|---|---|---|
| jd_match.py | 关键词+同义词匹配 | **三层匹配**：关键词+同义词 / 概念 / 证据；jieba 分词；gap 分类（evidence/partial/real） |
| bullet_rewrite.py | 26 个动词 | 80+ 个动词分 5 类；改写提示；NO_VERB 修复（弱动词替换） |
| ats_check.py | 基础规则 | 新增 5 条规则；学校缩写表外置 |

### 3. resume-builder 改动

- **新增清华特色资产**：3 个 yaml（departments / experience_types / scholarships）+ 1 个示例简历
- `references/writing-tips.md` 升级：加入清华经历写作指引

### 4. 核心能力升级路径

```
一版（career-toolkit）
  ├─ career-planner（Holland/MBTI/路径规划）  ❌ 砍掉
  ├─ resume-builder（11 主题渲染）
  └─ resume-optimizer
       ├─ jd_match（关键词+同义词）
       ├─ bullet_rewrite（26 动词）
       └─ ats_check（基础）

当前（resume-toolkit）
  ├─ resume-builder + 清华特色资产  ✅ 增强
  └─ resume-optimizer
       ├─ jd_parser         ✨ 新增
       ├─ jd_match          🔧 升级（三层匹配 + gap 分类）
       ├─ jd_integrate      ✨ 新增（5 策略 + 置信度）
       ├─ bullet_rewrite    🔧 升级（80+ 动词 + 弱动词替换）
       ├─ ats_check         🔧 升级（学校表 + 5 新规则）
       ├─ jd_optimize       ✨ 新增（双版本生成 + 不编造分级 + 夸大检测）
       └─ tests             ✨ 新增（45 测试）
```

### 5. 数据规模

- **代码变更**：+4878 / -1518 行
- **新增文件**：19 个（脚本 4 + 测试 5 + 资产 6 + demo 4）
- **删除文件**：12 个（career-planner 全部）
- **测试**：0 → 45 个用例全通过

---

## 三、设计取舍说明

1. **砍掉 career-planner**：用户明确要求「不希望是 AGI，希望在一个领域做到最好」。Holland/MBTI/路径规划偏离简历核心，删除以聚焦。

2. **双版本生成**：用户明确要求「生成两份，一份通用一份面向特定 JD，JD 版基于通用版」。通用版只修 Bullet 不碰 JD，JD 版继承通用版后深度适配。

3. **不编造原则**：用户明确要求「简历内容不可编造，若需要请多提问」。关键词融入分级，动作声明类一律需候选人确认；新增 bullet 禁止自动生成；夸大措辞检测并要求佐证。

4. **清华特色**：用户明确要求「面向清华同学，符合学校特点」。院系课程、经历类型、奖学金体系均定制。

---

## 四、本次分支提交文件清单

（按分支：`refactor/focus-resume-only`，commit 合并自提交 5d21ec6 至当前）

### 脚本改动

- `modules/resume-optimizer/scripts/jd_optimize.py` — 双版本生成编排 + 不编造分级 + 夸大检测
- `modules/resume-optimizer/scripts/jd_integrate.py` — 关键词自然融入引擎
- `modules/resume-optimizer/scripts/jd_match.py` — 三层匹配 + gap 分类
- `modules/resume-optimizer/scripts/jd_parser.py` — JD 解析器
- `modules/resume-optimizer/scripts/bullet_rewrite.py` — 动词库扩充 + 弱动词替换
- `modules/resume-optimizer/scripts/ats_check.py` — 规则扩充 + 学校缩写表

### 资产新增

- `modules/resume-optimizer/assets/concepts.yaml`
- `modules/resume-optimizer/assets/synonyms.yaml`
- `modules/resume-optimizer/assets/university_names.yaml`
- `modules/resume-builder/assets/tsinghua/departments.yaml`
- `modules/resume-builder/assets/tsinghua/experience_types.yaml`
- `modules/resume-builder/assets/tsinghua/scholarships.yaml`
- `modules/resume-builder/assets/examples/thu-cs-grad.yaml`

### 测试新增

- `modules/resume-optimizer/tests/test_jd_parser.py`
- `modules/resume-optimizer/tests/test_jd_match.py`
- `modules/resume-optimizer/tests/test_jd_integrate.py`
- `modules/resume-optimizer/tests/test_bullet_rewrite.py`
- `modules/resume-optimizer/tests/test_ats_check.py`

### 文档

- `SKILL.md` — 更新为 resume-toolkit 定位
- `modules/resume-optimizer/MODULE.md` — 双版本流程 + 不编造原则 + 夸大检测
- `modules/resume-builder/MODULE.md` — 清华特色资产说明
- `docs/SKILL_CHANGES_REPORT.md`（本文件）— 功能总览 + 改动对比

### Demo 数据

- `demo/resume-demo.yaml`
- `demo/resume-weak.yaml`
- `demo/jd-bytedance.txt`
- `demo/match.json` / `demo/integrate.json`
- `demo/optimized.yaml` / `demo/optimized-weak.yaml`
