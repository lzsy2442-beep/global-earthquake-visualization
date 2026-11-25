# -*- coding: utf-8 -*-
"""生成网页版：轻量外壳 HTML + 外置数据文件。

与 build_html*.py 的区别：
- 单文件版把数据内联进 HTML（适合离线分发）；
- 网页版把数据放到 site/data/ 下，首屏只有界面（约 100 KB），
  数据由前端 XHR 拉取并显示进度，还能被浏览器长期缓存。

产物：
  site/m5-cluster.html      外壳，数据 /data/eq-m5.json
  site/m5-points.html       外壳，同上（两个页面共用一份数据）
  site/m3-points.html       外壳，数据 /data/m3-pack.bin（原始二进制，省掉 Base64）
  site/data/eq-m5.json      6.85 MB 紧凑 JSON
  site/data/m3-pack.bin     10.4 MB 原始二进制
"""
import os
import json
import base64

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(BASE, "site")
DATA = os.path.join(BASE, "data")
OUTDATA = os.path.join(SITE, "data")


def read_json(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def render(tpl, data_url, all_points, m3_meta=None):
    html = (tpl.replace("__EQ_DATA__", "null")
               .replace("__ALL_POINTS_MODE__", "true" if all_points else "false")
               .replace('"__DATA_URL__"', '"%s"' % data_url))
    if m3_meta is not None:
        html = html.replace("__M3_META__", json.dumps(m3_meta, ensure_ascii=False, separators=(",", ":")))
    for token in ("__EQ_DATA__", "__DATA_URL__", "__ALL_POINTS_MODE__", "__M3_META__"):
        if token in html:
            raise SystemExit("占位符未替换: " + token)
    return html


def main():
    os.makedirs(OUTDATA, exist_ok=True)

    tpl_m5 = read_json(os.path.join(BASE, "scripts", "page_template.html"))
    tpl_m3 = read_json(os.path.join(BASE, "scripts", "page_template_m3.html"))

    # --- M5：紧凑 JSON 原样落盘（已经是 [t,lat,lon,depth,mag,type,en,zh] 的紧凑数组）
    m5_text = read_json(os.path.join(DATA, "earthquakes_1995_2026.json"))
    n_m5 = len(json.loads(m5_text))
    with open(os.path.join(OUTDATA, "eq-m5.json"), "w", encoding="utf-8", newline="\n") as f:
        f.write(m5_text)

    # --- M3：Base64 还原成原始二进制，前端直接用 DataView 解析
    with open(os.path.join(DATA, "m3_pack.json"), encoding="utf-8") as f:
        pack = json.load(f)
    raw = base64.b64decode(pack["b"])
    with open(os.path.join(OUTDATA, "m3-pack.bin"), "wb") as f:
        f.write(raw)
    meta = {"n": pack["n"], "stride": pack["stride"], "mt": pack["mt"]}

    # --- 三个外壳页面
    jobs = [
        ("m5-cluster.html", tpl_m5, "/data/eq-m5.json", False, None),
        ("m5-points.html", tpl_m5, "/data/eq-m5.json", True, None),
        ("m3-points.html", tpl_m3, "/data/m3-pack.bin", True, meta),
    ]
    for name, tpl, url, all_points, m3_meta in jobs:
        html = render(tpl, url, all_points, m3_meta)
        path = os.path.join(SITE, name)
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(html)
        print("%-18s %7.1f KB" % (name, os.path.getsize(path) / 1024.0))

    print("%-18s %7.1f MB  (%d 条)" % ("data/eq-m5.json", os.path.getsize(os.path.join(OUTDATA, "eq-m5.json")) / 1048576.0, n_m5))
    print("%-18s %7.1f MB  (%d 条)" % ("data/m3-pack.bin", os.path.getsize(os.path.join(OUTDATA, "m3-pack.bin")) / 1048576.0, pack["n"]))


if __name__ == "__main__":
    main()
