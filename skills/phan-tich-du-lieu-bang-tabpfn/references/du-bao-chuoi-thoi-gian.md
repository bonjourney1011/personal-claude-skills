# Dự báo chuỗi thời gian bằng TabPFN

> Nguồn: notebook L2 mục 4 (giá điện Đức). Từ mục 3 trở đi là bổ sung ngoài khoá học, dựa trên tài liệu dự báo chuẩn
> (Hyndman & Athanasopoulos, *Forecasting: Principles and Practice*) và các nghiên cứu năm 2026 về model nền trong tài chính.

## 1. Ý tưởng
TabPFN không có khái niệm thời gian. Nó coi các dòng là một bảng không thứ tự. Dự báo là hồi quy, trong đó các dòng
tương lai chưa có giá trị mục tiêu. Mọi hiểu biết về thời gian phải được đưa vào qua các cột.

## 2. Điều khoá học dạy
- Chỉ đưa cột thời gian thô: dự báo bị phẳng, vì mỗi giờ tương lai là một con số nằm ngoài vùng đã thấy.
- Thêm feature lịch (giờ trong ngày, thứ trong tuần): dải dự đoán hẹp lại và bám giá thật.
- Thêm biến ngoài **đã biết trước** cho tương lai (dự báo phụ tải, dự báo điện tái tạo): hẹp thêm.
- Cả tầm dự báo được đoán trong một lần gọi. Dải P10–P90 đi kèm không tốn thêm phép tính.

```python
hist["hour_of_day"] = hist["hour"].dt.hour
hist["day_of_week"] = hist["hour"].dt.dayofweek
reg = TabPFNRegressor()
reg.fit(hist[FEATURES], hist["price_eur"])
p10, p50, p90 = reg.predict(future[FEATURES], output_type="quantiles", quantiles=[0.1, 0.5, 0.9])
```

Gói `tabpfn-time-series` tự động hoá cách làm này (chỉ số chạy, feature lịch, feature mùa vụ tự dò). Nó chỉ nhận biến
ngoài đã biết trước cho tương lai; biến chỉ có trong quá khứ bị bỏ.

## 3. Ba câu hỏi phải trả lời trước khi dựng feature
1. **Chuỗi có mùa vụ rõ không?** Giá điện có chu kỳ ngày và tuần nên feature lịch rất mạnh. Giá tài sản tài chính gần
   như không có, nên feature lịch gần như vô dụng.
2. **Giá trị tương lai có nằm ngoài vùng đã thấy không?** Nếu có (giá có xu hướng), đừng dự báo mức giá. Dự báo
   **mức thay đổi**: `log(P[t+h] / P[t])`. Mức thay đổi nằm trong vùng model đã thấy.
3. **Feature nào thật sự biết được tại thời điểm dự báo?** Chỉ hai loại hợp lệ: thông tin tính từ dữ liệu đến hết
   ngày gốc, và sự kiện đã lên lịch trước.

## 4. Thiết kế "ngày gốc × tầm dự báo"
Dùng khi chuỗi không có mùa vụ rõ và cần nhiều tầm dự báo.

- Mỗi dòng là một cặp (ngày gốc `t`, tầm `h`).
- Mục tiêu: mức thay đổi từ `t` đến `t+h`.
- Feature: tính từ dữ liệu đến hết ngày `t`, cộng thêm cột `h`.
- Khi dự báo tại ngày gốc `T`: ngữ cảnh chỉ gồm các dòng có `t + h ≤ T`. Dòng nào có kết quả rơi sau `T` phải loại
  (gọi là purge). Bỏ bước này là rò rỉ.

## 5. Backtest đúng cách
- **Rolling-origin**: chọn nhiều ngày gốc trong quá khứ. Ở mỗi ngày gốc, chỉ dùng dữ liệu trước đó để dự báo, rồi so
  với giá trị thật. Một lần holdout như trong khoá học là không đủ.
- Cần ít nhất khoảng 100 ngày gốc, trải qua nhiều giai đoạn khác nhau.
- Các cửa sổ dự báo chồng lên nhau thì sai số tương quan với nhau. Khi kiểm định ý nghĩa thống kê, chỉ dùng các cửa sổ
  không chồng lấn.
- Chốt feature, tầm dự báo và quy tắc quyết định **trước** khi xem kết quả. Thử càng nhiều biến thể thì kết quả đẹp
  nhất càng có khả năng là do may.

## 6. Chỉ số
| Chỉ số | Đo cái gì |
|---|---|
| Pinball loss (trung bình qua các phân vị) | Chất lượng của cả phân phối dự báo; càng thấp càng tốt |
| Điểm kỹ năng = 1 − loss model / loss mốc ngây thơ | Dương là thắng mốc ngây thơ |
| MASE | Sai số tuyệt đối của trung vị chia cho sai số của mốc "giữ nguyên"; dưới 1 là thắng |
| Độ phủ dải 80% và 50% | Dải có trung thực không; phải gần 80% và 50% |
| Tỷ lệ đúng hướng | Chỉ có nghĩa khi kèm khoảng tin cậy và tính trên cửa sổ không chồng lấn |

Mốc ngây thơ bắt buộc: random walk (giá trị giữ nguyên, phân vị lấy từ phân phối thay đổi trong quá khứ).

## 7. Kỳ vọng thực tế với giá tài sản
- Các khảo sát năm 2026 chưa tìm thấy model nào thắng bền vững mốc "giá giữ nguyên" cho giá crypto ở tầm ngày đến tháng.
- Model nền thường kém GBDT đã tinh chỉnh khi dữ liệu trôi theo thời gian.
- Thứ dự báo được tốt hơn là biến động và độ rộng của dải. Nên trình bày kết quả dưới dạng dải xác suất đã kiểm chứng
  độ phủ, không trình bày một mức giá.
- Nhiều model chuỗi thời gian nền được pretrain trên giá công khai. Backtest "zero-shot" trên giai đoạn cũ có thể đẹp
  hơn thực tế. Bằng chứng đáng tin nhất là nhật ký dự báo thật, ghi trước khi biết kết quả.
