# 主题体系与定制

## 目录结构

```
assets/themes/<theme-name>/
├── template.html.j2   # Jinja2 模板，接收 data 变量
└── style.css          # WeasyPrint / 浏览器兼容 CSS
```

`render.py` 会用 Jinja2 加载 `template.html.j2`，`{% include 'style.css' %}` 把样式内联到 `<style>`。这样单个 HTML 文件就能同时用于浏览器预览和 PDF 打印，无需外链资源。

## 内置主题

| 主题 | 定位 | 适用 |
|---|---|---|
| `classic` | 单栏、传统中文简历 | A4 打印、投递国内公司 |

（后续可添加 `modern` 双栏、`academic` 学术长 CV 等。）

## 新增主题步骤

1. 复制 `classic/` 到 `assets/themes/<my-theme>/`
2. 改 `style.css` 调整字体、间距、颜色
3. 需要重排布局时改 `template.html.j2`；数据字段跟 schema 保持一致即可
4. 在 `resume.yaml` 的 `meta.theme` 里写 `<my-theme>`

## WeasyPrint 兼容注意

- 支持大部分 CSS 2.1 + 一部分 CSS 3，**不支持 Flexbox 的部分行为、Grid 部分行为、动画**——布局建议用块级 + `display: flex`（简单场景）或表格布局。
- 通过 `@page { size: A4; margin: ... }` 控制页边距。
- 中文字体：优先使用系统里安装的思源黑体 / PingFang / Microsoft YaHei；若在无字体环境，WeasyPrint 会降级到默认，但仍能生成 PDF，只是排版风格差异较大。

## 浏览器预览与 PDF 打印一致性

- 保持样式尽量简单：避免 fixed / sticky、flex `gap` 依赖等浏览器新特性
- 分页控制：给 `section` / `entry` 加 `page-break-inside: avoid;`，避免一条经历跨页
