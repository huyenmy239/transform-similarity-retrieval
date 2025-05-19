import numpy as np
from PIL import Image
from collections import defaultdict
import math
from typing import Dict, List, Tuple, Optional, Callable, Any
from dataclasses import dataclass
import heapq

# --------------------------
# Core Data Structures
# --------------------------


@dataclass
class TransformationOperator:
    """Represents a transformation operator that can be applied to images"""
    name: str
    parameters: Dict[str, type]  # Parameter names and their types
    apply_function: Callable[[np.ndarray, Dict[str, Any]], np.ndarray]  # Applies transformation to image

@dataclass
class InstantiatedOperator:
    """An operator with specific parameter values"""
    operator: TransformationOperator
    params: Dict[str, Any]
    
    def cost(self) -> float:
        return self.operator.cost_function(self.params)
    
    def apply(self, image: np.ndarray) -> np.ndarray:
        return self.operator.apply_function(image, self.params)

class TransformationSequence:
    """Sequence of transformation operations to apply to an image"""
    def __init__(self):
        self.operations: List[InstantiatedOperator] = []
        
    def add_operation(self, op: InstantiatedOperator):
        self.operations.append(op)
        
    def apply(self, image: np.ndarray) -> np.ndarray:
        current_image = image.copy()
        for op in self.operations:
            current_image = op.apply(current_image)
        return current_image

# --------------------------
# Transformation Library Manager
# --------------------------

class TransformationLibraryManager:
    """Manages a library of transformation operators"""
    def __init__(self):
        self.operators: Dict[str, TransformationOperator] = {}
        
    def TLMinsert(self, operator: TransformationOperator):
        """Add a new transformation operator to the library"""
        if operator.name in self.operators:
            raise ValueError(f"Operator {operator.name} already exists")
        self.operators[operator.name] = operator
        
    def TLMsearch(self, operator_name: str, params: Optional[Dict[str, Any]] = None) -> Optional[InstantiatedOperator]:
        """Retrieve an operator by name, optionally with parameters"""
        if operator_name not in self.operators:
            return None
            
        operator = self.operators[operator_name]
        if params is not None:
            # Validate parameters
            if set(params.keys()) != set(operator.parameters.keys()):
                raise ValueError("Parameter mismatch")
            for param, value in params.items():
                if not isinstance(value, operator.parameters[param]):
                    raise TypeError(f"Parameter {param} should be {operator.parameters[param]}, got {type(value)}")
            return InstantiatedOperator(operator, params)
        return operator
        
    def list_operators(self) -> List[str]:
        """List all available operator names"""
        return list(self.operators.keys())

# --------------------------
# Image Processing Utilities
# --------------------------

def load_image(path: str) -> np.ndarray:
    """Load an image from file into a numpy array"""
    img = Image.open(path)
    return np.array(img)

def save_image(image: np.ndarray, path: str):
    """Save a numpy array as an image"""
    Image.fromarray(image).save(path)

# --------------------------
# Transformation Operators
# --------------------------

def create_default_operators() -> List[TransformationOperator]:
    """Create a set of default transformation operators"""
    operators = []
    
    # Translation operator
    operators.append(TransformationOperator(
        name="translate",
        parameters={"dx": int, "dy": int},
        apply_function=lambda img, params: np.roll(img, (params["dy"], params["dx"]), axis=(0, 1))
    ))
    
    # Rotation operator
    operators.append(TransformationOperator(
        name="rotate",
        parameters={"angle": float},
        apply_function=lambda img, params: rotate_image(img, params["angle"])
    ))
    
    # Scaling operator
    operators.append(TransformationOperator(
        name="scale",
        parameters={"factor": float},
        apply_function=lambda img, params: scale_image(img, params["factor"])
    ))
    
    # Color adjustment operator
    operators.append(TransformationOperator(
        name="adjust_color",
        parameters={"channel": int, "delta": int},  # channel: 0=R, 1=G, 2=B
        apply_function=lambda img, params: adjust_color_channel(img, params["channel"], params["delta"])
    ))
    
    # Paint region operator
    operators.append(TransformationOperator(
        name="paint_region",
        parameters={
            "x1": int, "y1": int, "x2": int, "y2": int,  # Region coordinates
            "color": tuple  # (R, G, B)
        },
        apply_function=lambda img, params: paint_region(img, params)
    ))

    # Non-uniform scaling operator
    operators.append(TransformationOperator(
        name="nonuniform_scale",
        parameters={"scale_x": float, "scale_y": float},
        apply_function=lambda img, params: nonuniform_scale_image(img, params["scale_x"], params["scale_y"])
    ))
    
    return operators

def rotate_image(img: np.ndarray, angle: float) -> np.ndarray:
    """Rotate image by specified angle in degrees"""
    pil_img = Image.fromarray(img)
    return np.array(pil_img.rotate(angle))

def scale_image(img: np.ndarray, factor: float) -> np.ndarray:
    """Scale image by specified factor"""
    if factor <= 0:
        raise ValueError("Scale factor must be positive")
    h, w = img.shape[:2]
    pil_img = Image.fromarray(img)
    return np.array(pil_img.resize((int(w * factor), int(h * factor))))

def adjust_color_channel(img: np.ndarray, channel: int, delta: int) -> np.ndarray:
    """Adjust a specific color channel by delta value"""
    if channel < 0 or channel > 2:
        raise ValueError("Channel must be 0 (R), 1 (G), or 2 (B)")
    img = img.copy()
    img[:, :, channel] = np.clip(img[:, :, channel].astype(int) + delta, 0, 255)
    return img

def paint_region(img: np.ndarray, params: Dict[str, Any]) -> np.ndarray:
    """Paint a rectangular region with specified color"""
    x1, y1 = max(0, params["x1"]), max(0, params["y1"])
    x2, y2 = min(img.shape[1], params["x2"]), min(img.shape[0], params["y2"])
    img = img.copy()
    img[y1:y2, x1:x2] = params["color"]
    return img

def nonuniform_scale_image(img: np.ndarray, scale_x: float, scale_y: float) -> np.ndarray:
    """Scale image non-uniformly by scale_x and scale_y"""
    if scale_x <= 0 or scale_y <= 0:
        raise ValueError("Scale factors must be positive")
    h, w = img.shape[:2]
    new_size = (int(w * scale_x), int(h * scale_y))
    pil_img = Image.fromarray(img)
    return np.array(pil_img.resize(new_size))

# --------------------------
# Similarity Search
# --------------------------

class ImageRetrievalSystem:
    """Main system for retrieving similar images using transformation-based approach"""
    def __init__(self, tlm: TransformationLibraryManager):
        self.tlm = tlm
        self.images: Dict[str, np.ndarray] = {}  # image_id -> image data
        self.features: Dict[str, np.ndarray] = {}  # image_id -> feature vector
        
    def add_image(self, image_id: str, image: np.ndarray):
        """Add an image to the database"""
        self.images[image_id] = image
        self.features[image_id] = self._extract_features(image)
        
    def _extract_features(self, image: np.ndarray) -> np.ndarray:
        """Extract a simple feature vector from the image"""
        # In a real system, this would use more sophisticated feature extraction
        # For simplicity, we'll use average color and image dimensions
        h, w = image.shape[:2]
        avg_color = np.mean(image, axis=(0, 1))
        return np.concatenate([avg_color, [h/1000.0, w/1000.0]])  # Normalized
    
    def _generate_candidates(self, img: np.ndarray, 
                           base_seq: TransformationSequence) -> List[TransformationSequence]:
        """Generate candidate transformation sequences to explore"""
        candidates = []
        h, w = img.shape[:2]
        
        # Try translations in different directions
        for dx, dy in [(10, 0), (-10, 0), (0, 10), (0, -10)]:
            op = self.tlm.TLMsearch("translate", {"dx": dx, "dy": dy})
            if op:
                new_seq = TransformationSequence()
                new_seq.operations = base_seq.operations.copy()
                new_seq.add_operation(op)
                candidates.append(new_seq)
        
        # Try small rotations
        for angle in [-15, -5, 5, 15]:
            op = self.tlm.TLMsearch("rotate", {"angle": angle})
            if op:
                new_seq = TransformationSequence()
                new_seq.operations = base_seq.operations.copy()
                new_seq.add_operation(op)
                candidates.append(new_seq)
        
        # Try color adjustments
        for channel in [0, 1, 2]:  # R, G, B
            for delta in [-30, -10, 10, 30]:
                op = self.tlm.TLMsearch("adjust_color", {"channel": channel, "delta": delta})
                if op:
                    new_seq = TransformationSequence()
                    new_seq.operations = base_seq.operations.copy()
                    new_seq.add_operation(op)
                    candidates.append(new_seq)
        
        return candidates

# --------------------------
# Main Application
# --------------------------

def demo_custom_sequence(image_path: str, output_path: str):
    # Load image
    image = load_image(image_path)
    
    # Initialize TLM and operators
    tlm = TransformationLibraryManager()
    for op in create_default_operators():
        tlm.TLMinsert(op)
    
    # Define transformation sequence
    seq = TransformationSequence()

    # Nonuniform scale (e.g. shrink width, enlarge height)
    op1 = tlm.TLMsearch("nonuniform_scale", {"scale_x": 0.5, "scale_y": 1.5})
    seq.add_operation(op1)

    # Paint a region (after scaling)
    op2 = tlm.TLMsearch("paint_region", {
        "x1": 50, "y1": 50, "x2": 150, "y2": 150,
        "color": (255, 0, 0)  # Red
    })
    seq.add_operation(op2)

    # Nonuniform scale again (e.g. back to near original)
    op3 = tlm.TLMsearch("nonuniform_scale", {"scale_x": 2.0, "scale_y": 0.66})
    seq.add_operation(op3)

    # Apply sequence
    transformed = seq.apply(image)

    # Save result
    save_image(transformed, output_path)


import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox
from PIL import ImageTk, Image
import json
import numpy as np
import os

# ----- Nhúng các class và hàm bạn đã có từ trước -----
# Giả sử bạn đã định nghĩa các class: TransformationOperator, InstantiatedOperator,
# TransformationLibraryManager, TransformationSequence, và các hàm như load_image, save_image, create_default_operators, v.v.

# Giao diện người dùng
class TransformationGUI:
    def __init__(self, master):
        self.master = master
        self.master.title("Transformation Manager")
        
        self.tlm = TransformationLibraryManager()
        for op in create_default_operators():
            self.tlm.TLMinsert(op)

        self.image = None
        self.image_path = None
        self.display_image = None
        
        # Giao diện
        self.setup_widgets()
        
    def setup_widgets(self):
        # Khu vực thêm toán tử mới
        tk.Label(self.master, text="Nhập toán tử mới (JSON):").pack()
        self.operator_entry = tk.Text(self.master, height=5)
        self.operator_entry.pack()

        tk.Button(self.master, text="Thêm toán tử", command=self.add_operator).pack(pady=5)
        
        # Khu vực chọn ảnh và áp dụng biến đổi
        tk.Button(self.master, text="Chọn ảnh", command=self.load_image).pack(pady=5)
        self.image_label = tk.Label(self.master)
        self.image_label.pack()

        # Danh sách toán tử có sẵn
        tk.Label(self.master, text="Chọn toán tử để áp dụng:").pack()
        self.operator_listbox = tk.Listbox(self.master, selectmode=tk.MULTIPLE, width=50)
        self.operator_listbox.pack(pady=5)
        self.refresh_operator_list()

        tk.Button(self.master, text="Áp dụng toán tử", command=self.apply_operators).pack(pady=5)

    def refresh_operator_list(self):
        self.operator_listbox.delete(0, tk.END)
        for name in self.tlm.list_operators():
            self.operator_listbox.insert(tk.END, name)

    def add_operator(self):
        try:
            data = json.loads(self.operator_entry.get("1.0", tk.END))
            name = data["name"]
            parameters = data["parameters"]

            # Giả sử bạn cho người dùng chọn tên một hàm sẵn có (từ trước)
            # Ví dụ: bạn cho phép dùng apply_function = "translate"
            apply_function_name = data["apply_function"]
            func = globals().get(apply_function_name)
            if not callable(func):
                raise ValueError("Không tìm thấy hàm apply_function")

            new_op = TransformationOperator(name=name, parameters=parameters, apply_function=func)
            self.tlm.TLMinsert(new_op)
            self.refresh_operator_list()
            messagebox.showinfo("Thành công", f"Đã thêm toán tử {name}")
        except Exception as e:
            messagebox.showerror("Lỗi", f"Lỗi khi thêm toán tử: {e}")

    def load_image(self):
        filepath = filedialog.askopenfilename()
        if not filepath:
            return
        self.image_path = filepath
        img = load_image(filepath)
        self.image = img
        self.show_image(img)

    def show_image(self, img_np):
        img = Image.fromarray(img_np.astype(np.uint8))
        img.thumbnail((300, 300))
        self.display_image = ImageTk.PhotoImage(img)
        self.image_label.config(image=self.display_image)

    def apply_operators(self):
        if self.image is None:
            messagebox.showwarning("Chưa có ảnh", "Vui lòng chọn ảnh trước")
            return

        seq = TransformationSequence()
        selected = self.operator_listbox.curselection()

        try:
            for idx in selected:
                op_name = self.operator_listbox.get(idx)
                operator = self.tlm.TLMsearch(op_name)
                if isinstance(operator, TransformationOperator):
                    param_values = {}
                    for param, ptype in operator.parameters.items():
                        raw_val = simpledialog.askstring("Nhập tham số", f"{op_name} - {param} ({ptype.__name__}):")
                        if ptype == tuple:
                            val = tuple(map(int, raw_val.strip("()").split(",")))
                        else:
                            val = ptype(raw_val)
                        param_values[param] = val

                    inst = self.tlm.TLMsearch(op_name, param_values)
                    seq.add_operation(inst)

            transformed = seq.apply(self.image)
            self.show_image(transformed)

            # Lưu kết quả tạm thời
            save_image(transformed, "output_transformed.jpg")
            messagebox.showinfo("Hoàn tất", "Đã áp dụng và lưu ảnh kết quả tại output_transformed.jpg")
        except Exception as e:
            messagebox.showerror("Lỗi khi áp dụng", str(e))


# ---- Khởi động ứng dụng ----
if __name__ == "__main__":
    root = tk.Tk()
    app = TransformationGUI(root)
    root.mainloop()