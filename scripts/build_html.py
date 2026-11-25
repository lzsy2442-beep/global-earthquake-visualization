# -*- coding: utf-8 -*-
"""将紧凑数据注入页面模板，输出最终单文件 HTML。"""
import os, json

BASE = r"D:\LZSY\地震汇编"
TEMPLATE = os.path.join(BASE, "scripts", "page_template.html")
DATA = os.path.join(BASE, "data", "earthquakes_1995_2026.json")
OUT = os.path.join(BASE, "1995-2026年全球5级以上地震汇编.html")

with open(TEMPLATE, encoding="utf-8") as f:
    tpl = f.read()
with open(DATA, encoding="utf-8") as f:
    data = f.read()

token = "__EQ_DATA__"
assert token in tpl, "placeholder missing"
html = (tpl.replace(token, data)
           .replace("__ALL_POINTS_MODE__", "false")
           .replace('"__DATA_URL__"', '""'))
with open(OUT, "w", encoding="utf-8") as f:
    f.write(html)

print("output:", OUT)
print("size %.2f MB" % (os.path.getsize(OUT) / 1048576))
