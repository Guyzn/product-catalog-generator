#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
catalog_generator.py — 品牌化产品目录生成器 (通用/脱敏版)

流水线：
  HTML(品牌化自包含)  ──►  Playwright 渲染 PDF  ──►  PIL 压缩图片  ──►  pdftoppm+PIL 像素抽检校验

本文件从一个生产用目录生成脚本脱敏重构而来：
  - 品牌色 / 公司名 / 网站 / Logo 全部参数化 (CatalogConfig)，不写死任何公司
  - 产品图用 CSS 占位块代替，仓库自包含、零外部图片依赖、不泄露真实目录
  - 只保留可复用的「排版引擎 + 渲染/压缩/校验」方法论

依赖(可选，按需安装)：
  pip install playwright pillow
  playwright install chromium        # 仅 render_pdf 需要
  poppler (pdftoppm)                 # 仅 ocr_verify 需要 (mac: brew install poppler)

运行：
  python catalog_generator.py                # 仅生成 sample_catalog.html
  python catalog_generator.py --pdf          # 生成 HTML + 渲染 PDF
  python catalog_generator.py --compress imgs # 压缩 imgs/ 下图片
"""
import os
import sys
import argparse

# ---------------------------------------------------------------------------
# 配置
# ---------------------------------------------------------------------------
class CatalogConfig:
    def __init__(self, **kw):
        self.brand = kw.get("brand", "#1B3A5C")        # 主色(钢蓝)
        self.accent = kw.get("accent", "#E8712C")      # 强调色(橙)
        self.light = kw.get("light", "#F5F5F5")
        self.ink = kw.get("ink", "#222222")
        self.company = kw.get("company", "YOUR COMPANY")
        self.company_en = kw.get("company_en", "Your Company Ltd.")
        self.website = kw.get("website", "www.example.com")
        self.logo_text = kw.get("logo_text", "◣ COMPANY")
        self.contact = kw.get("contact", {})           # {phone,email,address}
        self.min_height_px = kw.get("min_height_px", 680)


# ---------------------------------------------------------------------------
# HTML 模板引擎
# ---------------------------------------------------------------------------
CSS_TMPL = """
*{box-sizing:border-box;}
html,body{margin:0;padding:0;font-family:'Noto Sans CJK SC','Noto Sans SC',sans-serif;color:%(brand)s;background:#fff;font-size:13px;line-height:1.55;}
a{color:%(accent)s;text-decoration:none;}
.wrap{max-width:960px;margin:0 auto;padding:0 18px 40px;}
.cover{height:100vh;min-height:%(minh)spx;background:%(brand)s;position:relative;display:flex;flex-direction:column;justify-content:flex-end;color:#fff;}
.cover::after{content:'';position:absolute;inset:0;background:linear-gradient(180deg,rgba(11,30,48,.35) 0%%,rgba(11,30,48,.78) 100%%);}
.cover .inner{position:relative;z-index:2;padding:48px 44px 54px;}
.cover .logo{font-weight:800;letter-spacing:2px;font-size:15px;opacity:.9;}
.cover h1{font-size:46px;margin:18px 0 6px;line-height:1.05;font-weight:800;letter-spacing:1px;}
.cover h1 small{display:block;font-size:20px;font-weight:500;opacity:.92;letter-spacing:6px;margin-top:8px;}
.cover .btn{display:inline-block;margin-top:22px;background:%(accent)s;color:#fff;padding:10px 20px;border-radius:4px;font-weight:700;letter-spacing:1px;}
.sec{page-break-before:always;margin-top:34px;}
.sec-h{display:flex;align-items:center;gap:12px;margin:10px 0 18px;}
.sec-h .bar{width:6px;height:30px;background:%(accent)s;border-radius:3px;}
.sec-h h2{font-size:23px;margin:0;color:%(brand)s;}
.sec-h .en{color:%(accent)s;font-size:13px;font-weight:600;letter-spacing:.5px;margin-left:auto;text-transform:uppercase;}
.lead{color:#444;margin:6px 0 18px;}
table{border-collapse:collapse;width:100%%;margin:12px 0;font-size:11.5px;page-break-inside:avoid;}
th,td{border:1px solid #cdd6e0;padding:5px 7px;text-align:center;vertical-align:middle;}
th{background:%(brand)s;color:#fff;font-weight:700;}
tbody tr:nth-child(even){background:%(light)s;}
.grade{page-break-inside:avoid;margin:22px 0;border:1px solid #dde3ec;border-radius:8px;overflow:hidden;}
.grade .gh{background:%(light)s;color:#fff;padding:12px 16px;display:flex;align-items:baseline;gap:12px;}
.grade .gh .g{font-size:20px;font-weight:800;}
.grade .gh .std{margin-left:auto;font-size:12px;opacity:.9;}
.grade .gb{background:%(brand)s;display:flex;align-items:center;justify-content:center;min-height:200px;color:%(accent)s;font-weight:800;font-size:14px;letter-spacing:1px;}
.grade .gi{padding:14px 18px;}
.kv{display:grid;grid-template-columns:repeat(2,1fr);gap:4px 22px;margin:8px 0;}
.kv b{color:%(brand)s;}
.chem{background:%(brand)s;color:#fff;border-radius:6px;padding:10px 12px;margin:8px 0;font-size:12px;line-height:1.7;}
.ht{background:#fafbfc;border-left:3px solid %(accent)s;padding:8px 12px;margin:8px 0;font-size:12px;}
.banner{background:%(accent)s;color:#fff;text-align:center;padding:16px;font-weight:700;letter-spacing:1px;margin:16px 0;border-radius:6px;}
.contact{background:%(brand)s;color:#fff;padding:30px;border-radius:8px;}
.contact .big{font-size:22px;font-weight:800;letter-spacing:1px;}
.contact table{border:none;margin:0;color:#fff;font-size:13px;}
.contact td{border:none;text-align:left;padding:3px 0;}
.contact td.k{color:%(accent)s;width:120px;font-weight:700;}
.foot{text-align:center;color:#999;font-size:11px;margin-top:30px;page-break-before:always;}
@media print{.cover{height:100vh;} @page{size:A4;margin:10mm;}}
"""


def h2(cn, en):
    return '<div class="sec-h"><span class="bar"></span><h2>%s</h2><span class="en">%s</span></div>' % (cn, en)


def table(headers, rows, leftfirst=False):
    th = "".join('<th class="l">%s</th>' % x if (leftfirst and i == 0) else '<th>%s</th>' % x
                 for i, x in enumerate(headers))
    body = ""
    for r in rows:
        tds = "".join('<td class="l">%s</td>' % c if (leftfirst and i == 0) else '<td>%s</td>' % c
                     for i, c in enumerate(r))
        body += "<tr>%s</tr>" % tds
    return "<table><thead><tr>%s</tr></thead><tbody>%s</tbody></table>" % (th, body)


def grade_card(g, cfg):
    chem = " ".join("%s %s" % (k, v) for k, v in g.get("chem", {}).items())
    blk = "<div class='grade'>"
    blk += "<div class='gh'><span class='g'>%s</span><span class='std'>%s</span></div>" % (g["grade"], g.get("std", ""))
    blk += "<div class='gb'>PRODUCT IMAGE<br>%s</div>" % g["grade"]
    blk += "<div class='gi'>"
    blk += "<div class='chem'>Chemical: %s</div>" % chem
    blk += "<div class='kv'><div><b>Steelmaking:</b> %s</div><div><b>Forming:</b> %s</div></div>" % (
        g.get("sm", "-"), g.get("ft", "-"))
    blk += "<div class='ht'><b>Heat Treatment:</b> %s</div>" % g.get("ht", "-")
    blk += "<p class='lead'>%s</p>" % g.get("desc", "")
    blk += "</div></div>"
    return blk


def build_html(cfg, grades, title_cn="产品目录", title_en="PRODUCTS PORTFOLIO"):
    css = CSS_TMPL % dict(brand=cfg.brand, accent=cfg.accent, light=cfg.light,
                          ink=cfg.ink, minh=cfg.min_height_px)
    parts = []
    parts.append("<!DOCTYPE html><html lang='zh-CN'><head><meta charset='utf-8'>")
    parts.append("<title>%s / %s</title><style>%s</style></head><body>" % (cfg.company, title_cn, css))
    # cover
    parts.append("""<div class="cover"><div class="inner">
      <div class="logo">%s</div>
      <h1>%s<small>%s</small></h1>
      <div class="btn">%s</div></div></div>""" % (cfg.logo_text, title_cn, title_en, cfg.website))
    # grades
    parts.append("<div class='wrap sec'>")
    parts.append(h2("重点牌号 / Key Grades", "Key Grades"))
    for g in grades:
        parts.append(grade_card(g, cfg))
    parts.append("</div>")
    # contact
    c = cfg.contact
    parts.append("<div class='wrap sec'><div class='contact'>")
    parts.append("<div class='big'>%s</div>" % cfg.company_en)
    if c.get("phone"):
        parts.append("<table><tr><td class='k'>Phone</td><td>%s</td></tr>" % c["phone"])
    if c.get("email"):
        parts.append("<tr><td class='k'>Email</td><td>%s</td></tr>" % c["email"])
    if c.get("address"):
        parts.append("<tr><td class='k'>Address</td><td>%s</td></tr>" % c["address"])
    parts.append("</table></div></div>")
    parts.append("<div class='foot'>%s · Generated by catalog_generator · © %s</div>" % (cfg.company, cfg.company))
    parts.append("</body></html>")
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# 渲染 / 压缩 / 校验
# ---------------------------------------------------------------------------
def render_pdf(html_path, pdf_path, chromium=None):
    """用 Playwright(headless chromium) 把 HTML 渲染成像素级 PDF。"""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        raise SystemExit("需要 playwright: pip install playwright && playwright install chromium")
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=chromium) if chromium else p.chromium.launch()
        page = browser.new_page()
        page.goto("file://" + os.path.abspath(html_path))
        page.pdf(path=pdf_path, format="A4", print_background=True,
                 margin={"top": "10mm", "bottom": "10mm", "left": "10mm", "right": "10mm"})
        browser.close()
    return pdf_path


def compress_images(image_dir, max_width=1240, quality=85):
    """PIL 批量压缩：等比缩放到 max_width 以内，存 JPEG q85。返回处理数。"""
    from PIL import Image
    n = 0
    for fn in os.listdir(image_dir):
        p = os.path.join(image_dir, fn)
        if not fn.lower().endswith((".png", ".jpg", ".jpeg")):
            continue
        im = Image.open(p).convert("RGB")
        if im.width > max_width:
            h = int(im.height * max_width / im.width)
            im = im.resize((max_width, h))
        out = os.path.splitext(p)[0] + ".jpg"
        im.save(out, "JPEG", quality=quality)
        n += 1
    return n


def ocr_verify(pdf_path, min_pages=1):
    """校验三板斧之一：pdftoppm 转图 + PIL 像素抽检，确认 PDF 非空白。返回每页是否非空。"""
    import subprocess
    from PIL import Image
    import tempfile
    d = tempfile.mkdtemp()
    try:
        subprocess.run(["pdftoppm", "-png", "-r", "80", pdf_path, os.path.join(d, "pg")],
                       check=True, capture_output=True)
    except FileNotFoundError:
        raise SystemExit("需要 poppler(pdftoppm): mac 用 brew install poppler")
    results = []
    for pg in sorted(os.listdir(d)):
        im = Image.open(os.path.join(d, pg)).convert("L")
        # 非空白判定：像素标准差 > 阈值
        import statistics
        px = list(im.getdata())
        sd = statistics.pstdev(px)
        results.append((pg, sd > 8))
    return results


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdf", action="store_true", help="渲染 PDF(需 playwright)")
    ap.add_argument("--html-out", default="sample_catalog.html")
    ap.add_argument("--pdf-out", default="sample_catalog.pdf")
    ap.add_argument("--chromium", default=None, help="chromium 可执行路径")
    args = ap.parse_args()

    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from sample_data import SAMPLE_GRADES, SAMPLE_CONFIG

    cfg = CatalogConfig(**SAMPLE_CONFIG)
    html = build_html(cfg, SAMPLE_GRADES)
    with open(args.html_out, "w", encoding="utf-8") as f:
        f.write(html)
    print("HTML written:", args.html_out, len(html), "bytes")

    if args.pdf:
        render_pdf(args.html_out, args.pdf_out, args.chromium)
        print("PDF written:", args.pdf_out)
        try:
            print("OCR verify:", ocr_verify(args.pdf_out))
        except SystemExit as e:
            print("skip OCR:", e)


if __name__ == "__main__":
    main()
