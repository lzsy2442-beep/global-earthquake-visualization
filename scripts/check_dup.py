# -*- coding: utf-8 -*-
import json, os, collections

DATA_DIR = r"D:\LZSY\地震汇编\data"
ts_all = []
id_map = {}
for year in range(2020, 2026):
    with open(os.path.join(DATA_DIR, f"usgs_m5_{year}.geojson"), encoding="utf-8") as f:
        data = json.load(f)
    for ft in data["features"]:
        t = ft["properties"]["time"]
        ts_all.append(t)
        id_map.setdefault(t, []).append((ft["id"], ft["properties"]["place"], ft["properties"]["mag"]))

dups = {t: v for t, v in id_map.items() if len(v) > 1}
print("duplicate timestamps:", len(dups))
for t, v in list(dups.items())[:20]:
    print(t, v)
