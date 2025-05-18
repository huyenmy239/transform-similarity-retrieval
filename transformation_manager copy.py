from dataclasses import dataclass
from typing import Callable, Dict, Any, List, Optional, Tuple, get_origin, get_args
import copy
from queue import PriorityQueue
from cost_function_server import CostFunctionServer

import matplotlib.pyplot as plt
from PIL import Image, ImageDraw


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


def nonuniform_scaling(params: Dict[str, Any], obj):
    new_w = (obj.x2 - obj.x1) * params["scale_x"]
    new_h = (obj.y2 - obj.y1) * params["scale_y"]
    obj.x2 = obj.x1 + int(new_w)
    obj.y2 = obj.y1 + int(new_h)
    return obj


def paint(params: Dict[str, Any], obj):
    obj.color = params["color"]
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
            "nonuniform_scale", {"scale_x": float, "scale_y": float}, nonuniform_scaling
        ),
        TransformationOperator("paint", {"color": Tuple[int, int, int]}, paint),
        TransformationOperator("move", {"axis": str, "distance": int}, move),
    ]


class ObjectConvertor:

    def __init__(
        self, tlm: TransformationLibraryManager, cost_server: CostFunctionServer
    ):
        self.tlm = tlm
        self.cost_server = cost_server

    # def convert(
    #     self, o1: ImageObjectRegion, o2: ImageObjectRegion
    # ) -> Optional[List[InstantiatedOperator]]:
    #     visited = set()
    #     pq = PriorityQueue()
    #     counter = 0
    #     pq.put((0, counter, [], o1))
    #     counter += 1

    #     while not pq.empty():
    #         cost_so_far, _, path, current = pq.get()

    #         if self.objects_equal(current, o2):
    #             return path, cost_so_far  # Trả về cả path và cost

    #         current_hash = self.hash_object(current)
    #         if current_hash in visited:
    #             continue
    #         visited.add(current_hash)

    #         for operator in self.tlm.operators.values():
    #             for params in self.generate_params(operator):
    #                 try:
    #                     instantiated = self.tlm.TLMsearch(operator.name, params)
    #                     new_obj = copy.deepcopy(current)
    #                     new_obj = instantiated.apply(new_obj)

    #                     # Tính chi phí bằng CostFunctionServer
    #                     operator_dict = {
    #                         "type": instantiated.operator.name,
    #                         "params": instantiated.params,
    #                     }
    #                     step_cost = self.cost_server.EvaluateCall(operator_dict)
    #                     print(
    #                         f"Cost from {current} to {new_obj}: {step_cost} (params: {params})")
    #                     total_cost = cost_so_far + step_cost
    #                     pq.put((total_cost, counter, path + [instantiated], new_obj))
    #                     counter += 1
    #                 except Exception:
    #                     continue
    #     return None, float("inf")
    def convert(
        self, o1: ImageObjectRegion, o2: ImageObjectRegion, visualize: bool = False
    ) -> Optional[Tuple[List[InstantiatedOperator], float]]:
        visited = set()
        pq = PriorityQueue()
        counter = 0
        pq.put((0, counter, [], o1))
        counter += 1

        if visualize:
            print("Ảnh bắt đầu:")
            self.display_object(o1, "Start")

        while not pq.empty():
            cost_so_far, _, path, current = pq.get()

            if self.objects_equal(current, o2):
                if visualize:
                    print("Ảnh kết thúc:")
                    self.display_object(current, "Target reached")
                return path, cost_so_far

            current_hash = self.hash_object(current)
            if current_hash in visited:
                continue
            visited.add(current_hash)

            for operator in self.tlm.operators.values():
                for params in self.generate_params(operator):
                    try:
                        instantiated = self.tlm.TLMsearch(operator.name, params)
                        new_obj = copy.deepcopy(current)
                        new_obj = instantiated.apply(new_obj)

                        operator_dict = {
                            "type": instantiated.operator.name,
                            "params": instantiated.params,
                        }
                        step_cost = self.cost_server.EvaluateCall(operator_dict)
                        total_cost = cost_so_far + step_cost

                        if visualize:
                            print(f"{instantiated.operator.name} {instantiated.params}")
                            self.display_object(
                                new_obj, f"{instantiated.operator.name}"
                            )

                        pq.put((total_cost, counter, path + [instantiated], new_obj))
                        counter += 1
                    except Exception:
                        continue
        return None, float("inf")

    def display_object(self, obj: ImageObjectRegion, title: str = ""):
        img = Image.new("RGB", (100, 100), (255, 255, 255))
        draw = ImageDraw.Draw(img)
        color = obj.color if obj.color else (0, 0, 0)
        draw.rectangle([obj.x1, obj.y1, obj.x2, obj.y2], fill=color, outline=(0, 0, 0))

        plt.imshow(img)
        plt.title(title)
        plt.axis("off")
        plt.show()

    def hash_object(self, obj):
        return (obj.x1, obj.y1, obj.x2, obj.y2, obj.color)

    def objects_equal(self, o1, o2):
        return self.hash_object(o1) == self.hash_object(o2)

    def generate_params(self, operator: TransformationOperator):
        if operator.name == "translate":
            for dx in [-30, -20, -10, 0, 10, 20, 30]:
                for dy in [-30, -20, -10, 0, 10, 20, 30]:
                    yield {"dx": dx, "dy": dy}
        elif operator.name == "scale":
            for s in [0.5, 1.0, 1.5, 2.0]:
                yield {"scale": s}
        elif operator.name == "nonuniform_scale":
            for sx in [0.5, 1.0, 1.5, 2.0]:
                for sy in [0.5, 1.0, 2.0]:
                    yield {"scale_x": sx, "scale_y": sy}
        elif operator.name == "paint":
            for color in [(255, 0, 0), (0, 255, 0), (0, 0, 255)]:
                yield {"color": color}
        elif operator.name == "move":
            for axis in ["x", "y"]:
                for d in [-10, 0, 10]:
                    yield {"axis": axis, "distance": d}


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
tlm = TransformationLibraryManager()
for op in create_default_object_operators():
    tlm.TLMinsert(op)

o1 = ImageObjectRegion(10, 10, 20, 20, (0, 0, 255))
o2 = ImageObjectRegion(10, 10, 20, 30, (255, 0, 0))
CFS = CostFunctionServer()

CFS.CostInsert(
    {"name": "rotate_cost", "type": "rotate", "formula": "(angle / 180) ** 2"}
)

CFS.CostInsert(
    {"name": "scale_cost", "type": "scale", "formula": "(sx - 1)**2 + (sy - 1)**2"}
)

CFS.CostInsert(
    {
        "name": "paint_cost",
        "type": "paint",
        "formula": "(diff(color1, color2)) ** 3 + (val1 - val2) ** 2",
    }
)
CFS.CostInsert(
    {
        "name": "nonuniform_scaling_cost",
        "type": "nonuniform_scaling",
        "formula": "(sx - sqrt(sx * sy))**2 + (sy - sqrt(sx * sy))**2",
    }
)


converter = ObjectConvertor(tlm, CFS)
result, cost = converter.convert(o1, o2)

# In ra các bước biến đổi
if result:
    for step in result:
        print(f"{step.operator.name} {step.params}")
    print(f"Chi phi: {cost}")

else:
    print("Khong tim duoc chuoi bien doi phu hop.")
