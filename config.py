import os
from dotenv import load_dotenv

# Tải cấu hình từ file .env
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
WEB_PORT = int(os.getenv("WEB_PORT", 5000))

# Chế độ hoạt động của Bot: 'polling' (Localhost - GetUpdates) hoặc 'webhook' (NGROK)
BOT_MODE = os.getenv("BOT_MODE", "polling").strip().lower()

# Cho phép nhận tham số dòng lệnh: python app.py --mode=polling hoặc --mode=webhook
import sys
for arg in sys.argv[1:]:
    if arg.startswith("--mode="):
        BOT_MODE = arg.split("=", 1)[1].strip().lower()
    elif arg == "--polling":
        BOT_MODE = "polling"
    elif arg == "--webhook":
        BOT_MODE = "webhook"

# Đường dẫn thư mục dữ liệu JSON
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
USERS_FILE = os.path.join(DATA_DIR, "users.json")
REQUESTS_FILE = os.path.join(DATA_DIR, "requests.json")

# URL Telegram Bot REST API
TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"
