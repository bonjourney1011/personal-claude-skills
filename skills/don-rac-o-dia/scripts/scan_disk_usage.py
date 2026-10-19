"""Read-only disk usage scan for the don-rac-o-dia skill (Windows).

Lists folders and reads file sizes only: never opens file contents, never deletes anything.
Writes to ~/disk-report: scan.json, sizes.csv (this scan), sizes-previous.csv (last scan), disk-map.html.
Usage: python scan_disk_usage.py [--root EXTRA_DIR ...] [--html-out PATH ...]
"""
import argparse
import csv
import datetime as dt
import json
import os
import shutil
import stat
import sys
import time

from build_disk_map_html import build_html
from cleanup_rules import (HOME, PATTERN_SPECS, REPORT_DIR, SYSDRIVE, build_items, expand_rule_paths, fmt_bytes,
                           match_pattern, rule_for_path, script_footer, script_header)

# Cloud sync folders and the photo library: skipped, never opened
SKIP_TOP = ("onedrive", "pictures", "icloud", "dropbox", "google drive", "wps cloud", "wpsdrive")
# Junctions/symlinks/cloud placeholders and files that are not really on disk (offline, recall on access)
NO_DATA = stat.FILE_ATTRIBUTE_REPARSE_POINT | stat.FILE_ATTRIBUTE_OFFLINE | 0x40000 | 0x400000
RECORD_DEPTH = 3
GROW_BYTES = 50 * 1024 ** 2
TOP_CHILDREN = 12
SMALL_GROUP_SHARE = 0.005


def is_under(path, root):
    p, r = os.path.normcase(path), os.path.normcase(root)
    return p == r or p.startswith(r.rstrip(os.sep) + os.sep)


def disp(path):
    return "~" + path[len(HOME):] if is_under(path, HOME) else path


class Scanner:
    def __init__(self, watch):
        self.watch = watch                # normcase(path) -> path of rule folders
        self.sizes, self.children = {}, {}
        self.watched, self.matches = {}, {}
        self.skipped, self.denied = [], 0

    def walk(self, path, depth=0, root=None, in_match=False):
        try:
            with os.scandir(path) as it:
                entries = list(it)
        except OSError:
            self.denied += 1
            return 0
        total = 0
        for e in entries:
            try:
                st = e.stat(follow_symlinks=False)
            except OSError:
                continue
            if getattr(st, "st_file_attributes", 0) & NO_DATA:
                continue
            if not stat.S_ISDIR(st.st_mode):
                total += st.st_size
                continue
            if depth == 0 and root == HOME and e.name.lower().startswith(SKIP_TOP):
                self.skipped.append(e.path)
                continue
            key = os.path.normcase(e.path)
            pid = None if in_match else match_pattern(e.path, root)
            # no pattern matches inside a match or a rule folder: nothing is counted twice
            size = self.walk(e.path, depth + 1, root, in_match or pid is not None or key in self.watch)
            total += size
            if pid:
                self.matches.setdefault(pid, []).append((e.path, size))
            if depth + 1 <= RECORD_DEPTH:
                self.sizes[e.path] = size
                self.children.setdefault(path, []).append(e.path)
            if key in self.watch:
                self.watched[key] = size
        return total


def load_prev():
    """Previous sizes.csv (+ roots from the previous scan.json, to know whether totals are comparable)."""
    path = os.path.join(REPORT_DIR, "sizes.csv")
    try:
        with open(path, newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
    except (OSError, csv.Error):
        return {}, None, None
    try:
        shutil.copyfile(path, os.path.join(REPORT_DIR, "sizes-previous.csv"))
    except OSError:
        pass
    try:
        with open(os.path.join(REPORT_DIR, "scan.json"), encoding="utf-8") as f:
            prev_roots = json.load(f).get("roots")
    except (OSError, ValueError):
        prev_roots = None
    prev = {r["path"]: int(r["bytes"]) for r in rows if (r.get("bytes") or "").isdigit()}
    return prev, (rows[0].get("scanned_at") if rows else None), prev_roots


def write_sizes_csv(rows, scanned_at):
    path = os.path.join(REPORT_DIR, "sizes.csv")
    try:
        with open(path + ".tmp", "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["path", "label", "bytes", "scanned_at"])
            w.writerows((p, label, size, scanned_at) for p, label, size in rows)
        os.replace(path + ".tmp", path)
    except OSError as e:
        print(f"Cảnh báo: không ghi được sizes.csv ({e}). Đóng file nếu đang mở trong Excel rồi quét lại.")


def default_kind(path):
    name = os.path.basename(path).lower()
    if name.startswith((".claude", ".codex")):
        return "agent"
    if name.startswith("."):
        return "tools"
    return "app" if os.path.basename(os.path.dirname(path)).lower() == "appdata" else "files"


def make_tile(sc, path, kind, prev, name=None):
    r, size, key = rule_for_path(path), sc.sizes.get(path, 0), disp(path)
    return dict(name=name or os.path.basename(path) or path, path=key, size=size,
                delta=size - prev[key] if key in prev else None, kind=r["kind"] if r else kind,
                safe=bool(r and r["cat"] == "safe"), rule=r["id"] if r else None)


def make_group(sc, path, name, prev):
    g = make_tile(sc, path, default_kind(path), prev, name)
    kids = sorted(sc.children.get(path, []), key=lambda p: -sc.sizes[p])
    g["children"] = [make_tile(sc, p, g["kind"], prev) for p in kids[:TOP_CHILDREN]]
    rest = sum(sc.sizes[p] for p in kids[TOP_CHILDREN:])
    loose = g["size"] - sum(sc.sizes[p] for p in kids)
    if rest > 0:
        g["children"].append(dict(name=f"{len(kids) - TOP_CHILDREN} thư mục khác", size=rest, kind=g["kind"]))
    if loose > 0:
        g["children"].append(dict(name="file lẻ", size=loose, kind=g["kind"]))
    return g


def build_groups(sc, roots, prev):
    tops = []
    for root in roots:
        if root != HOME:
            tops.append((root, root))
            continue
        for p in sc.children.get(root, []):
            if os.path.basename(p).lower() == "appdata":
                tops += [(c, "AppData\\" + os.path.basename(c)) for c in sc.children.get(p, [])]
            else:
                tops.append((p, "~\\" + os.path.basename(p)))
    total = sum(sc.sizes.get(p, 0) for p, _ in tops) or 1
    big = [t for t in tops if sc.sizes.get(t[0], 0) >= total * SMALL_GROUP_SHARE]
    small = [t for t in tops if t not in big and sc.sizes.get(t[0], 0) > 0]
    groups = [make_group(sc, p, n, prev) for p, n in big]
    if small:
        kids = sorted((make_tile(sc, p, default_kind(p), prev, n) for p, n in small), key=lambda t: -t["size"])
        groups.append(dict(name="Thư mục nhỏ khác", size=sum(k["size"] for k in kids), kind="files", children=kids))
    return sorted(groups, key=lambda g: -g["size"])


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", action="append", default=[], help="Extra folder outside home to scan")
    ap.add_argument("--html-out", action="append", default=[], help="Extra copy of disk-map.html")
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    sys.setrecursionlimit(20000)
    os.makedirs(REPORT_DIR, exist_ok=True)
    started, now = time.monotonic(), dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    roots = [HOME]
    for r in sorted({os.path.abspath(r) for r in args.root if os.path.isdir(r)}, key=len):
        if not any(is_under(r, k) or is_under(k, r) for k in roots):  # drop nested / overlapping roots
            roots.append(r)

    watch = expand_rule_paths()
    sc = Scanner(watch)
    for root in roots:
        sc.sizes[root] = sc.walk(root, root=root)
    on_sys = lambda p: os.path.splitdrive(p)[0].upper() == SYSDRIVE.upper()
    scanned_sys = sum(sc.sizes[r] for r in roots if on_sys(r))
    for key, path in watch.items():  # rule folders outside the roots, e.g. the Recycle Bin
        if key not in sc.watched and not any(is_under(path, r) for r in roots):
            sc.watched[key] = sc.walk(path, depth=RECORD_DEPTH)
            scanned_sys += sc.watched[key] if on_sys(path) else 0

    prev, prev_at, prev_roots = load_prev()
    same_roots = prev_roots is None or set(prev_roots) == {disp(r) for r in roots}
    groups = build_groups(sc, roots, prev)
    items = build_items(sc.watched, sc.matches)
    for i in items:
        key = "item:" + i["id"]
        comparable = same_roots or i["id"] not in PATTERN_SPECS  # project totals depend on which roots were scanned
        i["delta"] = i["size"] - prev[key] if key in prev and comparable else None
        i["paths"] = [dict(path=disp(p["path"]), size=p["size"]) for p in i["paths"]]

    write_sizes_csv([(disp(p), os.path.basename(p) or p, s) for p, s in sc.sizes.items()]
                    + [("item:" + i["id"], i["label"], i["size"]) for i in items], now)
    tiles = [t for g in groups for t in [g] + g["children"] if t.get("path")]
    increases = sorted([dict(label=t["path"], size=t["size"], delta=t["delta"]) for t in tiles]
                       + [dict(label=i["label"], size=i["size"], delta=i["delta"]) for i in items], key=lambda x: -(x["delta"] or 0))
    increases = [x for x in increases if x["delta"] is not None and x["delta"] >= GROW_BYTES]

    disk = shutil.disk_usage(SYSDRIVE + "\\")
    data = dict(scanned_at=now, prev_scanned_at=prev_at, roots=[disp(r) for r in roots],
                disk=dict(drive=SYSDRIVE, total=disk.total, used=disk.used, free=disk.free),
                scanned=scanned_sys, unmapped=max(0, disk.used - scanned_sys), skipped=[disp(p) for p in sc.skipped],
                denied=sc.denied, groups=groups, items=items, increases=increases[:12], grow_threshold=GROW_BYTES,
                script_header=script_header(now), script_footer=script_footer())
    with open(os.path.join(REPORT_DIR, "scan.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)
    html_paths = [os.path.join(REPORT_DIR, "disk-map.html")] + args.html_out
    build_html(data, html_paths)

    safe = [i for i in items if i["cat"] == "safe"]
    review = [i for i in items if i["cat"] == "review"]
    print(f"Quét xong (chỉ đọc) trong {time.monotonic() - started:.0f}s: {', '.join(data['roots'])}")
    print(f"Ổ {SYSDRIVE} còn trống {fmt_bytes(disk.free)} / {fmt_bytes(disk.total)}")
    print(f"An toàn để xóa: {fmt_bytes(sum(i['size'] for i in safe))} ({len(safe)} mục)"
          f" | Cần xem lại: {fmt_bytes(sum(i['size'] for i in review))} ({len(review)} mục)")
    for i in items[:8]:
        print(f"  [{'an toàn' if i['cat'] == 'safe' else 'xem lại'}] {i['id']}: {i['label']} - {fmt_bytes(i['size'])}")
    if prev_at:
        print(f"So với lần quét {prev_at}: {len(increases)} mục tăng >= {fmt_bytes(GROW_BYTES)}")
        for x in increases[:5]:
            print(f"  +{fmt_bytes(x['delta'])}  {x['label']}")
    else:
        print("Lần quét đầu tiên: lần sau sẽ so sánh với sizes.csv")
    print(f"Bỏ qua: {', '.join(data['skipped']) or 'không'} | {sc.denied} thư mục bị từ chối quyền")
    print("HTML:", *html_paths, sep="\n  ")


if __name__ == "__main__":
    main()
