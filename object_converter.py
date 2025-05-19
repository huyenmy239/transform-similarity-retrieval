import json
import os
import copy
from queue import PriorityQueue
from typing import Optional, List

from transformation_manager import TransformationLibraryManager, InstantiatedOperator, create_default_object_operators
from object_manager import ImageObjectRegion
from cost_function_server import CostFunctionServer

class ObjectConvertor:
    def __init__(self, tlm, cost_function_server, transformations_file):
        self.tlm = tlm
        self.cost_function_server = cost_function_server
        self.transformations_data = self.load_transformations(transformations_file)

    def convert(self, o1: ImageObjectRegion, o2: ImageObjectRegion, max_steps=1000, max_coord=10000) -> Optional[List[InstantiatedOperator]]:
        # Kiểm tra nếu object 1 và object 2 giống nhau (không xét tên)
        if self.objects_equal(o1, o2):
            print("Giống nhau")
            return []

        visited = set()
        pq = PriorityQueue()
        counter = 0
        pq.put((0 + self.heuristic(o1, o2), 0, counter, [], o1))  # (f_score, cost_so_far, counter, path, current)
        counter += 1
        step_count = 0

        while not pq.empty() and step_count < max_steps:
            step_count += 1
            f_score, cost_so_far, _, path, current = pq.get()

            if self.objects_equal(current, o2):
                print(f"Found solution after {step_count} steps")
                return path

            current_hash = self.hash_object(current)
            if current_hash in visited:
                continue
            visited.add(current_hash)

            for operator in self.tlm.operators.values():
                for params in self.generate_params(operator):
                    try:
                        instantiated = self.tlm.TLMsearch(operator.name, params)
                        if instantiated is None:
                            continue

                        new_obj = copy.deepcopy(current)
                        new_obj = instantiated.apply(new_obj)

                        # Giới hạn tọa độ để tránh trạng thái không hợp lý
                        if (new_obj.x1 < 0 or new_obj.y1 < 0 or 
                            new_obj.x2 > max_coord or new_obj.y2 > max_coord):
                            continue

                        operator_data = {
                            "type": instantiated.operator.name,
                            "params": {
                                **instantiated.params,
                                "color1": getattr(current, "color", (0, 0, 0)),
                                "color2": getattr(new_obj, "color", (0, 0, 0)),
                                "val1": getattr(current, "color", (0, 0, 0)),
                                "val2": getattr(new_obj, "color", (0, 0, 0)),
                                "dx": instantiated.params.get("dx", 0),
                                "dy": instantiated.params.get("dy", 0),
                                "scale": instantiated.params.get("scale", 1.0),
                                "sx": instantiated.params.get("scale_x", 1.0),
                                "sy": instantiated.params.get("scale_y", 1.0),
                                "angle": instantiated.params.get("angle", 0),
                                "a": instantiated.params.get("a", 0),
                                "b": instantiated.params.get("b", 0),
                                "area": (current.x2 - current.x1) * (current.y2 - current.y1),
                            }
                        }
                        cost = self.cost_function_server.EvaluateCall(operator_data)
                        new_cost = cost_so_far + cost
                        f_score = new_cost + self.heuristic(new_obj, o2)

                        pq.put((f_score, new_cost, counter, path + [instantiated], new_obj))
                        counter += 1
                    except Exception as e:
                        print(f"Error processing {operator.name} with params {params}: {e}")
                        continue
            print(f"Step {step_count}, queue size: {pq.qsize()}, visited: {len(visited)}")
        print(f"Stopped after {step_count} steps")
        return None
    
    def hash_object(self, obj):
        return (obj.x1, obj.y1, obj.x2, obj.y2, obj.color)

    def objects_equal(self, o1, o2):
        return self.hash_object(o1) == self.hash_object(o2)
    
    def heuristic(self, current: ImageObjectRegion, goal: ImageObjectRegion) -> float:
        current_width = current.x2 - current.x1
        current_height = current.y2 - current.y1
        goal_width = goal.x2 - goal.x1
        goal_height = goal.y2 - goal.y1
        scale_x_cost = abs(current_width - goal_width) / max(current_width, 1)
        scale_y_cost = abs(current_height - goal_height) / max(current_height, 1)
        size_cost = scale_x_cost + scale_y_cost
        color_cost = 3.0 if current.color != goal.color else 0.0
        # Thêm chi phí vị trí
        position_cost = (abs(current.x1 - goal.x1) + abs(current.y1 - goal.y1)) / 100
        return size_cost + color_cost + position_cost

    def load_transformations(self, filepath):
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Không tìm thấy file transformations: {filepath}")
        with open(filepath, "r") as f:
            return json.load(f).get("operators", [])

    def generate_params(self, operator):
        name = operator.name
        for entry in self.transformations_data:
            if entry["name"] == name:
                # Tự động chuyển list -> tuple nếu cần (ví dụ color)
                params = entry["parameters"]
                for key, value in params.items():
                    expected_type = operator.parameters.get(key)
                    if expected_type == tuple or (hasattr(expected_type, "__origin__") and expected_type.__origin__ == tuple):
                        if isinstance(value, list):
                            params[key] = tuple(value)
                yield params



# --- CHẠY DEMO ---
# tlm = TransformationLibraryManager()
# for op in create_default_object_operators():
#     tlm.TLMinsert(op)

# o1 = ImageObjectRegion("hihi", 400, 200, 500, 300, (0, 255, 0))
# o2 = ImageObjectRegion("hi", 400, 200, 500, 400, (255, 0, 255))

# cfs = CostFunctionServer()


# converter = ObjectConvertor(tlm, cfs, transformations_file="data/transformations.json")

# result = converter.convert(o1, o2)

# # In ra các bước biến đổi
# if result:
#     for step in result:
#         print(f"{step.operator.name} {step.params}")
# else:
#     print("Không tìm được chuỗi biến đổi phù hợp.")
