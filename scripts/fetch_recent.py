# -*- coding: utf-8 -*-
"""增量抓取 USGS 最新地震，生成 site/data/recent-m5.json / recent-m3.json。

设计要点：
- 只拉「最近窗口 + 上次同步点之后」的数据，不重复下载历史。
- 与已有文件合并、去重、按时间升序，滚动保留最近 KEEP_DAYS 天。
- 输出格式与页面内联数据完全一致：[t, lat, lon, depth, mag, magType, en, zh]
- 页面加载时按时间戳去重合并，只吸收比内联数据更新的记录。

用法：
    python scripts/fetch_recent.py            # 同时更新 M5 与 M3
    python scripts/fetch_recent.py --only m5  # 只更新 M5
"""
import json
import os
import sys
import time
import argparse
import urllib.parse
import urllib.request

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(BASE, "site", "data")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from place_translate import translate_place  # noqa: E402

USGS = "https://earthquake.usgs.gov/fdsnws/event/1/query"
KEEP_DAYS = 30          # 滚动保留天数
OVERLAP_HOURS = 6       # 与上次同步点重叠，避免边界漏事件
UA = "earthquake-visualization/1.0 (daily refresh)"

TARGETS = [
    {"key": "m5", "minmag": 5.0, "out": "recent-m5.json"},
    {"key": "m3", "minmag": 3.0, "out": "recent-m3.json"},
]


def iso(ms):
    return time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(ms / 1000.0))


def query(minmag, start_ms, end_ms):
    q = urllib.parse.urlencode({
        "format": "geojson",
        "starttime": iso(start_ms),
        "endtime": iso(end_ms),
        "minmagnitude": minmag,
        "orderby": "time-asc",
        "limit": 20000,
    })
    req = urllib.request.Request(USGS + "?" + q, headers={"User-Agent": UA})
    last = None
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=90) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as exc:  # noqa: BLE001
            last = exc
            time.sleep(3 * (attempt + 1))
    raise RuntimeError("USGS 请求失败: %s" % last)


def to_rows(geo, minmag):
    rows = []
    for feat in geo.get("features") or []:
        prop = feat.get("properties") or {}
        geom = feat.get("geometry") or {}
        coord = geom.get("coordinates") or []
        if len(coord) < 3:
            continue
        t_ms, mag = prop.get("time"), prop.get("mag")
        if t_ms is None or mag is None or float(mag) < minmag - 1e-9:
            continue
        place = (prop.get("place") or "").strip()
        try:
            zh = translate_place(place) if place else ""
        except Exception:  # noqa: BLE001
            zh = ""
        depth = coord[2]
        rows.append([
            int(t_ms),
            round(float(coord[1]), 4),
            round(float(coord[0]), 4),
            None if depth is None else round(float(depth), 1),
            round(float(mag), 1),
            prop.get("magType") or "",
            place,
            zh,
        ])
    return rows


def load_existing(path):
    if not os.path.exists(path):
        return []
    try:
        with open(path, encoding="utf-8") as f:
            pack = json.load(f)
        return pack.get("events") or []
    except Exception:  # noqa: BLE001
        return []


def merge(existing, fresh, cutoff_ms):
    seen, out = set(), []
    for row in existing + fresh:
        if not row or len(row) < 5:
            continue
        if row[0] < cutoff_ms:
            continue
        key = (int(row[0]), round(float(row[1]), 3), round(float(row[2]), 3))
        if key in seen:
            continue
        seen.add(key)
        out.append(row)
    out.sort(key=lambda r: r[0])
    return out


def run(target):
    path = os.path.join(OUT_DIR, target["out"])
    now_ms = int(time.time() * 1000)
    cutoff = now_ms - KEEP_DAYS * 86400000

    existing = load_existing(path)
    last_t = max((r[0] for r in existing), default=0)
    start = max(last_t - OVERLAP_HOURS * 3600000, cutoff) if last_t else cutoff
    # 首次运行或断更太久时，直接拉满整个窗口
    if now_ms - start > KEEP_DAYS * 86400000:
        start = cutoff

    geo = query(target["minmag"], start, now_ms)
    fresh = to_rows(geo, target["minmag"])
    events = merge(existing, fresh, cutoff)

    os.makedirs(OUT_DIR, exist_ok=True)
    pack = {
        "updated": now_ms,
        "minmag": target["minmag"],
        "count": len(events),
        "events": events,
    }
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(pack, f, ensure_ascii=False, separators=(",", ":"))

    size_kb = os.path.getsize(path) / 1024.0
    print("%-22s 拉取 %4d 条 / 合并后 %5d 条 / %6.1f KB  窗口起点 %s"
          % (target["out"], len(fresh), len(events), size_kb, iso(start)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", choices=["m5", "m3"], help="只更新其中一个数据集")
    args = ap.parse_args()
    targets = [t for t in TARGETS if not args.only or t["key"] == args.only]
    for t in targets:
        run(t)


if __name__ == "__main__":
    main()
