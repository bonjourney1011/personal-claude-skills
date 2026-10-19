---
name: don-rac-o-dia
description: >-
  DỌN RÁC Ổ ĐĨA (Windows): quét thư mục home ở chế độ CHỈ ĐỌC (chỉ đo dung lượng, không mở nội dung file),
  tìm dữ liệu tồn đọng từ quá trình code (cache npm/pip/uv/pnpm, Temp, cache trình duyệt/VS Code, node_modules,
  .next, venv, lịch sử phiên Claude Code/Codex, Docker/WSL, model AI), rồi dựng ARTIFACT "Bản đồ ổ đĩa": treemap
  dung lượng + danh sách đề xuất chia 2 nhóm "Có thể xóa an toàn" / "Cần xem lại trước khi xóa", tick chọn rồi
  Copy script PowerShell dùng lệnh clean chính thức của từng công cụ. Ghi ~/disk-report/sizes.csv và lần sau so
  sánh, đánh dấu mục tăng dung lượng. KHÔNG tự xóa gì. Dùng khi người dùng nói "dọn rác", "dọn ổ đĩa", "ổ C đầy",
  "hết dung lượng", "máy đầy", "quét dung lượng", "bản đồ dung lượng", "disk cleanup", "giải phóng ổ cứng".
---

# Dọn rác ổ đĩa

Nói tiếng Việt, ngắn gọn. `K` = `~/.claude/skills/don-rac-o-dia`. Windows, `python` (3.9+).

## Luật cứng
- **Chỉ đọc**: chỉ chạy các script trong `K/scripts`. Không mở nội dung file, không xóa, không chạy script dọn.
- Bỏ qua OneDrive / WPS Cloud / Dropbox / Pictures (thư viện ảnh), ổ ngoài, junction/symlink, thư mục bị từ chối quyền.
- Chạy script dọn chỉ khi người dùng bảo rõ ("chạy đi"). Mục "Cần xem lại" phải hỏi lại từng mục trước khi chạy.
- Trang artifact chứa đường dẫn máy (tên user, tên dự án): giữ riêng tư, không tự chia sẻ.

## Quy trình
1. **Quét** (1–3 phút; timeout 600000):
   ```
   python "K/scripts/scan_disk_usage.py" --html-out "<scratchpad>/disk-map.html" [--root <thư mục dự án ngoài home>]
   ```
   Nếu thư mục làm việc hiện tại nằm ngoài home (vd `C:\code` hoặc `D:\Projects`), thêm `--root` với thư mục cấp cao nhất của nó.
   Script tự đọc `~/disk-report/sizes.csv` cũ (chép sang `sizes-previous.csv`), so sánh, ghi file mới và in tóm tắt kèm id từng mục.
2. **Publish artifact** file `<scratchpad>/disk-map.html` (trang tự sinh từ template trong `K/assets`, dữ liệu từ lần quét):
   - Có `~/disk-report/artifact-url.txt` → `Artifact read` URL đó rồi publish với `url` để giữ link cũ.
   - Chưa có → publish mới (`icon: "storage"`), ghi URL vào `~/disk-report/artifact-url.txt`.
3. **Báo người dùng** (≤ 8 dòng): còn trống bao nhiêu; tổng "an toàn" + 3 mục lớn nhất; tổng "cần xem lại"; mục tăng so với
   lần trước (nếu có); link artifact. Nhắc: tick trên trang → **Copy script** → dán vào PowerShell, hoặc nói tên mục để mình tạo file.
4. **Khi người dùng chọn mục trong chat**: `python "K/scripts/make_cleanup_script.py" <id> <id> ...` → đưa đường dẫn
   `~/disk-report/cleanup-*.ps1` và tóm tắt từng khối lệnh. Không chạy.
5. Sau khi người dùng dọn xong: gọi lại skill để quét lại; trang sẽ hiện mức thay đổi.

## File
| File | Vai trò |
|---|---|
| `scripts/cleanup_rules.py` | Danh mục vị trí rác đã biết + mẫu thư mục dự án (node_modules, .next, venv…), lệnh dọn, lời giải thích. Thêm quy tắc mới ở đây. |
| `scripts/scan_disk_usage.py` | Quét chỉ đọc, so sánh `sizes.csv`, ghi `scan.json`, gọi dựng HTML |
| `scripts/build_disk_map_html.py` | Ghép `assets/` + dữ liệu thành trang. Chạy riêng để dựng lại từ `scan.json` sau khi sửa giao diện |
| `scripts/make_cleanup_script.py` | Tạo file `.ps1` (UTF-8 BOM) cho các id đã chọn |
| `assets/disk-map-*.{html,css,js}` | Giao diện: treemap, đề xuất có checkbox, thanh Copy script |

Đầu ra ở `~/disk-report/`: `scan.json`, `sizes.csv`, `sizes-previous.csv`, `disk-map.html`, `cleanup-*.ps1`, `artifact-url.txt`.

## Thêm quy tắc
Một dict trong `RULES` (`cleanup_rules.py`): `id`, `label`, `kind` (cache | build | agent | docker | ai | files), `cat`
(`SAFE` = công cụ tự tải/build lại; `REVIEW` = mất lịch sử, model, dữ liệu), `paths` (glob), `why` (xóa thì mất gì), và một
trong: `tool` + `cmd` (lệnh clean chính thức), `cmd` có `{p}` (chạy theo từng đường dẫn), `manual` (chỉ in hướng dẫn),
hoặc bỏ trống (làm trống thư mục). Ưu tiên lệnh chính thức của công cụ hơn xóa tay.
