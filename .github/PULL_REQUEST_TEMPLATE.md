## Mục đích

Thay đổi này giải quyết vấn đề gì?

## Phạm vi và tác động

- [ ] Chỉ thay đổi mã
- [ ] Thay đổi nguồn/cấu hình
- [ ] Thay đổi schema hoặc chỉ số
- [ ] Thay đổi tài liệu hoặc workflow

Mô tả ảnh hưởng đến khả năng tương thích hoặc thành phần phía sau:

## Provenance và quyền sử dụng dữ liệu

- Nguồn và phiên bản chính xác, nếu áp dụng:
- Giấy phép/điều khoản chính thức và yêu cầu ghi công đã rà soát:
- Ảnh hưởng liên quan đến PII hoặc tái phân phối:
- Dữ liệu thô không được đưa vào Git:

## Kiểm tra

- [ ] `ruff check .`
- [ ] `python -m pytest -q`
- [ ] `python -m compileall -q tools tests`
- [ ] Kiểm định dữ liệu lớn (ghi phiên bản, khu vực và đường dẫn báo cáo):

Liệt kê kiểm tra bị bỏ qua và lý do:

## Khả năng tái lập

- [ ] Đã ghi đầu vào/cấu hình và phiên bản schema
- [ ] Chỉ số có định nghĩa và mẫu số
- [ ] Pull request không chứa secret, dữ liệu cá nhân hoặc bản ghi nguồn số lượng lớn
