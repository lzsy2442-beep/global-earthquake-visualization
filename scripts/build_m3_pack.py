# -*- coding: utf-8 -*-
"""把 data/m3/usgs_m3_*.geojson 打包为固定 20 字节/条的二进制（ArrayBuffer），
   再 base64 输出，供单文件 HTML 内联。

字段布局（小端）：
    0-3   时间戳低 32 位 (uint32)
    4-5   时间戳高 16 位 (uint16)
    6-9   纬度 ×1e4 (int32)
    10-13 经度 ×1e4 (int32)
    14-15 深度 ×10 (int16，-32768 表示空)
    16    震级 ×10 − 30 (uint8)
    17    震级类型编号 (uint8)
    18-19 地区编号 (uint16)  ← 新增，指向 rt 对照表，用于国家级地名检索
"""
import json, os, base64, struct, glob, sys

BASE = r"D:\LZSY\地震汇编"
SRC_DIR = os.path.join(BASE, "data", "m3")
OUT = os.path.join(BASE, "data", "m3_pack.json")

sys.path.insert(0, os.path.join(BASE, "scripts"))
from regions import region_of, region_cn  # noqa: E402

files = sorted(glob.glob(os.path.join(SRC_DIR, "usgs_m3_*.geojson")),
               key=lambda p: int(os.path.basename(p).split("_")[2].split(".")[0]))
feats = []
for fp in files:
    with open(fp, encoding="utf-8") as f:
        feats.extend(json.load(f)["features"])
print("source files:", len(files), "raw features:", len(feats))

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
print("unique:", len(uniq))

# magType 枚举
mt_list = []
mt_idx = {}


def mt_id(s):
    s = s or ""
    if s not in mt_idx:
        mt_idx[s] = len(mt_list)
        mt_list.append(s)
    return mt_idx[s]


# 地区枚举（英文名 -> [英文, 中文]）
rt_list = []
rt_idx = {}


def rt_id(place):
    r = region_of(place)
    if not r:
        r = "Unknown"
    if r not in rt_idx:
        rt_idx[r] = len(rt_list)
        rt_list.append([r, region_cn(r)])
    return rt_idx[r]


STRIDE = 20
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
    rid = rt_id(p.get("place"))
    struct.pack_into("<IHiihBBH", buf, o,
                     t & 0xffffffff, (t >> 32) & 0xffff,
                     la, lo, dp, mg, mt_id(p.get("magType")), rid)
    o += STRIDE

b64 = base64.b64encode(bytes(buf)).decode("ascii")
payload = {"b": b64, "mt": mt_list, "rt": rt_list, "n": len(uniq), "stride": STRIDE}
with open(OUT, "w", encoding="utf-8") as f:
    json.dump(payload, f, ensure_ascii=False)

print("binary %.2f MB, base64 %.2f MB" % (len(buf) / 1048576, len(b64) / 1048576))
print("magType table:", len(mt_list))
print("region table:", len(rt_list), " 样例:", rt_list[:5])
print("output:", OUT)
