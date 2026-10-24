from flask import Flask
from config import WEB_PORT
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
    # Khởi động dịch vụ lắng nghe tin nhắn nền (Polling / Webhook)
    start_background_polling()

    # Khởi động máy chủ Web Dashboard
    print(f"[Go Absent] He thong dang chay tai http://localhost:{WEB_PORT}")
    app.run(host="0.0.0.0", port=WEB_PORT, debug=False)
