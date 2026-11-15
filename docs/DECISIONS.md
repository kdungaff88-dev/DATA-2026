# Nhật ký quyết định

Ghi lại các quyết định ảnh hưởng đến việc chọn nguồn, lưu trữ, schema, giấy
phép hoặc phạm vi thương mại. Thêm mục mới; không viết lại quyết định cũ nếu
không ghi rõ thay đổi.

## 2026-11-15 — Quy tắc kho mã và dữ liệu cục bộ

- **Đã quyết định:** Git lưu mã, cấu hình, tài liệu, kiểm thử và báo cáo gọn;
  dữ liệu nguồn/phái sinh dung lượng lớn được lưu cục bộ và bỏ qua.
- **Đã quyết định:** Bản chụp nguồn bất biến và được phân biệt theo phiên bản
  nguồn chính xác.
- **Đã quyết định:** Dùng DuckDB và Parquet cho quy trình profiling và chuẩn hóa
  cục bộ ban đầu.
- **Đã quyết định:** Downloader Overture mặc định yêu cầu phiên bản `latest`,
  phân giải thành phiên bản cụ thể qua STAC rồi ghi phiên bản đó vào manifest.
- **Phạm vi hiện tại:** Downloader hỗ trợ chọn theme/type Overture; mặc định là
  `places`. Bbox chỉ là bước lọc sơ bộ, đầu ra được lọc bằng polygon Census
  TIGERweb ACS2025, lớp "States" (layer 80), cho 50 bang, DC và các lãnh thổ
  được cấu hình. Chỉ giữ geometry nằm hoàn toàn trong polygon; feature cắt
  biên giới bị loại. Tại thời điểm ghi quyết định ban đầu, chưa có snapshot
  Overture nào được tải.
- **Chưa quyết định dài hạn:** Schema chuẩn hóa cuối cùng, niche mục tiêu và
  quyền tái phân phối thương mại. Mini Spike bên dưới chỉ ghim release cho một
  lần chạy; không thay đổi mặc định `latest`.

## 2026-11-15 — Kết quả Mini Data Spike Overture Places Hoa Kỳ

- **Snapshot:** Overture release `2026-10-21.0`, `places/place`, run
  `20261115T114934.225255Z`. GeoParquet đã lọc có 18,560,038 dòng, 21 cột,
  dung lượng 3,950,607,007 byte; SHA-256
  `3bb14b5b1959b2217bc21f44f17a71b93c6b1653f003d86c53216c6658534943`.
- **Ranh giới:** Tải ZIP TIGER/Line bị HTTP 403 từ Cloudflare. Không dùng bản
  sao không chính thức; dùng endpoint chính thức Census TIGERweb ACS2025,
  layer 80, đủ 56 đơn vị cấu hình. GeoJSON boundary có SHA-256
  `4576e828397491111baaf22d472f2557eea31e966b2444f841f8041614d84ca4`.
- **Lọc địa lý:** 20,571,368 candidate rows; giữ 18,560,038; loại 2,011,330
  (9.777%) theo predicate `covered_by`. Số bị loại không đồng nghĩa toàn bộ là
  ngoài Hoa Kỳ; chính sách cũng loại geometry không được polygon bao phủ hoàn
  toàn.
- **Chất lượng quan sát:** Không có ID null/trùng; 100% geometry được đo hợp lệ
  bằng Shapely theo batch. Tỷ lệ có `taxonomy.primary` 95.717%, website
  76.175%, phone 87.132%, email 35.479%. `operating_status` có ở 73.548%;
  thiếu status không được suy diễn là địa điểm đã đóng cửa. Báo cáo có chi tiết
  mọi cột, trường con địa chỉ/nguồn, confidence và kết quả theo category.
- **Bằng chứng kinh doanh:** Đây là bằng chứng về nguồn cung, schema và độ sẵn
  có trường; chưa kiểm chứng nhu cầu người mua, mức sẵn sàng chi trả hoặc payout.
  Điều khoản và source inventory Places đã được rà soát sơ bộ, nhưng quyền cho
  sản phẩm/field cụ thể và các theme khác còn phải kiểm tra;
  `pending_theme_specific_review` và `commercial_redistribution_approved: false`
  vẫn được giữ. Không bán hoặc tái phân phối snapshot trước khi hoàn tất kiểm tra.
- **Báo cáo và artifact:** `reports/overture_places_us_spike_2026-10-21.0/`.
  Snapshot cùng manifest/checksum nằm trong `data/raw/` cục bộ, bị Git bỏ qua.

## 2026-11-15 — Rà soát license Overture Places

- Đã đối chiếu Places Guide, Attribution and Licensing, schema `SourceItem`,
  văn bản CDLA-Permissive-2.0, Apache-2.0 và CC0-1.0. Places được phát hành
  theo license của nguồn; không chứa OSM theo tài liệu Overture tháng 10/2026.
- DuckDB inventory trên snapshot Hoa Kỳ ghi nhận 18 nhóm provider/dataset/license/
  property; các license quan sát là CDLA-Permissive-2.0, Apache-2.0 và CC0-1.0.
  Feature count giữa các source item có thể chồng lấp, không cộng thành tổng
  feature duy nhất. Chi tiết và SQL tái lập ở thư mục report của spike.
- Quyền CDLA cho phép dùng/sửa đổi/chia sẻ nếu khi chia sẻ Data có toàn văn
  license; Apache cho phép phân phối khi giữ license, notices, `NOTICE` áp dụng
  và thông báo file đã sửa; CC0 cho phép sử dụng rộng rãi nhưng không xóa quyền
  riêng tư/nhãn hiệu/quy định khác. Tham khảo các văn bản trong policy.
- Theme có OSM, bao gồm `base`, `buildings`, `divisions` và `transportation`,
  cần tuân thủ ODbL. Ghép CDLA Places với OSM vẫn có thể làm database kết quả
  chịu ODbL nếu là derivative database; phải rà riêng trước khi phát hành.
- **Phạm vi quyết định:** Hoàn thành ghi nhận điều khoản để agent/pipeline làm
  theo; chưa phê duyệt sản phẩm thương mại cụ thể. Giữ
  `commercial_redistribution_approved: false` đến khi rà đủ source/property,
  cách đóng gói, ghi công, quyền riêng tư và điều khoản marketplace.
- Quy tắc vận hành nằm trong `docs/OVERTURE_LICENSE_POLICY.md`; inventory nằm
  tại `reports/overture_places_us_spike_2026-10-21.0/license_inventory.csv`.
