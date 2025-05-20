from dataclasses import dataclass
from typing import Callable, Dict, Tuple, Any, List, Optional, get_args, get_origin
import json
import os

TRANSFORMATION_JSON_FILE = "data/transformations.json"


@dataclass
class TransformationOperator:
    name: str
    parameters: Dict[str, type]
    apply_function: Callable[[Dict[str, Any], Any], Any]  # Apply to an object or coordinate

@dataclass
class InstantiatedOperator:
    operator: TransformationOperator
    params: Dict[str, Any]

    def apply(self, target):
        return self.operator.apply_function(self.params, target)

class TransformationLibraryManager:
    def __init__(self):
        self.operators: Dict[str, TransformationOperator] = {}

    def TLMinsert(self, operator: TransformationOperator):
        if operator.name in self.operators:
            raise ValueError(f"Operator {operator.name} already exists")
        self.operators[operator.name] = operator

    def TLMsearch(self, operator_name: str, params: Optional[Dict[str, Any]] = None) -> Optional[InstantiatedOperator]:
        if operator_name not in self.operators:
            return None
        # Chuyển list thành tuple nếu cần thiết

        operator = self.operators[operator_name]
        

        if params is not None:
            for param, value in params.items():
                expected_type = operator.parameters[param]
                if expected_type == Tuple[int, int, int] and isinstance(value, list):
                    value = tuple(value)
                    params[param] = value  # Cập nhật lại params
                origin = get_origin(expected_type)

                if origin is tuple:
                    if not isinstance(value, tuple):
                        raise TypeError(f"{param} phải là tuple")
                    inner_types = get_args(expected_type)
                    if len(value) != len(inner_types):
                        raise TypeError(f"{param} phải có {len(inner_types)} phần tử")
                    for i, (v, t) in enumerate(zip(value, inner_types)):
                        if not isinstance(v, t):
                            raise TypeError(f"Phần tử {i} của {param} phải là {t.__name__}")
                else:
                    # Tránh isinstance với typing.Generic
                    if hasattr(expected_type, '__origin__'):
                        raise TypeError(f"Không hỗ trợ kiểm tra kiểu: {expected_type}")
                    if not isinstance(value, expected_type):
                        raise TypeError(f"{param} phải là {expected_type.__name__}, nhưng nhận được {type(value).__name__}")

            return InstantiatedOperator(operator, params)

        return operator

    def list_operators(self) -> List[str]:
        return list(self.operators.keys())

# --- Apply functions ---
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
    
    obj.x1 = int(obj.x1)
    obj.x2 = obj.x1 + int(new_w)
    obj.y1 = int(obj.y1)
    obj.y2 = obj.y1 + int(new_h)
    
    return obj

def paint(params: Dict[str, Any], obj):
    color = params.get("color")
    if not isinstance(color, tuple) or len(color) != 3:
        raise ValueError("Tham số 'color' phải là tuple gồm 3 phần tử (r, g, b)")
    
    obj.color = color
    return obj

def move(params: Dict[str, Any], obj):
    axis = params["axis"].lower()
    distance = params["distance"]

    if axis == "x":
        obj.x1 += distance
        obj.x2 += distance
    elif axis == "y":
        obj.y1 += distance
        obj.y2 += distance
    else:
        raise ValueError("Tham số 'axis' phải là 'x' hoặc 'y'.")

    return obj


# --- Default operators ---
def create_default_object_operators() -> List[TransformationOperator]:
    return [
        TransformationOperator(
            name="translate",
            parameters={"dx": int, "dy": int},
            apply_function=translate_object
        ),
        TransformationOperator(
            name="scale",
            parameters={"scale": float},
            apply_function=scale_object
        ),
        TransformationOperator(
            name="nonuniform_scale",
            parameters={"scale_x": float, "scale_y": float},
            apply_function=nonuniform_scaling
        ),
        TransformationOperator(
            name="paint",
            parameters={"color": Tuple[int, int, int]},
            apply_function=paint
        ),
        TransformationOperator(
            name="move",
            parameters={"axis": str, "distance": int},
            apply_function=move
        ),
    ]

def load_transformations_from_json(filepath=TRANSFORMATION_JSON_FILE):
    if os.path.exists(filepath):
        with open(filepath, "r") as f:
            return json.load(f)
    return {"operators": []}

def save_transformations_to_json(data, filepath=TRANSFORMATION_JSON_FILE):
    with open(filepath, "w") as f:
        json.dump(data, f, indent=4)

def normalize_params(params):
    """Chuyển tất cả tuple trong params thành list để so sánh/lưu với JSON"""
    normalized = {}
    for key, val in params.items():
        if isinstance(val, tuple):
            normalized[key] = list(val)
        else:
            normalized[key] = val
    return normalized


def find_existing_operator(data, name, params):
    norm_params = normalize_params(params)
    for entry in data["operators"]:
        if entry["name"] == name and entry["parameters"] == norm_params:
            return entry
    return None


def add_operator_to_json(name, params, filepath=TRANSFORMATION_JSON_FILE):
    data = load_transformations_from_json(filepath)
    norm_params = normalize_params(params)

    if not find_existing_operator(data, name, norm_params):
        data["operators"].append({
            "name": name,
            "parameters": norm_params
        })
        save_transformations_to_json(data, filepath)
        return "Thêm tham số mới thành công."
    return "Tham số đã có trong thư viện."
