# Khi nào không nên dùng TabPFN (hoặc không dùng một mình)

> Khoá học không có danh sách này. Nguồn: các báo cáo benchmark năm 2026 (TabArena, BeyondArena) và nghiên cứu về trôi
> dữ liệu theo thời gian (arXiv 2502.20260). Kiểm tra ngày 13/11/2026.

| Tình huống | Vì sao | Nên làm |
|---|---|---|
| Bảng từ 100k dòng trở lên | Trên benchmark bảng lớn, các model nền xếp dưới GBDT đã tinh chỉnh | Dùng GBDT; hoặc lấy mẫu ngữ cảnh rồi so cả hai |
| Dữ liệu trôi theo thời gian, chia theo thời gian hoặc theo nhóm | Model học trong ngữ cảnh suy giảm mạnh khi phân phối tương lai khác quá khứ | Backtest rolling-origin; giữ GBDT và mốc ngây thơ làm đối chứng |
| Cần trả lời trong vài mili giây trên CPU | Một lần dự đoán của TabPFN tốn hàng giây trên CPU, GBDT tốn mili giây | GBDT; hoặc API có KV cache nếu chấp nhận độ trễ mạng |
| Dữ liệu không được rời khỏi máy và mục đích thương mại | Trọng số từ v2.5 là phi thương mại | Mua license, hoặc dùng TabICL v2/Mitra |
| Câu hỏi nhân quả ("nếu làm X thì sao?") | Model dự đoán tương quan | Thiết kế thí nghiệm hoặc phương pháp nhân quả |
| Chỉ cần tra cứu, đếm, gộp nhóm | Không phải bài toán dự đoán | SQL hoặc pandas |
| Mẫu hình rất khác những gì prior bao phủ | Prior quyết định năng lực | Kiểm chứng kỹ trên tập test; cân nhắc fine-tune khi có trên 1.000 dòng |

## Cách dùng an toàn
1. Dùng TabPFN làm **baseline nhanh và mạnh** cho bảng nhỏ và vừa: không cần tune, có ngay độ bất định.
2. Luôn chạy thêm một GBDT hoặc mốc ngây thơ trên cùng tập test.
3. Khi hai model ngang nhau, lấy trung bình dự đoán của cả hai thường ổn định hơn từng model.
4. Kiểm độ phủ của dải dự đoán trước khi dùng dải đó để ra quyết định.
5. Viết thẳng trong báo cáo khi TabPFN không thắng baseline. Kết quả đó vẫn có giá trị.
