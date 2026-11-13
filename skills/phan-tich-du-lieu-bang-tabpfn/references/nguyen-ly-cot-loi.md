# Nguyên lý cốt lõi của TabPFN

> Nguồn: khoá "Tabular Foundation Models for Data Science Agents" (DeepLearning.AI + Prior Labs), bài 2, 3 và 7;
> notebook L6 (nanoTabPFN).

## 1. Bài toán
Có `X_train`, `y_train` (dữ liệu lịch sử có nhãn) và `X_test`. Cần phân phối xác suất của `y_test`. Đây là học có giám
sát thông thường. Điểm khác nằm ở cách giải.

## 2. Bảy nguyên lý

1. **Dự đoán không cần huấn luyện (in-context learning).** `fit()` chỉ nạp bảng lịch sử làm ngữ cảnh. Toàn bộ phép
   tính diễn ra lúc `predict()`: model đọc các dòng lịch sử cùng các dòng mới và trả kết quả trong một forward pass.
   Trọng số không đổi theo từng bộ dữ liệu. Nên gọi `X_train`/`y_train` là *context features*/*context labels*.

2. **Model được pretrain hoàn toàn trên dữ liệu tổng hợp.** Mỗi bước huấn luyện: sinh một bảng giả mới từ một chương
   trình gọi là *prior*, che nhãn của một phần dòng, cho model đoán, tính loss, cập nhật trọng số, rồi bỏ bảng đó.
   Lặp hàng trăm triệu lần. Kết quả là một *thuật toán học máy được học ra*.

3. **Prior quyết định năng lực.** Model chỉ tổng quát tốt trên những mẫu hình mà prior từng sinh ra. Trong L6, prior
   chỉ có đường thẳng thì model kém trên dữ liệu hình sin; thêm sóng sin vào prior thì model vượt logistic regression và
   random forest. Hệ quả thực tế: dữ liệu của mình càng khác những gì prior bao phủ thì càng phải kiểm chứng kỹ.

4. **Kiến trúc tôn trọng tính bất biến của bảng.** Mỗi ô thành một vector. Mỗi lớp có hai loại attention: theo hàng
   (các ô trong một dòng trao đổi thông tin) và theo cột (mọi dòng nhìn vào các dòng có nhãn). Dòng test nhìn dòng
   train, không có chiều ngược lại. Đổi thứ tự dòng hoặc cột không đổi kết quả.

5. **Hồi quy trả về một phân phối.** Model chia khoảng giá trị thành hàng nghìn ô và gán xác suất cho từng ô. Trung
   bình, trung vị, phân vị đều là tóm tắt của phân phối đó. Dải P10–P90 nghĩa là model cho rằng khoảng 80% khả năng giá
   trị thật nằm trong dải. Dải hẹp là tự tin, dải rộng là bất định.

6. **Feature engineering là context engineering.** Model không biết gì ngoài các cột được đưa vào. Thêm một cột mang
   thông tin thật (ví dụ giờ trong ngày cho giá điện) thì dải dự đoán hẹp lại rõ rệt.

7. **Dùng đúng công cụ.** LLM giỏi suy luận, ngôn ngữ và code. Tabular foundation model giỏi dự đoán thống kê trên
   bảng. Ghép hai thứ qua tool/MCP.

## 3. Vì sao LLM kém khi dự đoán trên bảng
- LLM tách số thành token chữ số, nên không nắm con số nguyên vẹn.
- LLM xử lý tuần tự và phải làm phẳng bảng. Một bảng 1 triệu dòng × 1.000 cột là khoảng 3–4 tỷ token.
- LLM không biết rằng đổi chỗ dòng hoặc cột vẫn là cùng một bảng.
- LLM không tất định và có thể bịa một câu trả lời nghe hợp lý.
- Với một khách hàng đã có trong dữ liệu, LLM chỉ tra cứu. Với khách mới, LLM đoán token kế tiếp chứ không ước lượng
  từ dữ liệu.

## 4. So với quy trình truyền thống
Quy trình cũ: làm sạch → chọn model → feature engineering → tune → triển khai → bảo trì, lặp lại cho từng bộ dữ liệu.
TabPFN bỏ được bước chọn model và tune. Vẫn phải làm: hiểu bài toán, chia dữ liệu đúng, chọn feature có nghĩa, đánh
giá so với baseline.

Khoá học nói các tabular foundation model đã vượt gradient-boosted trees (XGBoost, LightGBM, CatBoost) trên benchmark.
Điều này đúng với bảng nhỏ và vừa, dữ liệu độc lập. Nó **không** đúng trong mọi trường hợp, xem `khi-nao-khong-dung.md`.

## 5. Hướng phát triển (bài 7)
- Quy mô: 10.000 dòng (v2, 01/2025) lên 1 triệu dòng (v3, v3.5). Khoá học nhắc tới v4 với 10 triệu dòng. `[VERIFY]`
- Dữ liệu thực tế lộn xộn: theo nhóm, theo thời gian, số chiều cao, nhiều bảng quan hệ, mất cân bằng, cột văn bản.
- Nhân quả: Do-PFN mô phỏng can thiệp trong prior để ước lượng hiệu ứng từ dữ liệu quan sát.
