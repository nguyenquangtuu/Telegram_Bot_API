# Go Absent - Telegram Bot API

> Hệ thống tạo đơn xin nghỉ phép qua Telegram Bot và quản lý trên Website.

* 📊 **Slide:** [canva.link/ev4ftw6igngtc9z](https://canva.link/ev4ftw6igngtc9z)

---

## ⚙️ Cấu hình Bot & `.env`

1. Truy cập [**@BotFather**](https://t.me/BotFather) trên Telegram ➔ gửi `/newbot` làm theo hướng dẫn để lấy `BOT_TOKEN`.
2. Tạo file **`.env`** (hoặc sao chép từ `.env.example`):
```env
BOT_TOKEN=token_lay_tu_BotFather
WEB_PORT=5000
```

---

## ⚡ Khởi chạy ứng dụng ⭐

**Click đúp vào file `start.bat`**:
* Tự động cài đặt thư viện (`requirements.txt`).
* Tự động mở cửa sổ **Ngrok Tunnel** lấy link HTTPS.
* Tự động khởi chạy **Web Dashboard & Telegram Bot**.
* 🌐 Mở link HTTPS của Ngrok trên trình duyệt ➔ Bấm nút **Webhook** ➔ Bấm **Lưu Webhook**.

<details>
<summary>🛠️ <i>Hoặc khởi chạy thủ công bằng dòng lệnh (Click để mở)</i></summary>
<br>

```bash
# 1. Cài thư viện Python
pip install -r requirements.txt

# 2. Khởi chạy ứng dụng
python app.py

# 3. Mở tunnel Ngrok nhận Webhook (Mở cửa sổ dòng lệnh mới)
winget install ngrok    # Cài nếu máy chưa có
ngrok http 5000
```
</details>
