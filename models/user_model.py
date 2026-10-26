from datetime import datetime
from config import USERS_FILE
from models.base_model import read_json, write_json

class UserModel:
    @staticmethod
    def get_all():
        """Lấy toàn bộ danh sách người dùng"""
        return read_json(USERS_FILE, {})

    @staticmethod
    def get_by_id(user_id):
        """Lấy thông tin người dùng theo telegram_id"""
        users = UserModel.get_all()
        return users.get(str(user_id))

    @staticmethod
    def get_managers():
        """Lấy danh sách tất cả những người có role là manager"""
        users = UserModel.get_all()
        return [u for u in users.values() if u.get("role") == "manager"]

    @staticmethod
    def save_or_update(user_id, full_name, username, default_role="staff"):
        """Đăng ký người dùng nếu chưa có, hoặc trả về người dùng hiện tại"""
        users = UserModel.get_all()
        uid = str(user_id)
        if uid not in users:
            # Nếu hệ thống chưa có Quản lý nào, gán người đầu tiên làm Quản lý
            has_manager = any(u.get("role") == "manager" for u in users.values())
            assigned_role = "manager" if not has_manager else default_role

            users[uid] = {
                "telegram_id": int(user_id),
                "name": full_name,
                "username": username or "",
                "role": assigned_role,
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            write_json(USERS_FILE, users)
            return users[uid], True
        return users[uid], False

    @staticmethod
    def update_role(user_id, new_role):
        """Cập nhật vai trò người dùng (manager hoặc staff)"""
        users = UserModel.get_all()
        uid = str(user_id)
        if uid in users and new_role in ["manager", "staff"]:
            users[uid]["role"] = new_role
            write_json(USERS_FILE, users)
            return True, users[uid]
        return False, None

    @staticmethod
    def delete(user_id):
        """Xóa người dùng theo ID"""
        users = UserModel.get_all()
        uid = str(user_id)
        if uid in users:
            del users[uid]
            write_json(USERS_FILE, users)
            return True
        return False
