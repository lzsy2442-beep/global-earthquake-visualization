# -*- coding: utf-8 -*-
"""把 data/m3/usgs_m3_*.geojson 打包为固定 18 字节/条的二进制（ArrayBuffer），
   再 base64 输出，供单文件 HTML 内联。字段：t(48bit) lat lon depth mag magType。
   不含地名（体积约束）。"""
import json, os, base64, struct, glob

BASE = r"D:\LZSY\地震汇编"
SRC_DIR = os.path.join(BASE, "data", "m3")
OUT = os.path.join(BASE, "data", "m3_pack.json")

files = sorted(glob.glob(os.path.join(SRC_DIR, "usgs_m3_*.geojson")),
               key=lambda p: int(os.path.basename(p).split("_")[2].split(".")[0]))
feats = []
for fp in files:
    with open(fp, encoding="utf-8") as f:
        feats.extend(json.load(f)["features"])

# 时间升序 + 物理去重（同 time/lat/lon/mag）
feats.sort(key=lambda ft: ft["properties"]["time"])
seen = set()
uniq = []
for ft in feats:
    p = ft["properties"]
    lon, lat, depth = ft["geometry"]["coordinates"]
    key = (p["time"], round(lat, 4), round(lon, 4), p["mag"])
    if key in seen:
        continue
    seen.add(key)
    uniq.append(ft)

# magType 枚举
mt_list = []
mt_idx = {}
def mt_id(s):
    s = s or ""
    if s not in mt_idx:
        mt_idx[s] = len(mt_list)
        mt_list.append(s)
    return mt_idx[s]

STRIDE = 18
buf = bytearray(STRIDE * len(uniq))
o = 0
for ft in uniq:
    p = ft["properties"]
    lon, lat, depth = ft["geometry"]["coordinates"]
    t = int(p["time"])
    la = int(round(lat * 10000))
    lo = int(round(lon * 10000))
    if depth is None:
        dp = -32768
    else:
        dp = int(round(depth * 10))
        dp = max(-32767, min(32767, dp))
    mg = int(round(float(p["mag"]) * 10)) - 30
    mg = max(0, min(255, mg))
    struct.pack_into("<IHiihBB", buf, o,
                     t & 0xffffffff, (t >> 32) & 0xffff,
                     la, lo, dp, mg, mt_id(p.get("magType")))
    o += STRIDE

b64 = base64.b64encode(bytes(buf)).decode("ascii")
payload = {"b": b64, "mt": mt_list, "n": len(uniq), "stride": STRIDE}
with open(OUT, "w", encoding="utf-8") as f:
    json.dump(payload, f, ensure_ascii=False)

print("source files:", len(files))
print("raw features:", len(feats), "unique:", len(uniq))
print("binary %.2f MB, base64 %.2f MB" %
      (len(buf) / 1048576, len(b64) / 1048576))
print("magType table:", mt_list)
print("output:", OUT)
