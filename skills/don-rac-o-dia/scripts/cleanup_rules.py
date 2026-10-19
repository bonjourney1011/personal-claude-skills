"""Known cleanup targets on Windows and the PowerShell each one runs.

Rule fields: id, label, kind (legend colour), cat (safe | review), paths (globs), why (what you lose).
How it cleans:
  cmd + tool  -> run once if the tool exists (official clean command)
  cmd with {p} -> run per found path
  no cmd      -> empty the folder, keep the folder itself
  manual      -> print instructions only, never delete
"""
import glob
import os
import re

HOME = os.path.expanduser("~")
LOCAL = os.environ.get("LOCALAPPDATA") or os.path.join(HOME, "AppData", "Local")
ROAMING = os.environ.get("APPDATA") or os.path.join(HOME, "AppData", "Roaming")
SYSDRIVE = os.environ.get("SystemDrive", "C:")
REPORT_DIR = os.path.join(HOME, "disk-report")
SAFE, REVIEW = "safe", "review"
MIN_ITEM_BYTES = 10 * 1024 ** 2  # smaller findings are noise

CLEAR_CONTENTS = ("Get-ChildItem -LiteralPath {p} -Force -ErrorAction SilentlyContinue | "
                  "Remove-Item -Recurse -Force -ErrorAction SilentlyContinue")
OLD_CONTENTS = ("Get-ChildItem -LiteralPath {p} -Force -ErrorAction SilentlyContinue | "
                "Where-Object LastWriteTime -lt (Get-Date).AddDays(-3) | "
                "Remove-Item -Recurse -Force -ErrorAction SilentlyContinue")
REMOVE_DIR = "Remove-Item -LiteralPath {p} -Recurse -Force -ErrorAction SilentlyContinue"
OLD_JSONL = ("Get-ChildItem -LiteralPath {p} -Recurse -File -Filter *.jsonl -ErrorAction SilentlyContinue | "
             "Where-Object LastWriteTime -lt (Get-Date).AddDays(-30) | Remove-Item -Force")
J = os.path.join

RULES = [
    # --- Caches: the tool downloads again what it needs ---
    dict(id="npm-cache", label="npm cache", kind="cache", cat=SAFE, paths=[J(LOCAL, "npm-cache")],
         tool="npm.cmd", cmd="npm.cmd cache clean --force",
         why="Gói npm đã tải về. Lần cài sau tải lại từ mạng nên chậm hơn một chút."),
    dict(id="pnpm-store", label="pnpm store", kind="cache", cat=SAFE, paths=[J(LOCAL, "pnpm", "store")],
         tool="pnpm.cmd", cmd="pnpm.cmd store prune",
         why="Kho gói của pnpm. Lệnh prune chỉ xóa gói không còn dự án nào dùng. "
             "pnpm dùng hard link nên dung lượng thực giải phóng thường ít hơn con số này."),
    dict(id="yarn-cache", label="Yarn cache", kind="cache", cat=SAFE,
         paths=[J(LOCAL, "Yarn", "Cache"), J(LOCAL, "Yarn", "Berry", "cache")],
         tool="yarn.cmd", cmd="yarn.cmd cache clean", why="Gói Yarn đã tải về. Lần cài sau tải lại."),
    dict(id="pip-cache", label="pip cache", kind="cache", cat=SAFE, paths=[J(LOCAL, "pip", "cache")],
         tool="python", cmd="python -m pip cache purge", why="Gói Python đã tải về. Lần pip install sau tải lại."),
    dict(id="uv-cache", label="uv cache", kind="cache", cat=SAFE, paths=[J(LOCAL, "uv", "cache")],
         tool="uv", cmd="uv cache clean", why="Cache của uv. Lần cài sau tải lại."),
    dict(id="playwright", label="Playwright browsers", kind="cache", cat=SAFE, paths=[J(LOCAL, "ms-playwright")],
         tool="npx.cmd", cmd="npx.cmd --yes playwright uninstall --all",
         why="Trình duyệt dùng để test tự động. Cần lại thì chạy npx playwright install."),
    dict(id="puppeteer", label="Puppeteer browsers", kind="cache", cat=SAFE, paths=[J(HOME, ".cache", "puppeteer")],
         why="Chrome tải riêng cho Puppeteer. Tự tải lại khi script Puppeteer chạy lần sau."),
    dict(id="go-mod", label="Go module cache", kind="cache", cat=SAFE, paths=[J(HOME, "go", "pkg", "mod")],
         tool="go", cmd="go clean -modcache", why="Module Go đã tải. go build tải lại khi cần."),
    dict(id="nuget", label="NuGet packages", kind="cache", cat=SAFE, paths=[J(HOME, ".nuget", "packages")],
         tool="dotnet", cmd="dotnet nuget locals all --clear", why="Gói .NET đã tải. dotnet restore tải lại."),
    dict(id="gradle", label="Gradle cache", kind="cache", cat=SAFE, paths=[J(HOME, ".gradle", "caches")],
         why="Thư viện Java/Android đã tải. Build sau tải lại, lần đầu chậm."),
    dict(id="maven", label="Maven repository", kind="cache", cat=SAFE, paths=[J(HOME, ".m2", "repository")],
         why="Thư viện Java đã tải. Build sau tải lại."),
    dict(id="cargo", label="Cargo registry cache", kind="cache", cat=SAFE,
         paths=[J(HOME, ".cargo", "registry", "cache")], why="Gói Rust nén đã tải. cargo tải lại khi cần."),
    dict(id="conda", label="Conda package cache", kind="cache", cat=SAFE,
         paths=[J(HOME, d, "pkgs") for d in ("anaconda3", "miniconda3")], tool="conda", cmd="conda clean --all -y",
         why="Gói conda đã tải. Môi trường đang dùng không bị ảnh hưởng."),
    dict(id="temp", label="Thư mục Temp", kind="cache", cat=SAFE, paths=[J(LOCAL, "Temp")], cmd=OLD_CONTENTS,
         why="File tạm của Windows và ứng dụng. Chỉ xóa mục cũ hơn 3 ngày, file đang dùng tự bỏ qua, "
             "nên dung lượng giải phóng có thể ít hơn."),
    dict(id="crash-dumps", label="Crash dumps", kind="cache", cat=SAFE, paths=[J(LOCAL, "CrashDumps")],
         why="Bản ghi lỗi khi ứng dụng bị crash. Chỉ cần khi gửi báo lỗi."),
    dict(id="browser-cache", label="Cache trình duyệt (Chrome, Edge)", kind="cache", cat=SAFE,
         paths=[J(base, "User Data", "*", sub) for base in (J(LOCAL, "Google", "Chrome"), J(LOCAL, "Microsoft", "Edge"))
                for sub in ("Cache", "Code Cache")],
         why="Ảnh và script web đã lưu. Không mất mật khẩu, lịch sử hay tab. Đóng trình duyệt trước khi dọn."),
    dict(id="editor-cache", label="Cache VS Code / Cursor", kind="cache", cat=SAFE,
         paths=[J(ROAMING, app, sub) for app in ("Code", "Cursor")
                for sub in ("Cache", "CachedData", "CachedExtensionVSIXs", "Code Cache")],
         why="Cache của editor. Không mất extension hay cài đặt. Đóng editor trước khi dọn."),
    # --- Review first: history, models, data that is slow or impossible to get back ---
    dict(id="claude-sessions", label="Lịch sử phiên Claude Code", kind="agent", cat=REVIEW,
         paths=[J(HOME, ".claude*", "projects")], cmd=OLD_JSONL,
         why="Log các phiên chat. Script chỉ xóa file .jsonl cũ hơn 30 ngày (giữ memory), "
             "nên dung lượng giải phóng có thể ít hơn. Phiên đã xóa không /resume được."),
    dict(id="codex-sessions", label="Lịch sử phiên Codex", kind="agent", cat=REVIEW,
         paths=[J(HOME, ".codex", "sessions"), J(HOME, ".codex", "archived_sessions")], cmd=OLD_JSONL,
         why="Log các phiên Codex. Script chỉ xóa phiên cũ hơn 30 ngày. Phiên đã xóa không mở lại được."),
    dict(id="docker", label="Docker Desktop", kind="docker", cat=REVIEW, paths=[J(LOCAL, "Docker", "wsl")],
         tool="docker", cmd="docker system prune -a -f",
         why="Image, container dừng và cache build không dùng. File ổ ảo của Docker không tự co lại; "
             "muốn thu hồi hết thì vào Docker Desktop > Troubleshoot > Clean / Purge data."),
    dict(id="wsl", label="Linux trong WSL", kind="docker", cat=REVIEW,
         paths=[J(LOCAL, "Packages", "*CanonicalGroup*", "LocalState")],
         manual="Xem distro: wsl --list --verbose. Gỡ distro không dùng: wsl --unregister <tên> (mất toàn bộ dữ liệu trong đó).",
         why="Ổ ảo của Linux (Ubuntu…) trong WSL, chứa cả file và dự án bên trong."),
    dict(id="huggingface", label="Hugging Face models", kind="ai", cat=REVIEW, paths=[J(HOME, ".cache", "huggingface")],
         manual="Chạy riêng: hf cache delete (bản cũ: huggingface-cli delete-cache) rồi chọn model cần xóa trong menu.",
         why="Model và dataset AI đã tải. Tải lại có thể mất hàng GB."),
    dict(id="ollama", label="Ollama models", kind="ai", cat=REVIEW, paths=[J(HOME, ".ollama", "models")],
         manual="Xem model: ollama list. Xóa model không dùng: ollama rm <tên-model>.",
         why="Model AI chạy local. Tải lại mất nhiều thời gian."),
    dict(id="lm-studio", label="LM Studio models", kind="ai", cat=REVIEW,
         paths=[J(HOME, ".lmstudio", "models"), J(HOME, ".cache", "lm-studio", "models")],
         manual="Mở LM Studio > My Models và xóa model không dùng.", why="Model AI chạy local. Tải lại mất nhiều thời gian."),
    dict(id="rembg-models", label="Model tách nền rembg", kind="ai", cat=REVIEW, paths=[J(HOME, ".u2net")],
         why="Model tách nền ảnh/video (u2net, birefnet). rembg tự tải lại lần dùng sau, mỗi model vài trăm MB."),
    dict(id="capcut-cache", label="Cache CapCut", kind="cache", cat=REVIEW, paths=[J(LOCAL, "CapCut", "User Data", "Cache")],
         why="Hiệu ứng, ảnh, font CapCut đã tải. Dự án không nằm ở đây. Đóng CapCut trước; hiệu ứng sẽ tải lại khi dùng."),
    dict(id="recycle-bin", label="Thùng rác", kind="files", cat=REVIEW, paths=[J(SYSDRIVE + "\\", "$Recycle.Bin")],
         cmd=f"Clear-RecycleBin -DriveLetter {SYSDRIVE[0]} -Force", why="File bạn đã xóa. Dọn rồi không khôi phục được nữa."),
]

# Folders found anywhere in your projects while scanning
PATTERN_SPECS = {
    "node-modules": dict(names=("node_modules",), label="node_modules trong {n} dự án", kind="build", cat=REVIEW,
                         why="Thư viện của từng dự án Node. Xóa rồi phải chạy lại npm/pnpm install trong dự án đó."),
    "next-build": dict(names=(".next",), label="Bản build Next.js ({n} dự án)", kind="build", cat=SAFE,
                       why="Next.js tạo lại khi chạy dev hoặc build."),
    "py-caches": dict(names=("__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache"),
                      label="Cache Python ({n} thư mục)", kind="build", cat=SAFE,
                      why="Python và công cụ test/lint tự tạo lại khi chạy."),
    "python-venv": dict(names=(".venv", "venv"), label="Môi trường ảo Python ({n})", kind="build", cat=REVIEW,
                        why="Thư viện Python cài riêng cho dự án. Xóa rồi phải tạo lại venv và pip install."),
}
NAME_TO_PATTERN = {n: pid for pid, s in PATTERN_SPECS.items() for n in s["names"]}
# Never treat folders under these as project junk (global tools, editor extensions, Python installs)
SKIP_ANCESTORS = {"appdata", "site-packages", "anaconda3", "miniconda3", "miniforge3", "mambaforge",
                  "scoop", "pipx", "go"}


def fmt_bytes(b):
    gb, mb = 1024 ** 3, 1024 ** 2
    if b >= gb:
        return f"{b / gb:.0f} GB" if b >= 100 * gb else f"{b / gb:.1f} GB"
    return f"{round(b / mb)} MB" if b >= mb else f"{max(0, round(b / 1024))} KB"


def ps_quote(s):
    # PowerShell also ends single-quoted strings on typographic quotes (‘ ’ ‚ ‛): double them all
    return "'" + re.sub("['‘’‚‛]", lambda m: m.group(0) * 2, s) + "'"


def expand_rule_paths():
    """Resolve each rule's globs to existing folders. Returns {normcase(path): path} to watch while scanning."""
    watch = {}
    for r in RULES:
        r["_paths"] = sorted({p for g in r["paths"] for p in glob.glob(g) if os.path.isdir(p)})
        watch.update({os.path.normcase(p): p for p in r["_paths"]})
    return watch


def rule_for_path(path):
    key = os.path.normcase(path)
    for r in RULES:
        for p in r.get("_paths", []):
            rp = os.path.normcase(p)
            if key == rp or key.startswith(rp + os.sep):
                return r
    return None


def match_pattern(path, root):
    pid = NAME_TO_PATTERN.get(os.path.basename(path).lower())
    if not pid or not root:
        return None
    ancestors = os.path.relpath(os.path.dirname(path), root).lower().split(os.sep)
    if any((a.startswith(".") and a != ".") or a in SKIP_ANCESTORS for a in ancestors):
        return None
    if pid == "python-venv" and not os.path.isfile(os.path.join(path, "pyvenv.cfg")):
        return None
    return pid


def _preview(r, n):
    cmd = r.get("cmd")
    if r.get("manual"):
        return "Chỉ in hướng dẫn, không xóa gì"
    if cmd == OLD_JSONL:
        return "Xóa file .jsonl cũ hơn 30 ngày"
    if cmd == OLD_CONTENTS:
        return "Xóa mục cũ hơn 3 ngày (giữ lại thư mục gốc)"
    if cmd == REMOVE_DIR:
        return f"Xóa {n} thư mục"
    return cmd if cmd else "Làm trống thư mục (giữ lại thư mục gốc)"


def _script(r, label, size, paths):
    lines = [f"Write-Host {ps_quote(f'== {label} ({fmt_bytes(size)}) ==')}"]
    cmd = r.get("cmd") or CLEAR_CONTENTS
    if r.get("manual"):
        lines.append(f"Write-Host {ps_quote(r['manual'])}")
    elif "{p}" in cmd:
        lines += [cmd.replace("{p}", ps_quote(p)) for p in paths]
    elif r.get("tool"):
        skip = ps_quote(f"Bỏ qua: không thấy lệnh {r['tool']}")
        lines.append(f"if (Get-Command {r['tool']} -ErrorAction SilentlyContinue) {{ {cmd} }} else {{ Write-Host {skip} }}")
    else:
        lines.append(cmd)
    return "\n".join(lines)


def _item(r, label, found):
    size = sum(s for _, s in found)
    return dict(id=r["id"], label=label, kind=r["kind"], cat=r["cat"], why=r["why"], size=size,
                preview=_preview(r, len(found)), paths=[dict(path=p, size=s) for p, s in found],
                script=_script(r, label, size, [p for p, _ in found]))


def build_items(watched, matches):
    """watched: {normcase(path): bytes} for rule folders; matches: {pattern id: [(path, bytes)]}."""
    items = []
    for r in RULES:
        found = [(p, watched.get(os.path.normcase(p), 0)) for p in r.get("_paths", [])]
        found = [f for f in found if f[1] > 0]
        if sum(s for _, s in found) >= MIN_ITEM_BYTES:
            items.append(_item(r, r["label"], found))
    for pid, spec in PATTERN_SPECS.items():
        found = sorted((f for f in matches.get(pid, []) if f[1] > 0), key=lambda f: -f[1])
        if sum(s for _, s in found) >= MIN_ITEM_BYTES:
            items.append(_item({**spec, "id": pid, "cmd": REMOVE_DIR}, spec["label"].format(n=len(found)), found))
    return sorted(items, key=lambda i: -i["size"])


def script_header(scanned_at):
    return "\n".join([
        f"# Script dọn rác - skill don-rac-o-dia - theo lần quét {scanned_at}",
        "# Đọc kỹ từng khối trước khi chạy. Đóng trình duyệt / VS Code nếu dọn cache của chúng.",
        "# Cách chạy an toàn nhất: lưu thành file .ps1 rồi: powershell -ExecutionPolicy Bypass -File <file.ps1>",
        "$ErrorActionPreference = 'Continue'",
    ])


def script_footer():
    return "Write-Host 'Xong. Gọi lại skill don-rac-o-dia để quét và so sánh dung lượng mới.'"
