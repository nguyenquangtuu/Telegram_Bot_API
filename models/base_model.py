import os
import json
import threading

# Khóa luồng đảm bảo tính toàn vẹn khi nhiều tiến trình đọc/ghi đồng thời
file_lock = threading.Lock()

def read_json(filepath, default_value):
    """Đọc dữ liệu từ file JSON một cách an toàn"""
    with file_lock:
        if not os.path.exists(filepath):
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(default_value, f, ensure_ascii=False, indent=2)
            return default_value
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return default_value

def write_json(filepath, data):
    """Ghi dữ liệu vào file JSON an toàn"""
    with file_lock:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
