# -*- coding: utf-8 -*-
import json, os, re, collections

DATA_DIR = r"D:\LZSY\地震汇编\data"
places = []
for year in range(2020, 2026):
    with open(os.path.join(DATA_DIR, f"usgs_m5_{year}.geojson"), encoding="utf-8") as f:
        data = json.load(f)
    for ft in data["features"]:
        places.append(ft["properties"]["place"] or "")

dist_re = re.compile(r"^\d+\s+km\s+(N|S|E|W|NE|NW|SE|SW|NNE|NNW|SSE|SSW|ENE|ESE|WNW|WSW)\s+of\s+(.+)$", re.I)
pattern_dist = 0
pattern_plain = 0
suffixes = collections.Counter()
plains = collections.Counter()
for p in places:
    m = dist_re.match(p)
    if m:
        pattern_dist += 1
        rest = m.group(2)
        if "," in rest:
            suffixes[rest.rsplit(",", 1)[1].strip()] += 1
        else:
            suffixes["<no-comma: " + rest + ">"] += 1
    else:
        pattern_plain += 1
        plains[p] += 1

print("total:", len(places), "dist-pattern:", pattern_dist, "plain:", pattern_plain)
print("\n=== suffixes (country/region after comma) ===")
for k, v in suffixes.most_common():
    print(f"{v:6d}  {k}")
print("\n=== ALL unique plain place names (unique:", len(plains), ") ===")
for k, v in plains.most_common():
    print(f"{v:6d}  {k}")
