# -*- coding: utf-8 -*-
"""往站点公告里追加一条，供首页「公告」弹层展示。

用法：
    python scripts/add_notice.py --type feature --title "标题" --body "正文"
    python scripts/add_notice.py --list
    python scripts/add_notice.py --remove 2026-11-26-m3-split

类型：feature（新功能）/ data（数据）/ maintenance（维护）/ other（其他）

写完执行下面两条即可发布（Cloudflare 会自动重新部署）：
    git add site/data/notice.json && git commit -m "notice: 标题"
    git push
"""
import argparse
import datetime
import json
import os
import sys
import time

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NOTICE = os.path.join(BASE, "site", "data", "notice.json")
TYPES = ("feature", "data", "maintenance", "other")
MAX_ITEMS = 30


def load():
    if not os.path.exists(NOTICE):
        return {"updated": 0, "items": []}
    with open(NOTICE, encoding="utf-8") as f:
        data = json.load(f)
    data.setdefault("items", [])
    return data


def save(data):
    with open(NOTICE, "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--type", default="other", choices=TYPES)
    ap.add_argument("--title")
    ap.add_argument("--body", default="")
    ap.add_argument("--date", default=None, help="默认今天，格式 YYYY-MM-DD")
    ap.add_argument("--list", action="store_true", help="列出现有公告")
    ap.add_argument("--remove", metavar="ID", help="按 id 删除一条公告")
    args = ap.parse_args()

    data = load()

    if args.list:
        if not data["items"]:
            print("暂无公告")
        for it in data["items"]:
            print("[%s] %s  %s  (%s)" % (it.get("type"), it.get("date"), it.get("title"), it.get("id")))
        return

    if args.remove:
        before = len(data["items"])
        data["items"] = [i for i in data["items"] if i.get("id") != args.remove]
        if len(data["items"]) == before:
            print("没找到 id 为 %s 的公告" % args.remove)
            sys.exit(1)
        data["updated"] = int(time.time() * 1000)
        save(data)
        print("已删除 %s，剩余 %d 条" % (args.remove, len(data["items"])))
        return

    if not args.title:
        ap.error("必须提供 --title（或用 --list / --remove）")

    date = args.date or datetime.date.today().isoformat()
    item = {
        "id": "%s-%d" % (date, int(time.time() * 1000) % 100000),
        "date": date,
        "type": args.type,
        "title": args.title,
        "body": args.body,
    }
    data["items"].insert(0, item)
    data["items"] = data["items"][:MAX_ITEMS]
    data["updated"] = int(time.time() * 1000)
    save(data)

    print("已添加：")
    print("  [%s] %s  %s" % (item["type"], item["date"], item["title"]))
    print("当前共 %d 条公告" % len(data["items"]))
    print("")
    print("发布：")
    print('  git add site/data/notice.json && git commit -m "notice: %s"' % args.title)
    print("  git push")


if __name__ == "__main__":
    main()
