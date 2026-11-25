# Phần 2 — Vá lỗi trong source, Nginx và Apache

**Cập nhật nguồn: 25-11-2026.** Phần này hướng dẫn sửa nguyên nhân trong ứng dụng, sau đó gia cố reverse proxy/web server. Reverse proxy có thể giảm một số tác động, nhưng không thay thế authorization, validation, encoding hoặc cập nhật dependency trong ứng dụng.

## 1. Thứ tự vá một lỗi

1. **Xác nhận thành phần và đường chạy:** framework/runtime/package, phiên bản thực sự ở production, route bị ảnh hưởng, proxy/CDN, feature flag và role cần thiết.
2. **Ưu tiên containment an toàn:** tắt endpoint/feature bị ảnh hưởng hoặc áp dụng vendor workaround chỉ khi hiểu hậu quả; ghi thời hạn và owner. Không dùng rule WAF làm lý do trì hoãn bản vá.
3. **Sửa nguyên nhân gốc:** vá source hoặc nâng package; review diff; không chỉ lọc một chuỗi payload.
4. **Thêm hồi quy:** test case âm/dương cho authorization, dữ liệu test, trạng thái lỗi, quyền user khác và boundary conditions.
5. **Deploy có kiểm soát:** kiểm tra staging, canary nếu phù hợp, theo dõi lỗi/latency/logs, có rollback.
6. **Xác nhận sau deploy:** kiểm tra artifact/version trên mọi node/container, response/config sau CDN, scan lại trong scope được phép.
7. **Ghi lại:** CVE/alert, nguyên nhân, phiên bản trước/sau, test, rollout, exception và ngày hết hạn.

Với CVE, ưu tiên hướng dẫn maintainer và distro package. Version hiển thị có thể chưa phản ánh backport của OS; xác nhận bằng changelog/package advisory. Đổi banner hoặc ẩn version không vá lỗi.

## 2. Vá source ứng dụng

Ví dụ SQL dùng Python/SQLite; pseudocode cho framework khác phải chuyển sang API an toàn tương đương. Mẫu không phải bản vá tự động cho mọi dự án.

### 2.1 SQL injection và query động

**Không an toàn:**

~~~python
sql = f"SELECT title, body FROM notes WHERE title LIKE '%{query}%' AND is_public = 1"
rows = db.execute(sql).fetchall()
~~~

**An toàn hơn:**

~~~python
query = query[:100]
rows = db.execute(
    "SELECT title, body FROM notes WHERE title LIKE ? AND is_public = 1 LIMIT ?",
    (f"%{query}%", 50),
).fetchall()
~~~

Driver bind giá trị như dữ liệu, không phải cú pháp SQL. Giới hạn độ dài/kết quả để kiểm soát tài nguyên. Nếu tìm kiếm cần coi dấu % và _ là ký tự thường, escape chúng theo quy tắc LIKE của database rồi chỉ thêm wildcard do ứng dụng tạo. Tên bảng/cột/sort direction không thể bind như value: ánh xạ lựa chọn người dùng sang tập hằng do code sở hữu.

**Hồi quy:** input có dấu nháy/Unicode/chuỗi dài không làm đổi cấu trúc query; kết quả chỉ chứa record phù hợp; giới hạn query được áp dụng; không còn nối input vào SQL. Không kiểm chứng bằng cách lấy dữ liệu bí mật.

### 2.2 XSS: encode theo đúng nơi hiển thị

- Dùng framework template có auto-escape mặc định. Tránh tắt escape hoặc đánh dấu input là HTML tin cậy bằng helper như safe/raw/dangerouslySetInnerHTML nếu không có lý do và sanitizer.
- Với DOM, dùng API gán text (ví dụ textContent) thay vì parse chuỗi không tin cậy bằng innerHTML. URL cần allowlist scheme; chặn javascript: và scheme không cần thiết.
- Nếu sản phẩm cần rich text, dùng sanitizer HTML đang được duy trì, cấu hình allowlist tag/attribute nhỏ và cập nhật định kỳ. Encoding không phải sanitizer: chọn đúng thao tác theo context (HTML body, attribute, URL, JavaScript, CSS).
- Thêm CSP theo chế độ Report-Only, quan sát vi phạm, sửa dependency/inline script hợp lệ rồi mới enforce. Trusted Types có thể hạn chế DOM sinks ở browser hỗ trợ; không tự sanitize và policy quá rộng làm mất tác dụng.
- Regression test mỗi context; không coi một payload hoặc một header là bằng chứng đã xử lý mọi XSS.

### 2.3 CSRF và thao tác thay đổi trạng thái

- Dùng middleware CSRF của framework cho form/session cookie. Token cần gắn với session và được kiểm tra server-side; không nhận token chỉ vì xuất hiện ở URL hoặc được gắn vào mọi request bằng header mặc định.
- Không dùng GET để chuyển tiền, đổi email, xóa hoặc thay đổi trạng thái.
- Cookie SameSite là defense-in-depth, không thay token trong ứng dụng dùng cookie/session. Xem xét kiểm tra Origin/Referer cho request nhạy cảm theo môi trường/proxy.
- API dùng bearer token không tự động chịu cùng mô hình CSRF như cookie, nhưng vẫn cần bảo vệ token, CORS chính xác, quyền từng route và chống XSS.
- Test bằng hai origin test và tài khoản giả; request thiếu/sai token bị từ chối, request hợp lệ vẫn hoạt động.

### 2.4 BOLA/IDOR và phân quyền

Sai lầm phổ biến là chỉ xác thực đã đăng nhập rồi truy vấn record theo ID client cung cấp.

~~~python
# Principal lấy từ middleware xác thực, không từ request body.
record = repository.get_owned_record(
    record_id=requested_id,
    owner_id=current_principal.user_id,
)
if record is None:
    return not_found()
return render_record(record)
~~~

Hoặc load object rồi gọi policy/service như authorize(principal, action, object) trước khi trả/ghi dữ liệu. Kiểm tra quyền phía server tại mọi endpoint và từng object/property; owner/tenant lấy từ danh tính đã xác thực, không tin giá trị client. Dùng cùng policy cho UI/API/background job. Thống nhất 403/404 theo chính sách chống enumeration, nhưng 404 không thay kiểm tra quyền.

**Regression matrix:** user A đọc/sửa object A thành công; B không đọc/sửa object A; user thường không gọi admin action; tenant khác không truy cập record; field nhạy cảm không thể tự gán; background export áp dụng policy.

### 2.5 Upload an toàn

- Allowlist phần mở rộng cần thiết; kiểm tra signature/content phía server thay vì tin MIME từ browser. Loại file hai nghĩa và tên có path separator; giới hạn kích thước, số file, quota và thời gian xử lý.
- Tạo tên storage mới từ ID ngẫu nhiên do ứng dụng sinh; tên gốc chỉ lưu dạng metadata đã encode. Không nối tên client vào filesystem path.
- Lưu ngoài webroot hoặc bucket private; mặc định không execute và không serve dưới origin tin cậy nếu không cần. Download qua handler kiểm tra quyền, dùng Content-Disposition/Content-Type phù hợp và nosniff.
- Nếu giải nén archive, giới hạn số entry/kích thước sau giải nén/độ sâu; ngăn path traversal và symlink. Nếu cần, quét malware/CDR trong vùng cách ly; scanner không thay thế kiểm soát quyền và storage isolation.
- Dùng state machine: nhận vào quarantine → kiểm tra → publish; không cho người dùng khác truy cập trước khi kiểm tra hoàn tất.
- Test: file hợp lệ được nhận; extension kép/MIME giả/tên path/oversize/archive bất thường bị từ chối; file lưu không execute; user khác không tải được.

### 2.6 SSRF và URL do người dùng cung cấp

Thiết kế tốt nhất là không nhận URL tùy ý nếu nghiệp vụ chỉ cần một số provider đã biết. Dùng allowlist hostname/scheme; parse URL bằng thư viện chuẩn; resolve DNS và kiểm tra mọi IP trả về; chặn loopback/private/link-local/multicast/reserved; xử lý redirect (tốt nhất tắt hoặc kiểm tra từng hop); chống DNS rebinding bằng cách ràng buộc kết nối tới IP đã kiểm tra; giới hạn egress ở network/firewall; giới hạn timeout, response size và content type. Kiểm tra chuỗi URL đơn lẻ không đủ vì encoding, DNS và redirect.

Không xây URL sanitizer ad hoc hoặc xác minh SSRF bằng cách gọi metadata service. Dùng mock server trong lab, kiểm thử allowlist/redirect/block và theo dõi outbound egress.

### 2.7 Authentication, password và session

- Dùng identity provider hoặc thư viện framework được duy trì. Lưu mật khẩu bằng password-hashing algorithm chuyên dụng với salt/cost phù hợp; không dùng SHA-256 thông thường cho password.
- Reset password dùng token ngẫu nhiên, một lần, hết hạn, gắn đúng user/mục đích; phản hồi gửi reset không tiết lộ tài khoản tồn tại hay không.
- Xoay session ID sau login, MFA và nâng quyền; hủy phiên cũ khi logout, reset password hoặc thu hồi quyền. Cookie session: Secure, HttpOnly, SameSite phù hợp; không đặt Domain rộng nếu không cần.
- Rate limit theo account và tín hiệu phù hợp, có backoff/monitoring tránh biến thành DoS cho nạn nhân; MFA/passkey cho hành động rủi ro cao.
- Không ghi password, token, cookie hay mã recovery vào log.

### 2.8 Error handling, logging và exceptional conditions

- Trả lỗi chung cho client; giữ chi tiết điều tra trong log có access control, nhưng redact secret/PII.
- Phân biệt lỗi xác thực, authorization, validation, dependency timeout và lỗi nội bộ; không fail-open khi policy service/DB lỗi.
- Giới hạn request size, query cost, concurrency, timeout và retry; dùng bounded queue/circuit breaker cho dependency; retry thao tác có idempotency key.
- Đặt cleanup/rollback trong finally/context manager/transaction; test khi timeout, DB không sẵn sàng, disk/quota cạn và upstream trả lỗi.
- Log sự kiện audit có actor, action, object identifier ở mức tối thiểu, kết quả, timestamp và correlation ID; bảo vệ log khỏi sửa/xóa; không log toàn request body nếu có dữ liệu nhạy cảm.

### 2.9 Dependency và secret

- Bật lockfile, dependency update review, SCA và SBOM. Nâng phiên bản đã vá theo advisory maintainer; kiểm tra dependency bắc cầu và artifact/container đã build lại.
- Nếu secret từng commit: xóa khỏi source không đủ. Thu hồi/rotate secret, kiểm tra log/usage, rồi loại khỏi Git history theo quy trình tổ chức.
- CI token chỉ có quyền cần thiết; tách build/test/deploy, dùng protected environment và review release. Verify artifact provenance/signature nếu hỗ trợ.
- Với framework/runtime có advisory, inventory từng service/container; “latest” không đảm bảo mọi image đang chạy đã cập nhật.

## 3. Nginx — hardening reverse proxy

Các ví dụ là khung tham khảo cho app phía sau Nginx. Thay hostname, certificate, upstream, giới hạn body và rate theo workload. Cú pháp/module có thể khác giữa NGINX Open Source, Plus, ingress controller và distro package.

### 3.1 HTTPS, redirect và virtual host

~~~nginx
http {
    server_tokens off;

    # Default host không phục vụ nội dung ứng dụng.
    server {
        listen 80 default_server;
        server_name _;
        return 444;
    }

    server {
        listen 80;
        server_name app.example.test;
        return 301 https://app.example.test$request_uri;
    }

    server {
        listen 443 ssl;
        server_name app.example.test;
        ssl_certificate     /etc/ssl/certs/app-chain.pem;
        ssl_certificate_key /etc/ssl/private/app-key.pem;
        ssl_protocols TLSv1.2 TLSv1.3;

        # Chỉ bật HSTS khi HTTPS hoạt động đúng trên host này.
        add_header Strict-Transport-Security "max-age=31536000" always;
    }
}
~~~

444 là hành vi riêng của Nginx để đóng kết nối, không phải status HTTP chuẩn; có thể chọn default server khác theo vận hành. Redirect dùng canonical hostname cố định, tránh tạo open redirect từ Host header. Chỉ thêm includeSubDomains/preload vào HSTS khi mọi subdomain bắt buộc HTTPS và đã kiểm kê ảnh hưởng; HSTS có thể làm app HTTP-only không truy cập được trong thời gian dài.

Bảo vệ private key bằng quyền file tối thiểu, không commit key vào repo/image. TLS tốt không vá lỗi parser/proxy trong binary.

### 3.2 Security headers và CSP

~~~nginx
server {
    # ... listen 443 ssl; server_name; certificates ...
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header X-Frame-Options "DENY" always;
    add_header Permissions-Policy "camera=(), microphone=(), geolocation=()" always;

    # Bắt đầu Report-Only, thu thập vi phạm rồi tinh chỉnh policy.
    add_header Content-Security-Policy-Report-Only "default-src 'self'; object-src 'none'; base-uri 'self'; frame-ancestors 'none'" always;
}
~~~

Đây là baseline mẫu, không phải policy dùng nguyên trạng cho mọi website. X-Frame-Options DENY không phù hợp nếu trang phải được nhúng; điều chỉnh theo nghiệp vụ. CSP thường cần nonce/hash và allowlist cho scripts/styles/API/font/frame; default-src self có thể làm hỏng chức năng. Không bật unsafe-inline chỉ để hết lỗi nếu có thể chuyển sang nonce/hash. Khi policy đã quan sát/thử trên app, đổi Report-Only thành Content-Security-Policy từng bước.

**Bẫy kế thừa Nginx:** mặc định, add_header ở block con chỉ kế thừa từ cấp cha nếu block con không khai báo bất kỳ add_header nào. Một location thêm Cache-Control có thể làm mất security headers cấp server. NGINX từ 1.29.3 có add_header_inherit merge; trên bản cũ, lặp include header trong các block cần thiết hoặc thiết kế cấu hình không tạo block con ghi đè. Tránh phát cùng header hai lần; kiểm tra response tại từng location/status.

### 3.3 Reverse proxy và ranh giới header

~~~nginx
location / {
    proxy_pass http://application_upstream;
    proxy_http_version 1.1;
    proxy_set_header Host app.example.test;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
~~~

Ứng dụng chỉ được tin forwarded headers từ proxy do bạn quản lý. Nếu Nginx nằm sau CDN/load balancer, cấu hình real-IP chỉ cho CIDR proxy tin cậy; nếu không, client có thể giả IP và làm sai audit/rate limit. Host allowlist ở app và web server; proxy không tự đảm bảo authorization. Tránh forward header nội bộ/authentication không cần thiết.

### 3.4 Giới hạn tài nguyên và rate limit

~~~nginx
http {
    limit_req_zone $binary_remote_addr zone=login_limit:10m rate=5r/m;

    server {
        client_max_body_size 10m;
        client_header_timeout 10s;
        client_body_timeout 30s;

        location = /login {
            limit_req zone=login_limit burst=5 nodelay;
            proxy_pass http://application_upstream;
        }
    }
}
~~~

Rate limit IP chỉ là lớp bổ sung: NAT, IPv6, proxy chain và nhiều user chung IP ảnh hưởng kết quả. Khi sau CDN, key phải lấy từ real-IP đã xác thực. Chọn ngưỡng từ traffic hợp lệ; dùng dry-run nếu hỗ trợ trước khi chặn. Rate limit login không thay controls trong app. Giới hạn body phải đồng bộ với framework, body parser và object storage. Không đặt client_max_body_size bằng 0 vì điều đó vô hiệu giới hạn.

### 3.5 Tệp nhạy cảm, upload và static content

Không đặt .env, .git, backup, source map private, config hoặc upload có thể thực thi trong document root. Deny rules là lớp bổ sung:

~~~nginx
location ~ /\.(?!well-known/) {
    deny all;
}

location /uploads/ {
    # Chỉ nếu public download là yêu cầu; upload private nên qua app auth.
    autoindex off;
    types { }
    default_type application/octet-stream;
    add_header X-Content-Type-Options nosniff always;
}
~~~

Static upload tốt nhất nằm trên origin/bucket riêng, không có cookie phiên và không thực thi script. Nginx rule không thay việc lưu ngoài webroot, kiểm tra quyền download và đổi tên file trong ứng dụng. Nếu MIME override gây không tương thích, kiểm thử download và đặt Content-Type/Content-Disposition cụ thể.

### 3.6 Kiểm tra cấu hình và vận hành

Trước reload: review diff, dùng nginx -t, xác minh binary/package/module. Reload có kiểm soát; kiểm tra response headers trên trang thường, lỗi 4xx/5xx, redirect, file tĩnh, API, upload và upstream. Kiểm tra log không ghi secret. Nginx server_tokens off chỉ giảm lộ version qua một số response; phải cập nhật package để vá CVE.

## 4. Apache HTTP Server 2.4 — hardening VirtualHost

Các directive cần module phù hợp (mod_ssl, mod_headers, mod_alias, mod_reqtimeout). Xác nhận module đã nạp và cú pháp trong phiên bản/distro hiện dùng.

### 4.1 Redirect HTTPS và TLS

~~~apache
<VirtualHost *:80>
    ServerName app.example.test
    Redirect permanent / https://app.example.test/
</VirtualHost>

<VirtualHost *:443>
    ServerName app.example.test
    DocumentRoot /srv/www/app/public
    SSLEngine on
    SSLCertificateFile /etc/ssl/certs/app-chain.pem
    SSLCertificateKeyFile /etc/ssl/private/app-key.pem
    SSLProtocol TLSv1.2 TLSv1.3

    # Chỉ bật sau khi HTTPS đã được xác minh trên host này.
    Header always set Strict-Transport-Security "max-age=31536000"
</VirtualHost>
~~~

Redirect dùng hostname canonical cố định để tránh open redirect qua Host header. Không thêm HSTS includeSubDomains/preload nếu chưa xác nhận toàn bộ subdomain dùng HTTPS. Private key phải được bảo vệ và không nằm trong webroot.

### 4.2 Headers

~~~apache
<VirtualHost *:443>
    # ... TLS và app config ...
    Header always set X-Content-Type-Options "nosniff"
    Header always set Referrer-Policy "strict-origin-when-cross-origin"
    Header always set X-Frame-Options "DENY"
    Header always set Permissions-Policy "camera=(), microphone=(), geolocation=()"

    # Theo dõi report trước khi enforce; điều chỉnh theo frontend.
    Header always set Content-Security-Policy-Report-Only "default-src 'self'; object-src 'none'; base-uri 'self'; frame-ancestors 'none'"
</VirtualHost>
~~~

Header always hữu ích với redirect/error response nhưng onsuccess và always là hai bảng headers riêng trong Apache. Nếu backend (CGI/FastCGI/proxy) đã đặt cùng header, response có thể lặp. Kiểm tra response thật; với header từ handler, tài liệu mod_headers mô tả pattern unset trong bảng onsuccess rồi set trong always. Đừng xóa header của app nếu chưa biết nguồn. HSTS chỉ gửi qua HTTPS. CSP bắt đầu Report-Only và phải thử trên luồng hợp lệ.

### 4.3 Từ chối file cấu hình, source control và directory listing

~~~apache
<Directory "/srv/www/app/public">
    Options -Indexes
    AllowOverride None
    Require all granted
</Directory>

<FilesMatch "^(?:\.env(?:\..*)?|\.htaccess|\.htpasswd|composer\.(?:json|lock)|package-lock\.json|.*\.(?:bak|old|orig|swp))$">
    Require all denied
</FilesMatch>

<DirectoryMatch "(?:^|/)\.git(?:/|$)">
    Require all denied
</DirectoryMatch>
~~~

Thay document root bằng public directory tối thiểu. Nếu app cần .htaccess, hiểu và giới hạn AllowOverride đúng mức thay vì bật mọi override. Rule là lớp phụ: secret/source/backup không nên nằm trong webroot. Dùng Options -Indexes; tắt Includes/ExecCGI nếu app không cần nhưng kiểm tra ảnh hưởng module.

### 4.4 Giới hạn request và thời gian chờ

~~~apache
<VirtualHost *:443>
    # Chọn theo nhu cầu app và đồng bộ với body parser.
    LimitRequestBody 10485760
    RequestReadTimeout header=20-40,MinRate=500 body=20,MinRate=500
</VirtualHost>
~~~

mod_reqtimeout phải bật để dùng RequestReadTimeout. Thời gian quá thấp gây lỗi người dùng mạng chậm/upload hợp lệ; thử trên workload thật. LimitRequestFields, LimitRequestFieldSize, LimitRequestLine, Timeout, KeepAliveTimeout và MaxRequestWorkers cần chọn theo traffic, app và tài nguyên; không sao chép giá trị cực nhỏ mà chưa đo. Giới hạn Apache không thay giới hạn framework/upstream.

### 4.5 Logging và version disclosure

Giữ access/error logs có thời gian lưu, phân quyền và đồng bộ giờ; không ghi Authorization/Cookie/password/body nhạy cảm. Apache có thể giảm thông tin Server header bằng ServerTokens Prod và ServerSignature Off, nhưng đây không phải bản vá và không ẩn mọi dấu hiệu version. Cập nhật Apache, OpenSSL, modules, OS package và runtime. Bảo vệ log khỏi URL và khỏi process người dùng có thể sửa.

## 5. Kiểm tra cấu hình sau khi sửa

### Nginx

1. nginx -t xác nhận syntax; review nginx -T ở máy có quyền để hiểu config hiệu lực, không gửi output chứa đường dẫn/secret lên ticket công khai.
2. Kiểm tra HTTP redirect dùng hostname cố định và unknown Host không vào app.
3. Qua HTTPS xác nhận certificate chain, TLS policy, cookie/headers trên 2xx/3xx/4xx/5xx.
4. Kiểm tra location lồng nhau không làm rơi add_header; xem headers thực nhận sau CDN/load balancer.
5. Thử body ngay dưới/trên giới hạn bằng dữ liệu giả; xác nhận proxy/app xử lý lỗi có kiểm soát.
6. Xác nhận real client IP chỉ được tin từ proxy CIDR đã cấu hình; xem access/error logs đã redact.

### Apache

1. apachectl configtest (hoặc httpd -t theo distro) và xác minh module cần thiết đã bật.
2. Kiểm tra redirect, unknown Host, certificate, TLS và security headers.
3. Kiểm tra không truy cập được .env, .git, backup và directory listing; public asset hợp lệ vẫn hoạt động.
4. Kiểm tra header trùng từ backend/FastCGI và lỗi 4xx/5xx; xác minh sau proxy/CDN.
5. Thử upload/body/timeouts trên staging; xem log, error rate và worker pressure.

Không chạy active check trên production nếu chưa có phê duyệt/phương án vận hành. Với CSP, HSTS, CORS, rate limit hoặc body size, rollout theo giai đoạn và theo dõi ảnh hưởng chức năng.

## 6. Bảng ghép lỗi → nơi vá → bằng chứng hồi quy

| Lỗi | Vá chính trong source | Hardening hạ tầng | Hồi quy tối thiểu |
|---|---|---|---|
| SQL/NoSQL injection | Parameterized query/safe API; allowlist cấu trúc | DB least privilege/isolation; proxy không sửa query | Input lạ vẫn là dữ liệu; DB role không đọc bảng ngoài quyền |
| XSS | Auto-escape, output encoding theo context, safe DOM/sanitizer | CSP Report-Only rồi enforce, nosniff, isolate user content origin | HTML/attribute/URL/DOM render đúng; chức năng hợp lệ còn chạy |
| CSRF | CSRF middleware/token; state-changing không dùng GET | Cookie Secure/SameSite; CORS chính xác | Request test thiếu token bị từ chối |
| BOLA/IDOR | Authorization per object/property/function | Log/audit, segmentation hỗ trợ | User/tenant khác không đọc/ghi object |
| SSRF | URL allowlist, resolve/redirect checks, egress control | Egress firewall/proxy | Mock URL allowlisted chạy; private/redirect không được gọi |
| Upload | Validate, rename, quarantine/private storage, download auth | Body cap, static origin riêng, không serve executable | File lỗi/oversize bị chặn; user khác không tải; app không execute |
| CVE runtime/framework | Nâng package/runtime và rebuild artifact | Inventory, rollout, vendor workaround tạm thời | Mọi node/image chạy bản đã vá; smoke test qua |
| Config disclosure | Đưa secret/config ra khỏi public path/build | Deny sensitive files, no index, TLS/key permissions | .env/.git/backup bị từ chối; headers không lộ dư thừa |
| Resource exhaustion | Bound query, page size, timeout, queue, retry/idempotency | Request limits, rate limit, timeouts | Request vượt ngưỡng bị từ chối có kiểm soát |
| Error/logging | Fail closed; lỗi chung; audit/redaction | Access-controlled logs, request limits, alert routing | Dependency lỗi không mở quyền; log không chứa secret |

## 7. Nguồn chính thức

### OWASP và coding

- [OWASP Top 10:2025](https://top10.owasp.org/2025/)
- [ASVS 5.0.0](https://asvs.owasp.org/)
- [XSS Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html)
- [CSRF Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html)
- [SQL Injection Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html)
- [File Upload Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html)
- [SSRF Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Server_Side_Request_Forgery_Prevention_Cheat_Sheet.html)
- [Session Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html)

### Nginx

- [Nginx HTTPS servers](https://nginx.org/en/docs/http/configuring_https_servers.html)
- [Nginx SSL module](https://nginx.org/en/docs/http/ngx_http_ssl_module.html)
- [Nginx response headers and add_header inheritance](https://nginx.org/en/docs/http/ngx_http_headers_module.html)
- [Nginx proxy module and forwarded headers](https://nginx.org/en/docs/http/ngx_http_proxy_module.html)
- [Nginx request limits and server_tokens](https://nginx.org/en/docs/http/ngx_http_core_module.html)
- [Nginx request rate limiting](https://nginx.org/en/docs/http/ngx_http_limit_req_module.html)
- [F5 November 2026 security notification](https://my.f5.com/manage/s/article/K000164058)

### Apache

- [Apache Security Tips](https://httpd.apache.org/docs/2.4/en/misc/security_tips.html)
- [Apache mod_headers](https://httpd.apache.org/docs/2.4/mod/mod_headers.html)
- [Apache mod_ssl and SSLProtocol](https://httpd.apache.org/docs/2.4/mod/mod_ssl.html)
- [Apache mod_reqtimeout](https://httpd.apache.org/docs/2.4/mod/mod_reqtimeout.html)
- [Apache core request limits](https://httpd.apache.org/docs/2.4/mod/core.html)

### Current framework/runtime advisories

- [PHP security releases](https://www.php.net/archive/2026.php)
- [Next.js security advisories](https://github.com/vercel/next.js/security/advisories)
- [NIST NVD](https://nvd.nist.gov/) — tra cứu và đối chiếu CVE với advisory nhà phát hành/distro
