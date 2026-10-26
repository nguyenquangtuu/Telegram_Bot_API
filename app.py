from flask import Flask
from config import WEB_PORT, BOT_MODE
from controllers.web_controller import web_bp
from controllers.bot_controller import bot_bp, start_background_polling

def create_app():
    """Khởi tạo ứng dụng Flask và đăng ký các Controller (Blueprints)"""
    app = Flask(__name__)
    app.config["TEMPLATES_AUTO_RELOAD"] = True
    app.register_blueprint(web_bp)
    app.register_blueprint(bot_bp)
    return app

# Khởi tạo instance ứng dụng
app = create_app()

if __name__ == "__main__":
    print("=" * 60)
    print("       GO ABSENT - TELEGRAM BOT & WEB DASHBOARD")
    if BOT_MODE == "polling":
        print(" [CHE DO 1] Chay tren LOCALHOST - Nhan su kien qua GetUpdates")
        print("            -> Webhook bi vo hieu hoa tren Dashboard")
    else:
        print(" [CHE DO 2] Chay voi NGROK - Nhan su kien qua Webhook")
        print("            -> Cho phep cau hinh Webhook tren Dashboard")
    print("=" * 60)

    # Khởi động dịch vụ lắng nghe tin nhắn nền (Polling / Webhook)
    start_background_polling()

    # Khởi động máy chủ Web Dashboard
    print(f"[Go Absent] Dashboard Web dang chay tai: http://localhost:{WEB_PORT}")
    app.run(host="0.0.0.0", port=WEB_PORT, debug=False)
