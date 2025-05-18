import json
import math
import os
import numpy as np
import math
import re


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

        for existing_func in data:
            if existing_func["name"].lower() == cost_func["name"].lower():
                raise Exception(
                    f"Hàm chi phí với tên '{cost_func['name']}' đã tồn tại."
                )
            if existing_func["type"].lower() == cost_func["type"].lower():
                raise Exception(
                    f"Hàm chi phí với kiểu '{cost_func['type']}' đã tồn tại."
                )

        data.append(cost_func)
        with open(self.path, "w") as f:
            json.dump(data, f, indent=4)

    def diff(self, color1: str, color2: str) -> int:
        """Hàm diff: 0 nếu màu giống, 3 nếu khác"""
        return 0 if color1 == color2 else 3

    def cbrt(self, x):
        """Hàm tính căn bậc ba."""
        return x ** (1 / 3)

    def fourthrt(self, x):
        """Hàm tính căn bậc bốn."""
        return x ** (1 / 4)

    def rgb_to_val(self, color):
        # Nếu color là chuỗi (ví dụ "(2,0,1)"), chuyển thành tuple
        if isinstance(color, str):
            try:
                # Dùng eval nếu input an toàn, hoặc parse tay
                color = eval(color)  # Cẩn thận: eval chỉ dùng nếu input đáng tin cậy
                # Hoặc an toàn hơn (nếu sợ lỗi cú pháp):
                # import re
                # color = tuple(map(float, re.findall(r"[-+]?\d*\.\d+|\d+", color)))
            except Exception:
                raise ValueError(f"khong the chuyen '{color}'thanh bo 3 RGB")

        # Kiểm tra đúng định dạng RGB
        if not isinstance(color, (tuple, list)) or len(color) != 3:
            raise ValueError(f"gia tri mau: {color}, phai la 3 phan tu (r, g, b)")

        r, g, b = color
        # print(f"--- Tính toán giá trị cho phép biến đổi ---")
        # print(f"--- RGB: {color} ---")
        # print(f"--- Giá trị: {0.299 * r + 0.587 * g + 0.114 * b} ---")
        return 0.299 * r + 0.587 * g + 0.114 * b

    def EvaluateCall(self, operator: dict):
        """Tính chi phí của một phép biến đổi"""

        with open(self.path, "r") as f:
            cost_functions = json.load(f)

        for func in cost_functions:
            if func["type"] == operator["type"]:
                try:
                    local_env = dict(operator["params"])
                    local_env["diff"] = self.diff

                    local_env["sqrt"] = math.sqrt
                    local_env["cbrt"] = self.cbrt
                    local_env["fourthrt"] = self.fourthrt
                    local_env["sum"] = sum  # Hỗ trợ hàm sum cho toán tử ∑
                    local_env["rgb_to_val"] = self.rgb_to_val

                    # Kiểm tra các biến cần thiết
                    all_vars = re.findall(
                        r"\b[a-zA-Z_][a-zA-Z0-9_]*\b", func["formula"]
                    )
                    reserved = {"diff", "sqrt", "cbrt", "fourthrt", "sum", "rgb_to_val"}
                    required_vars = set(v for v in all_vars if v not in reserved)
                    missing_vars = required_vars - set(operator["params"].keys())
                    if missing_vars:
                        raise ValueError(f"thieu cac bien: {', '.join(missing_vars)}")

                    cost = eval(func["formula"], {}, local_env)
                    return cost
                except NameError as e:
                    raise RuntimeError(f"loi: bien hoac ham khong xac dinh: {e}")
                except Exception as e:
                    raise RuntimeError(f"loi khi tinh toan cong thuc: {e}")
        raise ValueError(f"khong tim thay cong thuc cho kieu {operator['type']}")
