import tkinter as tk
from tkinter import ttk, messagebox
from object_manager import ImageDatabase
from object_converter import ObjectConvertor
from cost_function_server import CostFunctionServer
from transformation_manager import TransformationLibraryManager, create_default_object_operators

class TabOC:
    def __init__(self, parent, db: ImageDatabase):
        self.parent = parent
        self.db = db
        self.tlm = TransformationLibraryManager()
        for op in create_default_object_operators():
            self.tlm.TLMinsert(op)
        self.setup_ui()

    def setup_ui(self):
        frame = tk.Frame(self.parent, bg="#f0f4f8")
        frame.pack(padx=20, pady=20, fill="both", expand=True)

        tk.Label(frame, text="Chọn ảnh 1:", font=("Helvetica", 10), bg="#f0f4f8").pack()
        self.image1_var = tk.StringVar()
        self.image1_box = ttk.Combobox(frame, textvariable=self.image1_var, width=25)
        self.image1_box['values'] = self.db.list_images()
        self.image1_box.pack(pady=5)

        tk.Label(frame, text="Chọn ảnh 2:", font=("Helvetica", 10), bg="#f0f4f8").pack()
        self.image2_var = tk.StringVar()
        self.image2_box = ttk.Combobox(frame, textvariable=self.image2_var, width=25)
        self.image2_box['values'] = self.db.list_images()
        self.image2_box.pack(pady=5)

        self.result_text = tk.Text(frame, height=10, width=40, font=("Helvetica", 9), bg="#ecf0f1")
        self.result_text.pack(pady=10)

        self.image1_box.bind("<<ComboboxSelected>>", self.update_image2_options)
        ttk.Button(frame, text="Chạy Convertor", command=self.run_convertor).pack(pady=10)

    def update_image2_options(self, event):
        selected_image1 = self.image1_var.get()
        all_images = self.db.list_images()
        updated_options = [img for img in all_images if img != selected_image1]
        self.image2_box['values'] = updated_options
        if self.image2_var.get() == selected_image1:
            self.image2_var.set("")

    def run_convertor(self):
        image1_name = self.image1_var.get()
        image2_name = self.image2_var.get()
        if not image1_name or not image2_name:
            messagebox.showerror("Lỗi", "Phải chọn cả hai ảnh")
            return

        if image1_name == image2_name:
            messagebox.showerror("Lỗi", "Ảnh 2 không được trùng với ảnh 1")
            return

        img1 = self.db.get_image(image1_name)
        img2 = self.db.get_image(image2_name)

        if len(img1.objects) != len(img2.objects):
            messagebox.showerror("Lỗi", "Hai ảnh phải có cùng số lượng object")
            return

        if len(img1.objects) == 0:
            messagebox.showerror("Lỗi", "Ảnh không có object để chuyển đổi")
            return

        converter = ObjectConvertor(self.tlm, CostFunctionServer(), transformations_file="data/transformations.json")
        objects_info = []
        for i in range(len(img1.objects)):
            obj1 = img1.objects[i]
            obj2 = img2.objects[i]
            result = converter.convert(obj1, obj2)
            if result is None:
                objects_info.append(f"Object {i+1} ({obj1.obj_id} -> {obj2.obj_id}):\n  Không tìm được chuỗi biến đổi phù hợp.")
            elif result == []:
                objects_info.append(f"Object {i+1} ({obj1.obj_id} -> {obj2.obj_id}):\n  Không cần biến đổi.")
            else:
                steps = "\n".join(f"  {step.operator.name} {step.params}" for step in result)
                objects_info.append(f"Object {i+1} ({obj1.obj_id} -> {obj2.obj_id}):\n{steps}")

        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, "\n".join(objects_info))