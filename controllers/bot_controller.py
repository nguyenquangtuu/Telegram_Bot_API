import time
import threading
from flask import Blueprint, request, jsonify
from config import BOT_TOKEN
from models.user_model import UserModel
from models.leave_model import LeaveModel
from services.telegram_service import TelegramService

bot_bp = Blueprint("bot", __name__)

# Cờ kiểm tra trạng thái Webhook: Nếu Webhook đang bật, tạm dừng getUpdates để tránh xung đột
is_webhook_active = False

# Lưu trạng thái nhập liệu tạm thời của người dùng: { "telegram_id": "WAITING_REASON" }
user_states = {}

# ==================== WEBHOOK ENDPOINT ====================

@bot_bp.route("/webhook", methods=["POST"])
def telegram_webhook():
    """Endpoint nhận tin nhắn / sự kiện được Telegram đẩy về qua Webhook"""
    try:
        update = request.get_json(force=True, silent=True) or {}
        process_update(update)
        return jsonify({"ok": True}), 200
    except Exception as e:
        print(f"[Webhook Error]: {e}")
        return jsonify({"ok": False, "error": str(e)}), 200


# ==================== BỘ ĐIỀU PHỐI TIN NHẮN (DISPATCHER) ====================

def process_update(u: dict):
    """Phân loại sự kiện từ Telegram (tin nhắn văn bản hoặc bấm nút Inline)"""
    if "message" in u:
        handle_incoming_message(u["message"])
    elif "callback_query" in u:
        handle_incoming_callback(u["callback_query"])


def handle_incoming_message(msg: dict):
    """Xử lý tin nhắn văn bản từ người dùng"""
    chat_id = msg.get("chat", {}).get("id")
    from_user = msg.get("from", {})
    user_id = str(from_user.get("id"))
    full_name = f"{from_user.get('first_name', '')} {from_user.get('last_name', '')}".strip() or "Người dùng"
    username = from_user.get("username", "")
    text = (msg.get("text") or "").strip()

    if not chat_id or not text:
        return

    # 1. Hủy thao tác hiện tại
    if text.lower() in ["/cancel", "/huy", "❌ hủy bỏ"]:
        user_states.pop(user_id, None)
        user = UserModel.get_by_id(user_id) or {}
        role = user.get("role", "staff")
        TelegramService.send_message(
            chat_id, 
            "❌ <b>Đã hủy thao tác.</b>", 
            reply_markup=TelegramService.get_main_inline(role)
        )
        return

    # 2. Lệnh /start: Đăng ký người dùng và gửi menu các nút Inline
    if text.startswith("/start"):
        user_states.pop(user_id, None)
        user, _ = UserModel.save_or_update(user_id, full_name, username, default_role="staff")
        role = user.get("role", "staff")
        role_label = "👑 Quản lý" if role == "manager" else "👤 Nhân viên"

        # Gửi 1 tin nhắn xóa sạch bàn phím cũ dưới ô input nếu có
        TelegramService.send_message(
            chat_id,
            f"👋 Xin chào <b>{full_name}</b> ({role_label})!",
            reply_markup=TelegramService.get_remove_keyboard()
        )

        welcome_text = (
            f"Chào mừng bạn đến với <b>Go Absent</b> - Hệ thống quản lý nghỉ phép.\n\n"
            f"👉 <i>Bấm chọn chức năng bên dưới tin nhắn này để bắt đầu:</i>"
        )
        TelegramService.send_message(chat_id, welcome_text, reply_markup=TelegramService.get_main_inline(role))
        return

    # 3. Yêu cầu xin nghỉ phép: "/leave [lý do]" hoặc "/xinnghi [lý do]"
    lower_text = text.lower()
    if lower_text.startswith("/leave") or lower_text.startswith("/xinnghi") or lower_text.startswith("/nghiphep") or text == "📝 Xin nghỉ phép":
        parts = text.split(maxsplit=1)
        if len(parts) > 1 and parts[1].strip() and not text.startswith("📝"):
            # Nếu người dùng gõ kèm lý do luôn: /leave Em bị sốt xin nghỉ
            submit_leave_request(user_id, chat_id, full_name, username, parts[1].strip())
        else:
            # Chờ người dùng nhập lý do
            user_states[user_id] = "WAITING_REASON"
            prompt_text = (
                "📝 <b>TẠO ĐƠN XIN NGHỈ PHÉP</b>\n\n"
                "Vui lòng nhập <b>lý do xin nghỉ</b> của bạn vào khung chat bên dưới:"
            )
            TelegramService.send_message(chat_id, prompt_text, reply_markup=TelegramService.get_cancel_inline())
        return

    # 4. Nhận lý do nghỉ phép khi đang ở trạng thái chờ nhập
    if user_states.get(user_id) == "WAITING_REASON":
        submit_leave_request(user_id, chat_id, full_name, username, text)
        return

    # 5. Xem lịch sử đơn của bản thân: "/history" (hoặc "/lichsu")
    if lower_text in ["/history", "/lichsu", "📋 lịch sử đơn"]:
        show_user_history(chat_id, user_id)
        return

    # 6. Xem danh sách chờ duyệt (Dành cho Quản lý): "/pending" (hoặc "/choduyet")
    if lower_text in ["/pending", "/choduyet", "⏳ đơn chờ duyệt"]:
        show_pending_requests(chat_id, user_id)
        return

    # 7. Trợ giúp: "/help"
    if lower_text in ["/help", "ℹ️ hướng dẫn"]:
        show_help_message(chat_id, user_id)
        return

    # 8. Lệnh phân quyền: /setrole <telegram_id> <manager|staff> (Dành cho Quản lý)
    if text.startswith("/setrole"):
        user = UserModel.get_by_id(user_id) or {}
        role = user.get("role", "staff")
        if role != "manager":
            TelegramService.send_message(chat_id, "❌ Lệnh này chỉ dành cho Quản lý.", reply_markup=TelegramService.get_main_inline(role))
            return

        parts = text.split()
        if len(parts) != 3 or parts[2].lower() not in ["manager", "staff"]:
            TelegramService.send_message(chat_id, "Cú pháp: <code>/setrole &lt;telegram_id&gt; &lt;manager|staff&gt;</code>", reply_markup=TelegramService.get_main_inline(role))
            return

        target_id, new_role = parts[1].strip(), parts[2].lower()
        success, updated = UserModel.update_role(target_id, new_role)
        if success:
            TelegramService.send_message(chat_id, f"✅ Đã đổi quyền của <b>{updated['name']}</b> thành <b>{new_role.upper()}</b>!", reply_markup=TelegramService.get_main_inline(role))
        else:
            TelegramService.send_message(chat_id, "❌ Không tìm thấy người dùng này trong hệ thống.", reply_markup=TelegramService.get_main_inline(role))
        return

    # Tin nhắn thông thường khác
    user = UserModel.get_by_id(user_id) or {}
    role = user.get("role", "staff")
    TelegramService.send_message(
        chat_id, 
        "👉 Vui lòng chọn chức năng bạn muốn thực hiện bên dưới tin nhắn:", 
        reply_markup=TelegramService.get_main_inline(role)
    )


def handle_incoming_callback(cb: dict):
    """Xử lý sự kiện khi người dùng bấm vào các nút Inline Keyboard"""
    cb_id = cb.get("id")
    data = cb.get("data", "")
    from_user = cb.get("from", {})
    user_id = str(from_user.get("id"))
    full_name = f"{from_user.get('first_name', '')} {from_user.get('last_name', '')}".strip() or "Người dùng"
    msg = cb.get("message", {})
    chat_id = msg.get("chat", {}).get("id")
    msg_id = msg.get("message_id")

    # 1. Bấm nút Tạo đơn xin nghỉ
    if data in ["btn_create_leave", "btn_start_leave"]:
        TelegramService.answer_callback_query(cb_id)
        user_states[user_id] = "WAITING_REASON"
        prompt_text = (
            "📝 <b>TẠO ĐƠN XIN NGHỈ PHÉP</b>\n\n"
            "Vui lòng nhập <b>lý do xin nghỉ</b> của bạn vào khung chat bên dưới:"
        )
        TelegramService.send_message(chat_id, prompt_text, reply_markup=TelegramService.get_cancel_inline())
        return

    # 2. Bấm nút Hủy thao tác nhập lý do
    if data == "btn_cancel_input":
        user_states.pop(user_id, None)
        TelegramService.answer_callback_query(cb_id, text="Đã hủy thao tác!")
        user = UserModel.get_by_id(user_id) or {}
        role = user.get("role", "staff")
        TelegramService.edit_message_text(
            chat_id, msg_id, 
            "❌ <b>Đã hủy thao tác tạo đơn.</b>", 
            reply_markup=TelegramService.get_main_inline(role)
        )
        return

    # 3. Bấm nút Xem lịch sử
    if data in ["btn_history", "btn_show_history"]:
        TelegramService.answer_callback_query(cb_id)
        show_user_history(chat_id, user_id)
        return

    # 4. Bấm nút Xem đơn chờ duyệt (Dành cho Quản lý)
    if data == "btn_pending":
        TelegramService.answer_callback_query(cb_id)
        show_pending_requests(chat_id, user_id)
        return

    # 5. Nhân viên bấm nút Hủy đơn đã nộp (cancel_req_<id>)
    if data.startswith("cancel_req_"):
        req_id = int(data.split("_")[2])
        success, msg_cancel = LeaveModel.cancel_request(req_id, user_id)
        if success:
            TelegramService.answer_callback_query(cb_id, text="Đã hủy đơn thành công!")
            user = UserModel.get_by_id(user_id) or {}
            role = user.get("role", "staff")
            TelegramService.send_message(
                chat_id,
                f"🗑️ <b>ĐÃ HỦY ĐƠN #NP{str(req_id).zfill(5)} THÀNH CÔNG!</b>\n\n"
                f"Đơn xin nghỉ phép của bạn đã được hủy bỏ.",
                reply_markup=TelegramService.get_main_inline(role)
            )
        else:
            TelegramService.answer_callback_query(cb_id, text=msg_cancel, show_alert=True)
        return

    # 6. Quản lý bấm Duyệt hoặc Từ chối đơn
    if data.startswith("approve_") or data.startswith("reject_"):
        user = UserModel.get_by_id(user_id) or {}
        if user.get("role") != "manager":
            TelegramService.answer_callback_query(cb_id, text="❌ Bạn không có quyền quản lý!", show_alert=True)
            return

        action = "APPROVED" if data.startswith("approve_") else "REJECTED"
        req_id = int(data.split("_")[1])

        success, err_msg, updated_req = process_leave_review(req_id, action, full_name)
        if not success:
            TelegramService.answer_callback_query(cb_id, text=err_msg or "Thao tác không hợp lệ!", show_alert=True)
            return

        TelegramService.answer_callback_query(cb_id, text="Đã xử lý xong!")
        status_label = "✅ ĐÃ CHẤP THUẬN" if action == "APPROVED" else "❌ ĐÃ TỪ CHỐI"
        orig_text = msg.get("text", "")
        updated_text = (
            f"{orig_text}\n\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"<b>{status_label}</b> bởi <b>{full_name}</b>\n"
            f"⏰ Lúc: {updated_req['reviewed_at']}"
        )
        TelegramService.edit_message_text(chat_id, msg_id, updated_text, reply_markup=None)
        return


# ==================== CÁC HÀM XỬ LÝ NGHIỆP VỤ BOT ====================

def submit_leave_request(user_id, chat_id, full_name, username, reason):
    """Tạo đơn xin nghỉ, lưu vào JSON và gửi thông báo tới toàn bộ Quản lý"""
    user_states.pop(str(user_id), None)
    user, _ = UserModel.save_or_update(user_id, full_name, username, default_role="staff")
    role = user.get("role", "staff")

    # Lưu đơn vào file JSON
    new_req = LeaveModel.create(user_id, full_name, reason)
    req_code = f"NP{str(new_req['id']).zfill(5)}"

    # 1. Báo thành công cho nhân viên kèm nút Hủy đơn & Xem lịch sử
    confirm_text = (
        f"✅ <b>ĐÃ GỬI ĐƠN XIN NGHỈ THÀNH CÔNG!</b>\n\n"
        f"• Mã đơn: <code>#{req_code}</code>\n"
        f"• Lý do: {reason}\n"
        f"• Thời gian gửi: {new_req['created_at']}\n\n"
        f"Đơn của bạn đã được chuyển tới ban quản lý để xét duyệt."
    )
    confirm_inline = {
        "inline_keyboard": [
            [{"text": f"🗑️ Hủy đơn #{req_code}", "callback_data": f"cancel_req_{new_req['id']}"}],
            [
                {"text": "📋 Xem lịch sử", "callback_data": "btn_history"},
                {"text": "📝 Tạo đơn khác", "callback_data": "btn_create_leave"}
            ]
        ]
    }
    TelegramService.send_message(chat_id, confirm_text, reply_markup=confirm_inline)

    # 2. Gửi thông báo đến TẤT CẢ Quản lý kèm nút [Duyệt] và [Từ chối]
    managers = UserModel.get_managers()
    username_str = f" (@{username})" if username else ""
    notify_text = (
        f"🔔 <b>YÊU CẦU NGHỈ PHÉP MỚI (#{req_code})</b>\n\n"
        f"👤 Nhân viên: <b>{full_name}</b>{username_str}\n"
        f"📝 Lý do: {reason}\n"
        f"⏰ Thời gian: {new_req['created_at']}\n\n"
        f"👉 Quản lý vui lòng chọn hành động:"
    )
    reply_markup = {
        "inline_keyboard": [
            [
                {"text": "✅ Duyệt", "callback_data": f"approve_{new_req['id']}"},
                {"text": "❌ Từ chối", "callback_data": f"reject_{new_req['id']}"}
            ]
        ]
    }
    for mgr in managers:
        TelegramService.send_message(mgr["telegram_id"], notify_text, reply_markup=reply_markup)

    return new_req


def process_leave_review(req_id, new_status, reviewer_name):
    """Cập nhật trạng thái duyệt đơn và bắn tin nhắn báo cho nhân viên"""
    success, message, updated_req = LeaveModel.update_status(req_id, new_status, reviewer_name)
    if success and updated_req:
        status_msg = "🎉 <b>ĐÃ ĐƯỢC CHẤP THUẬN!</b>" if new_status == "APPROVED" else "⚠️ <b>ĐÃ BỊ TỪ CHỐI!</b>"
        emp_text = (
            f"🔔 <b>KẾT QUẢ ĐƠN XIN NGHỈ (NP{str(updated_req['id']).zfill(5)})</b>\n\n"
            f"Trạng thái: {status_msg}\n"
            f"📝 Lý do nghỉ: {updated_req['reason']}\n"
            f"👨‍💼 Người duyệt: <b>{reviewer_name}</b>\n"
            f"⏰ Thời gian duyệt: {updated_req['reviewed_at']}"
        )
        TelegramService.send_message(
            updated_req["user_id"], 
            emp_text,
            reply_markup={"inline_keyboard": [[{"text": "📋 Xem lịch sử", "callback_data": "btn_history"}]]}
        )
    return success, message, updated_req


def show_user_history(chat_id, user_id):
    """Hiển thị 5 đơn xin nghỉ gần nhất của người dùng kèm các nút Inline tiện lợi"""
    user = UserModel.get_by_id(user_id) or {}
    role = user.get("role", "staff")
    my_reqs = LeaveModel.get_by_user(user_id)

    if not my_reqs:
        empty_inline = {
            "inline_keyboard": [
                [{"text": "📝 Tạo đơn xin nghỉ ngay", "callback_data": "btn_create_leave"}]
            ]
        }
        TelegramService.send_message(chat_id, "📋 Bạn chưa tạo đơn xin nghỉ phép nào.", reply_markup=empty_inline)
        return

    msg_body = "📋 <b>LỊCH SỬ ĐƠN NGHỈ PHÉP CỦA BẠN:</b>\n\n"
    inline_buttons = []

    for r in reversed(my_reqs[-5:]):
        if r["status"] == "PENDING":
            st = "🟡 Đang chờ duyệt"
            inline_buttons.append([{"text": f"🗑️ Hủy đơn #NP{str(r['id']).zfill(5)}", "callback_data": f"cancel_req_{r['id']}"}])
        elif r["status"] == "APPROVED":
            st = "🟢 Đã chấp thuận"
        elif r["status"] == "CANCELLED":
            st = "⚪ Đã hủy"
        else:
            st = "🔴 Đã từ chối"

        msg_body += (
            f"• <b>Đơn #NP{str(r['id']).zfill(5)}</b> ({st})\n"
            f"  📝 Lý do: {r['reason']}\n"
            f"  ⏰ Gửi lúc: {r['created_at']}\n"
        )
        if r.get("reviewed_by"):
            msg_body += f"  👨‍💼 Người duyệt: {r['reviewed_by']} ({r.get('reviewed_at') or ''})\n"
        msg_body += "\n"

    inline_buttons.append([
        {"text": "📝 Tạo đơn xin nghỉ", "callback_data": "btn_create_leave"},
        {"text": "🔄 Làm mới", "callback_data": "btn_history"}
    ])

    TelegramService.send_message(chat_id, msg_body, reply_markup={"inline_keyboard": inline_buttons})


def show_pending_requests(chat_id, user_id):
    """Hiển thị danh sách các đơn đang chờ duyệt cho Quản lý"""
    user = UserModel.get_by_id(user_id) or {}
    role = user.get("role", "staff")

    if role != "manager":
        TelegramService.send_message(
            chat_id, 
            "❌ Chức năng này chỉ dành cho Quản lý.", 
            reply_markup=TelegramService.get_main_inline(role)
        )
        return

    pending = LeaveModel.get_pending()
    if not pending:
        TelegramService.send_message(
            chat_id, 
            "🎉 Hiện tại không có đơn nào đang chờ duyệt!", 
            reply_markup=TelegramService.get_main_inline(role)
        )
        return

    TelegramService.send_message(chat_id, f"📋 Tìm thấy <b>{len(pending)} đơn</b> đang chờ xét duyệt:")
    for r in pending:
        reply_markup = {
            "inline_keyboard": [
                [
                    {"text": "✅ Duyệt", "callback_data": f"approve_{r['id']}"},
                    {"text": "❌ Từ chối", "callback_data": f"reject_{r['id']}"}
                ]
            ]
        }
        card_text = (
            f"📋 <b>Đơn #NP{str(r['id']).zfill(5)}</b>\n"
            f"👤 Nhân viên: <b>{r['user_name']}</b>\n"
            f"📝 Lý do: {r['reason']}\n"
            f"⏰ Thời gian: {r['created_at']}"
        )
        TelegramService.send_message(chat_id, card_text, reply_markup=reply_markup)


def show_help_message(chat_id, user_id):
    """Gửi tin nhắn hướng dẫn sử dụng bot"""
    user = UserModel.get_by_id(user_id) or {}
    role = user.get("role", "staff")

    help_text = (
        "💡 <b>HƯỚNG DẪN SỬ DỤNG GO ABSENT</b>\n\n"
        "👉 <b>Thao tác đơn giản qua các nút bấm bên dưới tin nhắn:</b>\n"
        "• Bấm <b>[ 📝 Tạo đơn xin nghỉ ]</b> ➔ Nhập lý do gửi đi.\n"
        "• Bấm <b>[ 📋 Xem lịch sử ]</b> ➔ Xem các đơn đã nộp và trạng thái.\n"
        "• Bấm <b>[ 🗑️ Hủy đơn ]</b> ➔ Hủy đơn đang chờ duyệt nếu có thay đổi.\n\n"
        "👉 <b>Các câu lệnh nhanh (Commands):</b>\n"
        "• <code>/start</code> - Mở Menu chức năng\n"
        "• <code>/leave &lt;Lý do&gt;</code> - Gửi nhanh đơn xin nghỉ\n"
        "• <code>/history</code> - Xem danh sách đơn đã nộp\n"
        "• <code>/cancel</code> - Hủy thao tác hiện tại\n"
        "• <code>/help</code> - Hướng dẫn sử dụng\n"
    )
    if role == "manager":
        help_text += (
            "\n👑 <b>Dành cho Quản lý:</b>\n"
            "• Gõ <code>/pending</code> để xem danh sách đơn đang chờ duyệt\n"
            "• Duyệt hoặc Từ chối trực tiếp bằng nút bấm ngay trên tin nhắn thông báo!\n"
        )
    TelegramService.send_message(chat_id, help_text, reply_markup=TelegramService.get_main_inline(role))


# ==================== POLLING DỰ PHÒNG KHI CHƯA CÓ WEBHOOK ====================

def start_background_polling():
    """Khởi động luồng chạy ngầm để nhận tin nhắn qua Long-Polling khi Webhook chưa bật"""
    TelegramService.setup_bot_commands()
    t = threading.Thread(target=polling_worker, daemon=True)
    t.start()


def polling_worker():
    """Vòng lặp lấy tin nhắn mới từ Telegram khi chưa cấu hình Webhook"""
    global is_webhook_active
    time.sleep(1)

    # Kiểm tra xem Webhook có đang hoạt động trên Telegram không
    info = TelegramService.get_webhook_info()
    if info and info.get("ok"):
        current_url = info.get("result", {}).get("url", "")
        if current_url:
            is_webhook_active = True
            print(f"[Webhook] Dang kich hoat voi URL: {current_url}")

    offset = None
    while True:
        try:
            if is_webhook_active:
                time.sleep(3)
                continue

            updates = TelegramService.get_updates(offset=offset, timeout=15)
            if updates and updates.get("ok"):
                for u in updates.get("result", []):
                    offset = u["update_id"] + 1
                    process_update(u)
        except Exception as e:
            time.sleep(2)
