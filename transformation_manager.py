from dataclasses import dataclass
from typing import Callable, Dict, Any, List, Optional, Tuple, get_origin, get_args
import copy
from queue import PriorityQueue

import numpy as np

from cost_function_server import CostFunctionServer
import matplotlib.pyplot as plt
import matplotlib.patches as patches


@dataclass
class TransformationOperator:
    name: str
    parameters: Dict[str, type]
    apply_function: Callable[[Dict[str, Any], Any], Any]


@dataclass
class InstantiatedOperator:
    operator: TransformationOperator
    params: Dict[str, Any]

    def apply(self, target):
        return self.operator.apply_function(self.params, target)


@dataclass
class ImageObjectRegion:
    x1: int
    y1: int
    x2: int
    y2: int
    color: Optional[Tuple[int, int, int]] = None


class TransformationLibraryManager:
    def __init__(self):
        self.operators: Dict[str, TransformationOperator] = {}

    def TLMinsert(self, operator: TransformationOperator):
        self.operators[operator.name] = operator

    def TLMsearch(
        self, operator_name: str, params: Optional[Dict[str, Any]] = None
    ) -> Optional[InstantiatedOperator]:
        if operator_name not in self.operators:
            return None
        operator = self.operators[operator_name]
        return InstantiatedOperator(operator, params)


def translate_object(params: Dict[str, Any], obj):
    obj.x1 += params["dx"]
    obj.x2 += params["dx"]
    obj.y1 += params["dy"]
    obj.y2 += params["dy"]
    return obj


def scale_object(params: Dict[str, Any], obj):
    cx = (obj.x1 + obj.x2) / 2
    cy = (obj.y1 + obj.y2) / 2
    w = (obj.x2 - obj.x1) * params["scale"] / 2
    h = (obj.y2 - obj.y1) * params["scale"] / 2
    obj.x1 = int(cx - w)
    obj.x2 = int(cx + w)
    obj.y1 = int(cy - h)
    obj.y2 = int(cy + h)
    return obj


# def nonuniform_scaling(params: Dict[str, Any], obj):
#     # Scale theo chiều ngang nếu sx khác 1.0
#     if "sx" in params and params["sx"] != 1.0:
#         w = obj.x2 - obj.x1
#         new_w = w * params["sx"]
#         print("new_w", new_w)
#         obj.x2 = obj.x1 + int(new_w)

#     # Scale theo chiều dọc nếu sy khác 1.0
#     if "sy" in params and params["sy"] != 1.0:
#         h = obj.y2 - obj.y1
#         new_h = h * params["sy"]
#         obj.y2 = obj.y1 + int(new_h)

#     return obj


def nonuniform_scaling(params: Dict[str, Any], obj):
    # Scale theo chiều ngang nếu sx khác 1.0
    # ✅ Vẽ hình minh họa kết quả sau khi scale
    # fig, ax = plt.subplots()
    # canvas_size = 300
    # img = np.ones((canvas_size, canvas_size, 3), dtype=np.uint8) * 255  # ảnh nền trắng

    # ax.imshow(img)
    # rect = patches.Rectangle(
    #     (obj.x1, obj.y1),
    #     obj.x2 - obj.x1,
    #     obj.y2 - obj.y1,
    #     linewidth=2,
    #     edgecolor="blue",
    #     facecolor="none",
    # )
    # ax.add_patch(rect)
    # ax.set_title(
    #     f"Scaled Region: sx={params.get('sx', 1.0)}, sy={params.get('sy', 1.0)}"
    # )
    # plt.axis("off")
    # plt.show()
    if "sx" in params and params["sx"] != 1.0:
        w = obj.x2 - obj.x1
        new_w = w * params["sx"]
        print("new_w", new_w)
        obj.x2 = obj.x1 + int(new_w)

    # Scale theo chiều dọc nếu sy khác 1.0
    if "sy" in params and params["sy"] != 1.0:
        h = obj.y2 - obj.y1
        new_h = h * params["sy"]
        obj.y2 = obj.y1 + int(new_h)

    # ✅ Vẽ hình minh họa kết quả sau khi scale
    # fig, ax = plt.subplots()
    # canvas_size = 300
    # img = np.ones((canvas_size, canvas_size, 3), dtype=np.uint8) * 255  # ảnh nền trắng

    # ax.imshow(img)
    # rect = patches.Rectangle(
    #     (obj.x1, obj.y1),
    #     obj.x2 - obj.x1,
    #     obj.y2 - obj.y1,
    #     linewidth=2,
    #     edgecolor="blue",
    #     facecolor="none",
    # )
    # ax.add_patch(rect)
    # ax.set_title(
    #     f"Scaled Region: sx={params.get('sx', 1.0)}, sy={params.get('sy', 1.0)}"
    # )
    # plt.axis("off")
    # plt.show()

    return obj


# def paint(params: Dict[str, Any], obj):
#     obj.color = params["color"]
#     return obj


def paint(params: Dict[str, Any], obj):
    color1 = params["color1"]
    color2 = params["color2"]
    val1 = params["val1"]
    val2 = params["val2"]

    # ✅ Chỉ thực hiện nếu màu hiện tại khớp với val1
    if obj.color != val1:
        return obj  # Không thay đổi gì nếu màu không khớp

    # Nếu màu đúng thì mới thực hiện sơn lại
    obj.color = val2
    return obj


def move(params: Dict[str, Any], obj):
    if params["axis"] == "x":
        obj.x1 += params["distance"]
        obj.x2 += params["distance"]
    else:
        obj.y1 += params["distance"]
        obj.y2 += params["distance"]
    return obj


def create_default_object_operators() -> List[TransformationOperator]:
    return [
        TransformationOperator("translate", {"dx": int, "dy": int}, translate_object),
        TransformationOperator("scale", {"scale": float}, scale_object),
        TransformationOperator(
            "nonuniform_scaling", {"sx": float, "sy": float}, nonuniform_scaling
        ),
        TransformationOperator("paint", {"color": Tuple[int, int, int]}, paint),
        TransformationOperator("move", {"axis": str, "distance": int}, move),
    ]


class ObjectConvertor:
    def __init__(
        self, tlm: TransformationLibraryManager, cost_function: CostFunctionServer
    ):
        self.tlm = tlm
        self.cost_function = cost_function

    def convert(
        self, o1: ImageObjectRegion, o2: ImageObjectRegion
    ) -> Optional[Tuple[List[InstantiatedOperator], float]]:
        visited = set()
        pq = PriorityQueue()
        counter = 0
        pq.put((0, counter, [], o1))
        counter += 1

        while not pq.empty():
            print("pq", pq.queue)
            cost_so_far, _, path, current = pq.get()
            if self.objects_equal(current, o2):
                del pq
                del visited
                print("Found path")
                print("Path:", path)
                return path, cost_so_far  # ✅ Chỉ trả khi tìm thấy

            current_hash = self.hash_object(current)
            if current_hash in visited:
                continue
            visited.add(current_hash)
            for operator in self.tlm.operators.values():
                for params in self.generate_params(operator):
                    # try:
                    instantiated = self.tlm.TLMsearch(operator.name, params)
                    if instantiated is None:
                        continue

                    new_obj = copy.deepcopy(current)
                    new_obj = instantiated.apply(new_obj)
                    # print("new object", new_obj)

                    cost = self.cost_function.EvaluateCall(
                        {
                            "type": instantiated.operator.name,
                            "params": instantiated.params,
                        }
                    )

                    total_cost = cost_so_far + cost
                    pq.put((total_cost, counter, path + [instantiated], new_obj))
                    counter += 1
                # except Exception as e:
                #     print(
                #         "Error applying operator:",
                #         operator.name,
                #         " with params:",
                #         params,
                #     )
                #     print("erroe:", e)
                #     continue

        # ✅ Không tìm thấy đường đi → trả về None
        return None

    def hash_object(self, obj):
        return (obj.x1, obj.y1, obj.x2, obj.y2, obj.color)

    def objects_equal(self, o1, o2):
        return self.hash_object(o1) == self.hash_object(o2)

    def generate_params(self, operator: TransformationOperator):
        # if operator.name == "translate":
        #     for dx in [-30, -20, -10, 0, 10, 20, 30]:
        #         for dy in [-30, -20, -10, 0, 10, 20, 30]:
        #             yield {"dx": dx, "dy": dy}

        # elif operator.name == "scale":
        #     for s in [0.5, 1.0, 1.5, 2.0]:
        #         yield {"scale": s}
        if operator.name == "nonuniform_scaling":
            for sx in [1.0]:
                for sy in [2.0]:
                    yield {"sx": sx, "sy": sy}  # ✅ sửa đúng theo JSON
        elif operator.name == "paint":
            # for color1 in [
            #     "green",
            # ]:
            #     for color2 in ["green", "red"]:
            #         for val1 in [(255, 0, 0)]:
            #             for val2 in [(255, 0, 0), (0, 0, 255)]:
            #                 yield {
            #                     "color1": color1,
            #                     "color2": color2,
            #                     "val1": val1,
            #                     "val2": val2,
            #                 }
            yield {
                "color1": "green",
                "color2": "pink",
                "val1": (0, 0, 255),
                "val2": (255, 0, 0),
            }

        # elif operator.name == "move":
        #     for axis in ["x", "y"]:
        #         for d in [-10, 0, 10]:
        #             yield {"axis": axis, "distance": d}

        # elif operator.name == "rotate":
        #     for angle in [0, 45, 90, 180]:
        #         yield {"angle": angle}

        # elif operator.name == "Test":
        #     for a in [1, 2, 3]:
        #         for b in [4, 5, 6]:
        #             yield {"a": a, "b": b}

    # def generate_params(self, operator: TransformationOperator):
    #     if operator.name == "translate":
    #         for dx in [-30, -20, -10, 0, 10, 20, 30]:
    #             for dy in [-30, -20, -10, 0, 10, 20, 30]:
    #                 yield {"dx": dx, "dy": dy}
    #     elif operator.name == "scale":
    #         for s in [0.5, 1.0, 1.5, 2.0]:
    #             yield {"scale": s}
    #     elif operator.name == "nonuniform_scale":
    #         for sx in [0.5, 1.0, 1.5, 2.0]:
    #             for sy in [0.5, 1.0, 2.0]:
    #                 yield {"sx": sx, "sy": sy}
    #     elif operator.name == "paint":
    #         for color in [(255, 0, 0), (0, 255, 0), (0, 0, 255)]:
    #             yield {"color": color}
    #     elif operator.name == "move":
    #         for axis in ["x", "y"]:
    #             for d in [-10, 0, 10]:
    #                 yield {"axis": axis, "distance": d}


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


# --- CHẠY DEMO ---
# tlm = TransformationLibraryManager()
# for op in create_default_object_operators():
#     tlm.TLMinsert(op)

# o1 = ImageObjectRegion(10, 10, 20, 20, (0, 0, 255))
# o2 = ImageObjectRegion(10, 10, 20, 30, (255, 0, 0))


# converter = ObjectConvertor(tlm, simple_cost_function)
# result = converter.convert(o1, o2)

# # In ra các bước biến đổi
# if result:
#     for step in result:
#         print(f"{step.operator.name} {step.params}")
# else:
#     print("Khong tim duoc chuoi bien doi phu hop.")
