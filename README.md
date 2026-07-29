# product-catalog-generator

> 品牌化产品目录生成器 · Branded Product Catalog Generator
> 一条流水线把「数据」变成「可印刷的像素级 PDF 目录」：HTML(品牌化) → Playwright 渲染 PDF → PIL 压缩图片 → pdftoppm+PIL 像素抽检。

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## 它能做什么

做外贸/制造业，常常需要一份**排版统一、可印刷、可发给客户**的产品目录 PDF。这个工具把流程标准化成四步：

1. **HTML 排版引擎** — 品牌色 / 公司名 / Logo 全部参数化，内联 CSS，单文件自包含（不依赖外网字体/图片）。
2. **Playwright 渲染 PDF** — 用 headless Chromium 把 HTML 像素级渲染成 A4 PDF（`print_background=True`，保留品牌底色）。
3. **PIL 压缩图片** — 产品图等比缩放到 ≤1240px，存 JPEG q85（例如 58MB → 9.2MB）。
4. **pdftoppm + PIL 像素抽检** — 转图算像素标准差，确认 PDF 非空白、渲染成功（校验三板斧之一）。

> 本仓库从一个生产用钢材目录脚本**脱敏重构**：所有公司名/联系方式/真实产品图均替换为占位，仓库零外部图片依赖、不泄露任何业务数据。

---

## 目录结构

```
catalog_generator.py   主程序(排版引擎 + render_pdf + compress_images + ocr_verify)
sample_data.py         示例：占位公司 + 4 个公开牌号(数据源自公开标准)
config.example.py      你的品牌配置样例(改成自己的即可)
```

---

## 快速开始

```bash
pip install playwright pillow
playwright install chromium     # 仅 --pdf 需要
brew install poppler            # 仅 ocr_verify 需要 (mac)

# 1) 仅生成 HTML(不需要浏览器)
python catalog_generator.py
# → sample_catalog.html

# 2) 生成 HTML + 渲染 PDF
python catalog_generator.py --pdf
# → sample_catalog.html + sample_catalog.pdf

# 3) 压缩图片目录
python catalog_generator.py --compress imgs/
```

用自己的数据：编辑 `sample_data.py`（或 import `CatalogConfig` 传你自己的 grades/config）：

```python
from catalog_generator import CatalogConfig, build_html
from sample_data import SAMPLE_GRADES

cfg = CatalogConfig(brand="#0E2236", accent="#E8712C",
                    company="ACME STEEL", website="www.acme.com")
html = build_html(cfg, SAMPLE_GRADES)
```

---

## 设计要点

- **单文件自包含 HTML**：CSS 内联、`@media print` 控制分页、品牌色抽成参数 —— 一份文件发给任何人都能原样渲染。
- **像素级可控**：列宽/行高/字体/边框/合并全在模板里写死，改一处即全局统一。
- **校验三板斧**（生产环境验证过）：`pypdf` 数页 → `pdftotext` 查中文层 → `pdftoppm`+`PIL` 像素抽检。本仓库实现其中像素抽检（`ocr_verify`）。

---

## License

MIT
