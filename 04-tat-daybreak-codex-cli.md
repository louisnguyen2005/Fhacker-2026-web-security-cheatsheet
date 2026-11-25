# Tắt Daybreak trong Codex CLI

**Cập nhật: 25-11-2026.** Hướng dẫn này dành cho Codex CLI. Daybreak là tùy chọn có thể bật/tắt; trạng thái được lưu theo phiên có thể khác với mặc định trong file cấu hình.

## 1. Kiểm tra phiên bản CLI

Mở terminal và chạy:

~~~sh
codex --version
~~~

Các điều khiển Daybreak trong CLI có từ Codex CLI `0.163.0`. Nếu phiên bản cũ, cập nhật rồi kiểm tra lại:

~~~sh
npm install -g @openai/codex@latest
codex --version
~~~

Nếu bạn cài CLI bằng SDK, CI hoặc một đường dẫn executable riêng, hãy cập nhật đúng runtime mà tiến trình đó đang dùng; cập nhật CLI toàn cục có thể không cập nhật runtime của SDK.

## 2. Tắt cho một lần chạy headless

Thêm `-c daybreak=false` vào lệnh `codex exec`:

~~~sh
codex exec -c daybreak=false "Review the changes in this repository."
~~~

Tùy chọn dòng lệnh chỉ áp dụng cho lần chạy đó và ghi đè giá trị trong `config.toml` cho lần chạy này. Đặt nó trong mọi lệnh/script/CI cần giữ Daybreak tắt.

## 3. Tắt trong phiên CLI tương tác

1. Mở phiên Codex CLI như bình thường.
2. Nhập `/daybreak` để chuyển trạng thái.
3. Nếu Daybreak đang bật, lệnh này tắt nó; nếu đang tắt, lệnh này bật nó.
4. Xác nhận trạng thái Codex báo sau khi chuyển. Thay đổi áp dụng cho các lượt tiếp theo trong thread hiện tại và được lưu làm mặc định cho phiên mới.

`/daybreak` là lệnh gạt, không phải lệnh “tắt” một chiều. Nếu chưa chắc trạng thái trước đó, đọc phản hồi của Codex rồi gạt lại khi cần.

## 4. Đặt mặc định tắt cho các phiên mới

1. Mở file cấu hình người dùng:

   - Mặc định: `~/.codex/config.toml`
   - Nếu đã đặt biến môi trường `CODEX_HOME`: `$CODEX_HOME/config.toml`

2. Thêm dòng sau ở cấp cao nhất, bên ngoài các section như `[features]`:

   ~~~toml
   daybreak = false
   ~~~

3. Lưu file và khởi chạy phiên Codex mới.
4. Nếu bạn dùng CI, máy chủ từ xa hoặc môi trường tự động hóa, sửa cấu hình trong chính môi trường chạy Codex đó. Cấu hình trên máy cá nhân không tự áp dụng cho runner/host khác.

Giá trị cấu hình là mặc định cho phiên mới. Thread được resume hoặc fork có thể giữ lựa chọn Daybreak đã lưu trước đó; thay cấu hình không tự ghi đè lựa chọn của những thread này. Trong trường hợp đó, tắt bằng `/daybreak` trong thread hoặc dùng `-c daybreak=false` cho lệnh headless.

## 5. Kiểm tra lại

- Chạy một lệnh headless đại diện với `-c daybreak=false`.
- Với phiên tương tác, xác nhận trạng thái Daybreak sau khi dùng `/daybreak`.
- Với cấu hình mặc định, mở một phiên mới sau khi lưu `daybreak = false`; kiểm tra cả thread cũ nếu bạn thường resume/fork thread.
- Kiểm tra riêng từng nơi chạy Codex: laptop, container, CI runner, SDK hoặc máy chủ từ xa.

## Phạm vi của các bước này

Các bước trên kiểm soát lựa chọn Daybreak trong Codex CLI. Chúng không thay đổi quyền truy cập tài khoản/workspace, không cấu hình ứng dụng khác hoặc Codex Desktop, và không phải cài đặt chung cho mọi SDK/app-server. Nếu mục tiêu là thay đổi chính sách dữ liệu hay cài đặt tài khoản, hãy xem trang cài đặt/quyền riêng tư tương ứng trong sản phẩm; `daybreak=false` chỉ điều khiển lựa chọn Daybreak cho lệnh/phiên CLI được cấu hình.

## Nguồn chính thức

- [Using Daybreak in Codex CLI — OpenAI Help Center](https://help.openai.com/en/articles/20001607-using-daybreak-in-codex-cli)
- [OpenAI Daybreak overview](https://help.openai.com/en/articles/20001258-openai-daybreak-trusted-access-for-cyber-overview)
