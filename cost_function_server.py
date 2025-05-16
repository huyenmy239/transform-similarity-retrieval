import json
import cv2
import numpy as np
import os

class CostFunctionServer:
    def __init__(self):
        self.cost_functions = []

    def CostInsert(self, cost_function: dict):
        if "name" in cost_function and "type" in cost_function and "formula" in cost_function:
            self.cost_functions.append(cost_function)
            print(f"Hàm chi phí '{cost_function['name']}' đã được thêm.")
        else:
            raise ValueError("Hàm chi phí phải có name, type, và formula.")

    def EvaluateCall(self, operator: dict):
        op_type = operator.get("type")
        params = operator.get("params", {})
        for cost_func in self.cost_functions:
            if cost_func["type"] == op_type:
                try:
                    formula = cost_func["formula"]
                    cost = eval(formula, {}, params)
                    print(f"Cost của phép '{op_type}':", cost)
                    return cost
                except Exception as e:
                    raise RuntimeError(f"Lỗi khi đánh giá công thức: {e}")
        raise ValueError(f"Không tìm thấy hàm chi phí cho phép biến đổi '{op_type}'.")


def apply_transformation(img, operator: dict):
    op_type = operator["type"]
    params = operator["params"]

    if op_type == "scale":
        sx, sy = params["sx"], params["sy"]
        h, w = img.shape[:2]
        return cv2.resize(img, (int(w * sx), int(h * sy)))

    elif op_type == "translate":
        dx, dy = params["dx"], params["dy"]
        h, w = img.shape[:2]
        M = np.float32([[1, 0, dx], [0, 1, dy]])
        return cv2.warpAffine(img, M, (w, h))

    elif op_type == "rotate":
        angle = params["angle"]
        h, w = img.shape[:2]
        center = (w / 2, h / 2)

        # Tính ma trận xoay ban đầu
        M = cv2.getRotationMatrix2D(center, angle, 1.0)

        # Tính toán kích thước mới của ảnh
        cos = np.abs(M[0, 0])
        sin = np.abs(M[0, 1])
        new_w = int((h * sin) + (w * cos))
        new_h = int((h * cos) + (w * sin))

        # Điều chỉnh ma trận để di chuyển ảnh vào giữa
        M[0, 2] += (new_w / 2) - center[0]
        M[1, 2] += (new_h / 2) - center[1]

        # Áp dụng phép biến đổi với kích thước mới
        return cv2.warpAffine(img, M, (new_w, new_h))


    elif op_type == "brightness":
        factor = params["factor"]
        bright_img = cv2.convertScaleAbs(img, alpha=factor, beta=0)
        return bright_img

    else:
        raise ValueError(f"Không hỗ trợ phép biến đổi '{op_type}'.")


def resize_for_display(img, width=800):
    h, w = img.shape[:2]
    ratio = width / w
    new_dim = (width, int(h * ratio))
    return cv2.resize(img, new_dim)

if __name__ == "__main__":
    # Khởi tạo server
    server = CostFunctionServer()

    # Thêm các hàm chi phí
    server.CostInsert({"name": "scale_cost", "type": "scale", "formula": "(sx - 1)**2 + (sy - 1)**2"})
    server.CostInsert({"name": "translate_cost", "type": "translate", "formula": "dx**2 + dy**2"})
    server.CostInsert({"name": "rotate_cost", "type": "rotate", "formula": "(angle/180)**2"})
    server.CostInsert({"name": "brightness_cost", "type": "brightness", "formula": "(factor - 1)**2"})

    # Load ảnh
    img = cv2.imread(r"images/test.jpg")
    if img is None:
        raise ValueError("Không load được ảnh")

    # Thay đổi phép biến đổi để test:
    # operator = {
    #     "type": "scale",
    #     "params": {
    #         "sx": 2.0,
    #         "sy": 1.5
    #     }
    # }
    operator = {
    "type": "translate",
    "params": {
        "dx": 100,
        "dy": 50
    }
}
#     operator = {
#     "type": "rotate",
#     "params": {
#         "angle": 90
#     }
# }
    # operator = {
    #     "type": "brightness",
    #     "params": {
    #         "factor": 1.3
    #     }
    # }



    # Áp dụng phép biến đổi và tính chi phí
    transformed_img = apply_transformation(img, operator)
    cost = server.EvaluateCall(operator)

    # Hiển thị ảnh
    cv2.imshow("Original", resize_for_display(img))
    cv2.imshow(f"{operator['type'].capitalize()} Result", resize_for_display(transformed_img))
    cv2.waitKey(0)
    cv2.destroyAllWindows()

    # Lưu kết quả
    cv2.imwrite(f"results/{operator['type']}_result.jpg", transformed_img)
