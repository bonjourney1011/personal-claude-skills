# Phiên bản, giới hạn và license

> **Kiểm tra ngày 13/11/2026.** Phần này đổi nhanh. Trước khi dựa vào một con số, mở lại nguồn chính thức:
> https://docs.priorlabs.ai/models · https://docs.priorlabs.ai/changelog · https://priorlabs.ai/pricing

## 1. Các phiên bản
| Model | Ra mắt | Dòng tối đa | Feature tối đa | Số lớp | Chạy ở đâu | License trọng số |
|---|---|---|---|---|---|---|
| TabPFN v2 | 01/2025 | 10.000 | 500 | 10 | Máy, API | Prior Labs License (Apache-2.0 + ghi công) |
| TabPFN-2.5 | 11/2025 | 100.000 | 2.000 | 10 | Máy | Phi thương mại |
| TabPFN-2.6 | 04/2026 | 100.000 | 2.000 | 10 | Máy, API | Phi thương mại |
| TabPFN-3 | 05/2026 | 1.000.000 | 2.000 | 160 | Máy; bản Plus và Thinking chỉ qua API | Phi thương mại |
| TabPFN-3.5 | 09/2026 | 1.000.000 | 20.000 (khuyên dùng ≤ 6.000) | 160 | Máy (Base, Fast); Plus và Thinking chỉ qua API | Phi thương mại |

- Khoá học dùng `tabpfn_client` 0.6.0 với TabPFN v3.5.
- Biến thể: *Plus* (cột văn bản), *Thinking* (tính thêm lúc fit để chính xác hơn), *Fast* (nhanh hơn).
- Khoá học nhắc tới v4 với 10 triệu dòng. `[VERIFY]`

## 2. License: điểm dễ vấp
- Mã nguồn gói `tabpfn` là Apache-2.0.
- **Trọng số tải về từ v2.5 trở đi chỉ cho phi thương mại.** Dùng thương mại trên máy riêng cần mua license.
- **API cloud** được dùng thương mại "trong phạm vi Điều khoản dịch vụ". Điều khoản ghi dành cho khách hàng doanh
  nghiệp, và Prior Labs có thể dùng dữ liệu gửi lên để cải thiện model trừ khi tắt tuỳ chọn đó.
- Tải trọng số cần đăng nhập và chấp nhận license; chạy không giao diện cần `TABPFN_TOKEN`.
- Chính sách sử dụng chấp nhận được (Acceptable Use Policy) chưa được đọc. `[VERIFY]` trước khi dùng cho mục đích tài
  chính hoặc y tế.

## 3. Hạn mức API (gói free)
| Hạng mục | Mức |
|---|---|
| Token | 5.000.000/ngày và 20.000.000/tháng, đặt lại lúc 00:00 UTC |
| Upload | 120/phút, 3.000/giờ |
| Fit | 60/phút, 1.000/giờ |
| Predict | 60/phút, 1.500/giờ |
| Thinking fit | 10/phút, 30/giờ |

Vượt hạn mức trả HTTP 429. Upload và fit thường không tốn token; predict và Thinking fit có tốn.
Ngữ cảnh tối đa mỗi estimator trên API: 200 triệu ô.

## 4. Chạy trên máy
- Nên có GPU khoảng 8 GB VRAM, bảng lớn cần 16 GB.
- CPU: có chốt chặn 5.000 dòng (v3, v3.5) hoặc 1.000 dòng (bản cũ). Bỏ chốt bằng
  `TABPFN_ALLOW_CPU_LARGE_DATASET=true` nhưng sẽ chậm.
- Không có GPU thì dùng API.

## 5. Gói liên quan
| Gói | Dùng cho |
|---|---|
| `tabpfn-client` | Gọi API cloud, giao diện giống scikit-learn |
| `tabpfn` | Chạy trên máy |
| `tabpfn-extensions` | SHAP và chọn feature, bài toán nhiều lớp, phát hiện ngoại lai, embedding |
| `tabpfn-time-series` | Dự báo chuỗi thời gian (v1.3.0, mặc định gọi API) |

## 6. Model khác cùng loại (để biết có lựa chọn)
| Model | License | Ghi chú |
|---|---|---|
| TabICL v2 | BSD-3 | Mở hoàn toàn, chạy được trên CPU, tới 500k dòng |
| Mitra v2 (AutoGluon) | Apache-2.0 | Mạnh với bảng nhỏ |
| TabDPT | Apache-2.0 | Tới 100k dòng |

Cần chạy thương mại trên máy riêng mà không mua license thì xem TabICL v2 hoặc Mitra.
