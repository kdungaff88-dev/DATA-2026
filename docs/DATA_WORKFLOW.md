# Quy trình dữ liệu và provenance

## Các lớp dữ liệu

1. **Raw:** tệp nguồn nguyên bản hoặc phần trích xuất trực tiếp từ nguồn, không
   chỉnh sửa sau khi thu thập và bất biến. Nếu là phần trích xuất theo vùng,
   lưu kèm phiên bản, bbox và cấu hình truy vấn.
2. **Staging:** nơi phân tích cú pháp, kiểm tra kiểu và làm sạch riêng cho nguồn.
   Không coi đầu ra của lớp này là sản phẩm chuẩn.
3. **Normalized:** schema nội bộ ổn định, có ánh xạ tường minh và giữ lại giá
   trị nguồn. Mỗi đầu ra ghi phiên bản schema và phiên bản mã biến đổi.
4. **Curated:** bộ dữ liệu hoặc sản phẩm đã tuyển chọn theo niche. Chỉ tạo sau
   khi đã xác định trường cần thiết, người mua, quyền sử dụng và cách cập nhật.

## Manifest nguồn

Trước khi thu thập, ghi lại:

- chủ sở hữu nguồn, dataset/theme, URL chính thức và phiên bản chính xác;
- ngày giờ thu thập (UTC), phạm vi địa lý và phương thức thu thập;
- giấy phép/điều khoản và yêu cầu ghi công của từng nguồn;
- đường dẫn tệp, dung lượng byte và checksum nếu có;
- schema đã quan sát, phiên bản biến đổi và giới hạn đã biết.

Không đánh dấu nguồn có thể dùng thương mại chỉ vì nguồn đó truy cập công khai.
Rà soát giấy phép và điều khoản của từng thành phần.

## Thu thập Overture theo phạm vi Hoa Kỳ

Theme được chọn trong `configs/data_sources/overture_us.yaml`; mặc định là
`places`. Có thể chọn thêm `addresses`, `base`, `buildings`, `divisions` hoặc
`transportation` bằng cấu hình hay tham số `--themes`.

1. `latest` được phân giải qua STAC thành phiên bản cụ thể; mọi theme/type trong
   một lần chạy dùng cùng phiên bản.
2. Index STAC của release được dùng để ước tính bảo thủ tổng kích thước các file
   ứng viên giao với bbox. Công cụ cũng kiểm tra dung lượng trống và từ chối tải
   nếu không đạt ngưỡng dự phòng; đây là metadata planning, chưa tải GeoParquet.
3. Bbox trong cấu hình chỉ để STAC giảm lượng dữ liệu cần đọc. Dữ liệu được lọc
   theo polygon hợp nhất từ lớp Census TIGERweb ACS2025 "States" (layer 80),
   GeoJSON trả về ở EPSG:4326. Candidate ngoài biên chỉ được đọc tạm và không
   được ghi vào output.
4. Chính sách biên giới là chỉ giữ feature có toàn bộ geometry được polygon Hoa
   Kỳ bao phủ. Feature cắt qua biên giới bị loại để không lưu geometry ngoài
   Hoa Kỳ. Mặc định bao gồm 50 bang, DC và các lãnh thổ được cấu hình; thay đổi
   danh sách đơn vị phải được ghi vào cấu hình và manifest.
5. Mỗi theme/type được lưu riêng trong `data/raw/`, giữ schema nguồn và có
   manifest ghi phiên bản Overture, checksum cấu hình, nguồn ranh giới, số
   candidate, số feature thuộc Hoa Kỳ, dung lượng và SHA-256.
6. Kiểm kê schema, null, chuỗi rỗng, danh sách rỗng, ID trùng, hình học và các
   trường chuyên biệt theo theme. Không suy diễn trạng thái thiếu là một kết
   luận nghiệp vụ.
7. Sau khi manifest downloader có trạng thái `completed`, tạo báo cáo tổng hợp
   bằng `tools/report_overture_places_spike.py`. Công cụ dùng DuckDB để đo mọi
   cột và các chỉ số theo category; geometry validity được kiểm tra theo batch
   bằng Shapely/PyArrow. Báo cáo phải ghi rõ mẫu số, hash, giới hạn và trạng thái
   license, đồng thời không chứa dòng dữ liệu nguồn.

Không dùng wildcard trên mọi phiên bản. Mỗi lần chạy phân giải `latest` một lần
rồi ghim phiên bản đó cho toàn bộ truy vấn. Ước tính dung lượng tải và dung
lượng đĩa còn trống trước khi lưu bản chụp lớn cục bộ.

Kết quả Mini Data Spike Places Hoa Kỳ ngày 2026-11-15 được lưu tại
`reports/overture_places_us_spike_2026-10-21.0/`. Đây là số đo của một snapshot,
không phải cam kết coverage cho release khác.

## Quy ước chuẩn hóa

- Giữ nguyên các cột và định danh từ nguồn.
- Bổ sung cột chuẩn hóa có tài liệu về kiểu, ánh xạ và ngữ nghĩa giá trị null.
- Không suy ra cơ sở kinh doanh đã đóng cửa từ trạng thái bị thiếu.
- Ánh xạ category phải tường minh và có phiên bản.
- Mỗi phép biến đổi phải cho kết quả xác định khi bản chụp nguồn và cấu hình
  không đổi.
- Ghi lại các dòng bị loại hoặc còn mơ hồ cùng số lượng; không âm thầm loại bỏ.

## Giấy phép và ghi công

Điều khoản và nguồn thành phần khác nhau theo theme Overture. Trước khi phân
phối, rà soát giấy phép và hướng dẫn ghi công của theme/type trong phiên bản
đang dùng; việc tải được dữ liệu không đồng nghĩa được tái phân phối thương mại.
Kiểm tra riêng `sources[*].license` và phạm vi `sources[*].property`; các source
item trong cùng feature có thể mang license hoặc phạm vi khác nhau. Tuân thủ
điều kiện đóng gói license, attribution và `NOTICE` áp dụng. Mọi join với
OSM/ODbL cần rà soát riêng trước khi chia sẻ database dẫn xuất.

Quy tắc Overture và danh sách nguồn chính thức nằm trong
`docs/OVERTURE_LICENSE_POLICY.md`. Ranh giới Census dùng làm mặt nạ địa lý cũng
được lưu phiên bản, URL và checksum.
