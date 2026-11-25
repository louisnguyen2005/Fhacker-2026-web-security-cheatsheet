# Web Security Cheatsheet (Tiếng Việt)

> Tài liệu học và tham khảo theo hướng phòng thủ. Chỉ kiểm thử hệ thống do bạn sở hữu hoặc có văn bản cho phép; ưu tiên lab localhost và môi trường staging đã sao lưu.

## Nội dung

- [Phần 1 — OWASP, lỗ hổng web và OWASP ZAP](01-owasp-web-security-zap.md)
- [Phần 2 — Vá lỗi trong ứng dụng, Nginx và Apache](02-patching-source-nginx-apache.md)

## Phạm vi và cách đọc

Cheatsheet giải thích khái niệm, dấu hiệu, kiểm tra an toàn, cách khắc phục và giới hạn của công cụ. Ví dụ cấu hình là điểm khởi đầu: cần điều chỉnh theo framework, phiên bản, kiến trúc, chính sách cookie/CORS và nhu cầu nghiệp vụ. Không chạy active scan, fuzzing hay forced browse trên mục tiêu ngoài phạm vi được phép.

## Nguồn

Tài liệu tham chiếu phiên bản chính thức mới nhất có thể xác minh tại ngày 25-11-2026. Mục lục nguồn cụ thể nằm cuối từng phần. Advisory CVE thay đổi theo thời gian; luôn mở advisory của nhà phát hành và kiểm tra bản vá tương ứng với nhánh đang dùng.
