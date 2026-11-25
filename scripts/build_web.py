# -*- coding: utf-8 -*-
"""生成网页版：轻量外壳 HTML + 外置数据文件。

与 build_html*.py 的区别：
- 单文件版把数据内联进 HTML（适合离线分发）；
- 网页版把数据放到 site/data/ 下，首屏只有界面（约 100 KB），
  数据由前端 XHR 拉取并显示进度，还能被浏览器长期缓存。

M3 数据按「近 N 年 / 更早历史」切成两段：
- 默认只加载近 N 年（约 1.7 MB），首屏从 8 MB 降到这个量级；
- 更早的历史放在 archive 文件里，页面提供按钮按需加载。

产物：
  site/m5-cluster.html         外壳，数据 /data/eq-m5.json
  site/m5-points.html          外壳，同上（两个页面共用一份数据）
  site/m3-points.html          外壳，数据 /data/m3-recent.bin（+ /data/m3-archive.bin）
  site/data/eq-m5.json         6.85 MB 紧凑 JSON
  site/data/m3-recent.bin      近 N 年原始二进制
  site/data/m3-archive.bin     N 年以前的原始二进制
"""
import os
import json
import base64
import datetime

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(BASE, "site")
DATA = os.path.join(BASE, "data")
OUTDATA = os.path.join(SITE, "data")

RECENT_YEARS = 5          # 默认加载最近多少年
YEAR_MS = 365.2425 * 86400 * 1000


def read_text(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def record_time(rec):
    return int.from_bytes(rec[0:4], "little") + int.from_bytes(rec[4:6], "little") * 4294967296


def split_bin(raw, stride, cutoff_ms):
    old, new = [], []
    for off in range(0, len(raw) - stride + 1, stride):
        rec = raw[off:off + stride]
        (new if record_time(rec) >= cutoff_ms else old).append(rec)
    return b"".join(old), b"".join(new)


def render(tpl, data_url, all_points, m3_meta=None, archive_url="", archive_label=""):
    html = (tpl.replace("__EQ_DATA__", "null")
               .replace("__ALL_POINTS_MODE__", "true" if all_points else "false")
               .replace('"__DATA_URL__"', '"%s"' % data_url)
               .replace('"__ARCHIVE_URL__"', '"%s"' % archive_url)
               .replace('"__ARCHIVE_LABEL__"', '"%s"' % archive_label))
    if m3_meta is not None:
        html = html.replace("__M3_META__", json.dumps(m3_meta, ensure_ascii=False, separators=(",", ":")))
    for token in ("__EQ_DATA__", "__DATA_URL__", "__ALL_POINTS_MODE__", "__M3_META__",
                  "__ARCHIVE_URL__", "__ARCHIVE_LABEL__"):
        if token in html:
            raise SystemExit("占位符未替换: " + token)
    return html


def main():
    os.makedirs(OUTDATA, exist_ok=True)

    tpl_m5 = read_text(os.path.join(BASE, "scripts", "page_template.html"))
    tpl_m3 = read_text(os.path.join(BASE, "scripts", "page_template_m3.html"))

    # --- M5：紧凑 JSON 原样落盘
    m5_text = read_text(os.path.join(DATA, "earthquakes_1995_2026.json"))
    n_m5 = len(json.loads(m5_text))
    with open(os.path.join(OUTDATA, "eq-m5.json"), "w", encoding="utf-8", newline="\n") as f:
        f.write(m5_text)

    # --- M3：Base64 还原成二进制，再按时间切成「近 N 年 / 更早」
    with open(os.path.join(DATA, "m3_pack.json"), encoding="utf-8") as f:
        pack = json.load(f)
    raw = base64.b64decode(pack["b"])
    stride = pack["stride"]
    n_all = pack["n"]
    max_t = record_time(raw[(n_all - 1) * stride:(n_all - 1) * stride + stride])
    min_t = record_time(raw[0:stride])
    cutoff_ms = max_t - RECENT_YEARS * YEAR_MS

    older, recent = split_bin(raw, stride, cutoff_ms)
    with open(os.path.join(OUTDATA, "m3-recent.bin"), "wb") as f:
        f.write(recent)
    with open(os.path.join(OUTDATA, "m3-archive.bin"), "wb") as f:
        f.write(older)

    # 旧的整包文件已不再使用
    stale = os.path.join(OUTDATA, "m3-pack.bin")
    if os.path.exists(stale):
        os.remove(stale)

    n_recent = len(recent) // stride
    n_old = len(older) // stride
    year_recent = datetime.datetime.fromtimestamp(cutoff_ms / 1000, datetime.UTC).year
    year_min = datetime.datetime.fromtimestamp(min_t / 1000, datetime.UTC).year
    label = "加载 %d–%d 完整历史（约 %.1f MB）" % (year_min, year_recent - 1, len(older) / 1048576.0)

    meta = {"n": n_all, "stride": stride, "mt": pack["mt"]}
    jobs = [
        ("m5-cluster.html", tpl_m5, "/data/eq-m5.json", False, None, "", ""),
        ("m5-points.html", tpl_m5, "/data/eq-m5.json", True, None, "", ""),
        ("m3-points.html", tpl_m3, "/data/m3-recent.bin", True, meta, "/data/m3-archive.bin", label),
    ]
    for name, tpl, url, all_points, m3_meta, arc_url, arc_label in jobs:
        html = render(tpl, url, all_points, m3_meta, arc_url, arc_label)
        path = os.path.join(SITE, name)
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(html)
        print("%-18s %7.1f KB" % (name, os.path.getsize(path) / 1024.0))

    print("%-18s %7.1f MB  (%d 条)" % ("data/eq-m5.json", os.path.getsize(os.path.join(OUTDATA, "eq-m5.json")) / 1048576.0, n_m5))
    print("%-18s %7.1f MB  (%d 条，%d 年起)" % ("data/m3-recent.bin", len(recent) / 1048576.0, n_recent, year_recent))
    print("%-18s %7.1f MB  (%d 条)" % ("data/m3-archive.bin", len(older) / 1048576.0, n_old))
    print("按钮文案: " + label)


if __name__ == "__main__":
    main()
