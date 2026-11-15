# Brief nghiên cứu nhu cầu — ROAD-13

Ngày rà soát: 2026-11-15. ROAD-13 đã đạt DoD về số lượng nguồn: **25 mục đã
được ghi vào DB2**, mỗi mục có buyer/pain/workaround, URL và ngày truy cập.
DB2 là nguồn sự thật cho từng mục; các ví dụ bên dưới là sáu tín hiệu ban đầu,
không phải toàn bộ danh sách.

## Ứng viên để tìm pain point

| Category | Dòng trong snapshot | Website | Phone | Email | Cách dùng |
|---|---:|---:|---:|---:|---|
| `real_estate_agent` | 412,399 | 87.384% | 97.878% | 61.897% | Ứng viên nghiên cứu |
| `contractor` | 202,118 | 76.394% | 85.880% | 42.338% | Ứng viên nghiên cứu |
| `automotive_repair` | 219,708 | 65.414% | 94.902% | 48.997% | Ứng viên nghiên cứu |
| `insurance_agency` | 235,802 | 79.143% | 74.635% | 39.213% | Ứng viên nghiên cứu |

Các tỷ lệ là coverage trong Overture, không phải đo độ chính xác, khả năng liên
hệ, nhu cầu hoặc khả năng bán. Các nhóm chỉ giúp chọn nơi tìm hiểu, không phải
thứ hạng sản phẩm.

## Tín hiệu ban đầu có URL

| # | Buyer / người có vấn đề | Nhiệm vụ hoặc khó khăn được nêu | Loại tín hiệu | Nguồn |
|---:|---|---|---|---|
| 1 | Người thuê nghiên cứu bất động sản | Muốn lập danh sách chủ sở hữu theo khu vực, gom nhiều tài sản cùng chủ và tránh trùng trước outreach. | Job thuê freelancer; chưa có bằng chứng dự án đã thanh toán | [Upwork — Bulk Property Owner Contacts](https://www.upwork.com/freelance-jobs/apply/Real-Estate-Data-Research-Lead-Generation-Specialist-Bulk-Property-Owner-Contacts_~022113417220768498950/) |
| 2 | Bên cho vay bất động sản | Cần duy trì hàng tuần danh sách owner/agent, xác minh liên hệ và cập nhật pipeline; người thuê yêu cầu báo giá và kinh nghiệm. | Job thuê freelancer, yêu cầu định kỳ | [Upwork — Real Estate Lead Researcher](https://www.upwork.com/freelance-jobs/apply/Real-Estate-Lead-Researcher-Real-Estate-Lead-Researcher-Cold-Email-Outreach-Zillow_~022111192117122909359/) |
| 3 | Công ty bất động sản | Cần chính xác owner/buyer lists, CRM sạch, loại trùng, ghi nguồn, sửa số sai/ngắt kết nối và lưu kết quả gọi. | Job có workflow về chất lượng và correction loop | [Upwork — Real Estate Data & CRM Manager](https://www.upwork.com/freelance-jobs/apply/Real-Estate-Data-CRM-Manager-Property-Research-List-Quality-REI-Reply_~022109367758067887960/) |
| 4 | Agency marketing địa phương | Đặt yêu cầu 100 lead dịch vụ địa phương mỗi tuần, cần phone call test, loại trùng, kiểm tra business còn mở và thay lead lỗi; nêu paid trial và giá cố định. | Tín hiệu mua dịch vụ có tiêu chí nghiệm thu rõ; không phải bán dataset Overture | [Upwork — Verified Local Service Business Leads](https://www.upwork.com/freelance-jobs/apply/Lead-Researcher-Weekly-Verified-Local-Service-Business-Leads_~022108279155467687872/) |
| 5 | Người làm outreach cho local business | Muốn danh sách 100 cơ sở có owner, phone, website, email và address; cần ghi rõ khi không tìm thấy, không duplicate/closed/made-up email. | Job yêu cầu contact dataset và chất lượng | [Upwork — Local Business Contacts](https://www.upwork.com/freelance-jobs/apply/Need-100-Local-Business-Contacts-from-Google-Maps-Owner-Names-Required_~022115132451164466321/) |
| 6 | Nhóm sales dùng prospecting databases | So sánh Apollo/ZoomInfo; trang G2 cho thấy người dùng đánh giá khác nhau về contact-data accuracy, cho thấy chất lượng dữ liệu là tiêu chí mua/so sánh, không chứng minh nhu cầu của niche địa phương. | Review tổng hợp; tín hiệu cạnh tranh gián tiếp | [G2 — Apollo vs. ZoomInfo](https://www.g2.com/compare/apollo-io-vs-zoominfo-sales) |

## Đánh giá độ mạnh và giới hạn

- 25 mục DB2 gồm **20 job listing Upwork**, **4 review G2** và **1 thảo luận
  Salesforce Trailblazer**. Job listing phản ánh yêu cầu dịch vụ/research,
  không tự chứng minh hợp đồng đã được thuê hoặc thanh toán.
- Bốn review G2 được phát hiện qua nguồn tổng hợp và được gắn độ chắc chắn thấp;
  cần xác nhận nội dung/ngữ cảnh trên trang review gốc trước khi tính điểm hoặc
  dùng làm bằng chứng niche.
- Các tín hiệu cho thấy nhu cầu về verified lists, freshness, dedupe,
  correction/CRM hygiene và quy mô địa lý. Chúng **chưa chứng minh** buyer muốn
  mua file dataset độc lập hoặc mua dữ liệu Overture.
- Không ghi bất kỳ job/review nào là doanh thu, completed contract hay payout;
  trạng thái thực hiện/thanh toán chưa được xác minh.
- Một số job yêu cầu owner names, personal/direct phone/email, skip tracing,
  cold outreach, social profiles hoặc call testing. Đây là cờ đỏ/vàng, không
  phải gợi ý đưa các trường đó vào sản phẩm. Cần rà privacy, luật marketing,
  marketplace AUP, source terms và license riêng.
- 25 mục là long-list evidence để sàng lọc, chưa đủ đa dạng/độc lập để chọn
  niche. Một số listing có chủ đề gần nhau và có thể hết hạn; không đếm cùng
  một nhu cầu nhiều lần nếu tiếp tục tìm từ các trang tổng hợp.
- Cần phỏng vấn buyer hoặc chạy thử offer/mockup không chứa record nguồn để xác
  nhận vấn đề, người ra quyết định, định dạng và willingness-to-pay.

## Long-list ROAD-15: 8 giả thuyết để tiếp tục research

Tám dòng mới được thêm vào DB2 ở giai đoạn `2. Long-list Niche`. Tất cả đang
màu vàng vì chưa hoàn thành rà soát rights/ToS theo đúng nguồn và cách phân
phối; chưa có niche nào được chọn. Dòng `[MẪU VÙNG XANH]` cũ trong DB2 là ví dụ,
không tính vào tám ứng viên này.

| # | Giả thuyết niche | Ranh giới an toàn ban đầu | Rủi ro / điều chưa biết |
|---:|---|---|---|
| 1 | HVAC/điện có license còn hiệu lực | Entity, loại/license/status/hết hạn, địa lý và URL nguồn; không owner contact | Public registry terms, attribution, quyền tái phân phối theo bang |
| 2 | Coverage directory home-service theo vùng/trade | Company-level profile; không tên/điện thoại/email cá nhân | Terms của từng directory và Overture source/property chưa được clearance |
| 3 | Coverage cơ sở theo hiện diện website | Chỉ số tổng hợp no/weak website hoặc audit do buyer chủ động yêu cầu | Paid job là nhu cầu dịch vụ; chưa chứng minh mua dataset; phương pháp đo và ToS cần rà |
| 4 | Directory coverage cho independent auto-repair | Hồ sơ cơ sở, category, địa lý; không owner contact | Chain classification, source rights và buyer format chưa biết |
| 5 | Coverage vùng fleet/service cho automotive | Chỉ business-level/aggregate geography, không tên người quyết định hay outreach | Có ít tín hiệu trực tiếp; fleet attributes cần nguồn và kiểm chứng riêng |
| 6 | Sàng lọc property multifamily cho EV charging | Dữ kiện property-level/aggregate; không owner/tenant personal data | Chỉ một job signal; utility/parking/property sources chưa rà terms |
| 7 | Freshness/dedup cho company records trong CRM | Read-only, company-level checks; không personal-contact enrichment | Tín hiệu G2 còn gián tiếp; verify review gốc, licensed reference data và willingness-to-pay |
| 8 | CRE property-level opportunity/availability | Property facts, ngày và URL nguồn; không owner contact hoặc listing-page resale | Nguồn listing/portal dễ có hạn chế; chưa xác nhận quyền sử dụng |

### Loại khỏi long-list hiện tại

- **Đỏ — lead list theo cá nhân:** owner/principal names gắn với personal
  email/mobile, skip tracing hoặc property-to-person mapping. Đã thêm một dòng
  `Đã loại (Killed)` trong DB2; giữ các raw pain records làm bằng chứng, không
  biến chúng thành đặc tả sản phẩm.
- **Đỏ/blocked — cold outreach bằng personal contacts:** không đưa vào sản phẩm
  hoặc pipeline khi chưa rà privacy, data-broker rules, luật marketing và AUP.
- **ToS:** chưa xác minh được trang điều khoản chính thức nào trong nhóm nguồn
  này kết luận rõ “cấm resale”. Vì vậy không gán nhãn cấm khi chưa có bằng
  chứng; mọi workflow dựa vào Google Maps, directory hoặc listing portal vẫn
  bị chặn ở mức vàng cho tới khi terms/permission cụ thể được đọc và lưu nguồn.
- Không ứng viên nào được gắn xanh/clearance. License Overture vẫn theo từng
  `sources[*].property`; `commercial_redistribution_approved` tiếp tục `false`.

## Kiểm tra Gate 1/Gate 2 — 2026-11-15

- **Apify và Gumroad:** theo xác nhận tạm thời của chủ dự án ngày 2026-11-15,
  hai tài khoản đã được chấp nhận và tài khoản nhận payout VND đã được xử lý.
  Ghi nhận này áp dụng ở cấp tài khoản/phương thức nhận; không khẳng định đã có
  khoản tiền thực nhận. Listing hoặc sản phẩm cụ thể vẫn cần được nền tảng chấp
  thuận theo điều khoản của sàn.
- **Apify:** điều khoản công khai yêu cầu KYC và billing/payment details; nêu
  20% commission cộng platform usage costs, invoice ngày 11 và payout thường
  ngày 21–25, ngưỡng USD 20 cho PayPal/Wise hoặc USD 100 cho phương thức khác,
  phí wire trung gian có thể USD 10–50. AUP cấm unsolicited mass messaging và
  hoạt động vi phạm luật/quyền bên thứ ba.
- **Gumroad:** Help page mô tả bank payouts theo danh sách quốc gia và PayPal
  fallback nếu bank không hỗ trợ. Chính sách cấm chia sẻ private information
  không có phép và nói không resell sản phẩm không do người bán tạo; không đủ
  căn cứ để kết luận mọi business dataset đều bị cấm hoặc được phép.
  Chính sách cấm chia sẻ private information không có phép và nói không resell
  sản phẩm không do người bán tạo; không đủ căn cứ để kết luận mọi business
  dataset đều bị cấm hoặc được phép.
- **CSLB California:** Public Data Portal cho tải miễn phí CSV/XLS với business
  name, license/status/class, address, phone và ngày hiệu lực; cảnh báo status
  có thể thay đổi sau thời điểm tải. Trang đã kiểm tra không nêu license tái
  phân phối thương mại. Xem đây là nguồn nghiên cứu tiềm năng, không phải quyền
  bán lại đã được cấp; không đưa personnel/owner contacts vào phạm vi.
- **Overture Places:** license khác theo source/property. Không xuất raw records
  hoặc gói thương mại cho tới khi rà đúng fields, notices/attribution và hình
  thức output; `commercial_redistribution_approved` vẫn `false`.
- **G2:** tìm theo bốn mã review chỉ trả về trang tổng hợp LeadGenius, không
  xác minh độc lập được nội dung trên các trang review gốc. Giữ các mục đó ở
  độ chắc chắn thấp; không dùng chúng làm căn cứ chọn niche.

**Quyết định:** đã chọn ba giả thuyết để thiết kế cho cả Gumroad và Apify:
(1) theo dõi license HVAC/điện, (2) CRM company-record hygiene, (3) báo cáo
độ phủ website local services. Gate 2 trở lại `Đang xử lý`; chưa hoàn thành vì
rights/ToS cho nguồn và output cụ thể chưa được clearance, review G2 gốc chưa
xác minh và chưa có buyer interview/paid transaction. Đặc tả nằm tại
`PRODUCT_DESIGN_TOP3.md`. Đây là screening vận hành, không phải tư vấn pháp lý.

## Việc tiếp theo

1. Prototype `Company CRM Hygiene Kit` local với dữ liệu tổng hợp; không dùng
   file khách hàng thật ở giai đoạn đầu.
2. Kiểm tra rights/ToS riêng cho CSLB, Overture source/property và website
   checks; không đưa record thật vào Gumroad sample/Apify output trước clearance.
3. Dùng mockup không chứa record nguồn để phỏng vấn buyer; job listing/review
   vẫn không được tính là giao dịch.
4. Mở trực tiếp bốn review G2; nếu không truy cập được, thay bằng review nguồn
   gốc khác. Chỉ chuyển sang sample/MVP sau buyer feedback và rights review.
