from typing import Callable, List, Optional, Tuple
from scipy.optimize import linear_sum_assignment
import numpy as np
from object_manager import ImageMeta, ImageObjectRegion
from transformation_manager import (
    InstantiatedOperator,
    ObjectConvertor,
    TransformationLibraryManager,
    create_default_object_operators,
)
from typing import List, Tuple
import numpy as np
from cost_function_server import CostFunctionServer


def compute_matching_using_hungarian(
    image1: ImageMeta,
    image2: ImageMeta,
    tlm: TransformationLibraryManager,
    cost_server: CostFunctionServer,
) -> List[
    Tuple[ImageObjectRegion, ImageObjectRegion, float, List[InstantiatedOperator]]
]:
    objs1 = image1.objects
    objs2 = image2.objects
    n = len(objs1)
    m = len(objs2)
    converter = ObjectConvertor(tlm, cost_server)

    # === ✅ Trường hợp đặc biệt 1: Mỗi ảnh chỉ có 1 đối tượng
    if n == 1 and m == 1:
        result = converter.convert(objs1[0], objs2[0])
        if result:
            ops, cost = result
            return [(objs1[0], objs2[0], cost, ops)]
        else:
            print("ket qua", result)
            print(f"[ERROR] khong tim duoc chuoi bien doi tu {objs1[0]} - {objs2[0]}")
            return [(objs1[0], objs2[0], None, None)]
        # return [(objs1[0], objs2[0], None, None)]

    # === Khởi tạo ma trận chi phí
    cost_matrix = np.full((n, m), 1e9)
    all_paths: List[List[Optional[List[InstantiatedOperator]]]] = [
        [None for _ in range(m)] for _ in range(n)
    ]

    for i in range(n):
        for j in range(m):
            s1 = objs1[i]
            s2 = objs2[j]
            result = converter.convert(s1, s2)
            if result:
                ops, cost = result
                cost_matrix[i][j] = cost
                all_paths[i][j] = ops
            else:
                print(f"[ERROR] khong tim duoc chuoi bien doi tu {s1} - {s2}")
                cost_matrix[i][j] = 1e9
                all_paths[i][j] = None

    # === Giải bài toán gán bằng Hungarian
    row_ind, col_ind = linear_sum_assignment(cost_matrix)

    result = []
    matched_rows = set()
    matched_cols = set()

    for i, j in zip(row_ind, col_ind):
        if all_paths[i][j] is not None:
            result.append((objs1[i], objs2[j], cost_matrix[i][j], all_paths[i][j]))
            matched_rows.add(i)
            matched_cols.add(j)

    # ✅ Kiểm tra nếu còn đúng 1 đối tượng chưa ghép ở mỗi ảnh
    unmatched_i = list(set(range(n)) - matched_rows)
    unmatched_j = list(set(range(m)) - matched_cols)

    if len(unmatched_i) == 1 and len(unmatched_j) == 1:
        remaining_i = unmatched_i[0]
        remaining_j = unmatched_j[0]

        s1 = objs1[remaining_i]
        s2 = objs2[remaining_j]

        print(f"[ WARNING] con mot cap chua ghep: chi so {remaining_i} - {remaining_j}")
        print(f"   Doi tuong anh 1: {s1}")
        print(f"   Doi tuong anh 2: {s2}")

        result.append((s1, s2, None, None))  # vẫn ghép nhưng không có chuyển đổi
    # === ✅ Lưu kết quả nếu có
    if result:
        with open("matching_result.txt", "w", encoding="utf-8") as f:
            for idx, (obj1, obj2, cost, ops) in enumerate(result):
                f.write(f"[Match {idx + 1}]\n")
                f.write(f"Object 1: ({obj1.x1}, {obj1.y1}, {obj1.x2}, {obj1.y2})\n")
                f.write(f"Object 2: ({obj2.x1}, {obj2.y1}, {obj2.x2}, {obj2.y2})\n")
                if cost is not None and ops is not None:
                    f.write(f"Cost: {cost:.4f}\n")
                    f.write("Transformations:\n")
                    for step in ops:
                        f.write(f"  - {step.operator.name} {step.params}\n")
                else:
                    f.write("No transformation found.\n")
                f.write("\n")  # dòng trống giữa các cặp
        print("[INFO] ket qua da duoc luu vao 'matching_result.txt'")
    return result


cost_server = CostFunctionServer("data/cost_function.json")

# Đảm bảo bạn đã thêm các hàm chi phí vào file trước khi gọi
CFS = CostFunctionServer()


# def simple_cost_function(instantiated_operator: InstantiatedOperator):
#     name = instantiated_operator.operator.name
#     if name == "translate":
#         return abs(instantiated_operator.params["dx"]) + abs(
#             instantiated_operator.params["dy"]
#         )
#     elif name == "scale":
#         return abs(instantiated_operator.params["scale"] - 1.0) * 10
#     elif name == "nonuniform_scale":
#         sx = instantiated_operator.params["scale_x"]
#         sy = instantiated_operator.params["scale_y"]
#         return (abs(sx - 1.0) + abs(sy - 1.0)) * 10
#     elif name == "paint":
#         return 5
#     elif name == "move":
#         return abs(instantiated_operator.params["distance"])
#     return 1


# Khởi tạo thư viện biến đổi
tlm = TransformationLibraryManager()
for op in create_default_object_operators():
    print(op.name)
    tlm.TLMinsert(op)

# --- Khởi tạo ví dụ 2 ảnh ---
image1 = ImageMeta(
    name="image1",
    width=6,
    height=6,
    objects=[
        ImageObjectRegion(10, 10, 20, 20, (0, 0, 255)),
        # ImageObjectRegion(10, 10, 20, 20, (255, 0, 0)),
        # ImageObjectRegion(10, 10, 20, 20, (255, 0, 0)),
    ],
)

image2 = ImageMeta(
    name="image2",
    width=6,
    height=6,
    objects=[
        ImageObjectRegion(10, 10, 20, 20, (255, 0, 0)),
        # ImageObjectRegion(10, 10, 20, 20, (0, 0, 255)),
        # ImageObjectRegion(10, 10, 20, 20, (255, 0, 0)),
    ],
)

result = compute_matching_using_hungarian(image1, image2, tlm, CFS)

for obj1, obj2, cost, steps in result:
    print(f"{obj1} - {obj2} (Chi phi: {cost})")

    # for step in steps:
    #     print(f"  - {step.operator.name} {step.params}")
