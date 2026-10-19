"""Render disk-map.html (the Artifact page) from scan data + assets/ template, CSS and JS.

Called by scan_disk_usage.py. Standalone: python build_disk_map_html.py [--out PATH ...]
rebuilds from ~/disk-report/scan.json (useful after editing the assets).
"""
import argparse
import json
import os

from cleanup_rules import REPORT_DIR

ASSETS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")


def _read(name):
    with open(os.path.join(ASSETS, name), encoding="utf-8") as f:
        return f.read()


def build_html(data, out_paths):
    payload = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    html = (_read("disk-map-template.html")
            .replace("/*__CSS__*/", _read("disk-map.css"))
            .replace("/*__JS__*/", _read("disk-map.js"))
            .replace("/*__DATA__*/null", payload))
    for path in out_paths:
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(html)
    return html


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", action="append", default=[])
    args = ap.parse_args()
    with open(os.path.join(REPORT_DIR, "scan.json"), encoding="utf-8") as f:
        scan = json.load(f)
    outs = [os.path.join(REPORT_DIR, "disk-map.html")] + args.out
    build_html(scan, outs)
    print("\n".join(outs))
