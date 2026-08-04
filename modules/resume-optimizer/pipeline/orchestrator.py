"""简历编排器。

整合所有模块，形成完整的简历生成流程。
负责调用各子模块，协调数据流，最终产出 YAML 格式的简历。
"""

import json
from pathlib import Path
from typing import Optional

import yaml

# 导入各子模块
from profile.profile_manager import ProfileManager
from jd.jd_analyzer import JDAnalyzer
from ranker.experience_ranker import ExperienceRanker
from condenser.content_condenser import ContentCondenser
from question.question_generator import QuestionGenerator


class ResumeOrchestrator:
    """简历编排器。

    整合 ProfileManager、JDAnalyzer、ExperienceRanker、
    ContentCondenser、QuestionGenerator 等模块。

    职责：信息库 → JD分析 → 筛选 → 精简 → 产出 YAML
    """

    def __init__(self, config: Optional[dict] = None):
        """初始化编排器。

        参数：
            config: 配置字典
        """
        self.config = config or {}

        # 初始化各子模块
        self.profile_manager = ProfileManager(
            self.config.get("profiles_dir", "profiles")
        )
        self.jd_analyzer = JDAnalyzer(
            self.config.get("concept_config_path")
        )
        self.experience_ranker = ExperienceRanker(
            self.config.get("selection_config")
        )
        self.content_condenser = ContentCondenser(
            self.config.get("condense_config")
        )
        self.question_generator = QuestionGenerator(
            self.config.get("max_questions", 10)
        )

    def build_resume(self, user_id: str, jd_text: Optional[str] = None,
                     update_profile: bool = True) -> dict:
        """构建简历（完整流程）。

        有 JD 时：生成 JD 适配版简历
        无 JD 时：生成通用版简历

        参数：
            user_id: 用户 ID
            jd_text: JD 文本（可选）
            update_profile: 是否更新信息库

        返回：
            构建结果，包含简历、问题、分析等
        """
        result = {
            "status": "success",
            "mode": "jd_optimized" if jd_text else "general",
            "steps": [],
            "resume": None,
            "jd_analysis": None,
            "questions": None,
            "errors": [],
        }

        # Step 1: 加载信息库
        profile = self.profile_manager.load_profile(user_id)
        if not profile:
            result["status"] = "error"
            result["errors"].append(f"用户 {user_id} 的信息库不存在")
            return result

        result["steps"].append({
            "step": "load_profile",
            "status": "success",
            "data": {
                "education_count": len(profile.get("education", [])),
                "work_count": len(profile.get("work", [])),
                "projects_count": len(profile.get("projects", [])),
            }
        })

        # Step 2: 分析 JD（仅当有 JD 时）
        jd_analysis = None
        if jd_text:
            try:
                jd_analysis = self.jd_analyzer.analyze(jd_text)
                result["jd_analysis"] = jd_analysis
                result["steps"].append({
                    "step": "analyze_jd",
                    "status": "success",
                    "data": {
                        "quality_score": jd_analysis.get("quality_score"),
                        "required_keywords_count": len(jd_analysis.get("keywords", {}).get("required", [])),
                        "concepts_count": len(jd_analysis.get("concept_mapping", [])),
                    }
                })
            except Exception as e:
                result["steps"].append({
                    "step": "analyze_jd",
                    "status": "error",
                    "error": str(e),
                })
                result["errors"].append(f"JD 分析失败：{e}")
                return result

        # Step 3: 筛选经历（基于 JD 或默认策略）
        try:
            selection_result = self.experience_ranker.rank(profile, jd_analysis)
            result["steps"].append({
                "step": "rank_experiences",
                "status": "success",
                "data": {
                    "selected_work": len(selection_result.get("work", [])),
                    "selected_projects": len(selection_result.get("projects", [])),
                    "hidden_count": len(selection_result.get("hidden_entries", [])),
                    "score_summary": selection_result.get("score_summary", {}),
                }
            })
        except Exception as e:
            result["steps"].append({
                "step": "rank_experiences",
                "status": "error",
                "error": str(e),
            })
            result["errors"].append(f"经历筛选失败：{e}")
            return result

        # Step 4: 精简内容
        try:
            condensed_resume = self.content_condenser.condense_resume(
                profile, selection_result
            )
            result["resume"] = condensed_resume
            result["steps"].append({
                "step": "condense_content",
                "status": "success",
                "data": {
                    "line_count": condensed_resume.get("line_count"),
                    "word_count": condensed_resume.get("word_count"),
                    "estimated_pages": condensed_resume.get("estimated_pages"),
                    "fits_one_page": condensed_resume.get("fits_one_page"),
                }
            })
        except Exception as e:
            result["steps"].append({
                "step": "condense_content",
                "status": "error",
                "error": str(e),
            })
            result["errors"].append(f"内容精简失败：{e}")
            return result

        # Step 5: 生成问题（仅当有 JD 时）
        if jd_analysis:
            try:
                question_set = self.question_generator.generate_questions(
                    profile, jd_analysis, selection_result
                )
                result["questions"] = question_set
                result["steps"].append({
                    "step": "generate_questions",
                    "status": "success",
                    "data": {
                        "total_questions": question_set.get("total_count"),
                        "high_priority": question_set.get("high_priority_count"),
                    }
                })
            except Exception as e:
                result["steps"].append({
                    "step": "generate_questions",
                    "status": "error",
                    "error": str(e),
                })
                result["errors"].append(f"问题生成失败：{e}")

        return result

    def build_resume_from_jd_file(self, user_id: str, jd_file_path: str) -> dict:
        """从 JD 文件构建简历。

        参数：
            user_id: 用户 ID
            jd_file_path: JD 文件路径

        返回：
            构建结果
        """
        jd_text = Path(jd_file_path).read_text(encoding="utf-8")
        return self.build_resume(user_id, jd_text)

    def save_result(self, result: dict, output_dir: str, user_id: str,
                     jd_name: str = "") -> dict:
        """保存构建结果。

        参数：
            result: 构建结果
            output_dir: 输出目录
            user_id: 用户 ID
            jd_name: JD 名称

        返回：
            保存的文件路径
        """
        output_path = Path(output_dir) / user_id / jd_name
        output_path.mkdir(parents=True, exist_ok=True)

        saved_files = {}

        # 保存简历（单一 YAML 文件）
        if result.get("resume"):
            resume_path = output_path / "resume.yaml"
            with open(resume_path, "w", encoding="utf-8") as f:
                yaml.dump(result["resume"], f, allow_unicode=True,
                         sort_keys=False, default_flow_style=False)
            saved_files["resume"] = str(resume_path)

        # 保存 JD 分析（仅当有 JD 时）
        if result.get("jd_analysis"):
            jd_path = output_path / "jd_analysis.yaml"
            with open(jd_path, "w", encoding="utf-8") as f:
                yaml.dump(result["jd_analysis"], f, allow_unicode=True,
                         sort_keys=False, default_flow_style=False)
            saved_files["jd_analysis"] = str(jd_path)

        # 保存问题集（仅当有问题时）
        if result.get("questions"):
            questions_path = output_path / "questions.json"
            with open(questions_path, "w", encoding="utf-8") as f:
                json.dump(result["questions"], f, ensure_ascii=False, indent=2)
            saved_files["questions"] = str(questions_path)

        # 保存构建结果摘要
        summary_path = output_path / "build_summary.json"
        summary = {
            "status": result.get("status"),
            "mode": result.get("mode"),
            "errors": result.get("errors", []),
            "steps": [
                {"step": s["step"], "status": s["status"]}
                for s in result.get("steps", [])
            ],
        }
        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        saved_files["summary"] = str(summary_path)

        return saved_files

    def update_profile_from_answers(self, user_id: str,
                                    question_set: dict) -> dict:
        """根据用户回答更新信息库。

        参数：
            user_id: 用户 ID
            question_set: 问题集（包含用户回答）

        返回：
            更新后的信息库
        """
        profile = self.profile_manager.load_profile(user_id)
        if not profile:
            raise FileNotFoundError(f"用户 {user_id} 的信息库不存在")

        # 处理已回答的问题
        for question in question_set.get("questions", []):
            if question.get("status") != "answered":
                continue

            answer = question.get("user_answer", "")
            if not answer:
                continue

            target_entry_id = question.get("target_entry_id", "")
            target_entry_type = question.get("target_entry_type", "")

            # 根据问题类型更新信息库
            question_type = question.get("type", "")

            if question_type == "missing_quantification":
                # 添加量化数据到对应的贡献
                self._add_quantification(profile, target_entry_id,
                                        target_entry_type, answer)

            elif question_type == "missing_descriptor":
                # 更新描述符
                self._update_descriptor(profile, target_entry_id,
                                       target_entry_type, answer, question)

            elif question_type == "clarification":
                # 更新经历描述
                self._clarify_entry(profile, target_entry_id,
                                   target_entry_type, answer, question)

        # 保存更新后的信息库
        return self.profile_manager.update_profile(user_id, profile)

    def _add_quantification(self, profile: dict, entry_id: str,
                             entry_type: str, answer: str):
        """添加量化数据。"""
        section_key = {
            "work": "work",
            "projects": "projects",
            "education": "education",
        }.get(entry_type, entry_type)

        entries = profile.get(section_key, [])
        for entry in entries:
            if entry.get("id") == entry_id:
                # 检查是否有 personal_contribution
                if entry.get("personal_contribution"):
                    # 给最后一个贡献添加 result
                    last_contrib = entry["personal_contribution"][-1]
                    if not last_contrib.get("result"):
                        last_contrib["result"] = answer
                else:
                    # 添加新的贡献
                    entry["personal_contribution"] = [
                        {
                            "action": "优化",
                            "target": "整体表现",
                            "result": answer,
                        }
                    ]
                break

    def _update_descriptor(self, profile: dict, entry_id: str,
                            entry_type: str, answer: str,
                            question: dict):
        """更新描述符。"""
        section_key = {
            "work": "work",
            "projects": "projects",
            "education": "education",
        }.get(entry_type, entry_type)

        entries = profile.get(section_key, [])
        for entry in entries:
            if entry.get("id") == entry_id:
                if "descriptor" not in entry:
                    entry["descriptor"] = {}

                # 如果是重要性评分问题
                if "打分" in question.get("question", ""):
                    try:
                        entry["descriptor"]["user_importance_rating"] = int(answer)
                    except ValueError:
                        pass
                # 如果是项目规模问题
                elif "规模" in question.get("question", ""):
                    if entry.get("project_context"):
                        entry["project_context"]["scale"] = answer
                    else:
                        entry["project_context"] = {"scale": answer}
                break

    def _clarify_entry(self, profile: dict, entry_id: str,
                        entry_type: str, answer: str,
                        question: dict):
        """澄清条目描述。"""
        section_key = {
            "work": "work",
            "projects": "projects",
            "education": "education",
        }.get(entry_type, entry_type)

        entries = profile.get(section_key, [])
        for entry in entries:
            if entry.get("id") == entry_id:
                # 更新第一个贡献的文本
                if entry.get("personal_contribution"):
                    entry["personal_contribution"][0]["text"] = answer
                elif entry.get("highlights"):
                    entry["highlights"][0] = answer
                break

    def list_profiles(self) -> list[str]:
        """列出所有用户信息库。"""
        return self.profile_manager.list_users()

    def delete_profile(self, user_id: str, confirm: bool = False) -> bool:
        """删除用户信息库。"""
        return self.profile_manager.delete_profile(user_id, confirm)