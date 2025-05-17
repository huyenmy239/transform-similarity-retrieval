from cost_function_server import CostFunctionServer

CFS = CostFunctionServer()

CFS.CostInsert({
    "name": "rotate_cost",
    "type": "rotate",
    "formula": "(angle / 180) ** 2"
})

CFS.CostInsert({
    "name": "scale_cost",
    "type": "scale",
    "formula": "(sx - 1)**2 + (sy - 1)**2"
})

CFS.CostInsert({
    "name": "paint_cost",
    "type": "paint",
    "formula": "(diff(color1, color2)) ** 3 + (val1 - val2) ** 2"
})

operator_paint = {
    "name": "paint_example",
    "type": "paint",
    "params": {
        "color1": "red",
        "val1": 10,
        "color2": "green",
        "val2": 7
    }
}

cost_paint = CFS.EvaluateCall(operator_paint)
print(f"Chi phí của phép biến đổi paint: {cost_paint}")