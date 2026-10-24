from datetime import datetime
from config import REQUESTS_FILE
from models.base_model import read_json, write_json

class LeaveModel:
    @staticmethod
    def get_all():
        """Lấy toàn bộ danh sách đơn xin nghỉ phép"""
        return read_json(REQUESTS_FILE, [])

    @staticmethod
    def get_by_id(req_id):
        """Tìm đơn xin nghỉ theo mã ID"""
        reqs = LeaveModel.get_all()
        return next((r for r in reqs if r["id"] == int(req_id)), None)

    @staticmethod
    def get_by_user(user_id):
        """Lấy danh sách đơn của một người dùng"""
        reqs = LeaveModel.get_all()
        return [r for r in reqs if str(r.get("user_id")) == str(user_id)]

    @staticmethod
    def get_pending():
        """Lấy danh sách các đơn đang ở trạng thái chờ duyệt (PENDING)"""
        reqs = LeaveModel.get_all()
        return [r for r in reqs if r["status"] == "PENDING"]

    @staticmethod
    def create(user_id, full_name, reason):
        """Tạo mới một yêu cầu nghỉ phép"""
        reqs = LeaveModel.get_all()
        new_id = (max([r["id"] for r in reqs], default=0)) + 1
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        new_req = {
            "id": new_id,
            "user_id": int(user_id),
            "user_name": full_name,
            "reason": reason,
            "status": "PENDING",
            "created_at": created_at,
            "reviewed_by": None,
            "reviewed_at": None
        }
        reqs.append(new_req)
        write_json(REQUESTS_FILE, reqs)
        return new_req

    @staticmethod
    def update_status(req_id, new_status, reviewer_name):
        """Cập nhật trạng thái duyệt đơn (APPROVED hoặc REJECTED)"""
        reqs = LeaveModel.get_all()
        for r in reqs:
            if r["id"] == int(req_id):
                if r["status"] != "PENDING":
                    return False, "Đơn này đã được xử lý trước đó", r
                r["status"] = new_status
                r["reviewed_by"] = reviewer_name
                r["reviewed_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                write_json(REQUESTS_FILE, reqs)
                return True, "Thành công", r
        return False, "Không tìm thấy đơn", None

    @staticmethod
    def delete(req_id):
        """Xóa đơn xin nghỉ theo mã ID"""
        reqs = LeaveModel.get_all()
        initial_len = len(reqs)
        reqs = [r for r in reqs if r["id"] != int(req_id)]
        if len(reqs) < initial_len:
            write_json(REQUESTS_FILE, reqs)
            return True
        return False

    @staticmethod
    def cancel_request(req_id, user_id):
        """Người dùng tự hủy đơn xin nghỉ của mình khi còn đang PENDING"""
        reqs = LeaveModel.get_all()
        for r in reqs:
            if r["id"] == int(req_id) and str(r.get("user_id")) == str(user_id):
                if r["status"] != "PENDING":
                    return False, "Đơn này đã được xử lý trước đó, không thể hủy."
                r["status"] = "CANCELLED"
                r["reviewed_by"] = "Người dùng tự hủy"
                r["reviewed_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                write_json(REQUESTS_FILE, reqs)
                return True, "Đã hủy đơn thành công"
        return False, "Không tìm thấy đơn hoặc bạn không có quyền hủy đơn này"
