---
name: phan-tich-du-lieu-bang-tabpfn
description: >-
  PHÂN TÍCH DỮ LIỆU BẢNG BẰNG TABPFN (tabular foundation model): nhận một bảng (CSV, Excel, DataFrame) và một câu hỏi
  dự đoán, chuyển phần thống kê cho TabPFN (phân loại, hồi quy có dải phân vị, dự báo chuỗi thời gian như hồi quy bảng),
  luôn so với một baseline (LightGBM hoặc mốc ngây thơ) trên cùng tập test, kiểm độ phủ của dải dự đoán, giải thích bằng
  SHAP/PDP, rồi viết báo cáo theo mẫu. Có luật chống rò rỉ dữ liệu, bảng phiên bản/giới hạn/license, và danh sách khi
  nào KHÔNG nên dùng TabPFN. Dùng khi người dùng nói "TabPFN", "tabular foundation model", "dự đoán trên bảng",
  "phân loại/hồi quy dữ liệu bảng", "churn", "dự báo chuỗi thời gian", "forecast", "so với XGBoost", "dải dự đoán",
  "phân vị", hoặc gọi /phan-tich-du-lieu-bang-tabpfn.
---

# Phân tích dữ liệu bảng bằng TabPFN

Nói tiếng Việt, ngắn gọn. `K` = `~/.claude/skills/phan-tich-du-lieu-bang-tabpfn`. Cần `python` 3.10+ và biến môi trường
`TABPFN_TOKEN` (xem `references/mcp-va-api.md`).

Ý chính: **LLM suy luận và giải thích, TabPFN dự đoán.** LLM không tự nghĩ ra con số dự đoán.

## Khi nào chuyển việc cho TabPFN
- Câu hỏi cần một giá trị **chưa có trong dữ liệu**: khách mới có rời bỏ không, căn nhà này giá bao nhiêu, tháng tới bán
  được bao nhiêu. Đây là dự đoán thống kê → TabPFN.
- Câu hỏi chỉ cần tra cứu, đếm, gộp nhóm trên dữ liệu đã có → dùng SQL/pandas, không cần model.
- Bảng trên 100k dòng, dữ liệu trôi mạnh theo thời gian, hoặc cần trả lời trong vài mili giây → đọc
  `references/khi-nao-khong-dung.md` trước.

## Luật cứng
1. **Chỉ fit trên dữ liệu lịch sử.** Không bao giờ fit trên tập test, kể cả để "thử nhanh".
2. **Luôn có baseline** chạy trên cùng tập test. Không có baseline thì không kết luận model tốt.
3. **Luôn báo độ bất định**: `predict_proba` cho phân loại, dải phân vị cho hồi quy. Không báo một con số trần.
4. **Dữ liệu có thời gian thì chia theo thời gian.** Không chia ngẫu nhiên. Feature chỉ dùng thông tin đã biết tại thời
   điểm dự đoán.
5. **Không tiền xử lý thừa**: không impute, không one-hot, không scale, không tune siêu tham số.
6. **Token chỉ nằm trong biến môi trường.** Không ghi vào file, không in ra màn hình, không commit.
7. SHAP và PDP mô tả tương quan mà model học được. Không diễn giải thành quan hệ nhân quả.
8. Dữ liệu gửi lên API của Prior Labs. Bảng có thông tin cá nhân hoặc bí mật của khách hàng thì hỏi người dùng trước.

## Quy trình
1. **Hiểu câu hỏi**: mục tiêu là cột nào, phân loại hay hồi quy, quyết định nào phụ thuộc vào kết quả, sai kiểu nào đắt hơn.
2. **Soát dữ liệu**: số dòng, số cột, kiểu cột, tỷ lệ thiếu, cột có nguy cơ rò rỉ (cột chỉ biết sau khi sự việc xảy ra).
   Đối chiếu giới hạn ở `references/phien-ban-gioi-han-license.md`.
3. **Chia dữ liệu**: lịch sử (có nhãn) / test (giữ riêng) / hiện tại (chưa có nhãn, cần dự đoán). Có cột thời gian thì
   cắt theo thời gian.
4. **Chạy đánh giá**:
   ```
   python "K/scripts/danh_gia_so_voi_baseline.py" <file.csv> --target <cột> [--time-col <cột ngày>] [--test-size 0.2]
   ```
   Script in chỉ số của TabPFN và LightGBM, kèm độ phủ dải P10–P90 cho hồi quy.
5. **Dự đoán và giải thích**: dự đoán cho phần "hiện tại", xếp hạng theo xác suất nếu cần. Giải thích theo
   `references/best-practice-va-loi-thuong-gap.md` (SHAP waterfall cho một dòng, beeswarm cho toàn cục, PDP).
6. **Viết báo cáo** theo `templates/report.md`: câu hỏi, dữ liệu, kết quả so với baseline, độ bất định, giới hạn.

Dự báo chuỗi thời gian: đọc `references/du-bao-chuoi-thoi-gian.md` trước khi dựng feature.

## File
| File | Vai trò |
|---|---|
| `references/nguyen-ly-cot-loi.md` | Model hoạt động thế nào, vì sao LLM kém với bảng |
| `references/best-practice-va-loi-thuong-gap.md` | Nên và không nên làm; đọc độ bất định; SHAP/PDP; KV cache |
| `references/du-bao-chuoi-thoi-gian.md` | Dự báo như hồi quy bảng, chống rò rỉ, backtest, chỉ số |
| `references/phien-ban-gioi-han-license.md` | Phiên bản, giới hạn, license, hạn mức API (kèm ngày kiểm tra) |
| `references/khi-nao-khong-dung.md` | Trường hợp TabPFN thua và cách xử lý |
| `references/mcp-va-api.md` | Cài MCP server, token, hạn mức, telemetry |
| `scripts/danh_gia_so_voi_baseline.py` | Đánh giá TabPFN và LightGBM trên cùng tập test |
| `templates/report.md` | Mẫu báo cáo |
