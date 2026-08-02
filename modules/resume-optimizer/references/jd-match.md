# JD 匹配规则

## 关键词提取策略

从 JD 文本中提取以下类别的关键词：

### 1. 硬技能（Hard Skills）

- **技术栈**：编程语言、框架、工具、平台（React, Go, K8s, Spark…）
- **领域能力**：算法、分布式系统、数据库优化、安全审计…
- **认证/标准**：PMP、CPA、AWS SA、等保…

提取信号：
- 出现在「岗位要求 / 任职资格 / 必备技能」段落的词权重 ×2
- 出现在「加分项 / 优先考虑」段落的词权重 ×1
- 同一关键词多次出现，权重按出现次数递增

### 2. 软技能 / 通用能力

- 沟通、团队协作、项目管理、抗压、自驱…
- 软技能在国内 JD 中普遍出现但区分度低，权重 ×0.5

### 3. 学历 / 经验门槛

- 学历要求：本科/硕士/博士
- 年限要求：X 年以上
- 行业偏好：互联网/金融/制造…

这部分不计入覆盖率评分，但作为「资格线」单独展示。

## 匹配逻辑

### 覆盖率计算

```
覆盖率 = 简历命中的硬技能关键词数 / JD 硬技能关键词总数
```

匹配来源（按优先级）：
1. `skills[].keywords` — 直接命中
2. `projects[].tech` — 项目技术栈命中
3. `work[].highlights` + `projects[].highlights` — 全文检索命中
4. `education[].courses` — 课程名命中（权重 ×0.5）

### 同义词归并

同义词库外置在 [assets/synonyms.yaml](../assets/synonyms.yaml)，当前覆盖 **200+ 组**同义词，包含：

- 编程语言（JavaScript/TypeScript/Python/Go/Rust…）
- 前端框架（React/Vue/Angular/Next.js…）
- 后端框架（Spring Boot/Django/FastAPI/Express…）
- 数据库（MySQL/PostgreSQL/MongoDB/Redis…）
- 消息队列/中间件（Kafka/RabbitMQ/Nginx…）
- 云原生/DevOps（Docker/K8s/CI-CD/Terraform…）
- 机器学习/AI（ML/DL/NLP/LLM/PyTorch…）
- 产品/运营（DAU/MAU/GMV/ROI/A-B测试…）
- 设计（UI/UX/Figma/Sketch…）
- 金融/财务（DCF/CPA/CFA/尽调…）

Agent 可根据上下文动态扩展同义词库——只需在 YAML 中追加新组即可。

### 重要度分级

| 级别 | 定义 | 示例 |
|------|------|------|
| 高 | 岗位核心能力，JD 中出现 ≥2 次或在「必备」段 | 岗位核心语言/框架 |
| 中 | 出现 1 次，在「要求」段 | 辅助工具链 |
| 低 | 仅在「加分」段或隐含提及 | 了解即可的技术 |

## 补齐建议生成规则

优先行动排序依据：
1. 重要度高 + 补齐成本低（已有相关经历只是没写上去）→ 最优先
2. 重要度高 + 需要新增经历/项目 → 建议补充描述或短期学习
3. 重要度中/低 → 仅列出，不作为行动项

输出格式见 MODULE.md。
