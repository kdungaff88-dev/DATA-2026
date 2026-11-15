# Đặc tả Top 3 sản phẩm — Gumroad và Apify

Ngày cập nhật: 2026-11-15
Trạng thái: Đặc tả thử nghiệm; chưa phê duyệt phát hành hay bán dữ liệu nguồn.

## 1. Quyết định và phạm vi

Chủ dự án tạm xác nhận ngày 2026-11-15 rằng tài khoản Gumroad và Apify đã
được chấp nhận, tài khoản nhận payout bằng VND đã được xử lý. DB1 ghi nhận đây
là xác nhận account-level; không diễn giải thành đã nhận một khoản payout thật.
Acceptance của tài khoản không phải approval cho listing hoặc product cụ thể.

Ba giả thuyết được đưa vào `4. Top 3 Deep Dive` trong DB2:

1. **Theo dõi license nhà thầu HVAC/điện:** sản phẩm narrow, buyer pain cụ thể,
   có job listing yêu cầu paid trial nhưng chưa có bằng chứng job được thuê hay
   thanh toán. CSLB cung cấp public data downloads; trang đã rà chưa nêu rõ
   quyền tái phân phối thương mại.
2. **Kiểm tra chất lượng company records cho CRM:** xử lý dữ liệu doanh nghiệp
   do khách hàng cung cấp, phát hiện bản ghi trùng, thiếu và cũ. Có tín hiệu từ
   job data-quality và Salesforce community; bốn review G2 chưa xác minh trang
   gốc và không được coi là bằng chứng đã mua.
3. **Báo cáo độ phủ website của doanh nghiệp dịch vụ địa phương:** phù hợp với
   đo độ phủ Places và nhu cầu research, nhưng chưa chứng minh người mua muốn
   mua dataset. Rights Overture, terms của nguồn web và cách đo trạng thái web
   vẫn cần rà.

Top 3 là **shortlist để thiết kế/kiểm chứng**, không phải kết luận rằng cả ba
được phép bán. Các giả thuyết về auto-repair, multifamily/EV, fleet và CRE vẫn
ở long-list hoặc reserve; không bị xóa.

### Cách chọn và mức độ tin cậy

So sánh định tính theo năm tiêu chí của roadmap: buyer signal (25%), tốc độ
kiểm chứng/ra tiền (25%), rủi ro pháp lý (15%), khác biệt (20%) và chi phí duy
trì (15%). Không công bố điểm số tổng vì nguồn hiện tại chủ yếu là listing,
không phải giao dịch; bốn review G2 chưa xác minh trực tiếp.

| Thứ tự | Lý do vào Top 3 | Điểm yếu/điều kiện |
|---|---|---|
| 1. License HVAC/điện | Hai listing cụ thể, một yêu cầu paid trial; registry California có file công khai với license status/class/expiry. | Không chứng minh đã thuê/trả tiền; public download không đồng nghĩa license tái phân phối. |
| 2. CRM company hygiene | Nhu cầu data-quality/dedup xuất hiện ở nhiều loại evidence; có thể bắt đầu bằng dữ liệu tổng hợp hoặc file do buyer đưa, không cần bán nguồn bên thứ ba. | G2 gốc chưa xác minh; pain broad, cần buyer interview; file khách hàng có thể lẫn personal data. |
| 3. Website coverage | Hai listing liên quan lead research theo website; Overture Places có website field đủ để thiết kế phép đo coverage. | Listing cần dịch vụ research, chưa chứng minh mua dataset; quyền source/property và ToS web chưa rõ. |

Auto-repair để reserve vì evidence ít hơn và listing gốc gắn với yêu cầu owner/
decision-maker; sau khi bỏ PII cần xác nhận lại rằng company-level coverage vẫn
giải quyết pain. EV/CRE/fleet hiện ít evidence hơn. Không có giả thuyết nào
được gọi là “validated” hoặc “đã bán”.

## 2. Định vị theo sàn

| Sản phẩm | Gumroad — file/digital kit | Apify Store — Actor |
|---|---|---|
| HVAC/điện license | Gói theo bang/khu vực, CSV/Parquet và data dictionary, snapshot date, nguồn và changelog. Chỉ có record sau khi được xác nhận quyền tái phân phối. | Nhận file registry chính thức do người dùng cung cấp hoặc dùng API/feed có quyền; lọc trade/status/vùng, so sánh hai snapshot và xuất audit/delta. |
| CRM company hygiene | Bộ công cụ chạy local: DuckDB/CSV template, quy tắc chuẩn hóa, synthetic fixture và quality report; file thật của khách hàng không tải lên Gumroad. | File-in/file-out Actor cho các cột doanh nghiệp đã giới hạn; phát hiện trùng, thiếu và freshness. Không giữ lại input sau thời hạn xử lý đã công bố. |
| Website coverage | Bản báo cáo theo metro/ngành với số liệu tổng hợp và phương pháp; file record doanh nghiệp chỉ sau rights review. | Actor phân tích snapshot/file do khách hàng cung cấp hoặc nguồn đã cấp phép; trả coverage summary. Không crawl Maps/directory hay website trước khi rà ToS/robots. |

### Ranh giới chung

- Không cung cấp owner/principal name, email cá nhân, mobile cá nhân, skip-traced
  contact, direct-mail list hay cold-outreach workflow.
- Không suy ra doanh nghiệp đóng cửa từ website không phản hồi hoặc field thiếu.
- Mọi record được phát hành phải giữ source ID, provider, source/property,
  snapshot/check date, transformation version và điều kiện license/attribution.
- Không dùng nguồn yêu cầu login, vượt cơ chế kiểm soát, hoặc scraper trái ToS.
- Gumroad và Apify có thể được dùng làm hai gói sản phẩm khác nhau; không dùng
  listing Apify để quảng bá hay điều hướng buyer sang sản phẩm ngoài Apify.
- Chưa xuất raw/derived Overture hoặc CSLB record trong sample công khai.
  `commercial_redistribution_approved` tiếp tục `false`.

## 3. Product brief

### Top 3 #1 — Theo dõi license nhà thầu HVAC/điện

**Buyer giả thuyết:** procurement/commercial contractor/property manager cần
xác minh vendor theo trade, vùng, trạng thái và ngày hết hạn license.

**Gumroad MVP**

- Tên thử: `California HVAC & Electrical License Status Pack`.
- Bản đầu chỉ gồm data dictionary, cách kiểm tra, coverage summary và synthetic
  preview. Chỉ bật download chứa record thật sau khi xác nhận rights của CSLB.
- Nếu được phép: CSV/Parquet theo snapshot; license number, business name,
  classification, status, issue/expiry date, geography, source URL, checked_at.
- Không thêm personnel file, owner names, email, mobile hoặc thông tin suy diễn.
- Giá thử ban đầu: USD 19 cho một vùng/nhóm trade; đây là giả thuyết test giá,
  không phải giá thị trường đã xác minh. Không cam kết cập nhật thuê bao ở V1.

**Apify MVP**

- Tên thử: `US Contractor License File Checker`.
- Input: registry CSV/XLS do buyer cung cấp hoặc endpoint có quyền sử dụng;
  filter theo trade/class, status và khu vực.
- Output: matched/filtered rows, validation errors, snapshot dates và delta
  report giữa hai file do buyer cung cấp.
- Chưa tự tải CSLB hoặc state portals cho tới khi điều khoản và quyền API được
  xác nhận. Pricing: free sample nhỏ; paid event theo một lần xử lý file sau
  khi đo platform cost và test willingness-to-pay.

**Điều kiện qua gate:** văn bản/điều khoản cho phép tái sử dụng hoặc phương án
chỉ xử lý file do buyer cung cấp; xác định quyền với business name/license
records, warranty/disclaimer, update cadence và giới hạn sử dụng.

### Top 3 #2 — CRM company-record hygiene

**Buyer giả thuyết:** RevOps, agency và SME cần giảm duplicate company records,
thiếu domain/địa chỉ, sai chuẩn tên và thiếu nguồn/ngày kiểm tra.

**Gumroad MVP**

- Tên thử: `Company CRM Hygiene Kit`.
- Tải xuống gồm tool chạy local, CSV schema/template, synthetic input/output,
  data dictionary, duplicate rules và audit report mẫu.
- Mặc định giữ dữ liệu trên máy buyer; không gửi file CRM qua email hay lưu vào
  Gumroad. Không kèm external company/contact database.
- Giá thử ban đầu: USD 19 cho license một người dùng; giá này là giả thuyết.

**Apify MVP**

- Tên thử: `Company Record Quality Audit`.
- Input: CSV/XLS với allowlist cột company name, domain, business address,
  category, source và source date.
- Output: normalized company name/domain, exact/near-duplicate group,
  missingness flags, freshness flags và audit trail. Không tự gán `closed`.
- Loại hoặc từ chối cột người thật, personal email/mobile, owner, notes tự do
  và dữ liệu nhạy cảm; không dùng input để train, enrich hoặc tái sử dụng.
- Dùng limited permissions; xóa run data theo retention đã nêu trong privacy
  notice. Chỉ monetization sau khi test cô lập dữ liệu/chi phí và rà DPA.
- Giá: tính theo run/batch sau khi đo usage; không chốt số trước khi có cost
  benchmark và ít nhất một buyer test.

**Điều kiện qua gate:** privacy notice và retention/deletion flow; kiểm tra
sole proprietor và dữ liệu có thể nhận diện cá nhân; hợp đồng xử lý nếu cần;
synthetic fixture cho test; buyer xác nhận đầu ra giải quyết pain.

### Top 3 #3 — Website coverage của local service businesses

**Buyer giả thuyết:** web/marketing agency cần tổng quan theo metro/ngành về
doanh nghiệp dịch vụ chưa có website hoặc có dấu hiệu web presence yếu.

**Gumroad MVP**

- Tên thử: `US Local Service Website Coverage Brief`.
- V1 là PDF/CSV tổng hợp theo metro và category: số lượng, coverage rate,
  định nghĩa chỉ số, snapshot date, nguồn và giới hạn.
- Chưa bán record-level Places. Chỉ cân nhắc file doanh nghiệp sau khi kiểm kê
  đúng `sources[*].license`/`property`, attribution/NOTICE và terms của nguồn
  phụ.
- Giá thử: USD 19 cho một metro report; giả thuyết cần kiểm chứng.

**Apify MVP**

- Tên thử: `Local Website Coverage Analyzer`.
- Input: file dữ liệu doanh nghiệp do buyer cung cấp hoặc snapshot được cấp
  phép; metro/category filters.
- V1 chỉ tính website field presence/coverage; không tự crawl. Sau khi rà
  robots/ToS và giới hạn tải mới thử HTTP checks, ghi rõ `reachable`,
  `unreachable` hay `not_checked`, không gọi đó là trạng thái doanh nghiệp.
- Output: aggregate report, method note và source lineage. Không xuất contact
  cá nhân hoặc gửi outreach.
- Giá: free small report rồi test paid run, sau khi đo compute và nhu cầu.

**Điều kiện qua gate:** xác định quyền record-level output Overture cho từng
provider/property; rà nguồn website; định nghĩa mẫu số và false-positive rate;
buyer xác nhận họ cần market coverage chứ không chỉ cần dịch vụ lead research.

## 4. Thứ tự phát triển và kiểm chứng

1. **Prototype local CRM hygiene trước** bằng dữ liệu tổng hợp; đây là đường ít
   phụ thuộc quyền dữ liệu bên thứ ba nhất. Chưa đưa file thật lên dịch vụ.
2. **Kiểm chứng buyer cho license pack** bằng mockup không có record nguồn;
   hỏi trực tiếp một buyer về 3–5 trường, tần suất cập nhật và mức giá thử.
3. **Website coverage** chỉ tiếp tục sau khi rights Overture/source-property và
   website terms được rà. Bắt đầu bằng report tổng hợp, không bằng lead list.
4. Mỗi giả thuyết chỉ chuyển sang `5. Sample & Smoke Test` sau khi có buyer
   feedback, data contract, rights/terms và test plan; chỉ chuyển sang MVP sau
   khi có willingness-to-pay đủ cụ thể.

## 5. Tiêu chí nghiệm thu cho prototype đầu tiên

- Synthetic fixture tối thiểu 50 company rows có exact duplicate, tên gần
  giống, domain thiếu/sai và source dates khác nhau.
- Kết quả xác định được khi input, config và code version không đổi.
- Xuất data dictionary và report: mẫu số, số duplicate, missingness, freshness
  flags, rows excluded và lý do.
- Không có person name, personal email, mobile, input thật hoặc source records
  trong test artifact.
- Có hướng dẫn chạy local bằng DuckDB/Python; chạy test và `git diff --check`.
- Prototype chỉ chứng minh workflow kỹ thuật, không chứng minh buyer demand,
  source permission hay khả năng thương mại.

## 6. Giả định và việc chưa biết

- 25 pain-point items là tín hiệu nghiên cứu, không phải bằng chứng đã hoàn
  thành giao dịch hay người mua dataset.
- Kênh/tài khoản được ghi nhận theo xác nhận tạm thời của chủ dự án. Phương
  thức cụ thể và giao dịch payout thật chưa được khẳng định.
- Giá trên là giá test giả thuyết, chưa có benchmark buyer hoặc competitor.
- Quyền bán lại Overture/CSLB và quyền product listing chưa được phê duyệt.
- Bốn review G2 cần được mở trên trang gốc; confidence không được nâng trước đó.
