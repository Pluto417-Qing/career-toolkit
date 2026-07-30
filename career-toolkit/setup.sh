#!/bin/bash
set -e

echo "======================================"
echo "  Career Toolkit Skill Pack 安装脚本"
echo "======================================"
echo ""

# 检测 Python
if command -v python3 &>/dev/null; then
    PYTHON=python3
elif command -v python &>/dev/null; then
    PYTHON=python
else
    echo "❌ 未检测到 Python，请先安装 Python 3.8+"
    echo "   macOS: brew install python3"
    echo "   Ubuntu: sudo apt install python3 python3-pip"
    exit 1
fi

PY_VERSION=$($PYTHON --version 2>&1 | awk '{print $2}')
echo "✓ Python 版本: $PY_VERSION"

# 安装 Python 依赖
echo ""
echo "→ 安装 Python 依赖..."
$PYTHON -m pip install --quiet PyYAML Jinja2 jsonschema

echo "✓ 核心依赖安装完成 (PyYAML, Jinja2, jsonschema)"

# 可选：WeasyPrint（PDF 导出）
echo ""
read -p "是否安装 WeasyPrint 以支持 PDF 导出？(y/N) " INSTALL_PDF
if [[ "$INSTALL_PDF" =~ ^[Yy]$ ]]; then
    if [[ "$(uname)" == "Darwin" ]]; then
        if command -v brew &>/dev/null; then
            echo "→ 安装 WeasyPrint 系统依赖 (cairo, pango, gdk-pixbuf)..."
            brew install cairo pango gdk-pixbuf libffi 2>/dev/null || true
        else
            echo "⚠ 未检测到 Homebrew，请手动安装: brew install cairo pango gdk-pixbuf"
        fi
    elif [[ "$(uname)" == "Linux" ]]; then
        echo "→ 安装 WeasyPrint 系统依赖..."
        sudo apt-get install -y libcairo2-dev libpango1.0-dev libgdk-pixbuf2.0-dev 2>/dev/null || true
    fi
    $PYTHON -m pip install --quiet weasyprint
    echo "✓ WeasyPrint 安装完成"
else
    echo "⏭ 跳过 PDF 支持（可随时运行 pip install weasyprint 补装）"
fi

# 安装 Skill 到 TRAE
SKILL_DIR="$(cd "$(dirname "$0")" && pwd)"
echo ""
echo "======================================"
echo "  ✅ 安装完成！"
echo "======================================"
echo ""
echo "Skill 路径: $SKILL_DIR"
echo ""
echo "使用方式："
echo "  在 TRAE 中直接对话即可触发："
echo "  • \"帮我做职业规划\" → 启动 career-planner"
echo "  • \"帮我写简历\"     → 启动 resume-builder"
echo ""
echo "手动命令："
echo "  # Holland 测评评分"
echo "  $PYTHON $SKILL_DIR/modules/career-planner/scripts/score_holland.py <answers.yaml>"
echo ""
echo "  # 简历渲染"
echo "  $PYTHON $SKILL_DIR/modules/resume-builder/scripts/render.py <resume.yaml> --out-dir ./out"
echo ""
