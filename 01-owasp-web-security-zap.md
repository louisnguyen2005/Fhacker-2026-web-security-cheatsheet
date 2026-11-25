# Phần 1 — OWASP, lỗ hổng web và OWASP ZAP

**Cập nhật nguồn: 25-11-2026.** Đây là tài liệu học/kiểm thử phòng thủ. Chỉ quét ứng dụng của bạn hoặc nơi có giấy phép rõ ràng. Dùng dữ liệu giả, tài khoản kiểm thử, môi trường staging/localhost và giới hạn tốc độ. Không thử hành động phá hoại, gửi thư/thanh toán thật hoặc truy cập dữ liệu người dùng.

## 1. Mô hình tư duy

Một lỗi web thường xuất hiện khi ranh giới tin cậy bị đặt sai: dữ liệu không tin cậy được hiểu như lệnh; người dùng được phép truy cập đối tượng/hành động không thuộc quyền của họ; hoặc cấu hình/bản dựng khiến thành phần ngoài dự kiến xử lý request. Khi kiểm tra, đi theo luồng:

1. **Tài sản:** tài khoản, hồ sơ, tệp, khóa, dữ liệu thanh toán, tính sẵn sàng.
2. **Danh tính và quyền:** ai gửi request, thuộc tenant/role nào, được đọc/ghi đối tượng nào?
3. **Luồng dữ liệu:** input đi qua parser/interpreter/render/template/cache/backend nào?
4. **Điều kiện triển khai:** phiên bản, feature flag, proxy, CDN, HTTP/2/3, cache, module, quyền hệ điều hành.
5. **Kiểm chứng có kiểm soát:** chứng minh bằng tài khoản và dữ liệu giả; dừng khi có dấu hiệu tác động ngoài dự kiến.
6. **Khắc phục và hồi quy:** sửa nguyên nhân gốc, thêm kiểm thử tự động, quét lại và theo dõi logs.

OWASP Top 10 là tài liệu nhận thức/ưu tiên rủi ro, không phải danh sách đầy đủ hay chứng nhận ứng dụng an toàn. Dùng OWASP ASVS để chuyển yêu cầu thành tiêu chí kiểm chứng cụ thể.

Để xem từng mục dưới dạng **code lỗi → cách tái hiện trong lab → bản vá → kiểm tra hồi quy**, đọc [Phần 5 — OWASP Top 10:2025: mã lỗi, tái hiện an toàn và bản vá](04-owasp-top10-code-exploit-fix.md).

## 2. OWASP Top 10:2025 — danh sách và cách xử lý

OWASP Top 10:2025 là phiên bản mới nhất của danh sách rủi ro ứng dụng web tại thời điểm cập nhật. Hai mục mới là **A03 Software Supply Chain Failures** và **A10 Mishandling of Exceptional Conditions**; SSRF được gộp vào **A01 Broken Access Control**; phạm vi rủi ro thư viện lỗi thời được mở rộng thành chuỗi cung ứng phần mềm. Đây là phân loại rủi ro tổng quát; mỗi dự án cần threat model riêng.

### A01:2025 — Broken Access Control

**Ý nghĩa:** máy chủ không kiểm tra đúng quyền cho từng đối tượng hoặc hành động. UI ẩn nút không phải kiểm soát truy cập. Lỗi thường gồm IDOR/BOLA, đọc/sửa tài nguyên người khác, gọi API quản trị bằng tài khoản thường, truy cập chéo tenant, bỏ qua workflow, tải tệp riêng tư bằng URL đoán được, hoặc SSRF do endpoint fetch URL chạm vào tài nguyên nội bộ.

**Kiểm tra an toàn:** tạo hai tài khoản/tenant test với dữ liệu riêng. Ghi request hợp lệ của A, rồi dùng phiên B kiểm tra đối tượng của B và một đối tượng giả của A. Thử vai trò thấp hơn với thao tác chỉ dành cho quản trị viên. Không dò ID người dùng thật. Với chức năng lấy URL từ server, kiểm tra thiết kế/allowlist trong code và dùng endpoint mô phỏng; không gọi metadata service hoặc địa chỉ nội bộ thật.

**Khắc phục:** xác thực quyền phía server trên mọi request và mọi đối tượng; mặc định từ chối; lấy owner/tenant từ session đã xác thực thay vì tin client; dùng policy tập trung; phân biệt quyền đọc/sửa/xóa; ký URL tải xuống có hạn dùng; kiểm tra quyền trước khi trả dữ liệu. Với fetch URL: hạn chế egress, allowlist host/scheme, chặn loopback/link-local/private IP sau phân giải DNS, xử lý redirect và kiểm tra lại đích.

**API liên quan:** OWASP API1 BOLA, API3 Broken Object Property Level Authorization và API5 Broken Function Level Authorization. Kiểm tra cả field-level: không trả hoặc cho phép gán thuộc tính nhạy cảm chỉ vì object cha được đọc.

### A02:2025 — Security Misconfiguration

**Ý nghĩa:** cấu hình không an toàn ở app, framework, cloud, proxy, container hoặc dịch vụ phụ trợ: debug bật ở production, directory listing, trang quản trị công khai, CORS quá rộng, header bảo mật thiếu/sai, lỗi tiết lộ nội bộ, credential mặc định, quyền file rộng, service thừa, hoặc reverse proxy tin header client tự đặt.

**Kiểm tra:** so sánh production với baseline đã duyệt; liệt kê endpoint, port, header, CORS, TLS, cookie, error pages và cấu hình đã triển khai; kiểm tra kết quả sau proxy/CDN. Dùng ZAP passive scan để tìm dấu hiệu header/cookie phổ biến, rồi xác minh thủ công vì cảnh báo phụ thuộc ngữ cảnh.

**Khắc phục:** cấu hình dưới dạng mã, review thay đổi, tắt thành phần không dùng, phân quyền tối thiểu, tách secret khỏi repo/image, thay trang lỗi mặc định, cấu hình allowlist host/CORS, khóa admin plane bằng mạng/SSO/MFA và có checklist triển khai lặp lại.

### A03:2025 — Software Supply Chain Failures

**Ý nghĩa:** rủi ro trong dependency, package registry, build runner, CI/CD, artifact, plugin, image container hoặc quy trình phát hành — không chỉ là thư viện cũ. Thành phần bị chiếm quyền, package nhầm tên, dependency bắc cầu, build không tái lập hoặc token CI quá rộng có thể đưa mã không mong muốn vào production.

**Kiểm tra:** kiểm kê dependency trực tiếp/bắc cầu và phiên bản; rà lockfile, registry, workflow CI, quyền token, image base và provenance artifact. Theo dõi advisory maintainer và distro. Chạy SCA/SBOM trong pipeline; xác minh chữ ký/hash nếu hỗ trợ.

**Khắc phục:** pin/cập nhật có review; dùng lockfile/registry tin cậy; giới hạn quyền token theo job/thời gian/repository; tách build khỏi production secrets; bảo vệ branch/release; tạo SBOM; xác minh artifact; cập nhật runtime/OS theo advisory; có quy trình thu hồi khóa và rebuild sạch. Cảnh báo SCA không tự chứng minh đã khai thác: xác định component có nằm trong build và có đường gọi hay không.

### A04:2025 — Cryptographic Failures

**Ý nghĩa:** dữ liệu nhạy cảm không được bảo vệ đúng khi truyền/lưu/dùng. Ví dụ HTTP cho luồng đăng nhập, thuật toán/chế độ lỗi thời, khóa/nonce tái sử dụng, mật khẩu băm nhanh thay vì password hashing chuyên dụng, secret commit vào Git hoặc lưu quá nhiều dữ liệu nhạy cảm.

**Khắc phục:** giảm dữ liệu cần lưu; TLS cho toàn phiên; thư viện crypto chuẩn và được duy trì; quản lý khóa bằng KMS/secret manager, luân phiên và giới hạn quyền; dùng password hashing chuyên dụng theo hướng dẫn hiện hành; không tự thiết kế thuật toán; kiểm tra backup/log/cache có lộ dữ liệu không.

### A05:2025 — Injection

**Ý nghĩa:** input bị ghép vào ngôn ngữ mà trình thông dịch thực thi — SQL/NoSQL/LDAP/OS command/template/HTML/JavaScript/GraphQL. XSS thuộc họ injection, nhưng cách phòng phụ thuộc context trình duyệt.

**Khắc phục:** API tham số hóa hoặc API không gọi interpreter; tách dữ liệu khỏi cấu trúc lệnh; allowlist identifier không thể bind như tên cột/sort; encoding đúng context khi render; safe DOM APIs; sanitizer HTML được duy trì nếu buộc nhận HTML. Validation giúp kiểm soát định dạng nhưng không thay parameterization/output encoding. Hạn chế quyền tài khoản DB và tiến trình.

**Ví dụ SQL an toàn (Python DB-API):**

~~~python
cursor.execute(
    "SELECT id, title FROM posts WHERE owner_id = ? AND status = ?",
    (current_user_id, requested_status),
)
~~~

Không ghép input vào query string. Với sort field, map lựa chọn UI sang tập hằng do code định nghĩa; không nối raw input làm tên cột.

### A06:2025 — Insecure Design

**Ý nghĩa:** quy trình nghiệp vụ không có kiểm soát cần thiết, ngay cả khi code chạy đúng như thiết kế. Ví dụ thiếu giới hạn lần thử, quy trình khôi phục tài khoản yếu, thiếu phân tách nhiệm vụ, cho phép đổi email rồi rút tiền ngay không xác minh, hoặc không định nghĩa hành vi an toàn khi backend lỗi.

**Khắc phục:** threat model từ lúc thiết kế; abuse case; giới hạn tốc độ/ngân sách; xác minh giao dịch nhạy cảm; phân tách nhiệm vụ; quy tắc trạng thái server-side; kiểm thử quyền theo vai trò và quy trình đầu-cuối; yêu cầu an toàn có tiêu chí chấp nhận.

### A07:2025 — Authentication Failures

**Ý nghĩa:** lỗi nhận diện người dùng hoặc thiết lập phiên: password reset/token dễ đoán/dùng lại, session fixation, không thu hồi phiên khi đổi mật khẩu, MFA yếu/bỏ qua, xác thực khác nhau giữa endpoint hoặc account enumeration.

**Khắc phục:** dùng thư viện/IdP chuẩn; MFA/passkey cho hành động rủi ro; giới hạn thử đăng nhập và khôi phục; phản hồi reset đồng nhất; token ngẫu nhiên, một lần, ngắn hạn, ràng buộc mục đích; xoay session ID sau đăng nhập/nâng quyền; thu hồi refresh token; cookie Secure, HttpOnly, SameSite phù hợp; re-authentication cho hành động quan trọng.

### A08:2025 — Software or Data Integrity Failures

**Ý nghĩa:** ứng dụng tin mã, cấu hình, cập nhật hoặc dữ liệu serialized mà không xác minh tính toàn vẹn/nguồn gốc. Ví dụ CI artifact không xác minh, deserialize dữ liệu không tin cậy, cập nhật plugin thiếu chữ ký, hoặc tin client-side state để quyết định quyền.

**Khắc phục:** verify nguồn gốc/chữ ký artifact; bảo vệ pipeline; không deserialize object tùy ý từ người dùng; dùng format hẹp/schema validation; integrity check cho dữ liệu nhạy cảm; server quyết định quyền/trạng thái; review script/plugin/extension.

### A09:2025 — Security Logging and Alerting Failures

**Ý nghĩa:** sự kiện bảo mật không được ghi đủ, cảnh báo không tới đúng người, log có thể sửa/xóa hoặc chứa dữ liệu nhạy cảm. Tổ chức khó phát hiện, điều tra và giới hạn sự cố.

**Khắc phục:** log đăng nhập thất bại, đổi quyền/MFA, truy cập dữ liệu nhạy cảm, lỗi kiểm soát truy cập và hành động quản trị; gắn correlation/request ID; đồng bộ thời gian; chống sửa log và phân quyền đọc; cảnh báo theo ngưỡng/chuỗi sự kiện; không ghi password, session token, secret hoặc PII quá mức; thử quy trình ứng cứu.

### A10:2025 — Mishandling of Exceptional Conditions

**Ý nghĩa:** lỗi, timeout, race condition, thiếu tài nguyên hoặc trạng thái bất thường khiến hệ thống bỏ qua kiểm soát, lộ stack trace/secret, tạo dữ liệu sai, giữ tài nguyên hoặc hoạt động fail-open. Đây là mục mới trong Top 10:2025.

**Khắc phục:** phân loại lỗi và trả phản hồi an toàn; không lộ stack trace/đường dẫn/token; timeout/giới hạn tài nguyên; cleanup giao dịch trong mọi nhánh; transaction/locking đúng; fail closed cho quyết định quyền; fault-injection trong test; bảo vệ idempotency khi retry.

## 3. Lỗ hổng và chủ đề web khác cần biết

Các chủ đề sau không phải tất cả đều là mục Top 10 riêng. Chúng đáng học vì xuất hiện trong ứng dụng/API hiện đại và một số cần kiểm thử thủ công.

| Chủ đề | Dấu hiệu cần rà soát | Hướng phòng thủ |
|---|---|---|
| XSS (stored, reflected, DOM) | Dữ liệu người dùng xuất hiện trong HTML/attribute/URL/script; framework escape bị bypass qua HTML thô | Auto-escape, encoding theo context, safe DOM APIs, sanitizer được duy trì; CSP/Trusted Types là lớp bổ sung |
| CSRF và client-side CSRF | Trình duyệt tự gửi cookie cho thao tác đổi trạng thái; endpoint nhận GET để thay dữ liệu; JS lấy URL không tin cậy rồi gửi request có quyền | CSRF token gắn session, kiểm tra Origin/Referer phù hợp, SameSite defense-in-depth, không đổi trạng thái bằng GET; ngăn XSS |
| SQL/NoSQL/ORM injection | Query/filter/regex/aggregation tạo từ input; dữ liệu vào shell hoặc template | Parameterization/safe query API; allowlist cấu trúc; quyền DB tối thiểu; timeout/kết quả có giới hạn |
| SSRF | Server tải URL do user cung cấp, webhook, preview ảnh, PDF fetcher | Allowlist scheme/host; resolve và kiểm tra IP; chặn private/loopback/link-local; xử lý redirect; egress firewall; timeout/size cap |
| XXE/XML entity expansion | XML parser bật DTD/external entities; parser có thể truy cập file/mạng | Tắt DTD/external entities, parser an toàn, giới hạn kích thước/độ sâu, cập nhật thư viện |
| Upload không an toàn | Tin extension/MIME client gửi; tên file do user quyết định; lưu trong webroot | Allowlist loại cần thiết, kiểm tra nội dung, tên do app sinh, lưu ngoài webroot, không execute, giới hạn size/độ sâu và quyền |
| Deserialization | Dữ liệu object từ client, queue, cache hoặc cookie được deserialize không xác thực | Tránh deserialize object tùy ý; schema hẹp; chữ ký không thay kiểm soát quyền; cập nhật runtime |
| Clickjacking/framing | Trang nhạy cảm có thể bị nhúng vào frame nguồn lạ | CSP frame-ancestors theo nhu cầu; X-Frame-Options cho tương thích cũ; kiểm tra OAuth/login |
| CORS sai | Origin phản chiếu tùy ý, credentials với wildcard, so sánh suffix sai | Origin allowlist chính xác; credentials chỉ khi cần; CORS không phải authentication; Vary: Origin khi cần |
| Cache poisoning/leakage | Cache key thiếu biến ảnh hưởng nội dung; cookie/tenant bị bỏ qua; private data lưu chung | Phân loại public/private; cache key đủ; no-store cho dữ liệu nhạy cảm; test nhiều user/tenant; review CDN/proxy/framework cache |
| HTTP request smuggling/desync | Proxy và origin parse framing/header khác nhau; nhiều hop/proxy | Chuẩn hóa/loại request mơ hồ; cập nhật proxy/origin; kiểm thử staging; tuân theo vendor advisory; không thử payload desync trên production |
| GraphQL/API | BOLA, field overexposure, introspection không phù hợp, query tốn tài nguyên, inventory lỗi thời | Authorization theo object/field/function; depth/complexity/cost limit; rate limit; schema inventory/versioning; giới hạn batch |
| WebSocket | Origin không kiểm tra, quyền không xét lại sau handshake, message không validate | Kiểm tra Origin/danh tính, authorize từng action, schema/size/rate limit, timeout, log, đóng session khi logout |
| Prototype pollution/client-side injection | Merge object tùy tiện; property path từ input; dependency xử lý object nguy hiểm | Map/null-prototype hoặc allowlist key; tránh merge input; cập nhật dependency; unit tests |
| LLM/agent trong web app | Prompt injection qua nội dung truy xuất; tool đọc dữ liệu ngoài quyền; output đưa thẳng vào SQL/HTML/command | Coi retrieved text/output là input không tin cậy; quyền tool tối thiểu; policy server-side; human approval cho hành động nhạy cảm; schema validation; audit |

## 4. Lỗ hổng mới được công bố — ví dụ có nguồn

Đây là snapshot một số advisory gần đây, **không phải danh sách mọi CVE mới**. Mốc dữ liệu 25-11-2026; phiên bản vá thay đổi theo nhánh và nhà phân phối. Ưu tiên advisory maintainer/vendor, sau đó advisory distro nếu dùng package OS.

### NGINX HTTP/2/HTTP/3 — công bố 18-11-2026

F5 phát hành out-of-band notification về nhiều lỗi NGINX; trong đó CVE-2026-123007 liên quan module HTTP/2, CVE-2026-123633 là lỗi xử lý HTTP/2 trong điều kiện proxy/backend cụ thể, và CVE-2026-121810 liên quan HTTP/3. Một số điều kiện cấu hình là bắt buộc; không suy từ banner/version đơn lẻ rằng máy chắc chắn bị ảnh hưởng. **Việc cần làm:** kiểm kê điểm terminate HTTP/2/3, bản NGINX Open Source/Plus/Ingress, module và kiến trúc proxy; đối chiếu advisory F5/distro; cập nhật bản đã vá theo đúng nhánh; nếu chưa thể cập nhật, áp dụng biện pháp tạm thời vendor khuyến nghị và đặt hạn xử lý. Không tự chế exploit để xác nhận.

- [F5 Out-of-band Security Notification — 18 Nov 2026](https://my.f5.com/manage/s/article/K000164058)
- [CERT-EU: Critical vulnerabilities in NGINX](https://cert.europa.eu/publications/security-advisories/2026-022)

### PHP request processing — công bố 21-10-2026

PHP công bố CVE-2026-109618 và CVE-2026-109619, hai lỗi nghiêm trọng có thể cho phép RCE chưa xác thực trong một số cách triển khai phục vụ web. PHP khuyến nghị cập nhật release nhánh đã vá; upstream nêu không có biện pháp thay thế đầy đủ. **Việc cần làm:** kiểm kê PHP-FPM, mod_php, php-cgi và runtime nhúng; cập nhật package/runtime; kiểm tra version trong từng container/host; rà image/base image và tái dựng; rotate secret nếu có căn cứ đã bị truy cập.

- [PHP official security release archive](https://www.php.net/archive/2026.php#2026-10-21-5)
- [PHP 2026 news archive](https://www.php.net/archive/2026.php)

### Next.js/React cache, response handling và image optimization — 2026

Advisories năm 2026 cho thấy rủi ro có thể nằm ở giao điểm framework–proxy–cache–upstream, không chỉ ở route handler. Ví dụ: lỗi cache leakage/poisoning; cross-client response injection trong self-hosted deployment với điều kiện reverse proxy; và lỗi nghiêm trọng liên quan Image Optimization/SVG. **Việc cần làm:** kiểm kê Next.js/React, runtime và dependency tối ưu ảnh; xác định App Router, cache features, self-hosted reverse proxy, HTTP/1.1 upstream response forwarding và image optimizer; cập nhật theo advisory. Tách cache theo user/tenant; không cache chung response riêng tư; không trả nguyên upstream response nếu chưa kiểm tra framing/headers.

- [Next.js security advisories — nguồn cập nhật của maintainer](https://github.com/vercel/next.js/security/advisories)
- [GHSA-2464-fhr4-w9xw — image optimization/SVG, Oct 2026](https://github.com/vercel/next.js/security/advisories/GHSA-2464-fhr4-w9xw)
- [GHSA-pc58-hwjq-p385 — cross-client response injection/disclosure, Nov 2026](https://github.com/vercel/next.js/security/advisories/GHSA-pc58-hwjq-p385)
- [GHSA-rhh4-g77r-r9qj — cache disclosure/poisoning, Nov 2026](https://github.com/vercel/next.js/security/advisories/GHSA-rhh4-g77r-r9qj)

## 5. OWASP ZAP — hướng dẫn từ cài đặt đến báo cáo

### 5.1 ZAP làm gì và không làm gì

OWASP ZAP (Zed Attack Proxy) là proxy kiểm thử web có thể quan sát/sửa HTTP(S), thu thập URL, chạy passive rules, active rules, fuzzing và automation. Passive scan phân tích request/response đã đi qua ZAP và thường ít tác động. Active scan gửi request kiểm thử có chủ đích: có thể làm đổi dữ liệu, kích hoạt email/thanh toán, gây tải hoặc làm hỏng dữ liệu. Chỉ active scan/fuzz trên lab hoặc môi trường được cho phép.

Không có cảnh báo không chứng minh ứng dụng an toàn. Spider không tự đăng nhập/hoàn thành mọi workflow; active rules chỉ kiểm tra một tập lỗi; logic quyền như BOLA, abuse case, race condition, quy tắc thanh toán và một số lỗi client-side cần kiểm thử thủ công hoặc công cụ bổ sung. Alert là giả thuyết cần xác minh; risk không thay đánh giá ảnh hưởng nghiệp vụ.

### 5.2 Cài đặt và khởi động an toàn

- Tải Desktop từ [Download chính thức](https://www.zaproxy.org/download/) hoặc dùng container chính thức. Stable phù hợp kiểm thử định kỳ; weekly có thay đổi thường xuyên hơn. Ghi phiên bản ZAP/add-on và thời điểm vào báo cáo.
- Cập nhật add-on trước khi quét; pin image/container digest nếu cần build tái lập.
- Mở session riêng cho engagement/môi trường; không tái sử dụng session có cookie/token thật giữa ứng dụng hoặc tài khoản.
- Chạy ZAP trên máy/lab riêng. Khóa API bằng API key, chỉ bind localhost/mạng tin cậy; không expose API unauthenticated ra Internet/LAN không tin cậy. Session/report có thể chứa token, URL nội bộ và PII; lưu như dữ liệu nhạy cảm.
- Dùng test account/dữ liệu giả. Tắt email, webhook, thanh toán và side effect ở staging nếu có thể. Có backup/rollback và người theo dõi.

### 5.3 Proxy trình duyệt qua ZAP

1. Mở ZAP và để proxy listen trên loopback khi dùng một máy. Xem địa chỉ/cổng trong Options → Network → Local Servers/Proxies (tên menu có thể đổi theo bản).
2. Dùng browser do Manual Explore mở, hoặc cấu hình profile riêng trỏ HTTP/HTTPS proxy về ZAP.
3. Với HTTPS, browser cần tin ZAP Root CA. Dùng profile test riêng và xóa profile/chứng chỉ sau lab; không cài CA lab vào profile cá nhân/máy production.
4. Mở ứng dụng test, đăng nhập, thao tác với dữ liệu giả. Quan sát History, Sites, Request/Response. Nếu không thấy traffic, kiểm tra proxy browser/listener/TLS trust/VPN/upstream proxy/app.
5. Dừng ghi traffic khi đủ luồng; session lưu cả nội dung request/response.

### 5.4 Đặt scope trước khi spider hoặc scan

1. Tạo Context, thêm include regex chính xác cho scheme/host/port/path được phép; regex ZAP thường phải khớp toàn URL.
2. Đưa context vào scope và bật **Protected mode**. Mode này chỉ cho hành động nguy hiểm trên URL trong scope. Safe chặn hành động nguy hiểm; Standard không hạn chế; ATTACK tự active-scan node trong scope vừa phát hiện.
3. Thêm exclude cho logout, delete, purchase, send mail, external OAuth, destructive admin, import/export hoặc endpoint tạo side effect. Thử include/exclude bằng URL thật trước scan.
4. Chỉ gộp domain/path cùng ứng dụng và cùng phạm vi. Không dùng wildcard toàn domain tiện tay; subdomain có thể thuộc bên thứ ba.
5. Xác minh scope bằng Sites Tree và History trước hành động có khả năng ghi dữ liệu.

### 5.5 Authentication và session

ZAP cần phiên hợp lệ để khám phá endpoint sau đăng nhập. Trong Context, cấu hình Authentication phù hợp (form-based, JSON-based, browser-based, script/OAuth khi cần), tạo User và xác nhận bằng logged-in/logged-out indicator đáng tin cậy. Dùng tài khoản quyền thấp trước; tạo context/session riêng cho mỗi role. Không ghi password/token vào YAML public, CI log hoặc repo; dùng secret store.

Kiểm tra ZAP vẫn authenticated khi crawl: redirect về login, token hết hạn, CSRF token thay đổi hoặc scan vô tình logout sẽ khiến chỉ trang đăng nhập được quét. Cấu hình session management và re-authentication khi cần. Logout cuối phiên; không để session file chứa credential trên máy chia sẻ.

### 5.6 Khám phá ứng dụng

- **Manual Explore:** người kiểm thử thao tác trình duyệt và xác thực workflow thật; tốt để seed request có state/role.
- **Traditional Spider:** nhanh, theo link/form HTML; hợp trang server-rendered, không hiểu đầy đủ SPA.
- **AJAX Spider:** dùng browser tự động và theo liên kết JavaScript; chậm hơn, cần browser driver/add-on.
- **Client Spider:** khám phá phía client/browser, hữu ích với SPA khi add-on hỗ trợ; đối chiếu node/API thu được với route inventory.
- **Import OpenAPI/GraphQL/Postman:** tăng coverage API không link từ UI; xác minh spec không trỏ nhầm môi trường và không chứa secret.
- **Forced Browse:** tìm path không liên kết bằng wordlist. Có thể tạo tải/chạm endpoint nhạy cảm; chỉ lab/staging, wordlist nhỏ, giới hạn tốc độ, loại trừ path ghi/xóa.

Spider không thay danh sách route. Đối chiếu cây ZAP với sitemap/API spec, role matrix, frontend routes và server logs; ghi phần chưa crawl được.

### 5.7 Passive Scan và Active Scan

**Passive scan:** thường tự chạy khi ZAP quan sát response. Tìm cookie flags, HTTPS, cache/header, mixed content, information disclosure, CSP và một số client-side signals. Nó không thay đổi request để khai thác. Chờ passive queue xong trước khi xuất report.

**Active scan:** chọn context/node, policy và giới hạn; bắt đầu với policy phù hợp rủi ro; đặt thread thấp, delay/throttle, time limit và exclude side effects. Chạy trước trên staging bản sao. Theo dõi logs/error rate/latency; dừng nếu có lỗi tăng, dữ liệu đổi, email gửi, queue phình hoặc request ra ngoài scope. Không bật alpha rules trong pipeline mặc định.

Active scan hữu ích với một số injection/misconfiguration nhưng không tự phát hiện logic quyền. Kiểm tra BOLA bằng hai user/tenant thử nghiệm; business flow bằng testcase; session bằng role riêng. Access Control Testing add-on hỗ trợ một số ma trận quyền nếu khai báo role/URL chính xác; vẫn cần review.

### 5.8 Request Editor, Replacer, Fuzzer và WebSocket

- **Request/Response editor:** xem header, cookie, body, redirect, cache và status; lưu request mẫu đã xóa token/PII.
- **Replacer:** thay giá trị động hoặc thêm header đánh dấu scan trong môi trường test; không dùng để giả danh hoặc vượt kiểm soát.
- **Fuzzer:** chọn tham số trong request lab, dùng payload nhỏ/không phá hoại, giới hạn số request/concurrency, đặt timeout và theo dõi server. Không fuzz credential trên dịch vụ thật.
- **WebSocket:** bật hỗ trợ/add-on; ghi message trong thao tác hợp lệ; kiểm tra auth/authorization/schema/rate limit bằng tài khoản test. Coverage DAST có giới hạn, nên xác minh thủ công.
- **Scripts/Add-ons:** cài từ Marketplace/nguồn chính thức; xem quyền/mã nguồn khi khả thi; pin version trong automation. Script có thể gửi request tùy ý.

### 5.9 ZAP CLI/Docker: baseline passive và full scan trong lab

**Baseline scan** chạy traditional spider có thời lượng giới hạn rồi passive scan; không chủ động tấn công nhưng vẫn crawl/tạo traffic. Chỉ thay đích bằng lab của bạn.

~~~sh
docker pull ghcr.io/zaproxy/zaproxy:stable
mkdir -p zap-output
docker run --rm -t \
  -v "$PWD/zap-output:/zap/wrk/:rw" \
  ghcr.io/zaproxy/zaproxy:stable \
  zap-baseline.py -t http://host.docker.internal:8000 \
  -m 2 -r baseline.html -J baseline.json
~~~

host.docker.internal phổ biến trên Docker Desktop; Linux có thể cần cấu hình host gateway hoặc network chung. Không mở cổng ZAP API để khắc phục lỗi kết nối. Mount thư mục output cần thiết; report có thể nhạy cảm.

**Full scan** gồm spider, có thể thêm modern spider và active scan; có thể chạy lâu và làm thay đổi dữ liệu. Chỉ trong môi trường được phép, bản sao staging/localhost, tài khoản thử nghiệm và có backup/monitor. Đặt time limit, context/exclude, policy hạn chế và throttle. Cú pháp tham số thay đổi theo image; kiểm tra trang Full Scan chính thức.

~~~sh
docker run --rm -t \
  -v "$PWD/zap-output:/zap/wrk/:rw" \
  ghcr.io/zaproxy/zaproxy:stable \
  zap-full-scan.py -t http://host.docker.internal:8000 \
  -m 5 -r full-scan.html -J full-scan.json
~~~

Không chạy ví dụ full scan lên production. Exit code 0 không phải chứng nhận an toàn; exit code scripts phụ thuộc rules/config. Đặt alert threshold phù hợp trong CI và giữ artifact có access control.

### 5.10 API scan và OpenAPI

ZAP có packaged API scan cho OpenAPI/Swagger, GraphQL và một số API spec. Import schema giúp tìm endpoint không link từ UI, nhưng schema không mô tả đầy đủ role/business rules. Bỏ secret/example nhạy cảm khỏi spec; xác nhận server URL là lab; xác định auth header bằng secret injection; đặt rate/concurrency và loại trừ mutation có side effect. API active scan cũng gửi request thay đổi dữ liệu.

~~~sh
docker run --rm -t \
  -v "$PWD:/zap/wrk/:rw" \
  ghcr.io/zaproxy/zaproxy:stable \
  zap-api-scan.py -t /zap/wrk/openapi.yaml \
  -f openapi -r api-report.html
~~~

Xác minh usage theo image; schema local phải được mount. Tránh để token trong command line vì có thể lộ qua process list/log; dùng secret store trong CI.

### 5.11 Automation Framework (YAML)

Automation Framework (AF) mô tả environment, context, authentication, spider, passive wait, active scan và report trong YAML; chạy trong Desktop hoặc container. Bắt đầu crawl/passive, sau đó mới thêm active scan cho staging riêng.

Ví dụ skeleton **lab-only**:

~~~yaml
---
env:
  contexts:
    - name: local-lab
      urls:
        - http://host.docker.internal:8000
  parameters:
    failOnError: true
    progressToStdout: true
jobs:
  - type: spider
    parameters:
      context: local-lab
      maxDuration: 2
  - type: passiveScan-wait
  - type: report
    parameters:
      template: traditional-html
      reportDir: /zap/wrk
      reportFile: zap-report.html
~~~

Đây là khung: xác minh template/parameters với version/add-on hiện có; thêm exclude/auth/context regex theo ứng dụng. Chỉ thêm job activeScan sau khi scope kiểm tra. Lệnh container thường chạy zap.sh ở command mode với autorun YAML đã mount; xem [AF guide](https://www.zaproxy.org/docs/automate/automation-framework/) và tài liệu từng job.

Trong CI: pin container; giới hạn thời gian/tài nguyên; dùng test account; không ghi secret vào artifact/log; baseline trên pull request; active scan chỉ ở staging/nightly có kiểm soát. Gate trên rule đã triage; exception cần owner/hạn hết hạn; không tắt rule toàn cục chỉ để pipeline xanh.

### 5.12 Đọc alert và triage false positive

Mỗi alert nên có: (1) rule ID/name, risk/confidence, URL/method/parameter và evidence request/response đã xóa secret; (2) điều kiện tái hiện an toàn, role test và tác động; (3) trạng thái confirmed/likely/false positive/accepted risk/not applicable/manual test; (4) root cause, owner, severity nghiệp vụ, remediation, deadline và regression test; (5) kết quả re-scan cùng scope/version/add-ons.

Không hạ risk/ignore trước khi xác minh. Alert Filters che kết quả, không vá lỗi. Nếu dùng filter, ghi lý do, URL/context chính xác, owner và hạn review.

### 5.13 Xuất báo cáo và dọn phiên

- Xuất HTML/JSON/XML/Markdown phù hợp người nhận; giới hạn report vào context/site cần thiết.
- Xóa cookie, Authorization header, password-reset URL, PII và dữ liệu bí mật trước khi chia sẻ.
- Ghi version ZAP/add-ons, target build, scope, role, thời gian, policy, spider, giới hạn tốc độ và phần chưa kiểm tra.
- Giữ session chỉ khi cần tái hiện; mã hóa/giới hạn quyền và đặt hạn xóa.
- Xóa test data/profile/certificate test; xác nhận không còn scan chạy nền.

## 6. Quy trình kiểm thử gợi ý

| Giai đoạn | Việc làm | Kết quả cần giữ |
|---|---|---|
| Chuẩn bị | Scope bằng văn bản, staging/lab, backup, test accounts, side effects off, liên hệ | Scope, owner, thời gian, điều kiện dừng |
| Khám phá | Manual Explore theo role; import OpenAPI; spider phù hợp app | URL/API inventory, role coverage, luồng nghiệp vụ |
| Phân tích | Passive scan; header/TLS/cookie; dependency/config review | Alert đã triage, version evidence, gaps |
| Kiểm thử chủ động | Chỉ lab/staging; policy/throttle/time limit; loại thao tác ghi | Evidence tối thiểu, server logs, scan config |
| Kiểm thử logic | Hai user/tenant/role test; state transition; abuse case | BOLA/IDOR, workflow, authorization |
| Vá và hồi quy | Sửa gốc; unit/integration tests; scan lại; kiểm tra logs | Diff, test, re-scan, ticket đã xử lý |

## 7. Tài liệu và nguồn chính

Ưu tiên tài liệu gốc. Living docs cần được mở lại trước mỗi đợt học/triage.

### OWASP

- [OWASP Top 10:2025](https://top10.owasp.org/2025/)
- [OWASP Developer Guide — Top 10](https://devguide.owasp.org/en/02-foundations/05-top-ten/)
- [OWASP ASVS 5.0.0](https://asvs.owasp.org/) — yêu cầu kiểm chứng kỹ thuật
- [OWASP Web Security Testing Guide](https://owasp.org/www-project-web-security-testing-guide/)
- [OWASP API Security Top 10:2023](https://owasp.org/API-Security/editions/2023/en/0x11-t10/)
- [OWASP Cheat Sheet Series](https://cheatsheetseries.owasp.org/) — [XSS Prevention](https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html), [CSRF Prevention](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html), [SQL Injection Prevention](https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html), [SSRF Prevention](https://cheatsheetseries.owasp.org/cheatsheets/Server_Side_Request_Forgery_Prevention_Cheat_Sheet.html), [File Upload](https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html), [Session Management](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html)
- [OWASP GenAI Security Project](https://genai.owasp.org/) — rủi ro LLM và agentic applications

### OWASP ZAP

- [ZAP Download](https://www.zaproxy.org/download/), [Getting Started](https://www.zaproxy.org/docs/desktop/start/), [Quick Start](https://www.zaproxy.org/docs/desktop/addons/quick-start/)
- [Modes and scope safety](https://www.zaproxy.org/docs/desktop/start/features/modes/), [Basic penetration test workflow](https://www.zaproxy.org/docs/desktop/start/pentest/), [Active Scan limitations and safety](https://www.zaproxy.org/docs/desktop/start/features/ascan/)
- [Contexts](https://www.zaproxy.org/docs/desktop/start/features/contexts/), [Authentication](https://www.zaproxy.org/docs/desktop/start/features/authentication/), [Authentication methods](https://www.zaproxy.org/docs/desktop/start/features/authmethods/)
- [Automation Framework](https://www.zaproxy.org/docs/automate/automation-framework/)
- [Docker guide](https://www.zaproxy.org/docs/docker/), [Baseline](https://www.zaproxy.org/docs/docker/baseline-scan/), [Full scan](https://www.zaproxy.org/docs/docker/full-scan/), [API scan](https://www.zaproxy.org/docs/docker/api-scan/)
- [Alerts catalogue](https://www.zaproxy.org/docs/alerts/), [Report generation](https://www.zaproxy.org/docs/desktop/addons/report-generation/)

### Advisory và tiêu chuẩn

- [F5 security notification](https://my.f5.com/manage/s/article/K000164058)
- [PHP official security release archive](https://www.php.net/archive/2026.php)
- [Next.js security advisories](https://github.com/vercel/next.js/security/advisories)
- [NIST National Vulnerability Database](https://nvd.nist.gov/) — tra cứu CVE, luôn đối chiếu vendor advisory
