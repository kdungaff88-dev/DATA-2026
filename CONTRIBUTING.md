# Hướng dẫn đóng góp

Kho mã được phát triển qua các thay đổi nhỏ, dễ rà soát và có thể tái lập. Đọc
`AGENTS.md` và `docs/DEVELOPMENT.md` trước khi đóng góp.

## Thiết lập cục bộ

```powershell
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
```

## Quy ước nhánh và thay đổi

- Dùng tên nhánh ngắn như `feat/profile-metrics`, `fix/parquet-schema` hoặc
  `docs/source-provenance`.
- Mỗi pull request chỉ nên xử lý một thay đổi logic.
- Nêu rõ tác động đến dữ liệu, schema, cấu hình và khả năng tương thích.
- Không commit bộ dữ liệu đã tải, tệp cơ sở dữ liệu, secret hoặc đường dẫn riêng
  trên máy.
- Khi thêm hoặc thay đổi nguồn, cập nhật manifest và ghi rõ giấy phép, ghi công,
  phiên bản, phạm vi và dung lượng dự kiến.

## Trước khi mở pull request

Chạy:

```powershell
ruff check .
python -m pytest -q
python -m compileall -q tools tests
```

Nếu không chạy được một bước kiểm tra, hãy nêu lý do và phần chưa xác minh.
Không báo kiểm định dữ liệu lớn đã đạt nếu chưa thực sự chạy trên đúng phiên
bản và khu vực được ghi nhận.

## Pull request

Dùng mẫu pull request của kho mã. Báo cáo cần gọn, không chứa bản ghi thô hoặc
dữ liệu cá nhân. Người review phải có thể tái lập thay đổi từ mã, cấu hình đã
quản lý phiên bản và đầu vào cục bộ được mô tả.
