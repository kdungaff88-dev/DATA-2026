# Quy tắc giấy phép Overture

Ngày rà soát: 2026-11-15. Đây là hướng dẫn tuân thủ kỹ thuật dựa trên tài liệu
công khai, không phải ý kiến pháp lý. Giấy phép và điều khoản phải được rà soát
lại cho từng release, theme, nguồn thành phần và cách phân phối.

## Kết luận cho Places

Tài liệu chính thức của Overture cho release tháng 10/2026 mô tả theme
`places` là đa giấy phép theo nguồn: phần lớn nguồn dùng CDLA-Permissive-2.0,
Foursquare dùng Apache-2.0 và AllThePlaces dùng CC0-1.0. Hướng dẫn Places nói
theme này không chứa dữ liệu OpenStreetMap (OSM). Đây không phải một giấy phép
duy nhất áp dụng đồng nhất cho mọi trường của mỗi feature.

Đã kiểm tra `sources` trong snapshot Hoa Kỳ `2026-10-21.0`. Các mã license quan
sát được là `CDLA-Permissive-2.0`, `Apache-2.0` và `CC0-1.0`; không thấy mã
ODbL trong inventory của snapshot này. Inventory nhóm theo provider, dataset,
license và `property` nằm ở
`reports/overture_places_us_spike_2026-10-21.0/license_inventory.csv`; câu SQL
tái lập nằm cạnh đó. Số feature của các nhóm có thể chồng lấp và không được
cộng để suy ra tổng số feature duy nhất.

`sources[*].property` là phạm vi áp dụng của source item. Giá trị rỗng chỉ
nguồn cho toàn feature, ngoại trừ các property có source item riêng; giá trị
như `/properties/operating_status` hoặc `/properties/confidence` giới hạn
source item vào property đó. Khi lọc, chuẩn hóa hoặc xuất dữ liệu, không suy
license của cả feature chỉ từ một source item; phải giữ và kiểm tra provenance
ở cấp property.

## Quyền được cấp và điều kiện chính

| License | Điều được cho phép theo văn bản license | Điều kiện cần giữ khi chia sẻ |
|---|---|---|
| CDLA-Permissive-2.0 | Sử dụng, sửa đổi và chia sẻ Data; license không đặt hạn chế lên `Results` theo định nghĩa trong license. | Khi chia sẻ Data, kèm toàn văn license, trong đó có tuyên bố miễn trừ bảo đảm và giới hạn trách nhiệm. Không tự phân loại một gói còn chứa record nguồn là `Results`. |
| Apache-2.0 | Sao chép, sửa đổi và phân phối Work/Derivative Works, kể cả thương mại, theo điều kiện license. | Kèm bản license; đánh dấu file đã sửa; giữ copyright/patent/trademark/attribution notices áp dụng; chuyển tiếp nội dung `NOTICE` áp dụng. License không cấp quyền dùng nhãn hiệu để ngụ ý chứng thực. |
| CC0-1.0 | Sao chép, sửa đổi và phân phối, kể cả thương mại, trong phạm vi quyền tác giả và quyền liên quan được từ bỏ. | CC0 không xóa quyền riêng tư, công khai hình ảnh, nhãn hiệu hoặc nghĩa vụ theo luật khác; không ngụ ý nguồn hoặc tác giả chứng thực sản phẩm. |
| ODbL-1.0 | Có thể dùng và khai thác thương mại theo license. | Nếu phân phối Derivative Database, phải đánh giá nghĩa vụ share-alike, ghi công và cung cấp quyền truy cập phù hợp cho database theo ODbL. Không ghép hoặc phát hành trước khi rà soát database và tư vấn khi chưa rõ. |

CDLA-Permissive-2.0 và Apache-2.0 đều kèm giới hạn bảo đảm; không quảng cáo
dữ liệu là chính xác, đầy đủ hoặc cập nhật theo thời gian thực nếu chưa có phép
đo riêng. Ghi công Overture và nguồn thành phần vẫn phải tuân theo yêu cầu
riêng của license/theme; việc có thể không phải điều kiện của CDLA-Permissive-2.0
không phải lý do bỏ qua attribution hoặc provenance.

## Phân biệt điều khoản theo theme

- Không lấy kết luận của `places` áp cho theme khác. Tài liệu Overture hiện mô
  tả `base`, `buildings`, `divisions` và `transportation` là các theme có nguồn
  OSM và được phát hành theo ODbL; kiểm tra lại guide và attribution của đúng
  theme/type/release trước mỗi lần dùng.
- Guide `addresses` mô tả các nguồn là open license dạng permissive nhưng có
  nguồn kèm điều kiện hoặc yêu cầu attribution; vẫn phải rà đúng source item.
- Guide Places cho phép ghép dữ liệu CDLA với OSM, nhưng database kết quả có
  thể phải tuân theo ODbL nếu là derivative database. Mọi join với OSM hoặc
  nguồn ODbL phải dừng ở bước phát hành cho đến khi có phân tích riêng.
- `addresses` và mọi theme khác phải được rà theo guide/attribution và
  `sources[*]` riêng; không suy ra từ `places`.
- Trang Terms of Use của website Overture không thay thế license dữ liệu. Quyền
  dùng dữ liệu phải căn cứ license theme/nguồn và yêu cầu ghi công tương ứng.

## Quy tắc bắt buộc cho agent và pipeline

1. Ghim release và lưu URL, ngày truy cập, manifest, checksum, config và bản
   license/NOTICE cần phân phối.
2. Trước khi xuất file hoặc API, kiểm kê `sources[*].provider`,
   `dataset`, `license`, `property` cho đúng snapshot và đúng các trường được
   đưa vào sản phẩm.
3. Chia output theo license khi cần; giữ source item/property lineage. Không
   gộp các giấy phép thành một tuyên bố “toàn bộ dataset dùng license X”.
4. Với CDLA-Permissive-2.0, kèm toàn văn license nếu chia sẻ Data. Với
   Apache-2.0, kèm license và `NOTICE` áp dụng, giữ các thông báo bắt buộc và
   đánh dấu thay đổi. Với CC0, vẫn giữ provenance và rà quyền ngoài copyright.
5. Không gắn nhãn “được phép tái phân phối thương mại” chỉ vì dữ liệu tải công
   khai hoặc trường `sources[*].license` đã có giá trị.
6. Không ghép OSM/ODbL vào dataset curated hoặc phát hành database dẫn xuất
   trước khi hoàn tất phân tích nghĩa vụ ODbL.
7. Rà PII, quyền riêng tư, quy định data broker, điều khoản marketplace và
   quyền của bên thứ ba độc lập với license bản đồ. Open license không tự cấp
   quyền xử lý mọi dữ liệu cá nhân hay quyền sử dụng nhãn hiệu.
8. Giữ `commercial_redistribution_approved: false` cho tới khi quyền của từng
   nguồn/property, hình thức đầu ra, ghi công, license bundle và marketplace
   được rà cho chính sản phẩm dự kiến. Khi điều khoản mơ hồ, dừng phân phối và
   xin tư vấn pháp lý.

## Nguồn chính thức

- [Overture Places Guide — nguồn và license theo theme](https://docs.overturemaps.org/guides/places/)
- [Overture Addresses Guide](https://docs.overturemaps.org/guides/addresses/)
- [Overture Base Guide](https://docs.overturemaps.org/guides/base/)
- [Overture Buildings Guide](https://docs.overturemaps.org/guides/buildings/)
- [Overture Divisions Guide](https://docs.overturemaps.org/guides/divisions/)
- [Overture Transportation Guide](https://docs.overturemaps.org/guides/transportation/)
- [Overture Attribution and Licensing](https://docs.overturemaps.org/attribution/)
- [Overture SourceItem schema — phạm vi `property` và `license`](https://docs.overturemaps.org/schema/reference/common/source_item/)
- [Overture theme definitions](https://docs.overturemaps.org/theme-definitions-table.html)
- [Overture Terms of Use](https://overturemaps.org/terms-of-use/)
- [CDLA-Permissive-2.0 — văn bản license](https://cdla.dev/permissive-2.0/)
- [Apache License 2.0 — văn bản license](https://www.apache.org/licenses/LICENSE-2.0)
- [CC0-1.0 — deed và giới hạn quyền ngoài copyright](https://creativecommons.org/publicdomain/zero/1.0/deed.en)
- [ODbL-1.0 — văn bản license](https://opendatacommons.org/licenses/odbl/1-0/)
