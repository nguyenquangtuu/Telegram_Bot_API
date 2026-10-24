import os
from dotenv import load_dotenv

# Tải cấu hình từ file .env
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
WEB_PORT = int(os.getenv("WEB_PORT", 5000))

# Đường dẫn thư mục dữ liệu JSON
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
USERS_FILE = os.path.join(DATA_DIR, "users.json")
REQUESTS_FILE = os.path.join(DATA_DIR, "requests.json")

# URL Telegram Bot REST API
TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"
