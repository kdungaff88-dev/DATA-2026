# Báo cáo Mini Data Spike — Overture Places Hoa Kỳ

- Thời điểm tạo: `2026-11-15T13:08:09.733387+00:00`
- Release Overture: `2026-10-21.0`
- Phạm vi: `us_census_state_equivalents`; theme `places`, type `place`.
- Số dòng sau lọc: **18,560,038**.
- Số cột: **21**.
- File đầu ra: **3,950,607,007 byte**; SHA-256 `3bb14b5b1959b2217bc21f44f17a71b93c6b1653f003d86c53216c6658534943`.

## Kết luận điều hành

Báo cáo này là bằng chứng về quy mô/schema/độ sẵn có trường của nguồn dữ liệu sau lọc Hoa Kỳ. Nó **không** chứng minh mức sẵn sàng chi trả, khả năng bán trên marketplace hay quyền tái phân phối thương mại. Chưa kiểm chứng nhu cầu người mua; trạng thái giấy phép vẫn phải được rà soát theo từng nguồn thành phần.

## Báo cáo trực quan quyết định

Mở `DECISION_REPORT.html` để xem biểu đồ độ sẵn có trường, quy mô category,
heatmap liên hệ, operating status, confidence, inventory license và bảng
provenance/điểm dừng. Báo cáo chỉ dùng artifact tổng hợp, không nhúng record
nguồn.

Tạo lại bằng:

```powershell
python tools/build_overture_decision_report.py
```

## Phạm vi và provenance

- Census: TIGERweb ACS2025 layer `80`, 56 đơn vị; SHA-256 `4576e828397491111baaf22d472f2557eea31e966b2444f841f8041614d84ca4`.
- Overture source: `s3://overturemaps-us-west-2/release/2026-10-21.0/theme=places/type=place/`; STAC catalog: `https://stac.overturemaps.org/catalog.json`.
- Thời gian ingest UTC: bắt đầu `2026-11-15T11:49:35.480812+00:00`, đọc nguồn `2026-11-15T11:49:39.152206+00:00`, hoàn tất `2026-11-15T12:40:31.767858+00:00`.
- STAC preflight: 8 file ứng viên, 6,110,495,166 byte.
- Số dòng ứng viên từ các bbox: 20,571,368; được giữ sau phép `covered_by`: 18,560,038; bị loại theo chính sách biên: 2,011,330 (9.777% candidate). Đây không phải số đếm thuần túy các feature ngoài Hoa Kỳ: predicate cũng loại geometry null/không giải mã được hoặc không được polygon bao phủ hoàn toàn.
- Trạng thái rà soát giấy phép: `pending_theme_specific_review`; đã chấp thuận tái phân phối thương mại: `False`.
- Config SHA-256: `fea9db3c20cd33ae5ddcb8414036a53a0dcea26b40b8a5affe849f25aca7ad76`.
- Downloader SHA-256: `76ab26eaa840a187e56f0d8d5b548ed15d506ac05f6c92c5504502dd3b234169`.

## Độ sẵn có trường

Mẫu số là toàn bộ dòng đầu ra. Với list chuỗi, trường được coi là có dữ liệu khi còn ít nhất một phần tử không null/không trắng; list struct được đếm riêng và các trường con có chỉ số riêng. Chuỗi scalar phải không trắng sau `TRIM`; các kiểu khác phải không null. `profile/column_profile.csv` tách NULL, chuỗi scalar trắng và list rỗng ở cấp cột; `field_availability.csv` đo thêm giá trị hữu dụng trong list.

| Trường | Dòng có dữ liệu | Tỷ lệ | Định nghĩa |
|---|---:|---:|---|
| `id` | 18,560,038 | 100.000% | Chuỗi không null và không rỗng sau TRIM. |
| `geometry` | 18,560,038 | 100.000% | Giá trị không null. |
| `names.primary` | 18,560,038 | 100.000% | Chuỗi không null và không rỗng sau TRIM. |
| `taxonomy.primary` | 17,765,197 | 95.717% | Chuỗi không null và không rỗng sau TRIM. |
| `taxonomy.alternates` | 46,985 | 0.253% | List có ít nhất một chuỗi không null và không trắng; lọc phần tử trong DuckDB. |
| `taxonomy.hierarchy` | 17,765,197 | 95.717% | List có ít nhất một chuỗi không null và không trắng; lọc phần tử trong DuckDB. |
| `basic_category` | 17,793,912 | 95.872% | Chuỗi không null và không rỗng sau TRIM. |
| `addresses` | 18,560,038 | 100.000% | List không null và có ít nhất một phần tử. |
| `websites` | 14,138,137 | 76.175% | List có ít nhất một chuỗi không null và không trắng; lọc phần tử trong DuckDB. |
| `phones` | 16,171,781 | 87.132% | List có ít nhất một chuỗi không null và không trắng; lọc phần tử trong DuckDB. |
| `emails` | 6,584,925 | 35.479% | List có ít nhất một chuỗi không null và không trắng; lọc phần tử trong DuckDB. |
| `socials` | 10,784,539 | 58.106% | List có ít nhất một chuỗi không null và không trắng; lọc phần tử trong DuckDB. |
| `confidence` | 18,560,038 | 100.000% | Giá trị không null. |
| `operating_status` | 13,650,573 | 73.548% | Chuỗi không null và không rỗng sau TRIM. |
| `sources` | 18,560,038 | 100.000% | List không null và có ít nhất một phần tử. |
| `brand` | 10,500,540 | 56.576% | Giá trị không null. |
| `brand.names.primary` | 1,651,662 | 8.899% | Chuỗi không null và không rỗng sau TRIM. |
| `addresses[*].freeform` | 17,865,547 | 96.258% | Ít nhất một phần tử có freeform không null và không trắng. |
| `addresses[*].locality` | 18,501,443 | 99.684% | Ít nhất một phần tử có locality không null và không trắng. |
| `addresses[*].postcode` | 17,962,192 | 96.779% | Ít nhất một phần tử có postcode không null và không trắng. |
| `addresses[*].region` | 18,312,206 | 98.665% | Ít nhất một phần tử có region không null và không trắng. |
| `addresses[*].country` | 18,559,901 | 99.999% | Ít nhất một phần tử có country không null và không trắng. |
| `sources[*].dataset` | 18,560,038 | 100.000% | Ít nhất một phần tử có dataset không null và không trắng. |
| `sources[*].license` | 18,560,038 | 100.000% | Ít nhất một phần tử có license không null và không trắng. |
| `sources[*].provider` | 18,560,038 | 100.000% | Ít nhất một phần tử có provider không null và không trắng. |
| `sources[*].record_id` | 18,560,038 | 100.000% | Ít nhất một phần tử có record_id không null và không trắng. |
| `sources[*].update_time` | 18,560,038 | 100.000% | Ít nhất một phần tử có update_time không null và không trắng. |
| `sources[*].confidence` | 18,560,038 | 100.000% | Ít nhất một phần tử có confidence không null. |

## Nhóm phân loại và trường sản phẩm

Bảng dưới là tối đa 20 category chính theo số dòng. CSV đầy đủ (tối đa 100 nhóm) ở `category_profile.csv`.

| Category chính | Số dòng | Tỷ trọng | Website có dữ liệu | Phone có dữ liệu | Address có dữ liệu |
|---|---:|---:|---:|---:|---:|
| (không có category chính) | 794,841 | 4.283% | 57.410 | 88.308 | 100.000 |
| real_estate_agent | 412,399 | 2.222% | 87.384 | 97.878 | 100.000 |
| christian_place_of_worship | 346,777 | 1.868% | 74.157 | 88.279 | 100.000 |
| health_care | 304,902 | 1.643% | 36.848 | 29.231 | 100.000 |
| real_estate_service | 238,333 | 1.284% | 65.870 | 59.761 | 100.000 |
| insurance_agency | 235,802 | 1.270% | 79.143 | 74.635 | 100.000 |
| automotive_repair | 219,708 | 1.184% | 65.414 | 94.902 | 100.000 |
| social_or_community_service | 207,284 | 1.117% | 84.473 | 84.474 | 100.000 |
| beauty_salon | 205,391 | 1.107% | 62.955 | 91.361 | 100.000 |
| contractor | 202,118 | 1.089% | 76.394 | 85.880 | 100.000 |
| historic_site | 185,781 | 1.001% | 68.361 | 72.067 | 100.000 |
| hair_salon | 182,242 | 0.982% | 75.811 | 96.882 | 100.000 |
| restaurant | 179,613 | 0.968% | 48.391 | 57.141 | 100.000 |
| professional_service | 167,272 | 0.901% | 79.376 | 92.718 | 100.000 |
| park | 164,327 | 0.885% | 52.788 | 47.038 | 100.000 |
| doctors_office | 156,438 | 0.843% | 82.889 | 97.741 | 100.000 |
| gas_station | 154,420 | 0.832% | 82.091 | 79.187 | 100.000 |
| financial_service | 146,402 | 0.789% | 75.939 | 67.754 | 100.000 |
| money_transfer_service | 139,118 | 0.750% | 97.337 | 75.165 | 100.000 |
| atm | 135,932 | 0.732% | 76.319 | 74.588 | 100.000 |

## Geometry

- Shapely kiểm tra 18,560,038 geometry: hợp lệ 18,560,038 (100.000% trên geometry không null), không hợp lệ 0, WKB không giải mã được 0, geometry rỗng 0, null 0. Phân tích theo batch; xem `geometry_profile.json`.

## Chỉ số định danh và confidence

- ID phân biệt: `18560038`; ID null: `0`; dòng ID trùng vượt mức đầu tiên: `0`.
- Confidence (nếu là trường số): trung bình `0.7993389040915048`, median `0.9199122190475464`, min `0.0`, max `1.0`.
- Phân bố confidence theo khoảng:

| Khoảng confidence | Số dòng | Tỷ trọng |
|---|---:|---:|
| < 0.50 | 2,172,638 | 11.706% |
| [0.50, 0.75) | 2,694,010 | 14.515% |
| [0.75, 0.90) | 2,666,627 | 14.368% |
| [0.90, 0.95) | 6,613,839 | 35.635% |
| [0.95, 1.00] | 4,412,924 | 23.776% |
| NULL | 0 | 0.000% |

- Phân bố trạng thái hoạt động (`operating_status`, nếu có) nằm trong `operating_status.csv`. Giá trị null/thiếu không được diễn giải là địa điểm đã đóng cửa.


## Ý nghĩa cho nghiên cứu sản phẩm

- Category chính có ở 95.717% dòng; website 76.175%, phone 87.132% và email 35.479%. Vì vậy không nên hứa một tỷ lệ có dữ liệu đồng nhất cho mọi loại địa điểm.
- Các thành phần địa chỉ đo được gồm freeform 96.258%, locality 99.684%, postcode 96.779% và region 98.665%.
- Operating status có giá trị ở 73.548% dòng; phần còn lại là thiếu trạng thái, không đồng nghĩa đã đóng cửa.
- Dùng `field_availability.csv` và `category_profile.csv` để chọn category mà thông tin liên hệ/địa chỉ có độ phủ đủ cho một giả thuyết sản phẩm.
- Đối chiếu trường nguồn với nhu cầu của người mua bằng phỏng vấn hoặc thử nghiệm chào bán trên marketplace; không tự đặt ngưỡng đạt sau khi đã nhìn thấy số.
- Chỉ xây enrichment sau khi xác nhận có khoảng trống cụ thể và quyền dùng từng nguồn. Mọi tuyên bố “đầy đủ/chính xác/cập nhật” cần phép đo riêng.

## Giới hạn

- Bbox chỉ là tiền lọc; record ngoài Hoa Kỳ có thể được đọc tạm. Output chỉ giữ geometry được Census polygon bao phủ hoàn toàn; feature cắt biên bị loại thay vì clipping.
- Tỷ lệ có trường không đánh giá tính đúng/sai, hợp lệ, mới hay liên hệ được. Một list có phần tử vẫn có thể chứa giá trị sai hoặc cũ.
- Snapshot đo một release và một ranh giới Census 2025; không đại diện cho tốc độ cập nhật hoặc mọi thời điểm.
- Chưa xác minh quyền thương mại/tái phân phối; không xuất bản hoặc bán snapshot này trước khi hoàn tất rà soát giấy phép/ghi công.
- Dữ liệu chất lượng không thay thế bằng chứng marketplace, payout hoặc giao dịch trả phí.

## Tệp đi kèm

- `profile/column_profile.csv`: schema và null/blank/empty-list theo cột.
- `field_availability.csv`: tỷ lệ có dữ liệu của các trường sản phẩm.
- `category_profile.csv`: quy mô và tỷ lệ trường theo category chính.
- `operating_status.csv`: phân bố trạng thái hoạt động nếu có.
- `confidence_distribution.csv`: phân bố confidence theo khoảng.
- `geometry_profile.json`: kiểm tra geometry theo batch.
- `spike_manifest.json`: nguồn, hash, package và chỉ số đầy đủ.
- `DECISION_REPORT.html`: bản trực quan hỗ trợ quyết định.
- `license_inventory.csv` và `license_inventory.sql`: inventory license theo
  source/property và truy vấn DuckDB tái lập.
