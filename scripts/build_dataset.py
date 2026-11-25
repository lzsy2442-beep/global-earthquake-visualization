# -*- coding: utf-8 -*-
"""整合 1995-2025 geojson 与 2026 Excel 为统一紧凑数据集。
记录格式: [t_ms, lat, lon, depth_km, mag, magType, en, zh]
"""
import json, os, sys
from datetime import datetime, timezone, timedelta
import openpyxl

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from place_translate import translate_place, unknown_items

DATA_DIR = r"D:\LZSY\地震汇编\data"
XLSX = r"D:\LZSY\地震汇编\2026年全球5级以上地震汇总.xlsx"
OUT_JSON = os.path.join(DATA_DIR, "earthquakes_1995_2026.json")

records = []
per_year = {}
seen_events = set()   # 物理事件去重键: (time, lat, lon, mag)
dropped = []

# ---- 1995-2025 geojson ----
for year in range(1995, 2026):
    with open(os.path.join(DATA_DIR, f"usgs_m5_{year}.geojson"), encoding="utf-8") as f:
        data = json.load(f)
    cnt = 0
    for ft in data["features"]:
        p = ft["properties"]
        lon, lat, depth = ft["geometry"]["coordinates"]
        key = (p["time"], round(lat, 4), round(lon, 4), p["mag"])
        if key in seen_events:
            dropped.append((year, ft["id"], p.get("place")))
            continue
        seen_events.add(key)
        en = p.get("place") or ""
        zh = translate_place(en)
        rec = [
            p["time"],
            round(lat, 4),
            round(lon, 4),
            round(depth, 1) if depth is not None else None,
            p["mag"],
            p.get("magType") or "",
            en,
            zh,
        ]
        records.append(rec)
        cnt += 1
    per_year[year] = cnt

# ---- 2026 Excel ----
wb = openpyxl.load_workbook(XLSX, read_only=True, data_only=True)
ws = wb["全球M5+地震目录"]
rows = list(ws.iter_rows(values_only=True))
wb.close()
cnt26 = 0
for r in rows[1:]:
    # 列: 序号, UTC时间, 北京时间, 震级, 震级类型, 深度, 纬度, 经度, 英文, 中文
    utc_str = str(r[1])
    dt = datetime.strptime(utc_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
    t_ms = int(dt.timestamp() * 1000)
    rec = [
        t_ms,
        round(float(r[6]), 4),
        round(float(r[7]), 4),
        round(float(r[5]), 1),
        float(r[3]),
        str(r[4]),
        str(r[8]),
        str(r[9]),
    ]
    key = (rec[0], rec[1], rec[2], rec[4])
    if key in seen_events:
        dropped.append((2026, r[0], r[8]))
        continue
    seen_events.add(key)
    records.append(rec)
    cnt26 += 1
per_year[2026] = cnt26

# ---- 全局校验 ----
assert len(records) == sum(per_year.values())
ts = [rec[0] for rec in records]
assert ts == sorted(ts), "not globally ascending"
keys_all = [(rec[0], rec[1], rec[2], rec[4]) for rec in records]
assert len(keys_all) == len(set(keys_all)), "duplicate physical events"
for rec in records:
    assert rec[4] >= 5.0
    assert -90 <= rec[1] <= 90 and -180 <= rec[2] <= 180
    assert rec[7]

with open(OUT_JSON, "w", encoding="utf-8") as f:
    json.dump(records, f, ensure_ascii=False, separators=(",", ":"))

print("per-year counts:", per_year)
print("dropped duplicate events:", dropped)
print("total records:", len(records))
print("output:", OUT_JSON, "size %.2f MB" % (os.path.getsize(OUT_JSON) / 1048576))
unk = unknown_items()
print("untranslated unique entries:", len(unk))
for u in unk[:50]:
    print("  UNK:", u)
