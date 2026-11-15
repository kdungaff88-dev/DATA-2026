# Chiến lược kiểm thử

Kiểm thử phải chạy lại được và mặc định không phụ thuộc dịch vụ bên ngoài hoặc
dữ liệu dung lượng lớn.

## Các cấp độ kiểm thử

1. **Unit test:** kiểm tra ánh xạ schema, ngữ nghĩa null/rỗng, quy tắc chuẩn hóa,
   xử lý đường dẫn, bbox, chọn theme, ước tính kích thước STAC và kiểm tra dung
   lượng đĩa.
2. **Kiểm thử tích hợp bằng fixture:** dùng tệp Parquet tổng hợp, dung lượng nhỏ
   để kiểm tra thao tác đọc DuckDB, phép biến đổi và tạo báo cáo.
3. **Kiểm tra data contract:** xác thực cột/kiểu bắt buộc, tính duy nhất của
   khóa, ánh xạ category được chấp nhận, quy tắc geometry/địa chỉ và ngưỡng tỷ
   lệ null đã ghi cho một phiên bản nguồn cụ thể.
4. **Chạy nghiệm thu dữ liệu lớn:** chỉ chạy khi được yêu cầu và phải giới hạn
   rõ phiên bản/khu vực. Ghi định danh đầu vào, số dòng, thời gian chạy, dung
   lượng, chỉ số và giới hạn đã biết trong `reports/`. Không báo đạt nếu chưa
   chạy.

## Lệnh kiểm tra thường dùng

```powershell
ruff check .
python -m pytest -q
python -m compileall -q tools tests
```

Kiểm thử tích hợp DuckDB bằng fixture phải chạy trong CI vì CI cài
`requirements-dev.txt`. Nếu máy cục bộ chưa có DuckDB, kiểm thử có thể bị bỏ qua;
phải ghi rõ phần tích hợp chưa được xác minh cho tới khi cài dependency và chạy
lại.

Kiểm thử downloader không được gọi STAC hoặc tải dữ liệu thật. Dùng phiên bản
cụ thể trong unit test để kiểm tra lập kế hoạch ngoại tuyến; kiểm thử có mạng
chỉ chạy riêng khi người dùng yêu cầu.

Kiểm thử lọc Hoa Kỳ dùng polygon tổng hợp để xác nhận chỉ geometry được polygon
bao phủ hoàn toàn mới được giữ lại. Không tải shapefile Census hoặc Overture
trong CI.

Report generator được kiểm thử bằng fixture Parquet tổng hợp; không dùng dữ liệu
Places thật và không gọi STAC trong các unit test.

## Quy tắc chất lượng dữ liệu

- Báo cáo riêng giá trị null, chuỗi trắng và danh sách rỗng.
- Ghi rõ mẫu số và định nghĩa chỉ số.
- Kiểm tra tường minh khóa trùng và schema drift.
- Không coi giá trị thiếu là dữ kiện phủ định về doanh nghiệp (ví dụ: thiếu
  trạng thái hoạt động không có nghĩa là đã đóng cửa).
- Không đưa bản ghi nguồn thật hoặc dữ liệu cá nhân vào fixture và log kiểm thử.

## Xử lý lỗi

Khi kiểm thử thất bại, giữ lại chi tiết lỗi và xác định nguyên nhân là do mã,
nguồn dữ liệu thay đổi hay giả định không còn đúng; thêm regression test khi
phù hợp. Không thay đổi ngưỡng chỉ để làm cho một lần chạy đạt; mọi thay đổi
ngưỡng phải được ghi nhận và phê duyệt.
