# Kế hoạch Mini Data Spike — Overture Places Hoa Kỳ

## Mục tiêu

Đo có thể tái lập quy mô, schema, độ đầy đủ và một số chỉ số chất lượng của
Overture Places trong phạm vi Hoa Kỳ. Kết quả dùng để quyết định có nên tiếp tục
nghiên cứu sản phẩm dữ liệu; không được diễn giải thành bằng chứng đã có người
mua hoặc bằng chứng quyền tái phân phối.

## Phạm vi đã ghim

- Nguồn: Overture Maps, theme `places`, feature type `place`.
- Release: `2026-10-21.0`, đã resolve từ STAC và truyền tường minh vào lệnh tải.
- Địa lý: 50 bang, Washington, DC và 5 đơn vị đảo được liệt kê trong cấu hình
  Census (`AS`, `GU`, `MP`, `PR`, `VI`); danh sách FIPS đầy đủ nằm trong cấu hình
  và manifest ranh giới.
- Tiền lọc: sáu bbox trong `configs/data_sources/overture_us.yaml`.
- Lọc đầu ra: chỉ giữ geometry được polygon Census bao phủ hoàn toàn. Feature
  cắt qua ranh giới bị loại, không clipping. Candidate ngoài Hoa Kỳ chỉ được đọc
  tạm để lọc, không được ghi vào GeoParquet.
- Bản ranh giới: Census TIGERweb ACS2025, layer 80, GeoJSON EPSG:4326.
- Điều khoản Places và source inventory của snapshot đã được rà soát sơ bộ;
  quyền cho sản phẩm/field cụ thể và các theme khác vẫn cần kiểm tra.
  `commercial_redistribution_approved` vẫn là `false`.

## Preflight

| Hạng mục | Kết quả |
|---|---:|
| File Places STAC giao bbox | 8 |
| Tổng `file:size` STAC ước tính | 6,110,495,166 byte |
| Dung lượng trống trước khi chạy | 631,872,086,016 byte |
| Ngưỡng dung lượng tối thiểu của downloader | 7,688,118,957 byte |
| Kết quả | Đạt; người dùng yêu cầu bắt đầu Mini Data Spike |

Tải ZIP TIGER/Line trực tiếp từ `www2.census.gov` bị HTTP 403 do Cloudflare.
Không dùng dữ liệu thay thế không chính thức; chuyển sang dịch vụ TIGERweb
ACS2025 chính thức của Census. Endpoint trả đủ 56 đơn vị đã cấu hình. GeoJSON
ranh giới lưu tại `data/raw/census/tigerweb=acs2025/us_states.geojson`, dung
lượng 38,177,175 byte, SHA-256:
`4576e828397491111baaf22d472f2557eea31e966b2444f841f8041614d84ca4`.

## Chỉ số cần báo cáo

1. Số dòng, số tệp, dung lượng và checksum của snapshot.
2. Schema và kiểu của từng cột; null, chuỗi trắng và list rỗng được tách riêng.
3. Tỷ lệ ID thiếu/trùng.
4. Độ sẵn có của tên, category, địa chỉ, website, phone, email, confidence,
   operating status và geometry — chỉ tính các trường thực sự có trong schema.
5. Phân bố category và operating status; kiểm tra geometry lỗi nếu thực hiện
   được mà không làm thay đổi snapshot.
6. Diễn giải cơ hội sản phẩm dưới dạng giả thuyết cần kiểm chứng; không kết luận
   về mức sẵn sàng chi trả từ chất lượng dữ liệu đơn thuần.

Báo cáo chỉ lưu chỉ số tổng hợp và schema, không chứa danh sách tên doanh nghiệp,
địa chỉ, số điện thoại hay website nguồn.

## Lệnh tái lập

```powershell
python tools/download_overture_us.py --release 2026-10-21.0 --themes places --download
python tools/report_overture_places_spike.py --input "data/raw/overture/release=2026-10-21.0/region=us-census-state-equivalents/run=20261115T114934.225255Z/theme=places/type=place" --output "reports/overture_places_us_spike_2026-10-21.0" --label "Overture Places US 2026-10-21.0"
```

Lệnh tạo báo cáo chỉ chạy sau khi downloader hoàn tất thành công.

## Kết quả thực thi

- Trạng thái: hoàn tất; ingest bắt đầu `2026-11-15T11:49:35Z`, hoàn tất
  `2026-11-15T12:40:31Z`.
- Candidate rows: 20,571,368; giữ lại 18,560,038; loại theo predicate biên
  2,011,330 (9.777%). Đây không phải số đếm thuần túy các feature ngoài Hoa Kỳ.
- Snapshot: 3,950,607,007 byte, SHA-256
  `3bb14b5b1959b2217bc21f44f17a71b93c6b1653f003d86c53216c6658534943`;
  DuckDB đọc 21 cột.
- ID: 18,560,038 khác biệt, không null, không có dòng trùng vượt ID đầu tiên.
- Geometry: 18,560,038/18,560,038 không null, giải mã được, hợp lệ và không
  rỗng theo kiểm tra Shapely 2.2 theo batch 100,000.
- Tỷ lệ có dữ liệu: `taxonomy.primary` 95.717%, website 76.175%, phone
  87.132%, email 35.479%; các trường con địa chỉ nằm trong khoảng 96.258%–
  99.999%. `operating_status` có ở 73.548%; null không được coi là đã đóng.
- Confidence: trung bình 0.7993, median 0.9199, min 0, max 1; phân bố theo
  khoảng nằm trong `confidence_distribution.csv`.
- Báo cáo chi tiết, phân bố theo category, schema/null/blank/list rỗng,
  provenance và giới hạn nằm trong `REPORT.md` và các artifact CSV/JSON cạnh đó.
- Kết quả là bằng chứng về nguồn cung và chất lượng trường, không chứng minh
  nhu cầu người mua, mức sẵn sàng chi trả hoặc quyền tái phân phối. License vẫn
  chờ rà soát theme-specific; không bán snapshot.

## Trạng thái task và bước tiếp theo

- **Mini Data Spike Overture Places US:** Hoàn thành ngày 2026-11-15. Kế hoạch,
  lệnh chạy, manifest, checksum, profile và báo cáo đã được lưu trong repo.
- **Báo cáo trực quan quyết định:** Đã tạo `DECISION_REPORT.html` bằng
  `tools/build_overture_decision_report.py`; chart/table lấy từ artifact tổng
  hợp, không đọc hoặc nhúng record nguồn.
- **Rà soát điều khoản chung Overture:** Đã ghi các quyền theo CDLA-Permissive-
  2.0, Apache-2.0, CC0-1.0, các nghĩa vụ ODbL và quy tắc theo source/property
  trong `docs/OVERTURE_LICENSE_POLICY.md`. Inventory và SQL tái lập được lưu
  tại `license_inventory.csv` và `license_inventory.sql`. Đây chưa phải phê
  duyệt thương mại cho sản phẩm cụ thể.
- **Bước tiếp theo được đề xuất — Gate 1: kiểm chứng quyền và nhu cầu cho một
  niche, trước khi xây sản phẩm.**
  1. Đối chiếu license/property của đúng các trường định xuất, gói license,
     attribution và `NOTICE`; xin tư vấn nếu phạm vi hoặc nghĩa vụ ODbL chưa
     chắc chắn. Không xuất bản khi còn mơ hồ.
  2. Chỉ đưa vào kiểm chứng nhu cầu, chưa chọn làm niche, các nhóm có quy mô và
     trường liên hệ đáng khảo sát trong `category_profile.csv` (ví dụ:
     `real_estate_agent`, `contractor`, `automotive_repair`). Dữ liệu profile
     chỉ cho biết độ sẵn có, không chứng minh có người mua.
  3. Xem xét sản phẩm thay thế/giá trên marketplace và làm phỏng vấn người mua
     tiềm năng để xác định một vấn đề lặp lại, định dạng cần mua và mức sẵn
     sàng trả tiền. Chỉ dùng số liệu tổng hợp hoặc mockup không chứa record
     nguồn cho đến khi quyền sử dụng được xác nhận.
  4. Hoàn tất đối chiếu AUP, phí và tình trạng payout của kênh bán. Việc cập
     nhật thông tin thanh toán hoặc hoàn tất KYC không được ghi là payout đã
     thử thành công.
- **ROAD-13 — Pain-point scan:** Đã ghi 25 mục vào DB2 ngày 2026-11-15
  (20 job listing, 4 review G2, 1 Salesforce community discussion). Từng dòng
  có người mua, pain/workaround, URL, ngày truy cập, funnel stage và mức chắc
  chắn/rủi ro. Job/review không đồng nghĩa giao dịch thành công. Bốn review G2
  cần xác nhận lại trên trang gốc; giữ mức chắc chắn thấp.
- **ROAD-15 — Gom pain point / loại rủi ro đỏ:** Đã thêm 8 giả thuyết mới vào
  DB2 ở `2. Long-list Niche`, tất cả vàng vì chưa hoàn tất rà rights/ToS. Một
  mô hình personal owner-contact/skip-tracing/cold outreach được đánh dấu
  `Đã loại (Killed)`; pain evidence thô vẫn được giữ. Dòng xanh mẫu trong DB2
  không tính là nghiên cứu thật. Chưa tìm được điều khoản chính thức chứng minh
  một nguồn cụ thể cấm resale; workflow Maps/directory/portal vẫn bị chặn cho
  tới khi terms được xác minh.
- **Gate 1 — Đang xử lý:** chủ dự án tạm xác nhận Gumroad/Apify đã chấp nhận
  tài khoản và đã xử lý tài khoản nhận payout bằng VND. DB1 ghi nhận account
  acceptance và payout setup theo xác nhận này, không khẳng định đã có tiền
  thực nhận. Còn rà AUP và quyền nguồn theo từng sản phẩm.
- **ROAD-12 / Gate 2 — Đang xử lý:** đã chọn Top 3 để thiết kế cho hai sàn:
  (1) theo dõi license nhà thầu HVAC/điện; (2) CRM company-record hygiene;
  (3) báo cáo độ phủ website doanh nghiệp dịch vụ địa phương. Cả ba còn vàng
  hoặc confidence thấp; chưa có rights/ToS clearance, buyer interview hay paid
  transaction. Bốn G2 review gốc vẫn chưa xác minh. Chi tiết tại
  `PRODUCT_DESIGN_TOP3.md`; chưa phát hành record thật.
- **Điều kiện trước khi build/listing:** quyền và nghĩa vụ license được xác
  nhận cho mô hình dự kiến; có bằng chứng nhu cầu cụ thể từ người mua; marketplace
  cho phép loại sản phẩm và có đường payout khả thi. Nếu thiếu một điều kiện,
  tiếp tục xác minh hoặc pivot; không tạo Actor/dataset để bán và không chi
  ngân sách trước khi qua gate.
