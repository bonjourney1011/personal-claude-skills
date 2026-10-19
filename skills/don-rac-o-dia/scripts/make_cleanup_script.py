"""Write a PowerShell cleanup script for the chosen items of the last scan. Never runs it.

Usage: python make_cleanup_script.py <item-id> [<item-id> ...]   (ids are printed by the scan)
Output: ~/disk-report/cleanup-YYYYMMDD-HHMM.ps1 (UTF-8 with BOM so Windows PowerShell 5.1 reads Vietnamese)
"""
import datetime as dt
import json
import os
import sys

from cleanup_rules import REPORT_DIR, fmt_bytes


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    with open(os.path.join(REPORT_DIR, "scan.json"), encoding="utf-8") as f:
        data = json.load(f)
    items = {i["id"]: i for i in data["items"]}
    ids = list(dict.fromkeys(sys.argv[1:]))
    unknown = [i for i in ids if i not in items]
    if not ids or unknown:
        print("Id không có trong lần quét gần nhất:", ", ".join(unknown) or "(chưa nhập id)")
        print("Các id hợp lệ:", ", ".join(items))
        sys.exit(1)
    blocks = [data["script_header"]] + [items[i]["script"] for i in ids] + [data["script_footer"]]
    out = os.path.join(REPORT_DIR, f"cleanup-{dt.datetime.now():%Y%m%d-%H%M}.ps1")
    with open(out, "w", encoding="utf-8-sig") as f:
        f.write("\n\n".join(blocks) + "\n")
    print(out)
    print(f"{len(ids)} mục, tối đa {fmt_bytes(sum(items[i]['size'] for i in ids))}")


if __name__ == "__main__":
    main()
