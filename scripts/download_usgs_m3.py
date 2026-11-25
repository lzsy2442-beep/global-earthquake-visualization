# -*- coding: utf-8 -*-
"""按时间窗下载 USGS FDSN-WS 全球 M3+ 地震目录（geojson），自动分块避开 2 万条上限。
   按年汇总保存为 usgs_m3_{year}.geojson。带重试、去重、校验。"""
import urllib.request, json, time, os, sys, datetime

OUT_DIR = r"D:\LZSY\地震汇编\data\m3"
os.makedirs(OUT_DIR, exist_ok=True)
BASE = "https://earthquake.usgs.gov/fdsnws/event/1/query"

def _get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=300) as resp:
        return resp.read()

def fetch_window(start, end, depth=0):
    """返回 [start,end) 窗口的 features；若超 2 万上限则二分。"""
    url = (f"{BASE}?format=geojson&starttime={start}&endtime={end}"
           "&minmagnitude=3.0&orderby=time-asc")
    for attempt in range(5):
        try:
            raw = _get(url)
            return json.loads(raw.decode("utf-8"))["features"]
        except urllib.error.HTTPError as e:
            if e.code == 400 and depth < 6:
                # 多半是事件数超限，按时间中点二分
                d0 = datetime.date.fromisoformat(start)
                d1 = datetime.date.fromisoformat(end)
                mid = d0 + (d1 - d0) / 2
                ms = mid.isoformat()
                left = fetch_window(start, ms, depth + 1)
                right = fetch_window(ms, end, depth + 1)
                return left + right
            wait = 4 * (attempt + 1)
            print(f"  window {start}~{end} HTTP {e.code}, retry in {wait}s")
            time.sleep(wait)
        except Exception as e:
            wait = 4 * (attempt + 1)
            print(f"  window {start}~{end} {e}, retry in {wait}s")
            time.sleep(wait)
    raise RuntimeError(f"window failed: {start} ~ {end}")

def month_windows(year):
    if year < 2026:
        for m in range(1, 13):
            s = datetime.date(year, m, 1)
            e = datetime.date(year + 1, 1, 1) if m == 12 else datetime.date(year, m + 1, 1)
            yield s.isoformat(), e.isoformat()
    else:
        # 2026：截至今天（含）
        today = datetime.date.today()
        for m in range(1, 13):
            s = datetime.date(year, m, 1)
            if s > today:
                break
            if m == 12:
                e = datetime.date(year + 1, 1, 1)
            else:
                e = datetime.date(year + 1, 1, 1)
                nm = datetime.date(year, m + 1, 1)
                e = nm
            if e > today:
                e = today + datetime.timedelta(days=1)
            yield s.isoformat(), e.isoformat()

def process_year(year):
    out = os.path.join(OUT_DIR, f"usgs_m3_{year}.geojson")
    if os.path.exists(out):
        with open(out, encoding="utf-8") as f:
            n = len(json.load(f)["features"])
        print(f"{year}: already exists ({n}), skip")
        return n
    feats = []
    for s, e in month_windows(year):
        feats.extend(fetch_window(s, e))
    # 去重（二分边界可能重复）+ 时间升序
    seen = set()
    uniq = []
    for ft in feats:
        if ft["id"] in seen:
            continue
        seen.add(ft["id"])
        uniq.append(ft)
    uniq.sort(key=lambda ft: ft["properties"]["time"])
    cleaned = []
    prev = 0
    for ft in uniq:
        p = ft["properties"]
        if p.get("time") is None or p.get("mag") is None or p["mag"] < 3.0:
            print(f"  drop invalid in {year}: id={ft.get('id')} mag={p.get('mag')}")
            continue
        if p["time"] < prev:
            print(f"  out-of-order in {year}: id={ft.get('id')}")
        cleaned.append(ft)
        prev = max(prev, p["time"])
    uniq = cleaned
    with open(out, "w", encoding="utf-8") as f:
        json.dump({"type": "FeatureCollection", "features": uniq}, f, ensure_ascii=False)
    print(f"{year}: {len(uniq)} events -> {out}", flush=True)
    return len(uniq)

if __name__ == "__main__":
    years = [int(y) for y in sys.argv[1:]] or list(range(1995, 2027))
    total = 0
    for y in years:
        total += process_year(y)
    print("DONE. total events:", total)
