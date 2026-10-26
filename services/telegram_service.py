import requests
from config import TELEGRAM_API_URL, BOT_TOKEN

class TelegramService:
    @staticmethod
    def call_api(method: str, payload: dict = None, http_method: str = "POST"):
        """Gửi HTTP request trực tiếp đến Telegram REST API"""
        if not BOT_TOKEN or BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
            return None

        url = f"{TELEGRAM_API_URL}/{method}"
        try:
            if http_method.upper() == "GET":
                response = requests.get(url, params=payload, timeout=35)
            else:
                response = requests.post(url, json=payload, timeout=35)

            result = response.json()
            if not result.get("ok"):
                print(f"[Telegram API Error] {method}: {result.get('description')}")
            return result
        except Exception as e:
            print(f"[Telegram Network Error] {method}: {e}")
            return None

    @staticmethod
    def send_message(chat_id, text, reply_markup=None, parse_mode="HTML"):
        """Gọi POST /sendMessage với chuẩn định dạng HTML"""
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": parse_mode
        }
        if reply_markup:
            payload["reply_markup"] = reply_markup
        return TelegramService.call_api("sendMessage", payload)

    @staticmethod
    def edit_message_text(chat_id, message_id, text, reply_markup=None, parse_mode="HTML"):
        """Gọi POST /editMessageText với chuẩn định dạng HTML"""
        payload = {
            "chat_id": chat_id,
            "message_id": message_id,
            "text": text,
            "parse_mode": parse_mode
        }
        if reply_markup is not None:
            payload["reply_markup"] = reply_markup
        return TelegramService.call_api("editMessageText", payload)

    @staticmethod
    def answer_callback_query(callback_query_id, text=None, show_alert=False):
        """Gọi POST /answerCallbackQuery phản hồi nút bấm Inline"""
        payload = {
            "callback_query_id": callback_query_id,
            "show_alert": show_alert
        }
        if text:
            payload["text"] = text
        return TelegramService.call_api("answerCallbackQuery", payload)

    @staticmethod
    def get_updates(offset=None, timeout=20):
        """Gọi GET /getUpdates để Long-Polling tin nhắn mới"""
        params = {"timeout": timeout}
        if offset is not None:
            params["offset"] = offset
        return TelegramService.call_api("getUpdates", params, http_method="GET")

    @staticmethod
    def get_webhook_info():
        """Gọi GET /getWebhookInfo lấy trạng thái Webhook"""
        return TelegramService.call_api("getWebhookInfo", http_method="GET")

    @staticmethod
    def set_webhook(url: str):
        """Gọi POST /setWebhook đăng ký URL nhận tin"""
        return TelegramService.call_api("setWebhook", {"url": url})

    @staticmethod
    def delete_webhook(drop_pending_updates: bool = True):
        """Gọi POST /deleteWebhook hủy Webhook trên Telegram để chuyển sang getUpdates"""
        payload = {"drop_pending_updates": drop_pending_updates}
        return TelegramService.call_api("deleteWebhook", payload)

    @staticmethod
    def get_ngrok_url():
        """Lấy URL HTTPS công khai từ Ngrok Web API cục bộ (cổng 4040) nếu đang chạy"""
        try:
            res = requests.get("http://127.0.0.1:4040/api/tunnels", timeout=2)
            if res.status_code == 200:
                data = res.json()
                for tunnel in data.get("tunnels", []):
                    public_url = tunnel.get("public_url", "")
                    if public_url.startswith("https://"):
                        return public_url
        except Exception:
            pass
        return None

    @staticmethod
    def setup_bot_commands():
        """Đăng ký danh sách menu lệnh [/] bằng tiếng Anh chuẩn với Telegram"""
        commands = [
            {"command": "start", "description": "Open main menu"},
            {"command": "leave", "description": "Submit a leave request"},
            {"command": "history", "description": "View your leave history"},
            {"command": "pending", "description": "View pending requests (Manager)"},
            {"command": "cancel", "description": "Cancel current action"},
            {"command": "help", "description": "How to use this bot"}
        ]
        return TelegramService.call_api("setMyCommands", {"commands": commands})

    # ==================== BÀN PHÍM TƯƠNG TÁC ====================
    @staticmethod
    def get_remove_keyboard():
        """Xóa hoàn toàn bàn phím bên dưới ô input"""
        return {"remove_keyboard": True}

    @staticmethod
    def get_main_inline(role: str = "staff"):
        """Các nút bấm Inline gắn liền với tin nhắn hệ thống gửi về"""
        buttons = [
            [
                {"text": "📝 Tạo đơn xin nghỉ", "callback_data": "btn_create_leave"},
                {"text": "📋 Xem lịch sử", "callback_data": "btn_history"}
            ]
        ]
        if role == "manager":
            buttons.append([
                {"text": "⏳ Đơn chờ duyệt", "callback_data": "btn_pending"}
            ])
        return {"inline_keyboard": buttons}

    @staticmethod
    def get_cancel_inline():
        """Nút hủy thao tác Inline đính kèm tin nhắn"""
        return {
            "inline_keyboard": [
                [{"text": "❌ Hủy thao tác", "callback_data": "btn_cancel_input"}]
            ]
        }
