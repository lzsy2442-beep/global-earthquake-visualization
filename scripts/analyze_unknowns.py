# -*- coding: utf-8 -*-
"""扫描 1995-2025 geojson，分类输出未译条目，便于补词典。"""
import json, os, sys, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from place_translate import translate_place, unknown_items, _DIST_RE

DATA_DIR = r"D:\LZSY\地震汇编\data"
places = set()
for year in range(1995, 2026):
    with open(os.path.join(DATA_DIR, f"usgs_m5_{year}.geojson"), encoding="utf-8") as f:
        data = json.load(f)
    for ft in data["features"]:
        p = ft["properties"].get("place")
        if p:
            places.add(p)

for p in sorted(places):
    translate_place(p)

unk = unknown_items()
print("total unique places:", len(places), "unknown unique:", len(unk))

# 分类
dist_suffix = {}   # 距离模式且逗号后缀未译：收集后缀
dist_plain = set() # 距离模式无逗号整体未译
plain = set()      # 整体地名未译
for u in unk:
    m = _DIST_RE.match(u)
    if m:
        rest = m.group(3).strip()
        if "," in rest:
            name_part, suffix = rest.rsplit(",", 1)
            dist_suffix.setdefault(suffix.strip(), []).append(u)
        else:
            dist_plain.add(rest)
    else:
        plain.add(u)

print("\n=== 距离模式未知后缀（%d 个后缀）===" % len(dist_suffix))
for suf, items in sorted(dist_suffix.items()):
    print(f"[{suf}] x{len(items)} e.g. {items[0]}")

print("\n=== 距离模式无逗号整体（%d）===" % len(dist_plain))
for x in sorted(dist_plain):
    print(" ", x)

print("\n=== 整体地名未译（%d）===" % len(plain))
for x in sorted(plain):
    print(" ", x)
