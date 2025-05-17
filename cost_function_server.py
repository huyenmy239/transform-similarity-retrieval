import json
import os

class CostFunctionServer:
    def __init__(self, path="data/cost_function.json"):
        self.path = path
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        if not os.path.exists(self.path):
            with open(self.path, "w") as f:
                json.dump([], f)

    def CostInsert(self, cost_func: dict):
        """Thêm hàm chi phí mới vào thư viện, nếu chưa có"""
        with open(self.path, "r") as f:
            data = json.load(f)
        
        # Kiểm tra xem hàm chi phí với cùng 'name' hoặc 'type' đã tồn tại chưa
        for existing_func in data:
            if existing_func["name"] == cost_func["name"] or existing_func["type"] == cost_func["type"]:
                print(f"Hàm chi phí '{cost_func['name']}' hoặc kiểu '{cost_func['type']}' đã tồn tại, không thêm lại.")
                return
        
        # Nếu chưa tồn tại, thêm mới
        data.append(cost_func)
        with open(self.path, "w") as f:
            json.dump(data, f, indent=4)
        print(f"Đã thêm hàm chi phí: {cost_func['name']}")


    def diff(self, color1: str, color2: str) -> int:
        """Hàm diff: 0 nếu màu giống, 3 nếu khác"""
        return 0 if color1 == color2 else 3
    
    def EvaluateCall(self, operator: dict):
        """Tính chi phí của một phép biến đổi"""
        with open(self.path, "r") as f:
            cost_functions = json.load(f)

        for func in cost_functions:
            if func["type"] == operator["type"]:
                try:
                    local_env = dict(operator["params"])
                    local_env["diff"] = self.diff

                    cost = eval(func["formula"], {}, local_env)
                    return cost
                except Exception as e:
                    raise RuntimeError(f"Lỗi khi tính toán công thức: {e}")
        raise ValueError(f"Không tìm thấy hàm chi phí cho kiểu {operator['type']}")
