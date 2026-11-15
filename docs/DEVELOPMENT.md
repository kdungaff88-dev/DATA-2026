# Hướng dẫn phát triển

## Môi trường

- Python 3.11 trở lên.
- DuckDB để profiling và biến đổi Parquet cục bộ.
- Git để quản lý mã, cấu hình, tài liệu, kiểm thử và báo cáo gọn.
- Dữ liệu lớn phải lưu cục bộ hoặc tại nơi lưu trữ được phê duyệt rõ ràng, không
  đưa vào Git.

Tạo môi trường ảo và cài các dependency phục vụ phát triển:

```powershell
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
```

## Quy trình thay đổi

1. Đọc `AGENTS.md`, `docs/DATA_WORKFLOW.md`, manifest nguồn liên quan và
   `docs/DECISIONS.md`.
2. Kiểm tra `git status` trước khi sửa và giữ nguyên các thay đổi không liên
   quan.
3. Khi làm với nguồn dữ liệu, chốt phiên bản, hoàn tất manifest và rà soát quyền
   sử dụng trước. Ước tính dung lượng đĩa trước khi thu thập.
4. Tách riêng các bước thu thập, profiling, chuẩn hóa và tuyển chọn theo sản
   phẩm.
5. Đảm bảo phép biến đổi có thể chạy lại từ mã và cấu hình đã quản lý phiên bản.
   Ghi lại run ID, phiên bản schema, số lượng và chỉ số chất lượng.
6. Thêm kiểm thử bằng fixture tổng hợp và cập nhật tài liệu liên quan.
7. Chạy `ruff check .`, `python -m pytest -q` và
   `python -m compileall -q tools tests`.

## Quy ước mã

- Ưu tiên module nhỏ, đầu vào và đầu ra tường minh.
- Đặt thao tác I/O ở rìa hệ thống; viết logic chuẩn hóa sao cho kiểm thử được mà
  không cần mạng hoặc tệp nguồn lớn.
- Dùng type hint cho hàm công khai và tên rõ ràng để phân biệt giá trị nguồn với
  giá trị đã chuẩn hóa.
- Xử lý riêng các trường hợp thiếu, rỗng, sai định dạng và chưa xác định.
- Tránh hard-code ID phiên bản, thông tin xác thực, đường dẫn cá nhân và ngưỡng
  không có giải thích. Đặt lựa chọn riêng theo nguồn trong manifest/cấu hình và
  ghi rõ cơ sở của ngưỡng.
- Khi thay đổi schema hoặc chỉ số, phải nêu ảnh hưởng đến báo cáo hiện có và
  thành phần sử dụng phía sau.

## Tiếp nhận nguồn dữ liệu

Trước khi thêm nguồn, hoàn thiện manifest gồm URL chính thức, cách đánh phiên
bản, giấy phép/điều khoản, ghi công, phạm vi địa lý, dung lượng dự kiến, đánh
giá PII và chu kỳ cập nhật. Quyền chưa rõ thì không được tái phân phối, nhưng
vẫn có thể rà soát cục bộ. Không bắt đầu tải qua mạng nếu chưa được người dùng
cho phép rõ ràng.

## Đầu ra cục bộ

- `data/raw/`: bản chụp bất biến.
- `data/staging/`: dữ liệu trung gian có thể tạo lại.
- `data/normalized/`: đầu ra chuẩn hóa cục bộ có phiên bản schema.
- `data/curated/`: đầu ra phục vụ sản phẩm.
- `reports/`: báo cáo gọn, có thể rà soát và quản lý phiên bản an toàn.

Rà soát tệp được tạo trước khi đưa vào staging. `.gitignore` chỉ là lớp bảo vệ,
không thay thế việc kiểm tra `git status`.
