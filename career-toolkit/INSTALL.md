# 安装指引

## 方式一：一键安装（推荐）

```bash
cd ~/Desktop/user_skills/career-toolkit
bash setup.sh
```

脚本会自动检测环境并安装依赖，按提示操作即可。

---

## 方式二：手动安装

### 1. 确认 Python 环境

```bash
python3 --version  # 需要 3.8+
```

如未安装：
- **macOS**: `brew install python3`
- **Ubuntu/Debian**: `sudo apt install python3 python3-pip`
- **Windows**: 从 python.org 下载安装，或使用 WSL

### 2. 安装核心依赖

```bash
pip install PyYAML Jinja2 jsonschema
```

这三个包即可支持全部核心功能（测评评分、简历校验、HTML 渲染）。

### 3. 安装 PDF 导出支持（可选）

PDF 导出依赖 WeasyPrint，它需要系统级图形库：

**macOS:**
```bash
brew install cairo pango gdk-pixbuf libffi
pip install weasyprint
```

**Ubuntu/Debian:**
```bash
sudo apt-get install libcairo2-dev libpango1.0-dev libgdk-pixbuf2.0-dev
pip install weasyprint
```

**Windows (WSL):**
```bash
sudo apt-get install libcairo2-dev libpango1.0-dev libgdk-pixbuf2.0-dev
pip install weasyprint
```

> 不安装 WeasyPrint 不影响其他功能，HTML 预览仍可正常使用。

### 4. 放置 Skill 文件

确保 `career-toolkit/` 目录位于 TRAE 的 user_skills 路径下：

```
~/Desktop/user_skills/career-toolkit/
```

TRAE 会自动扫描此目录下的 `SKILL.md` 并注册为可用 Skill。

---

## 验证安装

运行以下命令确认依赖正常：

```bash
cd ~/Desktop/user_skills/career-toolkit

# 验证 Holland 评分脚本
python3 modules/career-planner/scripts/score_holland.py --help

# 验证简历校验
python3 modules/resume-builder/scripts/validate.py --help

# 验证简历渲染
python3 modules/resume-builder/scripts/render.py --help
```

三个命令都能正常打印帮助信息即为安装成功。

---

## 使用方式

安装完成后无需任何额外配置，在 TRAE 中对话即可：

```
用户: 我是大三计算机的，帮我规划一下毕业后的方向
→ 自动加载 career-planner，开始引导式对话

用户: 帮我写一份简历
→ 自动加载 resume-builder，开始收集信息
```

也可以直接使用命令行工具：

```bash
# Holland 测评
python3 modules/career-planner/scripts/score_holland.py answers.yaml

# MBTI 测评
python3 modules/career-planner/scripts/score_mbti.py answers.yaml

# 生成可视化报告
python3 modules/career-planner/scripts/render_plan_visual.py career_plan.yaml -o report.html

# 简历校验
python3 modules/resume-builder/scripts/validate.py resume.yaml

# 简历渲染（HTML）
python3 modules/resume-builder/scripts/render.py resume.yaml --out-dir ./out

# 简历渲染（HTML + PDF）
python3 modules/resume-builder/scripts/render.py resume.yaml --out-dir ./out --pdf

# 转 Markdown（飞书发布用）
python3 modules/resume-builder/scripts/to_markdown.py resume.yaml
```

---

## 卸载

删除目录即可，无全局副作用：

```bash
rm -rf ~/Desktop/user_skills/career-toolkit
pip uninstall PyYAML Jinja2 jsonschema weasyprint  # 可选
```

---

## 常见问题

**Q: 没有网络能用吗？**
A: 可以。核心功能完全离线运行。唯一需要网络的是可视化 HTML 中的 Chart.js 雷达图（从 CDN 加载），如需离线可将 chart.js 文件下载到本地。

**Q: WeasyPrint 安装失败怎么办？**
A: WeasyPrint 依赖系统图形库（Cairo/Pango），安装问题通常是系统库缺失。可以先跳过 PDF 导出，用 HTML 预览后浏览器打印为 PDF 作为替代方案。

**Q: 支持 Windows 吗？**
A: 推荐使用 WSL (Windows Subsystem for Linux)。Python 脚本本身跨平台兼容，但 WeasyPrint 在原生 Windows 上安装较复杂。
