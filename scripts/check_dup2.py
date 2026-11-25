# -*- coding: utf-8 -*-
import json, os

with open(r"D:\LZSY\地震汇编\data\usgs_m5_2021.geojson", encoding="utf-8") as f:
    data = json.load(f)
for ft in data["features"]:
    if ft["id"] in ("ak0212o88mof", "ak0212o88mqd"):
        print(json.dumps(ft, ensure_ascii=False, indent=1))
        print("-" * 60)
