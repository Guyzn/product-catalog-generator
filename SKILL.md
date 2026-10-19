---
name: product-catalog-generator
description: 数据驱动产品目录流水线——把结构化产品数据（牌号/成分/参数表）一键变成品牌化可印刷 PDF 目录：HTML 排版引擎（品牌色/公司名/Logo/联系方式全参数化，单文件自包含）→ Playwright 渲染 A4 PDF → PIL 批量压缩产品图（≤1240px q85）→ pdftoppm+PIL 像素抽检验证非空白。适用：已有产品/牌号数据表要快速批量出统一版式目录、数据更新后重跑出稿、批量压缩产品图片；提到「产品目录」「catalog」「数据表生成目录」「压图」「出目录 PDF」等词时使用。边界：本 Skill 是**数据流水线**，版式为内置固定模板、改一处全局统一，胜在快和稳；需要印刷级定制版式（对开拼版、跨页大图、一牌号一整页、多风格主题色板、送印出血/裁切标记、双语混排）时改用 industrial-print-skill（D 对开 Catalog / E 单页作品集 / F 单页技术数据）。
---

# 产品目录数据流水线 Skill（product-catalog-generator）

> 一条流水线把「数据」变成「可印刷的 PDF 目录」：
> **数据（Python dict）→ 品牌化单文件 HTML → Playwright A4 PDF → 图片压缩 → 像素抽检**
> 从生产用钢材目录脚本脱敏重构：仓库零真实数据、零外部图片依赖。

## 路由（第一步，必做）——本 Skill vs industrial-print-skill

两个 Skill 都能出「产品目录」，分工在**驱动方式**：

| | 本 Skill · 数据流水线 | industrial-print-skill · 印刷排版引擎 |
|---|---|---|
| 驱动方式 | **数据驱动**：喂结构化数据，内置固定模板 | **设计驱动**：内容 JSON + 多套版式锁死风格 |
| 出稿速度 | 分钟级，一条命令 | 半小时级，逐页构建+校验 |
| 版式定制 | 模板内改（改一处全局统一） | 任意（对开/跨页/双语/多风格） |
| 送印规格 | 标准 A4 PDF（@page 10mm 边距） | TrimBox/BleedBox/裁切标记/300ppi 管控 |
| 适合 | 数据表现成、要快、要可反复重跑 | 要设计感、要送印、要牌号一整页精排 |

**判断口诀：数据在手求快 → 本 Skill；版式求精求送印 → industrial-print-skill。**
两边可组合：先用本 Skill 压图（`--compress`），再用 industrial-print-skill 排版。

## 环境（按需安装）

```bash
pip install playwright pillow
playwright install chromium     # 仅渲染 PDF 需要
brew install poppler            # 仅像素抽检需要 (mac)
```

## 四步流水线

1. **HTML 排版引擎** — `build_html(cfg, grades)`：品牌色/公司名/Logo/联系全参数化，CSS 内联，单文件自包含（断网原样渲染）
2. **Playwright 渲染 PDF** — `render_pdf()`：headless Chromium，A4、`print_background=True` 保留品牌底色
3. **PIL 压缩图片** — `compress_images(dir)`：等比缩到 ≤1240px、JPEG q85（实测 58MB → 9.2MB）
4. **像素抽检** — `ocr_verify()`：pdftoppm 转图 + 像素标准差 > 8 判定非空白，逐页返回结果

## 快速开始

```bash
python catalog_generator.py                # 仅生成 sample_catalog.html（不需要浏览器）
python catalog_generator.py --pdf          # HTML + PDF + 像素抽检
python catalog_generator.py --compress imgs/   # 批量压缩图片目录
# 可选：--html-out out.html --pdf-out out.pdf --chromium /path/to/chromium
```

## 换成自己的数据（真实项目的标准做法）

**不要改 sample_data.py 提交真实数据**——在本地新建数据文件（如 `my_catalog.py`），仓库保持脱敏：

```python
from catalog_generator import CatalogConfig, build_html, render_pdf, ocr_verify
from my_data import GRADES          # 你自己的牌号/产品数据

cfg = CatalogConfig(
    brand="#1B3A5C", accent="#E8712C",          # 主色/强调色
    company="ACME STEEL", company_en="Acme Steel Ltd.",
    website="www.acme.com", logo_text="◣ ACME",
    contact=dict(phone="86-xxx", email="sales@acme.com", address="..."),
)
html = build_html(cfg, GRADES, title_cn="产品目录", title_en="PRODUCTS PORTFOLIO")
open("acme_catalog.html", "w", encoding="utf-8").write(html)
render_pdf("acme_catalog.html", "acme_catalog.pdf")
print(ocr_verify("acme_catalog.pdf"))           # 每页 (文件名, 是否非空白)
```

**产品条目字段**（dict，全部可选除 `grade`）：

| 字段 | 含义 | 示例 |
|---|---|---|
| `grade` | 牌号/型号（卡片标题） | `"1.2344"` |
| `std` | 执行标准（标题右侧） | `"DIN 17350"` |
| `category` | 分组/筛选用途 | `"hot"` / `"alloy"` |
| `chem` | 成分表（dict，展平成一行） | `{"C": "0.37-0.43", "Cr": "4.80-5.50"}` |
| `sm` / `ft` | 冶炼方式 / 成型方式 | `"EAF+LF+VD"` / `"Hot rolled / forged"` |
| `ht` | 热处理（左侧强调条块） | `"Quench 1020-1050℃; temper 560-580℃."` |
| `desc` | 一句话卖点 | `"Hot work tool steel..."` |

**配置字段**（`CatalogConfig`）：`brand` 主色、`accent` 强调色、`light` 斑马纹底、`ink` 正文色、`company`/`company_en`、`website`、`logo_text`、`contact{phone,email,address}`、`min_height_px` 封面最小高。

## 改版式

全部版式在 `catalog_generator.py` 的 `CSS_TMPL`（单处写死原则）：
- 封面 `.cover`（满屏品牌底+渐变遮罩+大标题）、章节头 `.sec-h`（色条+中英标题）
- 牌号卡 `.grade`（标题条+图位+成分块+热处理块+卖点）
- 联系页 `.contact`、页脚 `.foot`
- 产品图默认是 CSS 占位块 `.gb`；真实图片先 `--compress` 压好，再把 `.gb` 换成 `<img>` 本地引用

## 纪律

1. **脱敏红线**：真实客户/公司数据、产品图一律不进仓库；样本只放公开标准数据与占位
2. **改模板不改数据**：品牌差异走 `CatalogConfig`，不要手改生成的 HTML（数据变了就重跑）
3. **交付前必跑 `ocr_verify`**：像素抽检非空白才允许发客户；PDF 交付再看一眼页数与中文层（pypdf/pdftotext）
