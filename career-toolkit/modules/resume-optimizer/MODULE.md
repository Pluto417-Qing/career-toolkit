# Resume Optimizer

对已有简历做「求职强化」—— 聚焦三个国内最实用的原子能力。

## 三项原子 Skill

| # | 名称 | 触发词 | 输入 | 输出 |
|---|------|--------|------|------|
| 1 | **JD 匹配** | 帮我匹配 JD、这个岗位我合适吗、关键词覆盖率 | JD 文本 + resume.yaml | 覆盖率报告 + 缺失技能清单 + 优先补齐建议 |
| 2 | **Bullet 量化改写** | 帮我改 bullet、量化改写、优化经历描述 | resume.yaml 中的 highlights | 逐条改写对照 + 追问量化数据 |
| 3 | **中文 ATS 检查** | ATS 检查、简历体检、格式合规吗 | resume.yaml（或 PDF/HTML） | 逐项合规报告 + 修复建议 |

## 何时使用

用户已经有简历（`resume.yaml` 或粘贴的文本/PDF），想要：
- 检验简历和特定岗位 JD 的匹配度
- 让经历描述更具说服力（量化、结构化）
- 确保简历在国内 ATS 系统中被正确解析

不覆盖：从零生成简历（交给 `resume-builder`）；职业方向选择（交给 `career-planner`）。

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

## Skill 2：Bullet 量化改写

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

## Skill 3：中文 ATS 检查

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
- Bullet 改写和 ATS 修复完成后，Agent 直接更新 `resume.yaml`，可立即调用 `resume-builder` 重新渲染
- 典型链路：`resume-builder 生成 → resume-optimizer 强化 → resume-builder 重渲染`

## 目录导航

- [references/jd-match.md](references/jd-match.md) — JD 关键词提取与匹配规则
- [references/bullet-rewrite.md](references/bullet-rewrite.md) — Bullet 诊断与改写规则
- [references/ats-check.md](references/ats-check.md) — 中文 ATS 检查规则表
- [scripts/jd_match.py](scripts/jd_match.py) — JD 匹配脚本
- [scripts/bullet_rewrite.py](scripts/bullet_rewrite.py) — Bullet 诊断脚本
- [scripts/ats_check.py](scripts/ats_check.py) — ATS 检查脚本
