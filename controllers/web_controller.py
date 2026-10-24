from flask import Blueprint, render_template, jsonify, request
from models.leave_model import LeaveModel
from models.user_model import UserModel
from services.telegram_service import TelegramService
import controllers.bot_controller as bot_ctrl

web_bp = Blueprint("web", __name__)

# ==================== GIAO DIỆN WEB ====================

@web_bp.route("/")
def index():
    """Giao diện Dashboard quản lý chính (Bootstrap 5)"""
    return render_template("index.html")


# ==================== 1. REST API: ĐƠN NGHỈ PHÉP (/api/leaves) ====================

@web_bp.route("/api/leaves", methods=["GET"])
@web_bp.route("/api/v1/leaves", methods=["GET"])
def get_leaves():
    """Lấy danh sách đơn nghỉ phép (hỗ trợ lọc theo trạng thái và tìm kiếm)"""
    leaves = LeaveModel.get_all()
    status_filter = request.args.get("status")
    search_query = request.args.get("q", "").strip().lower()

    if status_filter and status_filter != "ALL":
        leaves = [l for l in leaves if l.get("status") == status_filter.upper()]

    if search_query:
        leaves = [
            l for l in leaves
            if search_query in str(l.get("user_name", "")).lower()
            or search_query in str(l.get("reason", "")).lower()
            or search_query in f"np{str(l.get('id', '')).zfill(5)}".lower()
        ]

    return jsonify({"success": True, "data": leaves, "total": len(leaves)}), 200

@web_bp.route("/api/leaves/<int:req_id>", methods=["GET"])
@web_bp.route("/api/v1/leaves/<int:req_id>", methods=["GET"])
def get_leave_detail(req_id):
    """Lấy chi tiết 1 đơn theo mã ID"""
    leave = LeaveModel.get_by_id(req_id)
    if not leave:
        return jsonify({"success": False, "message": "Không tìm thấy đơn"}), 404
    return jsonify({"success": True, "data": leave}), 200

@web_bp.route("/api/leaves", methods=["POST"])
@web_bp.route("/api/v1/leaves", methods=["POST"])
def create_leave():
    """Tạo đơn xin nghỉ mới qua REST API"""
    data = request.get_json(silent=True) or {}
    user_id = data.get("user_id")
    user_name = data.get("user_name")
    reason = data.get("reason")
    username = data.get("username", "")

    if not user_id or not user_name or not reason:
        return jsonify({"success": False, "message": "Vui lòng nhập đủ user_id, user_name, reason"}), 400

    new_req = bot_ctrl.submit_leave_request(user_id, user_id, user_name, username, reason)
    return jsonify({"success": True, "data": new_req, "message": "Tạo đơn thành công"}), 201

@web_bp.route("/api/leaves/<int:req_id>", methods=["PATCH", "PUT"])
@web_bp.route("/api/v1/leaves/<int:req_id>", methods=["PATCH", "PUT"])
def review_leave(req_id):
    """Quản trị viên xét duyệt hoặc từ chối đơn"""
    data = request.get_json(silent=True) or {}
    action = data.get("action") or data.get("status")
    reviewer = data.get("reviewer", "Quản trị viên (Web)")

    if action not in ["APPROVED", "REJECTED"]:
        return jsonify({"success": False, "message": "Hành động chỉ có thể là APPROVED hoặc REJECTED"}), 400

    success, message, updated_req = bot_ctrl.process_leave_review(req_id, action, reviewer)
    if success:
        return jsonify({"success": True, "data": updated_req, "message": "Cập nhật thành công!"}), 200
    return jsonify({"success": False, "message": message}), 400

@web_bp.route("/api/leaves/<int:req_id>", methods=["DELETE"])
@web_bp.route("/api/v1/leaves/<int:req_id>", methods=["DELETE"])
def delete_leave(req_id):
    """Xóa một đơn xin nghỉ theo ID"""
    success = LeaveModel.delete(req_id)
    if success:
        return jsonify({"success": True, "message": "Đã xóa đơn thành công"}), 200
    return jsonify({"success": False, "message": "Không tìm thấy đơn để xóa"}), 404


# ==================== 2. REST API: NGƯỜI DÙNG (/api/users) ====================

@web_bp.route("/api/users", methods=["GET"])
@web_bp.route("/api/v1/users", methods=["GET"])
def get_users():
    """Lấy danh sách người dùng"""
    users_dict = UserModel.get_all()
    users_list = list(users_dict.values())
    role_filter = request.args.get("role")

    if role_filter:
        users_list = [u for u in users_list if u.get("role") == role_filter.lower()]

    return jsonify({"success": True, "data": users_list, "total": len(users_list)}), 200

@web_bp.route("/api/users/<user_id>", methods=["PATCH", "PUT"])
@web_bp.route("/api/v1/users/<user_id>", methods=["PATCH", "PUT"])
def update_user_role(user_id):
    """Cập nhật vai trò người dùng (manager hoặc staff)"""
    data = request.get_json(silent=True) or {}
    new_role = data.get("role")

    if new_role not in ["manager", "staff"]:
        return jsonify({"success": False, "message": "Vai trò chỉ có thể là 'manager' hoặc 'staff'"}), 400

    success, updated_user = UserModel.update_role(user_id, new_role)
    if success:
        return jsonify({"success": True, "data": updated_user, "message": "Cập nhật vai trò thành công!"}), 200
    return jsonify({"success": False, "message": "Không tìm thấy người dùng"}), 404


# ==================== 3. REST API: TELEGRAM WEBHOOK (/api/webhook) ====================

@web_bp.route("/api/webhook", methods=["GET"])
@web_bp.route("/api/v1/webhook", methods=["GET"])
@web_bp.route("/api/webhook/status", methods=["GET"])
def get_webhook_status():
    """Kiểm tra trạng thái Webhook trên Telegram"""
    info_res = TelegramService.get_webhook_info()
    if info_res and info_res.get("ok"):
        result = info_res.get("result", {})
        url = result.get("url", "")
        data = {
            "is_active": bool(url),
            "url": url,
            "pending_count": result.get("pending_update_count", 0),
            "last_error": result.get("last_error_message", "")
        }
        return jsonify({"success": True, "data": data, "is_active": bool(url), "url": url}), 200
    return jsonify({"success": False, "data": {"is_active": False, "url": ""}}), 500

@web_bp.route("/api/webhook", methods=["POST"])
@web_bp.route("/api/v1/webhook", methods=["POST"])
@web_bp.route("/api/webhook/set", methods=["POST"])
def set_webhook():
    """Đăng ký địa chỉ Webhook URL mới với Telegram"""
    data = request.get_json(silent=True) or {}
    webhook_url = (data.get("url") or "").strip()

    if not webhook_url:
        return jsonify({"success": False, "message": "Vui lòng nhập URL Webhook!"}), 400

    if not webhook_url.startswith("https://"):
        return jsonify({"success": False, "message": "Telegram yêu cầu URL phải có giao thức HTTPS"}), 400

    res = TelegramService.set_webhook(webhook_url)
    if res and res.get("ok"):
        bot_ctrl.is_webhook_active = True
        return jsonify({"success": True, "message": "Đăng ký Webhook thành công!", "url": webhook_url}), 200

    err_desc = res.get("description") if res else "Không kết nối được tới Telegram API"
    return jsonify({"success": False, "message": f"Telegram từ chối: {err_desc}"}), 400

@web_bp.route("/api/webhook", methods=["DELETE"])
@web_bp.route("/api/v1/webhook", methods=["DELETE"])
@web_bp.route("/api/webhook/delete", methods=["POST"])
def delete_webhook():
    """Hủy Webhook trên Telegram để chuyển về chế độ Polling"""
    res = TelegramService.delete_webhook()
    if res and res.get("ok"):
        bot_ctrl.is_webhook_active = False
        return jsonify({"success": True, "message": "Đã hủy Webhook thành công!"}), 200
    return jsonify({"success": False, "message": "Không thể xóa Webhook trên Telegram"}), 400


# ==================== LEGACY COMPATIBILITY ====================

@web_bp.route("/api/data", methods=["GET"])
def api_data():
    """Endpoint tương thích ngược để lấy toàn bộ dữ liệu đơn và người dùng"""
    return jsonify({
        "requests": LeaveModel.get_all(),
        "users": UserModel.get_all()
    })
