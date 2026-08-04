# Resume Optimizer

对已有简历做「求职强化」—— 聚焦四个国内最实用的原子能力，外加一个一键编排入口。

## 五项原子 Skill

| # | 名称 | 触发词 | 输入 | 输出 |
|---|------|--------|------|------|
| 0 | **一键优化** | 帮我优化简历贴合这个 JD、一键适配 | JD 文本 + resume.yaml | **优化后 resume.yaml + 小报告** |
| 1 | **JD 匹配** | 帮我匹配 JD、这个岗位我合适吗、关键词覆盖率 | JD 文本 + resume.yaml | 三层匹配报告 + gap 分类 + 改写建议 |
| 2 | **JD 关键词融入** | 把 JD 关键词融入简历、帮我改得贴合 JD | 匹配结果 match.json + resume.yaml | 自然改写建议（不堆砌）+ 置信度 |
| 3 | **Bullet 量化改写** | 帮我改 bullet、量化改写、优化经历描述 | resume.yaml 中的 highlights | 逐条改写对照 + 追问量化数据 |
| 4 | **中文 ATS 检查** | ATS 检查、简历体检、格式合规吗 | resume.yaml（或 PDF/HTML） | 逐项合规报告 + 修复建议 |

## Skill 0：双版本生成（jd_optimize.py）

### 定位

> 用户给了简历 + JD，要的不是分析报告，而是「直接给我两份改好的简历」。

这是简历生成的核心场景。jd_optimize.py 生成**两份**简历：

| 版本 | 文件名 | 做了什么 | 适用场景 |
|------|--------|---------|---------|
| **通用版** | resume-general.yaml | 仅修 Bullet 基础问题（补动词），不碰 JD | 多岗位投递 |
| **JD 适配版** | resume-jd.yaml | 通用版 + JD 关键词融入 + 内容侧重调整 | 针对该岗位投递 |

### 生成流程

```
resume.yaml + jd.txt
  → jd_match（三层匹配 + gap 分类）
  → jd_integrate（关键词融入建议）
  → bullet_rewrite（量化诊断）
  → ats_check（ATS 检查）
  → 生成通用版（只修 Bullet）
  → 生成 JD 适配版（通用版 + JD 深度适配）
  → 输出：resume-general.yaml + resume-jd.yaml + 小报告
```

### 两版区别

**通用版**：
- 修复 NO_VERB（缺少动词的 bullet 自动补动词，弱动词替换而非叠加）
- 不融入 JD 关键词
- 不调整求职意向
- 适合海投

**JD 适配版**（基于通用版）：
- 融入 evidence_gap 关键词（**分级应用，见下**）
- 调整求职意向体现目标岗位
- 补充领域经验技能组（JD 命中的概念，标注「推断」需核对）
- 适合精准投递

### 不编造原则（核心约束）

简历内容**绝不编造**。关键词融入按编造风险分级：

| 级别 | 策略 | 处理方式 | 原因 |
|------|------|---------|------|
| **可自动** | explicit + confidence ≥ 0.9 | 仅补规范名（`（相关技术：X）`） | bullet 的 tech 列表已有同义词，不改语义 |
| **需确认** | tech_list / enrich / summary | 生成提问清单，**不写入简历** | 涉及「基于 X 优化」「使用 X 实现」等动作声明 |
| **禁止** | new_context | 归入确认清单提问 | 需新增整条 bullet，构成编造经历 |

skills 补充的概念标注「（推断）」并加入确认清单——非候选人自述，需人工核对。

### 夸大风险检测

扫描原简历和 JD 版，检测以下措辞并在报告中提示：

- **高风险词**：精通、熟练掌握、资深、专家、深入研究、深度精通
- **中风险词**：千万级、亿级、百万级、海量、极致、完美、巨大、显著提升

每条提示包含位置、原词、风险级别和改写建议。夸大措辞不会自动修改，只在报告中标注，需候选人提供佐证。

### 报告输出

报告包含以下章节：
1. 生成概况（覆盖、修改数、需确认数、夸大提示数）
2. 通用版修改（仅 Bullet 修复）
3. JD 适配版修改（自动融入 + label/skill 调整）
4. **需候选人确认**（按风险分级，未确认前不写入简历）
5. **夸大风险提示**（原简历中的可疑措辞）
6. 无法填补的 gap（real_gap，不虚构）
7. Bullet 剩余问题（需手动改写）

### 调用脚本

```bash
python3 scripts/jd_optimize.py resume.yaml --jd jd.txt --out-dir ./output
```

输出：
- `output/resume-general.yaml` — 通用版
- `output/resume-jd.yaml` — JD 适配版
- 小报告（打印到 stdout）

## 何时使用

用户已经有简历（`resume.yaml` 或粘贴的文本/PDF），想要：
- 检验简历和特定岗位 JD 的匹配度
- 让经历描述更具说服力（量化、结构化）
- 确保简历在国内 ATS 系统中被正确解析

不覆盖：从零生成简历（交给 `resume-builder`）。

---

## Skill 1：JD 匹配

### 工作流

1. **接收 JD**：用户粘贴岗位描述（或给出链接，Agent 提取正文）
2. **提取 JD 关键词**：调用脚本提取结构化需求
3. **与简历交叉匹配**：逐项对比，输出覆盖率
4. **生成报告**：

```
## JD 匹配报告

**岗位**：{title} @ {company}
**整体关键词覆盖率**：{covered}/{total} = {percent}%

### ✅ 已覆盖（{n} 项）
- React — 出现在 skills.keywords + projects.tech
- ...

### ❌ 缺失（{n} 项）
| 关键词 | 重要度 | 补齐建议 |
|--------|--------|----------|
| Kubernetes | 高（JD 出现 3 次） | 建议在 projects 中补充容器化部署经历 |
| ...

### 🎯 优先行动
1. ...（最多 3 条，按投入产出比排序）
```

### 调用脚本

```bash
python3 scripts/jd_match.py <resume.yaml> --jd <jd.txt>
```

脚本输出 JSON，Agent 负责格式化为上述报告呈现给用户。

### 关键词提取规则

详见 [references/jd-match.md](references/jd-match.md)。

---

## Skill 2：JD 关键词自然融入

### 核心理念

> **不是把关键词塞进简历，而是让已有经历自然地体现 JD 要求。**

五条原则：
1. 关键词融入已有经历，不新增虚假经历
2. 单条 bullet 最多融入 1 个新关键词，避免堆砌
3. 融入后的句子必须语义通顺，不能生硬插入
4. 优先融入「相关度最高」的经历段
5. 标注置信度，低置信度的建议需用户确认

### 工作流

1. **先跑 JD 匹配**，生成 `match.json`
2. **读取 evidence_gap 列表**（有相关经历但没写出来的关键词）
3. **对每个 gap，在简历中找最佳融入位置**：
   - 相关度评分（0-1）：已有同义词 > tech 列表关联 > 文本关联 > summary 关联 > 无关联
4. **生成改写建议**，标注策略和置信度
5. **堆砌检测**：如果同一 bullet 被建议融入多个关键词，警告并只推荐 1 个

### 五种融入策略

| 策略 | 含义 | 置信度 | 示例 |
|------|------|--------|------|
| explicit | 已有同义词，只需写规范名 | 0.9 | 简历有 Docker，JD 要 K8s → 补写 Kubernetes |
| tech_list | tech 列表有关联技术 | 0.7 | 简历有 Spring Cloud，JD 要微服务 |
| enrich | 文本有概念关联词 | 0.6 | 简历有「限流」，JD 要高并发 |
| summary | summary 有关联内容 | 0.5 | summary 提了性能优化，JD 要调优 |
| new_context | 需新增一条 bullet | 0.3 | 需用户确认是否有真实经历 |

### 调用脚本

```bash
# 先跑匹配
python3 scripts/jd_match.py resume.yaml --jd jd.txt > match.json
# 再跑融入
python3 scripts/jd_integrate.py resume.yaml --match match.json
```

### 输出格式

```
## JD 关键词融入建议

### 🟢 高置信度（直接可用）
1. **Kubernetes** → work[0] 字节跳动
   - 策略：显式补写（简历 tech 已有 Docker）
   - 原文：独立完成 30+ 广告投放场景的 schema 化改造
   - 建议：独立完成 30+ 广告投放场景的 schema 化改造，基于 Kubernetes 部署

### 🟡 中置信度（建议确认）
2. **微服务** → projects[0] SRT项目
   - 策略：丰富描述
   - 建议：补充「使用微服务架构拆分模块」

### ⚠️ 堆砌警告
work[0] 的 bullet[0] 被建议融入 2 个关键词（Kubernetes, 微服务），建议只选 1 个最相关的

### ❌ 无法融入
3. **Kafka** — 简历无相关经历，不建议虚构
```

---

## Skill 3：Bullet 量化改写

### 工作流

1. **定位 bullets**：从 `resume.yaml` 读取所有 `highlights` 字段
2. **逐条诊断**：识别"形容词式/职责式/模糊式"描述
3. **改写建议**：给出改写版本，标注需要用户补充的量化数据占位符 `[?]`
4. **交互确认**：用户补充数据后，Agent 更新 `resume.yaml`

### 输出格式

```
## Bullet 量化改写

### work[0] — 字节跳动 / 前端实习

| # | 原文 | 问题 | 改写建议 |
|---|------|------|----------|
| 1 | 参与了广告投放系统的开发 | 无动词主语、无量化、无结果 | **主导**广告投放系统 [模块名] 开发，覆盖 [?] 个投放场景，CTR 提升 [?]% |
| 2 | ... | ... | ... |

> 💡 标记 [?] 的地方需要你补充具体数字，回复我即可更新简历。
```

### 诊断规则

详见 [references/bullet-rewrite.md](references/bullet-rewrite.md)。

---

## Skill 4：中文 ATS 检查

### 工作流

1. **读取简历**：从 `resume.yaml` 加载结构化数据
2. **逐项检查**：按规则表逐条检测
3. **输出报告**：

```
## ATS 合规检查报告

**总计**：{total} 项检查，✅ {pass} 通过，⚠️ {warn} 警告，❌ {fail} 不通过

| # | 检查项 | 状态 | 说明 | 修复建议 |
|---|--------|------|------|----------|
| 1 | 姓名字段 | ✅ | — | — |
| 2 | 时间格式统一 | ❌ | work[1].start 为 "2023年3月"，其余为 "2023.03" | 统一为 YYYY.MM 格式 |
| ...

### 高优修复（必须改）
1. ...

### 建议优化（改了更好）
1. ...
```

### 调用脚本

```bash
python3 scripts/ats_check.py <resume.yaml>
```

### 检查规则

详见 [references/ats-check.md](references/ats-check.md)。

---

## 联动 resume-builder

- 本模块的输入是 `resume-builder` 的产出（`resume.yaml`）
- **双版本生成**完成后，两份 YAML 都可调用 `resume-builder` 渲染为 PDF
- 典型链路：
  ```
  resume-builder 对话收集 → resume.yaml
    → jd_optimize 双版本生成
      → resume-general.yaml（通用版）
      → resume-jd.yaml（JD 适配版）
    → resume-builder 分别渲染为 PDF
  ```

## 目录导航

- [references/jd-match.md](references/jd-match.md) — JD 三层匹配规则与 Gap 分类
- [references/bullet-rewrite.md](references/bullet-rewrite.md) — Bullet 诊断与改写规则
- [references/ats-check.md](references/ats-check.md) — 中文 ATS 检查规则表
- [scripts/jd_optimize.py](scripts/jd_optimize.py) — 一键优化编排脚本
- [scripts/jd_match.py](scripts/jd_match.py) — JD 三层匹配脚本
- [scripts/jd_parser.py](scripts/jd_parser.py) — JD 解析器
- [scripts/jd_integrate.py](scripts/jd_integrate.py) — JD 关键词自然融入脚本
- [scripts/bullet_rewrite.py](scripts/bullet_rewrite.py) — Bullet 诊断脚本
- [scripts/ats_check.py](scripts/ats_check.py) — ATS 检查脚本
- [assets/synonyms.yaml](assets/synonyms.yaml) — 同义词库（200+ 组）
- [assets/concepts.yaml](assets/concepts.yaml) — 概念映射库（25 组）
- [assets/university_names.yaml](assets/university_names.yaml) — 高校缩写表（70+ 所）
