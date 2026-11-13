# Báo cáo dự đoán: <tên bài toán>

Ngày chạy: <dd/mm/yyyy> · Model: TabPFN <phiên bản> qua `tabpfn-client` <phiên bản> · Baseline: <tên>

## 1. Câu hỏi
<Quyết định nào phụ thuộc vào kết quả. Mục tiêu là cột nào. Sai kiểu nào đắt hơn.>

## 2. Dữ liệu
| Phần | Số dòng | Giai đoạn | Vai trò |
|---|---|---|---|
| Lịch sử | | | Ngữ cảnh cho model |
| Test | | | Chỉ để chấm điểm |
| Hiện tại | | | Cần dự đoán |

- Số feature: <n>. Tỷ lệ thiếu cao nhất: <cột, %>.
- Cột đã loại vì nguy cơ rò rỉ: <danh sách và lý do>.
- Cách chia: <theo thời gian / ngẫu nhiên, và vì sao>.

## 3. Kết quả trên tập test
| Chỉ số | TabPFN | Baseline | Bên nào tốt hơn |
|---|---|---|---|
| | | | |

Độ phủ dải P10–P90 (hồi quy): <x%> (kỳ vọng khoảng 80%).

## 4. Dự đoán
<Bảng hoặc danh sách xếp hạng, luôn kèm xác suất hoặc dải phân vị.>

## 5. Điều gì dẫn dắt dự đoán
<SHAP toàn cục, một hoặc hai ví dụ cụ thể, PDP nếu có. Ghi rõ đây là tương quan.>

## 6. Giới hạn
- <Dữ liệu nhỏ, giai đoạn ngắn, trôi dữ liệu, feature thiếu…>
- <Điều chưa kiểm chứng.>

## 7. Đề xuất
<Hành động cụ thể, ngưỡng quyết định, và khi nào cần chạy lại.>
