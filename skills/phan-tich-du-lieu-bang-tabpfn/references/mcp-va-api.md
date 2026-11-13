# Kết nối TabPFN: API và MCP

> Nguồn: bài 6 của khoá học và tài liệu Prior Labs (https://docs.priorlabs.ai/agentic/mcp). Kiểm tra ngày 13/11/2026.

## 1. Tài khoản và token
1. Tạo tài khoản Prior Labs tại https://ux.priorlabs.ai và chấp nhận điều khoản.
2. Lấy token API.
3. Trong phần cài đặt tài khoản, tắt tuỳ chọn cho phép dùng dữ liệu của mình để cải thiện model nếu không muốn.
4. Đặt biến môi trường (PowerShell, cho người dùng hiện tại):
   ```powershell
   [Environment]::SetEnvironmentVariable("TABPFN_TOKEN", "<token>", "User")
   ```
   Trên GitHub Actions: lưu vào Secrets với tên `TABPFN_TOKEN`.

Không ghi token vào file, không in ra log, không commit.

## 2. Dùng từ Python
```
pip install tabpfn-client
```
```python
import os
import tabpfn_client
from tabpfn_client import TabPFNRegressor

tabpfn_client.set_access_token(os.environ["TABPFN_TOKEN"])
```
`[VERIFY]` tên hàm đăng nhập theo phiên bản client đang cài; khoá học giấu bước này trong `helper.init_tabpfn()`.

Tắt telemetry: đặt `TABPFN_DISABLE_TELEMETRY=1`.

## 3. Dùng từ agent qua MCP
MCP server chính thức của Prior Labs chạy từ xa, đăng nhập bằng OAuth:
```
claude mcp add --transport http tabpfn https://api.priorlabs.ai/mcp/server
```
Server cung cấp các tool để fit, dự đoán, xem trạng thái fit; model đã fit được cache phía server. Đăng nhập OAuth phải
do người dùng tự làm trong phiên tương tác.

Luồng xử lý của agent:
1. Người dùng hỏi (ví dụ "Khách C-1046 có rời bỏ không?").
2. LLM nhận ra đây là dự đoán trên dữ liệu chưa thấy.
3. LLM gọi tool với ngữ cảnh (dữ liệu lịch sử) và truy vấn (dòng mới).
4. TabPFN trả phân phối dự đoán.
5. LLM diễn giải kết quả bằng lời.

Cấu trúc repo demo của khoá học, dùng làm khuôn cho dự án mới:
```
.mcp.json    khai báo MCP server
skills/      skill handoff: khi nào chuyển việc, cách lấy dữ liệu, mẫu báo cáo
scripts/     lấy dữ liệu, chạy baseline, đánh giá
```
Script lấy dữ liệu chia thành ba phần: `historical` (có nhãn), `current` (chưa có nhãn) và `test` (giống `current`
nhưng có nhãn, chỉ để chấm điểm).

## 4. Chọn MCP hay Python
| Việc | Dùng |
|---|---|
| Hỏi đáp nhanh trên một bảng nhỏ trong lúc trò chuyện | MCP |
| Đánh giá có baseline, backtest, pipeline chạy định kỳ | Python (`tabpfn-client`), vì cần lặp lại được và kiểm soát việc chia dữ liệu |

## 5. Hạn mức
Xem `phien-ban-gioi-han-license.md` mục 3. Trước khi chạy một backtest lớn, gọi thử một lần và xem lượng token đã dùng
trên trang tài khoản, rồi nhân lên.
