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
| `modern` | 双栏（深色侧边栏 + 右主栏）、现代风格 | 互联网/设计岗、突出技能与联系方式 |
| `academic` | 单栏学术长 CV、衬线字体、无页数限制 | 科研岗申请、学术会议、奖学金申报 |
| `minimal` | 极简留白、无装饰线、轻字重 | 设计/产品/创意岗、外企 |
| `compact` | 紧凑高密度、小字号、深色 section 标题条 | 经验丰富需压缩至一页 |
| `elegant` | 衬线标题 + 无衬线正文、铜棕色调、左竖线装饰 | 管理/文职/外企/高端猎头投递 |
| `infographic` | 左面板技能进度条 + 右主栏时间线、绿色主题 | 互联网/产品/运营、强调可视化 |
| `metro` | 扁平化设计、青色大色块 banner 头部、卡片式条目 | 互联网产品岗、UI/UX 设计 |
| `creative` | 渐变色头部、圆角卡片条目、珊瑚暖色调 | 设计/营销/创意岗、个性化投递 |
| `executive` | 深色 navy 头部 + 金色点缀、商务高端感 | 高管/资深人士、猎头/高端岗位 |
| `tech` | 暗色背景、等宽字体、终端风格 section 标记 | 开发工程师、技术岗、极客风格 |

## 多语言支持

所有内置主题均支持通过 `meta.language` 切换界面语言：

| 值 | 效果 |
|---|---|
| `zh`（默认） | 中文标签：教育经历、项目经历… |
| `en` | 英文标签：Education、Projects… |
| `zh-en` | 双语标签：教育经历 / Education… |

```yaml
meta:
  language: en   # 切换为英文简历
  theme: classic
```

实现方式：每个模板顶部维护一个 `_i18n` 字典（zh / en / zh-en 三组），通过 `{% set t = _i18n[lang] %}` 选取，section 标题和内联标签统一使用 `{{ t.xxx }}`。新增主题时复制该结构即可。

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
