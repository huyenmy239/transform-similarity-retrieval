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
    cost_matrix = np.full((n, m), np.inf)
    all_paths: List[List[Optional[List[InstantiatedOperator]]]] = [
        [None for _ in range(m)] for _ in range(n)
    ]

    converter = ObjectConvertor(tlm, cost_server)

    for i in range(n):
        for j in range(m):
            s1 = objs1[i]
            s2 = objs2[j]
            ops = converter.convert(s1, s2)
            if ops is None:
                print(f" khong tim duoc chuoi bien doi tu {s1} - {s2}")
                
            if ops is not None:
                cost_matrix[i][j] = 1
                all_paths[i][j] = ops

            print(f"Cost from {s1} to {s2}: (ops: {ops})")
    print("---", cost_matrix[i][j], print(all_paths[i][j]))
    row_ind, col_ind = linear_sum_assignment(cost_matrix)

    result = []
    for i, j in zip(row_ind, col_ind):
        if all_paths[i][j] is not None:
            result.append((objs1[i], objs2[j], cost_matrix[i][j], all_paths[i][j]))

    return result


cost_server = CostFunctionServer("data/cost_function.json")

# Đảm bảo bạn đã thêm các hàm chi phí vào file trước khi gọi
CFS = CostFunctionServer()

# CFS.CostInsert(
#     {"name": "rotate_cost", "type": "rotate", "formula": "(angle / 180) ** 2"}
# )

# CFS.CostInsert(
#     {"name": "scale_cost", "type": "scale", "formula": "(sx - 1)**2 + (sy - 1)**2"}
# )

# CFS.CostInsert(
#     {
#         "name": "paint_cost",
#         "type": "paint",
#         "formula": "(diff(color1, color2)) ** 3 + (val1 - val2) ** 2",
#     }
# )
# CFS.CostInsert(
#     {
#         "name": "nonuniform_scaling_cost",
#         "type": "nonuniform_scaling",
#         "formula": "(sx - sqrt(sx * sy))**2 + (sy - sqrt(sx * sy))**2",
#     }
# )


def simple_cost_function(instantiated_operator: InstantiatedOperator):
    name = instantiated_operator.operator.name
    if name == "translate":
        return abs(instantiated_operator.params["dx"]) + abs(
            instantiated_operator.params["dy"]
        )
    elif name == "scale":
        return abs(instantiated_operator.params["scale"] - 1.0) * 10
    elif name == "nonuniform_scale":
        sx = instantiated_operator.params["scale_x"]
        sy = instantiated_operator.params["scale_y"]
        return (abs(sx - 1.0) + abs(sy - 1.0)) * 10
    elif name == "paint":
        return 5
    elif name == "move":
        return abs(instantiated_operator.params["distance"])
    return 1


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
        ImageObjectRegion(20, 10, 20, 20, (0, 0, 255)),
        # ImageObjectRegion(20, 10, 20, 20, (255, 0, 0)),
    ],
)

image2 = ImageMeta(
    name="image2",
    width=6,
    height=6,
    objects=[
        ImageObjectRegion(20, 10, 20, 20, (255, 0, 0)),
        # ImageObjectRegion(10, 10, 20, 20, (255, 0, 0)),
    ],
)

result = compute_matching_using_hungarian(image1, image2, tlm, simple_cost_function)

for obj1, obj2, cost, steps in result:
    print(f"{obj1} - {obj2} (Chi phi: {cost})")

    for step in steps:
        print(f"  - {step.operator.name} {step.params}")
