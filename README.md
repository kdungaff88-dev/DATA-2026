# DATA-2026

Dự án kỹ thuật dữ liệu cục bộ, có thể tái lập, nhằm đánh giá, chuẩn hóa và
đóng gói các bộ dữ liệu có giá trị thương mại. Nguồn đầu tiên đang được đánh
giá là Overture Maps Places tại Hoa Kỳ.

## Nguyên tắc làm việc

- Giữ nguyên bất biến từng bản chụp dữ liệu nguồn đã thu thập.
- Trước khi biến đổi dữ liệu, ghi lại nguồn, phiên bản, ngày lấy, việc rà soát
  giấy phép/ghi công, phạm vi địa lý và định danh tệp.
- Không đưa tệp dữ liệu lớn hoặc cơ sở dữ liệu DuckDB cục bộ vào Git. Git chỉ
  quản lý mã, cấu hình, tài liệu, kiểm thử và báo cáo gọn.
- Mọi phép biến đổi phải chạy lại được từ mã và cấu hình đã quản lý phiên bản.
- Giữ các trường nguồn; bổ sung trường chuẩn hóa thay vì âm thầm ghi đè hoặc
  loại bỏ giá trị gốc.
- Khi chưa xác minh, ghi rõ tình trạng giấy phép, tư cách người bán hoặc payout
  là chưa rõ; không suy đoán.

## Cấu trúc kho mã

- `configs/data_sources/`: cấu hình thu thập và provenance theo từng nguồn.
- `data/raw/`: bản chụp nguồn cục bộ bất biến; Git bỏ qua thư mục này.
- `data/staging/`: dữ liệu trung gian tạm; Git bỏ qua thư mục này.
- `data/normalized/`: dữ liệu chuẩn hóa cục bộ theo phiên bản; Git bỏ qua.
- `data/curated/`: dữ liệu cục bộ đã tuyển chọn cho sản phẩm; Git bỏ qua.
- `docs/`: kiến trúc, quyết định và quy trình vận hành.
- `reports/`: báo cáo profiling và chất lượng gọn, có thể rà soát.
- `tools/`: công cụ kiểm tra dữ liệu cục bộ.
- `tests/`: kiểm thử có thể chạy lại cho công cụ và phép biến đổi.
- `AGENTS.md`: hướng dẫn chuẩn cho các coding agent.
- `CONTRIBUTING.md`: quy trình đóng góp và yêu cầu pull request.
- `.github/`: CI, cập nhật phụ thuộc, biểu mẫu issue và mẫu review.

## Phát triển

Đọc `AGENTS.md`, sau đó làm theo `CONTRIBUTING.md`,
`docs/DEVELOPMENT.md` và `docs/TESTING.md` trước khi thay đổi mã.

## Thiết lập cục bộ

Cần Python 3.11 trở lên.

```powershell
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
```

Profiling một tệp hoặc thư mục Parquet đã có sẵn trên máy:

```powershell
python tools/profile_parquet.py --input "data/raw/overture/release=REPLACE_ME/region=us-census-state-equivalents/run=REPLACE_ME/theme=places/type=place" --output "reports/overture-us-places-profile"
```

Tạo báo cáo spike đầy đủ từ snapshot đã tải thành công:

```powershell
python tools/report_overture_places_spike.py --input "data/raw/overture/release=REPLACE_ME/region=us-census-state-equivalents/run=REPLACE_ME/theme=places/type=place" --output "reports/overture-places-us-spike" --label "Overture Places US RELEASE"
```

Báo cáo gồm schema, null/blank/list-rỗng, độ sẵn có trường sản phẩm, phân bố
category/status, provenance và giới hạn diễn giải. Chỉ số chất lượng nguồn
không thay thế bằng chứng nhu cầu hoặc giao dịch của người mua.

Lập kế hoạch lấy Places Hoa Kỳ từ phiên bản Overture mới nhất (đọc STAC metadata
để ước tính dung lượng; chưa tải GeoParquet):

```powershell
python tools/download_overture_us.py
```

Có thể chọn một hoặc nhiều theme; mặc định là `places`. Các lựa chọn gồm
`addresses`, `base`, `buildings`, `divisions`, `places` và `transportation`:

```powershell
python tools/download_overture_us.py --themes places,buildings
```

Chỉ thêm `--download` khi muốn tải thật:

```powershell
python tools/download_overture_us.py --themes places,buildings --download
```

Bbox chỉ là bước giảm dữ liệu đọc từ xa. Đầu ra được lọc theo polygon lớp
TIGERweb ACS2025 "States" (layer 80) của U.S. Census Bureau; chỉ giữ feature có toàn bộ geometry nằm trong các
bang, DC và lãnh thổ có trong cấu hình. Các feature cắt qua biên giới bị loại,
không bị cắt hình học. Bản ghi ngoài Hoa Kỳ có thể được đọc tạm trong quá trình
lọc từ xa nhưng không được ghi vào GeoParquet đầu ra. Mỗi theme/type có manifest
riêng, phiên bản Overture, ranh giới Census, số dòng, dung lượng và SHA-256.

Đọc `docs/DATA_WORKFLOW.md` trước khi thu thập. Điều khoản khác nhau theo theme;
manifest chỉ ghi nguồn rà soát, không xác nhận quyền tái phân phối thương mại.
Lập kế hoạch hiển thị ước tính bảo thủ từ dung lượng file STAC và ổ đĩa còn
trống; `--download` sẽ bị từ chối nếu dung lượng trống thấp hơn ngưỡng dự phòng.
Tải nhiều theme có thể cần nhiều thời gian; chỉ chọn theme cần thiết.
