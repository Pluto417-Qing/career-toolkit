# JD 匹配规则

## 整体架构

```
原始 JD 文本                     简历 resume.yaml
     ↓                                ↓
JD 解析器                         能力提取
  · 噪音清洗                        · 关键词提取（按 section 分组）
  · 段落识别                        · 概念检测（全文匹配概念关联词）
  · 需求拆解                        · 证据提取（年限/学历/管理/量化）
  · 需求分类
  · 质量评分
     ↓                                ↓
     └──────── 三层匹配引擎 ────────────┘
                   ↓
           Gap 分类 + 改写建议
```

## JD 获取方式

用户可以通过以下方式提供 JD：

1. **直接粘贴**（最常用）：用户在对话中粘贴 JD 文本，Agent 保存为 `jd.txt` 后调用脚本
2. **URL 提取**：用户给出招聘页面 URL，Agent 用 WebFetch 抓取正文，去掉导航/广告/推荐列表后保存
3. **文件路径**：用户已有 JD 文件，直接传路径

无论哪种来源，JD 都先过解析器清洗。

## JD 标准化管道

### ① 噪音清洗

过滤掉无关内容：
- 公司介绍 / 关于我们
- 薪资福利 / 办公环境
- 投递方式 / 联系方式
- 空行 / 分隔线 / emoji 装饰

### ② 段落识别

| 段落 | 正则匹配 | 权重 |
|------|----------|------|
| 任职要求 | `任职要求\|岗位要求\|必备条件\|Required` | ×2.0 |
| 加分项 | `加分项\|优先考虑\|Preferred\|Bonus` | ×0.5 |
| 岗位职责 | `岗位职责\|工作内容\|你将负责` | ×1.0 |
| 未分类 | 不匹配以上 | ×1.0 |

### ③ 需求拆解

把段落内容拆成独立需求条目：
- 支持数字编号（`1. 2. 3.` / `1、2、3、`）
- 支持 bullet 符号（`• - * ●`）
- 支持分号分隔（`；` `;`）

### ④ 需求分类

| 类型 | 检测规则 | 示例 |
|------|----------|------|
| skill | 默认类型，技术/领域关键词 | React, 高并发, 机器学习 |
| experience | 含「N年」模式 | 3年以上开发经验 |
| education | 含学历关键词 | 本科及以上 |
| certification | 含证书关键词 | PMP, CPA, AWS认证 |
| soft_skill | 含软技能关键词且无英文技术词 | 良好的沟通能力 |

### ⑤ 质量评分

| 检查项 | 扣分 | 说明 |
|--------|------|------|
| 要求条目 < 3 | -20 | JD 可能不完整 |
| 要求条目 < 5 | -10 | 可能有遗漏 |
| 无技术技能要求 | -15 | 像废话 JD |
| 无年限要求 | -5 | 建议补充 |
| 模糊要求占比 > 70% | -15 | 「熟悉互联网技术」式废话过多 |

---

## 三层匹配引擎

### Layer 1：关键词 + 同义词匹配

同义词库外置在 [assets/synonyms.yaml](../assets/synonyms.yaml)，200+ 组同义词。

匹配来源（按优先级）：
1. `skills[].keywords` — 直接命中
2. `projects[].tech` — 项目技术栈命中
3. `work[].highlights` + `projects[].highlights` — 全文检索命中
4. `education[].courses` — 课程名命中

### Layer 2：概念匹配

概念库外置在 [assets/concepts.yaml](../assets/concepts.yaml)，25 个概念组。

**概念不是同义词，而是包含关系：**

| JD 中的概念 | 简历中匹配的关联词 |
|------------|-------------------|
| 高并发 | QPS, TPS, 万级, 百万级, 限流, 降级, 熔断 |
| 分布式 | 微服务, RPC, gRPC, 分布式锁, 负载均衡 |
| 大数据 | Spark, Hive, Hadoop, Flink, 数据仓库 |
| 团队管理 | 带领, 管理, leader, mentor, 招聘 |
| 机器学习 | ML, 模型训练, 特征工程, 推荐算法 |
| 性能优化 | 调优, JVM调优, 慢查询, 索引优化 |
| 容器化 | Docker, K8s, Helm, 容器编排 |

当 Layer 1 未匹配时，检查 JD 关键词是否属于简历已体现的某个概念。

### Layer 3：证据匹配

对非技能类需求（年限/学历/管理），直接检查简历中的硬性证据：

| JD 要求 | 简历检查项 | 方法 |
|---------|-----------|------|
| 3年经验 | `work[].start-end` 时间跨度 | 计算所有 work 段的总月数 |
| 本科及以上 | `education[].degree` 学历等级 | 映射为等级比较 |
| 团队管理经验 | highlights 中是否有管理类动词 | 检测「带领/管理/组长」等 |
| 高并发经验 | highlights 中是否有量化指标 | 检测 QPS/用户数等数字 |
| GitHub/开源 | profiles 中是否有 GitHub 链接 | 检查 URL |

---

## Gap 分类

对每个未匹配的 JD 需求，分为三类：

### evidence_gap（有但没写）— 🟡 最有价值

**定义：** 简历有相关经历，但没有明确写出来。

**检测逻辑：**
1. JD 关键词的子串出现在简历某个 section 的 term 中
2. JD 关键词出现在简历全文中（但不在结构化字段里）
3. JD 关键词属于某个概念，且简历已体现该概念

**输出示例：**
```
🟡 evidence_gap: Kubernetes
   suggestion: 简历中已有相关内容（tech: Docker），建议明确写出「Kubernetes」并补充使用场景和规模
```

**为什么最有价值：** 用户只需要在现有经历中补充几个关键词，不需要新增经历。这是改动最小、效果最大的优化。

### partial_gap（部分匹配）

**定义：** 有相关但不完全对口的经验。

**检测逻辑：** 概念匹配命中但关键词不匹配，说明有概念级经验但缺乏具体技术点。

### real_gap（真的没有）— 🔴

**定义：** 简历完全没有相关经历，也不属于任何已体现的概念。

**输出示例：**
```
🔴 real_gap: Kafka
   简历中未找到任何 Kafka 或消息队列相关经历
```

---

## 输出格式

```json
{
  "overall_score": 72.0,
  "dimension_scores": {
    "技术栈匹配": 85.0,
    "经验学历": 100.0
  },
  "total_keywords": 20,
  "covered_count": 14,
  "missing_count": 6,
  "coverage_percent": 70.0,
  "covered": [...],
  "missing": [...],
  "gap_summary": {
    "evidence_gap": 3,
    "partial_gap": 0,
    "real_gap": 3
  },
  "evidence_gaps": [...],
  "real_gaps": [...],
  "rewrite_suggestions": [
    {
      "keyword": "Kubernetes",
      "section": "required",
      "suggestion": "简历中已有相关内容（tech: Docker），建议明确写出「Kubernetes」并补充使用场景和规模"
    }
  ],
  "resume_evidence": {
    "work_years": 1.5,
    "degree_level": 2,
    "has_github": true,
    "has_management": false,
    "has_quant_metrics": true,
    "concepts_matched": ["高并发", "微服务架构", "性能优化"]
  }
}
```

---

## Agent 呈现指南

Agent 拿到 JSON 后，按以下结构呈现给用户：

```
## JD 匹配报告

**综合贴合度：72/100**

### 维度得分
- 技术栈匹配：85%
- 经验学历：100%

### ✅ 已覆盖（14 项）
- React — 出现在 skills + projects.tech
- 高并发 — 概念匹配（简历中体现了 QPS/限流等）
...

### 🟡 有但没写（3 项）— 补上这几个关键词就能提升覆盖率
1. Kubernetes — 简历有 Docker 经验，建议补充 K8s 使用场景
2. 微服务 — 简历有 Spring Cloud 经验，建议在 highlights 中明确提及
3. CI/CD — 简历有 Jenkins 经验，建议补充流水线描述

### 🔴 真正缺失（3 项）
1. Kafka — 简历未找到消息队列相关经历
...

### 📝 改写建议
1. 在「字节跳动 / 后端实习」的 highlights 中补充：
   「主导容器化部署，使用 Kubernetes 管理 20+ 节点集群」
2. ...
```
