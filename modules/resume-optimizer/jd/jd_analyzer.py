"""JD 分析器。

解析职位描述，提取关键词、技能要求、概念关联。
"""

import re
from pathlib import Path
from typing import Optional

import yaml
import jieba

from .jd_types import Keyword, JDAnalysis, Requirements, ConceptMapping


class JDAnalyzer:
    """JD 分析器。"""

    def __init__(self, concept_config_path: str = None):
        """初始化分析器。

        参数：
            concept_config_path: 概念关键词配置文件路径
        """
        self.concept_config = self._load_concept_config(concept_config_path)
        self.concepts = self.concept_config.get("concepts", [])
        self.synonyms = self.concept_config.get("synonyms", {})
        self.weight_rules = self.concept_config.get("weight_rules", {})

    def analyze(self, jd_text: str) -> JDAnalysis:
        """分析 JD 文本。

        参数：
            jd_text: JD 文本

        返回：
            分析结果
        """
        # 清理文本
        cleaned_text = self._clean_text(jd_text)

        # 提取关键词
        required_keywords = self._extract_keywords(cleaned_text, "required")
        preferred_keywords = self._extract_keywords(cleaned_text, "preferred")
        soft_skills = self._extract_soft_skills(cleaned_text)

        # 提取要求
        requirements = self._extract_requirements(cleaned_text)

        # 构建概念映射
        concept_mapping = self._build_concept_mapping(
            required_keywords + preferred_keywords
        )

        # 计算质量评分
        quality_score = self._calculate_quality_score(cleaned_text, requirements)

        return {
            "meta": {
                "analyzed_at": self._get_timestamp(),
                "text_length": len(jd_text),
                "source": "auto",
            },
            "keywords": {
                "required": required_keywords,
                "preferred": preferred_keywords,
            },
            "soft_skills": soft_skills,
            "requirements": requirements,
            "concept_mapping": concept_mapping,
            "raw_text": jd_text,
            "quality_score": quality_score,
        }

    def analyze_file(self, jd_path: str) -> JDAnalysis:
        """从文件分析 JD。

        参数：
            jd_path: JD 文件路径

        返回：
            分析结果
        """
        with open(jd_path, "r", encoding="utf-8") as f:
            jd_text = f.read()
        return self.analyze(jd_text)

    # ═══════════════════════════════════════════
    # 文本清理
    # ═══════════════════════════════════════════

    def _clean_text(self, text: str) -> str:
        """清理 JD 文本。"""
        # 移除多余空白
        text = re.sub(r'\s+', ' ', text)
        # 移除特殊字符（保留中英文和常用符号），- 放在 [] 末尾避免被当作范围
        text = re.sub(r'[^\w\u4e00-\u9fff，。、；：""''（）\\s./+#-]', '', text)
        return text.strip()

    # ═══════════════════════════════════════════
    # 关键词提取
    # ═══════════════════════════════════════════

    def _extract_keywords(self, text: str, keyword_type: str) -> list[Keyword]:
        """提取关键词。

        参数：
            text: 清理后的文本
            keyword_type: required 或 preferred

        返回：
            关键词列表
        """
        keywords = []

        # 1. 从概念映射中查找核心技术关键词
        all_tech_keywords = self._get_all_tech_keywords()

        for tech_kw, synonyms in all_tech_keywords.items():
            # 检查关键词或同义词是否出现在文本中
            found = self._find_in_text(tech_kw, synonyms, text)
            if found:
                # 根据位置判断权重
                weight = self._determine_weight(found, text, keyword_type)
                keywords.append({
                    "keyword": tech_kw,
                    "weight": weight,
                    "synonyms": synonyms,
                    "category": self._get_category_for_keyword(tech_kw),
                    "original_text": found,
                })

        # 2. 提取正则匹配的关键词
        pattern_keywords = self._extract_pattern_keywords(text)
        for kw in pattern_keywords:
            # 检查是否已存在
            if not any(k["keyword"] == kw["keyword"] for k in keywords):
                keywords.append(kw)

        # 3. 如果关键词太多，按权重排序取前 20 个
        keywords.sort(key=lambda k: k["weight"], reverse=True)
        return keywords[:20]

    def _find_in_text(self, keyword: str, synonyms: list[str], text: str) -> Optional[str]:
        """查找关键词或同义词是否在文本中。"""
        # 先检查原关键词
        if keyword.lower() in text.lower():
            return keyword

        # 检查同义词
        for syn in synonyms:
            if syn.lower() in text.lower():
                return syn

        return None

    def _determine_weight(self, found_text: str, text: str, default_type: str) -> int:
        """确定关键词权重。"""
        # 如果出现在"要求"、"必备"等词附近，权重更高
        high_weight_patterns = [
            r'要求.*?' + re.escape(found_text),
            r'必备.*?' + re.escape(found_text),
            r'必须.*?' + re.escape(found_text),
            r'required.*?' + re.escape(found_text),
            r'must.*?' + re.escape(found_text),
        ]

        for pattern in high_weight_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return self.weight_rules.get("required_keywords", 10)

        # 如果出现在"加分"、"优先"等词附近，权重中等
        medium_weight_patterns = [
            r'加分.*?' + re.escape(found_text),
            r'优先.*?' + re.escape(found_text),
            r'preferred.*?' + re.escape(found_text),
            r'plus.*?' + re.escape(found_text),
        ]

        for pattern in medium_weight_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return self.weight_rules.get("preferred_keywords", 5)

        # 默认权重
        if default_type == "required":
            return self.weight_rules.get("required_keywords", 8)
        else:
            return self.weight_rules.get("preferred_keywords", 5)

    def _get_all_tech_keywords(self) -> dict[str, list[str]]:
        """获取所有技术关键词及其同义词。"""
        result = {}
        for concept in self.concepts:
            for keyword_list in concept.get("keywords", {}).values():
                if isinstance(keyword_list, list):
                    for kw in keyword_list:
                        if kw not in result:
                            # 查找同义词
                            syns = self.synonyms.get(kw, [])
                            result[kw] = list(set([kw] + syns))
        return result

    def _get_category_for_keyword(self, keyword: str) -> str:
        """获取关键词的分类。"""
        for concept in self.concepts:
            for category, keywords in concept.get("keywords", {}).items():
                if keyword in (keywords if isinstance(keywords, list) else []):
                    return f"{concept['concept']}/{category}"
        return "其他"

    def _extract_pattern_keywords(self, text: str) -> list[Keyword]:
        """通过正则模式提取关键词。"""
        keywords = []

        # 匹配常见技术栈格式
        patterns = [
            (r'(?:精通|熟练|熟悉|掌握|了解)\s*([\w\u4e00-\u9fff]+)', 8),
            (r'([\w]+)\s*(?:框架|框架开发)', 6),
            (r'使用\s*([\w]+)', 5),
        ]

        for pattern, weight in patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                kw = match.group(1)
                if len(kw) >= 2:  # 过滤太短的词
                    keywords.append({
                        "keyword": kw,
                        "weight": weight,
                        "synonyms": [],
                        "category": "文本提取",
                        "original_text": match.group(0),
                    })

        return keywords

    def _extract_soft_skills(self, text: str) -> list[Keyword]:
        """提取软技能关键词。"""
        soft_skill_keywords = [
            "团队协作", "沟通能力", "学习能力", "解决问题",
            "创新能力", "责任心", "抗压能力", "领导能力",
            "teamwork", "communication", "leadership",
        ]

        skills = []
        for skill in soft_skill_keywords:
            if skill.lower() in text.lower():
                skills.append({
                    "keyword": skill,
                    "weight": self.weight_rules.get("soft_skills", 3),
                    "synonyms": [],
                    "category": "软技能",
                    "original_text": skill,
                })

        return skills

    # ═══════════════════════════════════════════
    # 要求提取
    # ═══════════════════════════════════════════

    def _extract_requirements(self, text: str) -> Requirements:
        """提取经验和学历要求。"""
        requirements = {
            "experience": {},
            "education": {},
            "position_type": "",
            "industry": "",
        }

        # 经验要求
        exp_patterns = [
            (r'应届生', {"level": "应届生", "years": 0}),
            (r'应届毕业生', {"level": "应届生", "years": 0}),
            (r'1[-~—]?2年', {"level": "初级", "years": 1}),
            (r'2[-~—]?3年', {"level": "中级", "years": 2}),
            (r'3[-~—]?5年', {"level": "高级", "years": 3}),
            (r'5年以上', {"level": "专家", "years": 5}),
        ]

        for pattern, exp in exp_patterns:
            if re.search(pattern, text):
                requirements["experience"] = exp
                break

        # 学历要求
        edu_patterns = [
            (r'博士|PhD', {"level": "博士"}),
            (r'硕士|研究生', {"level": "硕士"}),
            (r'本科|学士', {"level": "本科"}),
            (r'大专|专科', {"level": "大专"}),
        ]

        for pattern, edu in edu_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                requirements["education"] = edu
                break

        # 学历偏好
        preferred_patterns = [
            (r'985|211|双一流', "985/211/双一流"),
            (r'海外名校|海外知名', "海外名校"),
            (r'Top\s*\d+', "Top 院校"),
        ]

        for pattern, pref in preferred_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                requirements["education"]["preferred"] = pref
                break

        # 岗位类型
        position_patterns = [
            (r'前端|Frontend|FE', "前端开发"),
            (r'后端|Backend|BE|Server', "后端开发"),
            (r'全栈|Fullstack', "全栈开发"),
            (r'移动端|Mobile', "移动端开发"),
            (r'算法|Algorithm', "算法开发"),
            (r'测试|QA|Quality', "测试"),
            (r'产品|Product', "产品"),
            (r'运营|Operation', "运营"),
            (r'设计|Design', "设计"),
        ]

        for pattern, pos in position_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                requirements["position_type"] = pos
                break

        return requirements

    # ═══════════════════════════════════════════
    # 概念映射
    # ═══════════════════════════════════════════

    def _build_concept_mapping(self, keywords: list[Keyword]) -> list[ConceptMapping]:
        """构建概念映射。

        将提取的关键词映射到更高层的概念，便于匹配相关经历。
        """
        keyword_strings = set(k["keyword"] for k in keywords)
        mappings = []

        for concept in self.concepts:
            concept_keywords = set()
            for kw_list in concept.get("keywords", {}).values():
                if isinstance(kw_list, list):
                    concept_keywords.update(kw_list)

            # 检查哪些概念关键词被匹配到
            matched = concept_keywords & keyword_strings

            # 如果匹配到至少 1 个关键词，建立概念映射
            if matched:
                # 获取该概念下的所有关键词（用于扩展匹配）
                all_concept_keywords = []
                for kw_list in concept.get("keywords", {}).values():
                    if isinstance(kw_list, list):
                        all_concept_keywords.extend(kw_list)

                mappings.append({
                    "concept": concept["concept"],
                    "matched_keywords": list(matched),
                    "related_keywords": all_concept_keywords,
                })

        return mappings

    # ═══════════════════════════════════════════
    # 质量评分
    # ═══════════════════════════════════════════

    def _calculate_quality_score(self, text: str, requirements: Requirements) -> float:
        """计算 JD 质量评分。

        评分维度：
        - 长度（是否足够详细）
        - 关键词密度（技术关键词占比）
        - 明确性（是否有具体要求）
        """
        score = 0.0

        # 长度评分（0-0.3）
        text_len = len(text)
        if text_len >= 500:
            score += 0.3
        elif text_len >= 200:
            score += 0.2
        elif text_len >= 50:
            score += 0.1

        # 关键词密度（0-0.4）
        tech_kw_count = len(self._get_all_tech_keywords())
        if tech_kw_count > 0:
            score += 0.3

        # 明确性（0-0.3）
        if requirements.get("experience"):
            score += 0.1
        if requirements.get("education"):
            score += 0.1
        if requirements.get("position_type"):
            score += 0.1

        return round(min(score, 1.0), 2)

    # ═══════════════════════════════════════════
    # 工具方法
    # ═══════════════════════════════════════════

    def _load_concept_config(self, path: Optional[str]) -> dict:
        """加载概念配置。"""
        if path is None:
            # 默认路径
            path = str(Path(__file__).parent.parent / "assets" / "concept_keywords.yaml")

        if Path(path).exists():
            with open(path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        return {"concepts": [], "synonyms": {}, "weight_rules": {}}

    def _get_timestamp(self) -> str:
        """获取当前时间戳。"""
        import time
        return time.strftime("%Y-%m-%d %H:%M:%S")

    def get_concepts_for_keyword(self, keyword: str) -> list[str]:
        """获取关键词所属的概念。

        参数：
            keyword: 关键词

        返回：
            概念列表
        """
        concepts = []
        for concept in self.concepts:
            for kw_list in concept.get("keywords", {}).values():
                if isinstance(kw_list, list) and keyword in kw_list:
                    concepts.append(concept["concept"])
                    break
        return concepts

    def get_related_keywords(self, keyword: str) -> list[str]:
        """获取关键词的相关词（同一概念下的其他词）。

        参数：
            keyword: 关键词

        返回：
            相关词列表
        """
        related = set()
        for concept in self.concepts:
            for kw_list in concept.get("keywords", {}).values():
                if isinstance(kw_list, list) and keyword in kw_list:
                    related.update(kw_list)
        return list(related)

    def save_analysis(self, analysis: JDAnalysis, output_path: str):
        """保存分析结果。

        参数：
            analysis: 分析结果
            output_path: 输出路径
        """
        with open(output_path, "w", encoding="utf-8") as f:
            yaml.dump(analysis, f, allow_unicode=True, sort_keys=False, default_flow_style=False)