# -*- coding: utf-8 -*-
"""全点状版本：所有地震直接以单点标注（不聚类），输出独立单文件 HTML。"""
import os

BASE = r"D:\LZSY\地震汇编"
TEMPLATE = os.path.join(BASE, "scripts", "page_template.html")
DATA = os.path.join(BASE, "data", "earthquakes_1995_2026.json")
OUT = os.path.join(BASE, "1995-2026年全球5级以上地震点状图.html")

with open(TEMPLATE, encoding="utf-8") as f:
    tpl = f.read()
with open(DATA, encoding="utf-8") as f:
    data = f.read()

assert "__EQ_DATA__" in tpl and "__ALL_POINTS_MODE__" in tpl
html = (tpl.replace("__EQ_DATA__", data)
           .replace("__ALL_POINTS_MODE__", "true")
           .replace('"__DATA_URL__"', '""'))
with open(OUT, "w", encoding="utf-8") as f:
    f.write(html)

print("output:", OUT)
print("size %.2f MB" % (os.path.getsize(OUT) / 1048576))
