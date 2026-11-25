# -*- coding: utf-8 -*-
"""M3+ 全点状版本：内联二进制压缩包，输出独立单文件 HTML（无地名，位置以经纬度显示）。"""
import os

BASE = r"D:\LZSY\地震汇编"
TEMPLATE = os.path.join(BASE, "scripts", "page_template_m3.html")
PACK = os.path.join(BASE, "data", "m3_pack.json")
OUT = os.path.join(BASE, "1995-2026年全球3级以上地震点状图.html")

with open(TEMPLATE, encoding="utf-8") as f:
    tpl = f.read()
with open(PACK, encoding="utf-8") as f:
    pack = f.read()

assert "__EQ_DATA__" in tpl and "__ALL_POINTS_MODE__" in tpl
html = (tpl.replace("__EQ_DATA__", pack)
           .replace("__ALL_POINTS_MODE__", "true")
           .replace("__M3_META__", "null")
           .replace('"__DATA_URL__"', '""'))
with open(OUT, "w", encoding="utf-8") as f:
    f.write(html)

print("output:", OUT)
print("size %.2f MB" % (os.path.getsize(OUT) / 1048576))
