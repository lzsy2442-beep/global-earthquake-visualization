# -*- coding: utf-8 -*-
import json, random
from datetime import datetime, timezone, timedelta

with open(r"D:\LZSY\地震汇编\data\earthquakes_2020_2026.json", encoding="utf-8") as f:
    recs = json.load(f)

bj = timezone(timedelta(hours=8))
def show(rec):
    t_utc = datetime.fromtimestamp(rec[0]/1000, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    t_bj = datetime.fromtimestamp(rec[0]/1000, tz=bj).strftime("%Y-%m-%d %H:%M:%S")
    print("EN :", rec[6])
    print("ZH :", rec[7])
    print("UTC:", t_utc, "| BJ:", t_bj, "| M:", rec[4], rec[5], "| depth:", rec[3], "| lat/lon:", rec[1], rec[2])
    print("-" * 70)

# 固定抽样：每年首条 + 若干随机
random.seed(7)
idxs = [0]
for year in range(2021, 2027):
    for i, r in enumerate(recs):
        if datetime.fromtimestamp(r[0]/1000, tz=timezone.utc).year == year:
            idxs.append(i)
            break
idxs += random.sample(range(len(recs)), 12)
for i in sorted(set(idxs)):
    show(recs[i])
