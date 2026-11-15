# Cấu trúc dữ liệu cục bộ

Tệp lớn hoặc được tạo từ nguồn dữ liệu phải lưu cục bộ, không đưa vào Git:

```text
data/
  raw/<source>/<theme>/release=<release>/...
  staging/<run-id>/...
  normalized/<dataset>/<schema-version>/...
  curated/<product>/<version>/...
```

Lớp `raw` là bất biến. Mỗi phiên bản nguồn mới có đường dẫn riêng; không ghi
đè bản chụp trước đó. Lưu manifest nguồn và báo cáo gọn trong Git, nhưng không
commit tệp Parquet, tệp cơ sở dữ liệu hoặc dữ liệu khách hàng.

Trước khi thu thập dữ liệu số lượng lớn, kiểm tra phiên bản đã chọn, dung lượng
ước tính, dung lượng trống, điều khoản nguồn và khả năng lọc partition hoặc
tải riêng khu vực cần thiết.
