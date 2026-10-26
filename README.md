# Go Absent - Telegram Bot API

> Hệ thống tạo đơn xin nghỉ phép qua Telegram Bot và quản lý trên Website.

* 📊 **Slide:** [canva.link/ev4ftw6igngtc9z](https://canva.link/ev4ftw6igngtc9z)

---

## 📋 Chuẩn bị

* **Python 3.8+** (tick chọn *Add to PATH* khi cài): [Tải Python](https://www.python.org/downloads/)
* **Telegram Bot Token**: [Hướng dẫn tạo Bot](#huong-dan-tao-bot) 
* **Ngrok**: [Tải Ngrok](https://dashboard.ngrok.com/get-started/setup)

---

## ⚙️ Cấu hình `.env`

Tạo file **`.env`** tại thư mục gốc (hoặc sao chép từ `.env.example`):

```env
BOT_TOKEN=token_lay_tu_BotFather
WEB_PORT=5000
```

---

## ⚡ Khởi chạy ứng dụng ⭐

Chỉ cần **nhấp đúp vào file `start.bat`**, hệ thống sẽ hiển thị các tùy chọn để bạn lựa chọn.

* **[1] Dùng GetUpdates lấy sự kiện mới**
* **[2] Nhận Webhook qua NGROK**

<details>
<summary>🛠️ <i>Hoặc khởi chạy thủ công bằng dòng lệnh (Click để mở)</i></summary>
<br>

```bash
# 1. Cài thư viện Python
pip install -r requirements.txt

# 2. Khởi chạy chế độ Localhost (GetUpdates)
python app.py --mode=polling

# Hoặc khởi chạy chế độ NGROK (Webhook)
python app.py --mode=webhook
# Đồng thời mở ngrok ở cửa sổ riêng:
ngrok http 5000
```
</details>

---

<a id="huong-dan-tao-bot"></a>
## 🤖 Hướng dẫn tạo Telegram Bot & lấy Token

| Bước | Thao tác | Chi tiết |
| :---: | :--- | :--- |
| **1** | Mở chat với [**@BotFather**](https://t.me/BotFather) | Nhấn **Start** để bắt đầu trò chuyện |
| **2** | Gửi lệnh `/newbot` | Khởi tạo tiến trình tạo bot mới |
| **3** | Nhập **Tên hiển thị** (Name) | Đặt tên hiển thị tùy ý cho Bot |
| **4** | Nhập **Username** | Tên định danh duy nhất, **bắt buộc kết thúc bằng `bot`** |
| **5** | Copy **HTTP API Token** | Sao chép chuỗi token nhận được dán vào `BOT_TOKEN` trong file `.env` |
