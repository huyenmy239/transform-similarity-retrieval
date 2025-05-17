from cost_function_server import CostFunctionServer
import numpy as np

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
val1 = np.ones((2, 2, 3), dtype=np.uint8) * 100
val2 = np.ones((2, 2, 3), dtype=np.uint8) * 120

operator_paint = {
    "name": "paint_example",
    "type": "paint",
    "params": {
        "color1": "red",
        "val1": val1,
        "color2": "green",
        "val2": val2,
    },
}
operator_nonuniform_scaling = {
    "type": "nonuniform_scaling",
    "params": {"sx": 1.0, "sy": 1.5},
}
cost_paint = CFS.EvaluateCall(operator_paint)
print(f"Chi phí của phép biến đổi paint: {cost_paint}")
cost_nonuniform_scaling = CFS.EvaluateCall(operator_nonuniform_scaling)
print(
    f"Chi phí của phép biến đổi nonuniform scaling: {cost_nonuniform_scaling}"
)  # ~0.126
