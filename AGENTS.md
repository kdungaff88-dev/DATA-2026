# Hướng dẫn cho Agent

Các quy tắc này áp dụng cho mọi agent và trợ lý lập trình tự động làm việc
trong kho mã. Đọc tệp này cùng tài liệu liên quan trước khi thay đổi mã, schema,
cấu hình nguồn dữ liệu hoặc dữ liệu.

## Bối cảnh dự án

DATA-2026 là dự án kỹ thuật dữ liệu dài hạn, có thể tái lập. Python 3.11+ và
DuckDB/Parquet là bộ công cụ ban đầu. Nguồn đầu tiên đang được đánh giá là
Overture Maps Places tại Hoa Kỳ. Không được mặc định phiên bản dữ liệu, niche
cuối cùng hoặc quyền tái phân phối thương mại nếu chưa ghi nhận quyết định rõ
ràng.

Đọc các tài liệu liên quan:

- `docs/DATA_WORKFLOW.md`: các lớp dữ liệu, provenance và chuẩn hóa.
- `docs/OVERTURE_LICENSE_POLICY.md`: quyền theo license Overture, nghĩa vụ chia
  sẻ và các điểm dừng trước khi phân phối.
- `docs/DEVELOPMENT.md`: quy ước phát triển cục bộ.
- `docs/TESTING.md`: cấp độ kiểm thử và lệnh chạy.
- `docs/DECISIONS.md`: quyết định đã chốt và vấn đề còn mở.
- `configs/data_sources/`: cấu hình trước khi làm việc với từng nguồn.

## Quy tắc dữ liệu bắt buộc

- Giữ bản chụp dữ liệu nguồn bất biến. Không ghi đè phiên bản tại chỗ; lưu
  phiên bản mới hoặc đợt thu thập mới ở đường dẫn riêng.
- Không đưa dữ liệu khối lượng lớn, cơ sở dữ liệu DuckDB cục bộ, thông tin xác
  thực hoặc dữ liệu khách hàng vào Git. Tuân thủ `.gitignore`; không ép thêm tệp
  đang bị bỏ qua.
- Khi chuẩn hóa, giữ các trường và định danh nguồn. Bổ sung trường chuẩn hóa có
  tài liệu thay vì âm thầm ghi đè hoặc xóa dữ liệu gốc.
- Trước khi biến đổi hoặc phân phối, ghi lại nguồn, phiên bản chính xác, thời
  điểm thu thập, phạm vi địa lý, giấy phép/điều khoản, ghi công, schema và định
  danh tệp.
- Dữ liệu truy cập công khai không đồng nghĩa với quyền tái phân phối thương
  mại không giới hạn. Nếu chưa rõ giấy phép, điều khoản, PII hoặc provenance,
  phải ghi là chưa xác minh; không tự suy diễn quyền sử dụng.
- Với Overture, đọc `docs/OVERTURE_LICENSE_POLICY.md` và kiểm tra source item
  theo đúng release, gồm `sources[*].license` và `sources[*].property`. Không
  coi một theme hoặc cả một feature là cùng license khi nguồn/phạm vi property
  khác nhau. Chỉ phân phối kèm license, attribution và `NOTICE` áp dụng; mọi
  join với OSM/ODbL phải qua rà soát riêng. Giữ
  `commercial_redistribution_approved: false` cho đến khi sản phẩm và từng
  nguồn/property được duyệt cụ thể.
- Không kết luận cơ sở kinh doanh đã đóng cửa chỉ vì thiếu trạng thái hoặc
  trạng thái chưa rõ.
- Không thu thập sau đăng nhập, vượt cơ chế kiểm soát truy cập hoặc vi phạm
  điều khoản của nguồn.
- Agent không được tải dữ liệu, gọi dịch vụ bên ngoài hoặc cài package qua mạng
  nếu người dùng chưa cho phép rõ ràng.
- CI trong `.github/workflows/` được phép cài các dependency đã khai báo; CI
  không được thu thập dữ liệu nguồn hoặc gọi dịch vụ dữ liệu.

## Quy trình kỹ thuật

1. Trước khi sửa, kiểm tra cách triển khai hiện tại, trạng thái Git, manifest
   nguồn và tài liệu liên quan.
2. Nêu tác động dự kiến khi thay đổi schema dùng chung, data contract, định dạng
   cấu hình hoặc workflow.
3. Thực hiện thay đổi nhỏ, có thể tái lập. Một lần thử chỉ hữu ích khi có thể
   khôi phục đầu vào, phiên bản mã/cấu hình, chỉ số và kết quả.
4. Thêm hoặc cập nhật kiểm thử cho hành vi thay đổi. Ưu tiên fixture nhỏ cục bộ
   cho kiểm thử thường ngày; kiểm thử dữ liệu lớn phải là tùy chọn và có tài
   liệu.
5. Chạy các kiểm tra liên quan trong `docs/TESTING.md`. Báo trung thực kiểm tra
   nào bị bỏ qua hoặc thiếu dependency.
6. Cập nhật tài liệu và nhật ký quyết định khi hành vi hoặc giả định đã chốt
   thay đổi.

## Quy ước Python và dữ liệu

- Hỗ trợ Python 3.11 trở lên.
- Tách phần trích xuất theo nguồn khỏi công cụ profiling và chuẩn hóa dùng
  chung.
- Với cùng bản chụp đầu vào và cấu hình, phép biến đổi phải cho kết quả xác
  định.
- Khai báo rõ phiên bản schema và ánh xạ category; không âm thầm ép kiểu khi
  nguồn thay đổi không tương thích.
- Tạo báo cáo gọn có định nghĩa chỉ số, số lượng và metadata nguồn/lần chạy.
- Không dùng bản ghi nguồn thật trong fixture unit test; hãy tạo fixture tổng
  hợp.

## Git và hành động bên ngoài

- Không commit, push, tạo release hoặc thay đổi cấu hình remote trừ khi người
  dùng yêu cầu rõ ràng.
- Không xóa bỏ hoặc ghi đè thay đổi của người dùng.
- Không đưa secret hoặc dữ liệu thô vào issue, pull request, artifact CI hay
  log.

## Quy tắc ngôn ngữ

- README, tài liệu trong `docs/`, ghi chú quyết định, nội dung issue/PR, comment,
  docstring và thông báo trợ giúp do dự án viết phải dùng tiếng Việt.
- Giữ nguyên tên file, tên biến/hàm, khóa cấu hình/schema, lệnh, thuật ngữ chuẩn
  và trích dẫn từ nguồn bên ngoài khi cần để đảm bảo tính tương thích.
- Khi bổ sung nội dung tiếng Anh vì lý do kỹ thuật hoặc tương thích, giải thích
  lý do trong nội dung liên quan.
