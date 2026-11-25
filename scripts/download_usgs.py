# -*- coding: utf-8 -*-
"""按年下载 USGS FDSN-WS 全球 M5+ 地震目录（geojson），带重试与校验。"""
import urllib.request, json, time, os, sys

OUT_DIR = r"D:\LZSY\地震汇编\data"
os.makedirs(OUT_DIR, exist_ok=True)

BASE = "https://earthquake.usgs.gov/fdsnws/event/1/query"

def fetch_year(year):
    url = (f"{BASE}?format=geojson&starttime={year}-01-01&endtime={year+1}-01-01"
           "&minmagnitude=5.0&orderby=time-asc")
    last_err = None
    for attempt in range(4):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=180) as resp:
                raw = resp.read()
            data = json.loads(raw.decode("utf-8"))
            feats = data["features"]
            # 基本校验：时间升序、震级阈值、年份归属
            prev = 0
            for ft in feats:
                t = ft["properties"]["time"]
                m = ft["properties"]["mag"]
                assert t >= prev, "not ascending"
                assert m is not None and m >= 5.0, "mag below 5"
                prev = t
            out = os.path.join(OUT_DIR, f"usgs_m5_{year}.geojson")
            with open(out, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False)
            # 唯一性校验
            ids = [ft["id"] for ft in feats]
            assert len(ids) == len(set(ids)), "duplicate ids"
            t0 = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(feats[0]["properties"]["time"]/1000))
            t1 = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(feats[-1]["properties"]["time"]/1000))
            print(f"{year}: {len(feats)} events, {t0} UTC -> {t1} UTC, saved {out}")
            return len(feats)
        except Exception as e:
            last_err = e
            wait = 3 * (attempt + 1)
            print(f"{year} attempt {attempt+1} failed: {e}; retry in {wait}s")
            time.sleep(wait)
    raise RuntimeError(f"fetch {year} failed: {last_err}")

if __name__ == "__main__":
    years = [int(y) for y in sys.argv[1:]] or list(range(2020, 2026))
    total = 0
    for y in years:
        total += fetch_year(y)
    print("DONE. total events:", total)
