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

## 6. Các công cụ và tích hợp khác có trong `daybreak.txt`

Các mục dưới đây là cài đặt riêng của từng chương trình; không dùng lẫn cấu hình Codex CLI với cấu hình của ứng dụng khác.

### oh-my-pi (omp)

PR [#17508](https://github.com/can1357/oh-my-pi/pull/17508) đã được merge; changelog ghi cài đặt này có từ bản `18.14.1`. Đây là cài đặt của omp, không phải của Codex CLI. Theo tài liệu settings của dự án, khóa `providers.openai-codex.daybreak` có mặc định `true`, vì vậy cần đặt tường minh `false` nếu muốn ngừng omp tự động yêu cầu chương trình Daybreak Blue trên tài khoản ChatGPT đủ điều kiện.

**Cách đặt bằng lệnh:**

~~~sh
omp config set providers.openai-codex.daybreak false
omp config get providers.openai-codex.daybreak
~~~

Lệnh thứ hai cần trả về `false`. Có thể dùng giao diện `/settings` hoặc sửa file YAML cấu hình omp; cấu trúc tương ứng:

~~~yaml
providers:
  openai-codex:
    daybreak: false
~~~

Nếu bản omp cài trên máy cũ hơn `18.14.1`, cập nhật omp trước, rồi kiểm tra khóa bằng `omp config get`. Tài liệu của omp nói cài đặt này ngừng tự động gửi `access_programs.cyber = "daybreak_blue"`; nó không bao gồm các model Daybreak Blue chuyên dụng có tên `gpt-daybreak-blue-*`. Vì thế, không xem thiết lập này như một công tắc chung cho mọi model hoặc ứng dụng.

### t3code

Issue [#27835](https://github.com/pingdotgg/t3code/issues/27835) ghi nhận một giới hạn trong tích hợp app-server: tại bản và môi trường người báo cáo kiểm tra, thêm `-c daybreak=false` vào tham số khởi chạy provider không làm t3code gửi `cyberAccessProgram: "standard"` trong từng `turn/start`. Tài liệu OpenAI cho app-server nói lựa chọn phải được gửi ở mỗi turn; bỏ trường đó không tự động đồng nghĩa với tắt Daybreak.

Issue được đóng là **not planned** ngày 12-11-2026 vì maintainer xem đây là đề xuất hành vi mới. Issue nói người báo cáo không có workaround đã xác minh ngay trong t3code. Vì vậy:

1. Không dựa riêng vào `-c daybreak=false` trong cấu hình provider của t3code để chứng minh mỗi turn đã chạy theo chế độ `standard`.
2. Nếu cần chế độ `standard`, dùng client có hỗ trợ gửi `cyberAccessProgram: "standard"` ở mỗi turn, hoặc dùng Codex CLI gốc theo các bước ở trên.
3. Trước khi đổi quy trình, kiểm tra release notes và issue/PR mới của t3code; việc issue cũ đóng không chứng minh các phiên bản mới vẫn còn lỗi hay đã được sửa.

### Codex Security CLI

Đây là CLI quét bảo mật riêng, có cờ Daybreak riêng. Hướng dẫn Codex Security hiện hành nêu Codex `0.163.0` trở lên mặc định để Daybreak tắt trong CLI này; cài đặt của lần scan cần chỉ định riêng vì môi trường scan được cô lập khỏi cấu hình cá nhân.

**Chạy scan với mặc định an toàn (Daybreak tắt):**

~~~sh
npx @openai/codex-security scan .
~~~

**Bật tường minh cho một lần scan được phép:**

~~~sh
npx @openai/codex-security scan . --codex daybreak=true
~~~

**Ghi tường minh Daybreak tắt cho lần scan:**

~~~sh
npx @openai/codex-security scan . --codex daybreak=false
~~~

Trong file dự án Codex Security, giá trị tương ứng nằm dưới khóa `codex`:

~~~yaml
codex:
  daybreak: false
~~~

Thiết lập này được giữ trong scan recipe/resume và truyền cho worker deep scan theo hướng dẫn của Codex Security. Cờ đó chỉ cấu hình tùy chọn Daybreak của Codex chạy bởi Codex Security CLI; nó không thay đổi trạng thái Codex CLI tương tác hay quyền truy cập tài khoản.

### Tách biệt các cơ chế

| Công cụ | Tùy chọn tắt | Lưu ý |
|---|---|---|
| Codex CLI tương tác | `/daybreak` (lệnh gạt; kiểm tra phản hồi sau khi chuyển) | Cũng lưu lựa chọn mặc định cho phiên mới; thread cũ có thể giữ trạng thái đã lưu |
| Codex CLI headless | `-c daybreak=false` | Chỉ cho lần chạy đó; áp dụng vào đúng môi trường chạy lệnh |
| Codex CLI mặc định | `daybreak = false` trong `config.toml` | Mặc định cho phiên mới; không ghi đè lựa chọn đã lưu của thread cũ |
| oh-my-pi | `providers.openai-codex.daybreak: false` | Khóa omp riêng, mặc định `true`; không bao gồm model `gpt-daybreak-blue-*` |
| Codex Security CLI | `--codex daybreak=false` hoặc `codex.daybreak: false` | Cấu hình scan riêng; từ Codex `0.163.0` mặc định tắt theo tài liệu CLI |
| t3code | Chưa có bước tắt đã được xác minh trong issue #27835 | `-c daybreak=false` một mình không khiến app-server gửi `standard` mỗi turn |

## 7. Nếu mục tiêu là kiểm soát việc dùng dữ liệu để cải thiện model

Đây là cài đặt dữ liệu riêng với công tắc Daybreak. Với tài khoản ChatGPT cá nhân, hướng dẫn OpenAI hiện nêu nội dung tương tác trong **Daybreak sessions** có thể được dùng để cải thiện model ngay cả khi `Improve the model for everyone` đang tắt. Thiết lập đó vẫn áp dụng cho hoạt động khác ngoài phiên Trusted Access/Daybreak.

Để kiểm tra hoặc tắt lựa chọn chia sẻ dữ liệu thông thường trên tài khoản cá nhân:

1. Mở ChatGPT trên web và vào **Settings**.
2. Chọn **Data controls**.
3. Kiểm tra **Improve the model for everyone**; nếu không muốn chia sẻ cho hoạt động thông thường, tắt công tắc này.
4. Với tài khoản cá nhân, nếu không muốn nội dung được xử lý theo ngoại lệ nêu cho Daybreak sessions, đừng bật Daybreak cho phiên đó. Dùng các bước tắt đúng client ở trên.

OpenAI ghi rằng tùy chọn training thông thường vẫn áp dụng cho Codex tasks trên tài khoản cá nhân, nhưng đồng thời nêu ngoại lệ Daybreak nói trên. Tài khoản/workspace Business, Enterprise và Edu có chính sách dữ liệu khác; kiểm tra chính sách workspace của bạn. Các thiết lập training này không thay thế xác nhận trạng thái Daybreak trong client, còn `daybreak=false` không thay thế lựa chọn dữ liệu cấp tài khoản.

## Phạm vi và nguồn

Các tùy chọn trên điều khiển lựa chọn Daybreak ở từng CLI/tích hợp; chúng không tự thay đổi quyền truy cập tài khoản/workspace hoặc cài đặt quyền riêng tư/dữ liệu ở cấp tài khoản. Kiểm tra cài đặt riêng trong sản phẩm nếu mục tiêu của bạn là thay đổi chính sách dữ liệu.

## Nguồn chính thức

- [Using Daybreak in Codex CLI — OpenAI Help Center](https://help.openai.com/en/articles/20001607-using-daybreak-in-codex-cli)
- [OpenAI Daybreak overview](https://help.openai.com/en/articles/20001258-openai-daybreak-trusted-access-for-cyber-overview)
- [Data controls in ChatGPT — gồm phần Trusted Access on personal accounts](https://help.openai.com/en/articles/7730893-data-controls-in-chatgpt)
- [How your data is used to improve model performance](https://help.openai.com/en/articles/5722486-how-your-data-is-used-to-improve-model-performance)
- [oh-my-pi PR #17508](https://github.com/can1357/oh-my-pi/pull/17508) và [settings reference](https://github.com/can1357/oh-my-pi/blob/main/docs/settings.md)
- [t3code issue #27835](https://github.com/pingdotgg/t3code/issues/27835)
- [Codex Security CLI — Daybreak opt-in](https://github.com/openai/codex-security/blob/main/sdk/typescript/docs/cli.md#daybreak-opt-in)
- [Codex Security commit 04df406](https://github.com/openai/codex-security/commit/04df406934b8d15879abd54c8841d856ba181804)
