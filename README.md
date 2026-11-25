# Web Security Cheatsheet (Tiếng Việt)

> Tài liệu học và tham khảo theo hướng phòng thủ. Chỉ kiểm thử hệ thống do bạn sở hữu hoặc có văn bản cho phép; ưu tiên lab localhost và môi trường staging đã sao lưu.

## Nội dung

- [Phần 1 — OWASP, lỗ hổng web và OWASP ZAP](01-owasp-web-security-zap.md)
- [Phần 2 — Vá lỗi trong ứng dụng, Nginx và Apache](02-patching-source-nginx-apache.md)
- [Phần 3 — Hiểu và giải lab FCTF cục bộ](03-understand-and-solve-local-lab.md)
- [Phần 4 — Tắt Daybreak trong Codex CLI](04-tat-daybreak-codex-cli.md)

Script giải và nộp flag chỉ kết nối tới FCTF local lab trên 127.0.0.1: [solve_local_lab.py](scripts/solve_local_lab.py).

## Phạm vi và cách đọc

Cheatsheet giải thích khái niệm, dấu hiệu, kiểm tra an toàn, cách khắc phục và giới hạn của công cụ. Ví dụ cấu hình là điểm khởi đầu: cần điều chỉnh theo framework, phiên bản, kiến trúc, chính sách cookie/CORS và nhu cầu nghiệp vụ. Không chạy active scan, fuzzing hay forced browse trên mục tiêu ngoài phạm vi được phép.

## Nguồn

Tài liệu tham chiếu phiên bản chính thức mới nhất có thể xác minh tại ngày 25-11-2026. Mục lục nguồn cụ thể nằm cuối từng phần. Advisory CVE thay đổi theo thời gian; luôn mở advisory của nhà phát hành và kiểm tra bản vá tương ứng với nhánh đang dùng.
