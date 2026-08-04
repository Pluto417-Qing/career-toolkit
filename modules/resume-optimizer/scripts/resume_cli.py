#!/usr/bin/env python
"""简历生成命令行工具。

整合所有模块提供完整的 CLI 接口。
"""

import argparse
import json
import sys
from pathlib import Path

# 添加模块路径
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from profile.profile_manager import ProfileManager, create_profile_from_resume
from jd.jd_analyzer import JDAnalyzer
from ranker.experience_ranker import ExperienceRanker
from condenser.content_condenser import ContentCondenser
from condenser.expression_optimizer import ExpressionOptimizer
from condenser.highlighter import Highlighter
from question.question_generator import QuestionGenerator
from pipeline.orchestrator import ResumeOrchestrator
from pipeline.template_system import TemplateManager

# 向后兼容别名
ResumeBuilder = ResumeOrchestrator


def main():
    """主入口。"""
    parser = create_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # 根据命令分发
    if args.command == "build":
        cmd_build(args)
    elif args.command == "analyze-jd":
        cmd_analyze_jd(args)
    elif args.command == "profile":
        cmd_profile(args)
    elif args.command == "optimize":
        cmd_optimize(args)
    elif args.command == "templates":
        cmd_templates(args)
    elif args.command == "compare":
        cmd_compare(args)


def create_parser():
    """创建命令行解析器。"""
    parser = argparse.ArgumentParser(
        prog="resume",
        description="简历生成工具 - 信息库驱动的智能简历构建系统",
    )

    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # ═══════════════════════════════════════════
    # build 命令：构建简历
    # ═══════════════════════════════════════════
    build_parser = subparsers.add_parser("build", help="构建简历")
    build_parser.add_argument("user_id", help="用户 ID")
    build_parser.add_argument("--jd", required=True, help="JD 文件路径或文本")
    build_parser.add_argument("--out-dir", default="output", help="输出目录")
    build_parser.add_argument("--template", default="modern",
                              choices=["classic", "modern", "minimal", "creative"],
                              help="模板风格")
    build_parser.add_argument("--format", default="html",
                              choices=["html", "markdown", "json"],
                              help="输出格式")
    build_parser.add_argument("--interactive", action="store_true",
                              help="交互模式")
    build_parser.add_argument("--verbose", action="store_true",
                              help="详细输出")

    # ═══════════════════════════════════════════
    # analyze-jd 命令：分析 JD
    # ═══════════════════════════════════════════
    jd_parser = subparsers.add_parser("analyze-jd", help="分析 JD")
    jd_parser.add_argument("jd_file", help="JD 文件路径")
    jd_parser.add_argument("--out", help="输出文件路径")

    # ═══════════════════════════════════════════
    # profile 命令：信息库管理
    # ═══════════════════════════════════════════
    profile_parser = subparsers.add_parser("profile", help="信息库管理")
    profile_parser.add_argument("action",
                                choices=["list", "show", "create", "migrate", "delete"],
                                help="操作类型")
    profile_parser.add_argument("--user-id", help="用户 ID")
    profile_parser.add_argument("--resume", help="旧版简历文件路径（用于迁移）")
    profile_parser.add_argument("--confirm", action="store_true",
                                help="确认删除")

    # ═══════════════════════════════════════════
    # optimize 命令：优化文本
    # ═══════════════════════════════════════════
    opt_parser = subparsers.add_parser("optimize", help="优化文本")
    opt_parser.add_argument("text", help="要优化的文本")
    opt_parser.add_argument("--mode", default="standard",
                            choices=["standard", "aggressive", "conservative"],
                            help="优化模式")

    # ═══════════════════════════════════════════
    # templates 命令：列出模板
    # ═══════════════════════════════════════════
    subparsers.add_parser("templates", help="列出所有模板")

    # ═══════════════════════════════════════════
    # compare 命令：对比模板
    # ═══════════════════════════════════════════
    compare_parser = subparsers.add_parser("compare", help="对比模板")
    compare_parser.add_argument("user_id", help="用户 ID")
    compare_parser.add_argument("--jd", required=True, help="JD 文件路径")
    compare_parser.add_argument("--out", help="对比报告输出路径")

    return parser


# ═══════════════════════════════════════════════════════════
# 命令实现
# ═══════════════════════════════════════════════════════════

def cmd_build(args):
    """构建简历。"""
    print(f"🔨 构建简历...")
    print(f"   用户 ID: {args.user_id}")
    print(f"   JD: {args.jd}")
    print(f"   模板: {args.template}")

    # 初始化构建器
    builder = ResumeBuilder()

    # 加载 JD
    jd_text = load_jd(args.jd)
    if not jd_text:
        print("❌ 无法加载 JD")
        return

    # 构建简历
    result = builder.build_resume(args.user_id, jd_text)

    if result["status"] != "success":
        print(f"❌ 构建失败：{result.get('errors', [])}")
        return

    # 输出详细信息
    if args.verbose:
        print("\n📊 构建详情：")
        for step in result["steps"]:
            status = "✅" if step["status"] == "success" else "❌"
            print(f"   {status} {step['step']}")
            if step.get("data"):
                for key, value in step["data"].items():
                    print(f"      - {key}: {value}")

    # 获取模板
    template_manager = TemplateManager()
    template = template_manager.get_template(args.template)
    if not template:
        print(f"❌ 模板不存在：{args.template}")
        return

    # 渲染
    output = template.render(result["resume"], args.format)

    # 保存
    output_path = Path(args.out_dir) / args.user_id / "resume.html"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(output, encoding="utf-8")

    print(f"\n✅ 简历已生成：{output_path}")
    print(f"   页数：{result['resume'].get('estimated_pages')}")
    print(f"   是否一页：{result['resume'].get('fits_one_page')}")

    # 显示问题
    if result["questions"]:
        print(f"\n❓ 需要确认的问题：{result['questions']['total_count']} 个")
        print(f"   高优先级：{result['questions']['high_priority_count']}")

        if args.interactive:
            handle_interactive_questions(builder, args.user_id, result["questions"])


def cmd_analyze_jd(args):
    """分析 JD。"""
    print(f"🔍 分析 JD...")

    jd_text = Path(args.jd_file).read_text(encoding="utf-8")

    analyzer = JDAnalyzer()
    result = analyzer.analyze(jd_text)

    print(f"\n📊 分析结果：")
    print(f"   质量评分：{result['quality_score']}")
    print(f"   必备关键词：{len(result['keywords']['required'])} 个")
    print(f"   加分关键词：{len(result['keywords']['preferred'])} 个")
    print(f"   概念映射：{len(result['concept_mapping'])} 个")

    print(f"\n🔴 必备关键词：")
    for kw in result["keywords"]["required"][:10]:
        print(f"   - {kw['keyword']} (权重 {kw['weight']})")

    print(f"\n🧩 概念映射：")
    for concept in result["concept_mapping"]:
        print(f"   - {concept['concept']}: {concept.get('matched_keywords', [])}")

    if args.out:
        analyzer.save_analysis(result, args.out)
        print(f"\n💾 分析结果已保存：{args.out}")


def cmd_profile(args):
    """信息库管理。"""
    manager = ProfileManager()

    if args.action == "list":
        users = manager.list_users()
        print(f"📋 用户列表 ({len(users)} 个)：")
        for user in users:
            profile = manager.load_profile(user)
            if profile:
                name = profile.get("basics", {}).get("name", user)
                print(f"   - {user}: {name}")

    elif args.action == "show":
        if not args.user_id:
            print("❌ 请指定 --user-id")
            return

        profile = manager.load_profile(args.user_id)
        if not profile:
            print(f"❌ 用户不存在：{args.user_id}")
            return

        basics = profile.get("basics", {})
        print(f"👤 用户信息：")
        print(f"   姓名：{basics.get('name', '')}")
        print(f"   标签：{basics.get('label', '')}")
        print(f"   邮箱：{basics.get('email', '')}")
        print(f"   教育背景：{len(profile.get('education', []))} 条")
        print(f"   工作经历：{len(profile.get('work', []))} 条")
        print(f"   项目经历：{len(profile.get('projects', []))} 条")

    elif args.action == "create":
        if not args.user_id:
            print("❌ 请指定 --user-id")
            return

        print(f"📝 创建信息库：{args.user_id}")
        print("   请交互式输入信息（待实现）")

    elif args.action == "migrate":
        if not args.user_id or not args.resume:
            print("❌ 请指定 --user-id 和 --resume")
            return

        print(f"📦 迁移旧版简历：{args.resume}")
        profile = create_profile_from_resume(args.resume)
        manager.create_profile(args.user_id, profile)
        print(f"✅ 迁移成功：{args.user_id}")

    elif args.action == "delete":
        if not args.user_id:
            print("❌ 请指定 --user-id")
            return

        if not args.confirm:
            print("⚠️ 删除操作需要 --confirm 确认")
            return

        success = manager.delete_profile(args.user_id, confirm=True)
        if success:
            print(f"✅ 已删除：{args.user_id}")
        else:
            print(f"❌ 删除失败")


def cmd_optimize(args):
    """优化文本。"""
    optimizer = ExpressionOptimizer()
    optimized = optimizer.optimize_text(args.text, mode=args.mode)

    print(f"📝 原文：{args.text}")
    print(f"✨ 优化后：{optimized}")

    suggestions = optimizer.suggest_improvements(args.text)
    if suggestions:
        print(f"\n💡 改进建议：")
        for s in suggestions[:5]:
            print(f"   - [{s['priority']}] {s['issue']}")
            print(f"     {s['suggestion']}")


def cmd_templates(args):
    """列出模板。"""
    manager = TemplateManager()
    templates = manager.list_templates()

    print("📋 可用模板：")
    for t in templates:
        print(f"\n   {t['name']}: {t['display_name']}")
        print(f"   {t['description']}")


def cmd_compare(args):
    """对比模板。"""
    print(f"🔄 对比模板...")

    builder = ResumeBuilder()

    jd_text = load_jd(args.jd)
    if not jd_text:
        print("❌ 无法加载 JD")
        return

    result = builder.build_resume(args.user_id, jd_text)
    if result["status"] != "success":
        print(f"❌ 构建失败：{result.get('errors', [])}")
        return

    template_manager = TemplateManager()
    comparison = template_manager.compare_templates(result["resume"])

    print(f"\n📊 模板对比：")
    for t in comparison["templates"]:
        print(f"   - {t['display_name']}: HTML 长度 {t['html_length']} 字符")

    print(f"\n💡 推荐：")
    for rec in comparison["recommendations"]:
        print(f"   - {rec['template']}: {rec['reason']}")

    if args.out:
        Path(args.out).write_text(json.dumps(comparison, ensure_ascii=False, indent=2),
                                  encoding="utf-8")
        print(f"\n💾 对比报告已保存：{args.out}")


# ═══════════════════════════════════════════════════════════
# 辅助函数
# ═══════════════════════════════════════════════════════════

def load_jd(source: str) -> str:
    """加载 JD 文本。

    参数：
        source: JD 文件路径或文本

    返回：
        JD 文本
    """
    path = Path(source)
    if path.exists():
        return path.read_text(encoding="utf-8")
    else:
        # 假设是直接输入的文本
        return source


def handle_interactive_questions(builder: ResumeBuilder, user_id: str,
                                  question_set: dict):
    """处理交互式问题。

    参数：
        builder: 构建器
        user_id: 用户 ID
        question_set: 问题集
    """
    questions = question_set.get("questions", [])

    for i, q in enumerate(questions):
        if q.get("status") != "pending":
            continue

        print(f"\n❓ 问题 {i+1}/{len(questions)} [{q['priority']}]:")
        print(f"   {q['question']}")

        if q.get("options"):
            print("   选项：")
            for opt in q["options"]:
                print(f"     - {opt['value']}: {opt['label']}")

        # 读取用户输入
        answer = input("   回答（输入 's' 跳过，'q' 退出）: ")

        if answer.lower() == 'q':
            break
        elif answer.lower() == 's':
            builder.question_generator.skip_question(question_set, q["id"])
        else:
            builder.question_generator.answer_question(question_set, q["id"], answer)

    # 更新信息库
    if any(q.get("status") == "answered" for q in questions):
        print("\n💾 更新信息库...")
        builder.update_profile_from_answers(user_id, question_set)
        print("✅ 信息库已更新")


if __name__ == "__main__":
    main()