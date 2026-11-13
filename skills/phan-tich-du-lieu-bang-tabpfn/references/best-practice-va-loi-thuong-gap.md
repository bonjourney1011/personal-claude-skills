# Best practice và lỗi thường gặp

> Nguồn: notebook L2, L3, L4 và bài 3–6 của khoá học. Mục 6 là bổ sung ngoài khoá học.

## 1. Tiền xử lý: làm ít đi
| Không làm | Lý do |
|---|---|
| Impute giá trị thiếu | Model xử lý `NaN` trực tiếp (bộ bệnh tim trong khoá học thiếu khoảng hai phần ba) |
| One-hot encode | Cột phân loại được nhận diện tự động; chuỗi thô như tên khu phố dùng được luôn |
| Scale, chuẩn hoá | Model tự chuẩn hoá theo các dòng có nhãn |
| Tune siêu tham số | Không cần |

Một ngoại lệ: khi truyền mảng numpy (`.values`) thì kiểu cột bị mất. Lúc đó phải truyền `categorical_features_indices`.

## 2. API cơ bản
```python
from tabpfn_client import TabPFNClassifier, TabPFNRegressor

clf = TabPFNClassifier()
clf.fit(X_train, y_train)            # chỉ nạp ngữ cảnh
nhan = clf.predict(X_test)
xac_suat = clf.predict_proba(X_test)

reg = TabPFNRegressor()
reg.fit(X_train, y_train)
trung_binh = reg.predict(X_test)     # mặc định là trung bình
p10, p50, p90 = reg.predict(X_test, output_type="quantiles", quantiles=[0.1, 0.5, 0.9])
```
Kết quả qua API có thể đổi khi Prior Labs cập nhật model. Ghi lại phiên bản client và ngày chạy trong báo cáo.

## 3. Luôn đọc độ bất định
- Phân loại: dùng `predict_proba` khi cần xếp hạng hoặc tự chọn ngưỡng. Ngưỡng 0,5 hiếm khi là ngưỡng đúng cho bài
  toán kinh doanh.
- Hồi quy: báo trung vị kèm dải P10–P90.
- **Kiểm độ phủ**: trên tập test, tỷ lệ giá trị thật nằm trong dải P10–P90 phải gần 80%. Thấp hơn nhiều là model quá
  tự tin. Cao hơn nhiều là dải quá rộng.
  ```python
  trong_dai = (y_test >= p10) & (y_test <= p90)
  print(f"Dải 10–90 phủ {trong_dai.mean():.0%}")
  ```

## 4. Đánh giá
- Giữ riêng tập test và so với baseline.
- Phân loại: confusion matrix, precision, recall, ROC AUC. Chọn chỉ số theo loại sai đắt hơn (y tế thường ưu tiên recall).
- Hồi quy: MAE (cùng đơn vị với mục tiêu) và R². Xem thêm sai số theo từng vùng giá trị, vì vùng ít mẫu thường sai nhiều.
- Rò rỉ dữ liệu: bất kỳ thông tin nào của tập test lọt vào lúc fit đều làm kết quả đẹp giả.

## 5. Giải thích dự đoán
| Công cụ | Trả lời câu hỏi | Cách đọc |
|---|---|---|
| SHAP waterfall | Vì sao dòng này được dự đoán như vậy? | Đi từ dự đoán tham chiếu; thanh dương đẩy lên, thanh âm kéo xuống; tổng bằng dự đoán cuối |
| SHAP beeswarm | Model dựa vào feature nào nhiều nhất? | Mỗi chấm là một dòng × một feature; màu là giá trị feature |
| Partial dependence | Đổi một feature thì dự đoán đổi ra sao? | Giữ các feature khác, quét một feature |

- SHAP gọi model hàng trăm lần. Fit với `fit_mode="fit_with_cache"` trước, dùng mẫu nền khoảng 10 dòng và giải thích
  khoảng 10 dòng test.
- Yếu tố dẫn đầu của một dòng cụ thể có thể khác bức tranh toàn cục.
- Đây là tương quan và độ nhạy của model, không phải nhân quả.

## 6. KV cache
```python
clf = TabPFNClassifier(fit_mode="fit_with_cache")
clf.fit(X_train, y_train)   # chậm hơn vì dựng cache
```
Câu hỏi quyết định: sẽ dự đoán bao nhiêu lần từ cùng một ngữ cảnh trước khi thay nó?

| Tình huống | Dùng cache? |
|---|---|
| Nhiều request rời rạc, ngữ cảnh cố định hoặc đổi chậm | Có |
| Dự đoán một lô lớn một lần | Không cần |
| Dữ liệu train đổi thường xuyên | Không, dựng cache tốn hơn lợi ích |

Khi đo tốc độ: tách thời gian model và thời gian cả request, chạy làm nóng trước, lấy trung vị.

## 7. Điều khoá học không dạy (bổ sung)
- Khoá học không so sánh trực tiếp với GBDT. Luôn tự chạy baseline.
- Khoá học không dạy ensemble, fine-tuning, bảng rất lớn, bài toán nhiều lớp. Các gói `tabpfn-extensions` và
  `tabpfn.finetuning` có hỗ trợ; đọc tài liệu chính thức trước khi dùng. Fine-tune dễ overfit dưới khoảng 1.000 dòng
  và thường làm xấu calibration.
- Dữ liệu có thời gian: xem `du-bao-chuoi-thoi-gian.md`.
