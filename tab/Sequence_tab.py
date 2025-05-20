import tkinter as tk
from tkinter import ttk, messagebox
import json
from PIL import Image, ImageDraw, ImageTk
from transformation_manager import TransformationLibraryManager, load_transformations_from_json, create_default_object_operators
from object_manager import ImageDatabase, save_database
from cost_function_server import CostFunctionServer

class TabSequence:
    def __init__(self, parent, db: ImageDatabase):
        self.parent = parent
        self.db = db
        self.db_file = "image_database.pkl"
        self.tlm = TransformationLibraryManager()
        for op in create_default_object_operators():
            self.tlm.TLMinsert(op)  # Thêm toán tử mặc định
        self.server = CostFunctionServer()
        self.tk_image = None
        self.setup_ui()

    def setup_ui(self):
        self.main_frame = tk.Frame(self.parent, bg="#f0f4f8")
        self.main_frame.pack(padx=10, pady=10, fill="both", expand=True)

        # Frame cho canvas
        canvas_frame = tk.LabelFrame(self.main_frame, text="Xem trước ảnh", font=("Helvetica", 12, "bold"), bg="#f0f4f8", fg="#2c3e50")
        canvas_frame.pack(side=tk.LEFT, padx=10, pady=5, fill="both", expand=True)

        self.canvas = tk.Canvas(canvas_frame, width=600, height=500, bg="white", highlightthickness=1, highlightbackground="#bdc3c7")
        self.canvas.pack(padx=10, pady=10, side=tk.LEFT, fill="both", expand=True)

        v_scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=self.canvas.yview)
        v_scrollbar.pack(side=tk.RIGHT, fill="y")
        self.canvas.configure(yscrollcommand=v_scrollbar.set)

        h_scrollbar = ttk.Scrollbar(canvas_frame, orient="horizontal", command=self.canvas.xview)
        h_scrollbar.pack(side=tk.BOTTOM, fill="x")
        self.canvas.configure(xscrollcommand=h_scrollbar.set)

        # Frame cho điều khiển
        self.control_frame = tk.Frame(self.main_frame, bg="#f0f4f8")
        self.control_frame.pack(side=tk.RIGHT, padx=10, pady=5, fill="y")

        # Combobox chọn ảnh
        tk.Label(self.control_frame, text="Chọn ảnh:", font=("Helvetica", 10), bg="#f0f4f8").pack()
        self.selected_image = tk.StringVar()
        self.image_selector = ttk.Combobox(self.control_frame, textvariable=self.selected_image, width=25)
        self.image_selector['values'] = self.db.list_images()
        self.image_selector.pack(pady=5)
        self.image_selector.bind("<<ComboboxSelected>>", self.display_selected_image)

        # Frame chọn object và biến đổi
        self.selection_frame = tk.LabelFrame(self.control_frame, text="Chọn object và phép biến đổi", font=("Helvetica", 10, "bold"), padx=10, pady=10, bg="#ecf0f1", fg="#2c3e50")
        self.selection_frame.pack(fill="x", pady=5)

        tk.Label(self.selection_frame, text="Chọn object:", font=("Helvetica", 10), bg="#ecf0f1").pack()
        self.object_var = tk.StringVar()
        self.object_box = ttk.Combobox(self.selection_frame, textvariable=self.object_var, width=30, state="disabled")
        self.object_box.pack(pady=5)

        operators_frame = tk.LabelFrame(self.selection_frame, text="Chọn phép biến đổi", font=("Helvetica", 10, "bold"), padx=5, pady=5, bg="#ecf0f1", fg="#2c3e50")
        operators_frame.pack(fill="x", pady=5)

        transformations = load_transformations_from_json()
        self.operator_options = {op["name"]: [json.dumps(params) for params in [entry["parameters"] for entry in transformations["operators"] if entry["name"] == op["name"]]] for op in transformations["operators"]}

        operators = list(self.operator_options.keys())
        self.operator_var = tk.StringVar(value=operators[0] if operators else "")
        operator_box = ttk.Combobox(operators_frame, textvariable=self.operator_var, values=operators, width=15)
        operator_box.pack(side=tk.LEFT, padx=5)

        self.params_var = tk.StringVar(value=self.operator_options[operators[0]][0] if operators else "")
        params_box = ttk.Combobox(operators_frame, textvariable=self.params_var, values=self.operator_options.get(self.operator_var.get(), []), width=30)
        params_box.pack(side=tk.LEFT, padx=5)

        def update_params(*args):
            new_operator = self.operator_var.get()
            params_box['values'] = self.operator_options.get(new_operator, [])
            params_box.set(self.operator_options.get(new_operator, [""])[0] if self.operator_options.get(new_operator) else "")

        self.operator_var.trace('w', update_params)

        selected_ops_frame = tk.LabelFrame(self.selection_frame, text="Các phép biến đổi đã chọn", font=("Helvetica", 10, "bold"), padx=5, pady=5, bg="#ecf0f1", fg="#2c3e50")
        selected_ops_frame.pack(fill="x", pady=5)
        self.selected_ops_listbox = tk.Listbox(selected_ops_frame, height=5, width=50, font=("Helvetica", 9), bg="#f9f9f9")
        self.selected_ops_listbox.pack()

        self.temp_transformations = []

        def add_transformation():
            operator = self.operator_var.get()
            params_str = self.params_var.get()
            if not operator or not params_str:
                messagebox.showerror("Lỗi", "Vui lòng chọn toán tử và tham số")
                return
            try:
                params = json.loads(params_str)
                self.temp_transformations.append((operator, params))
                self.selected_ops_listbox.insert(tk.END, f"{operator} {params}")
            except json.JSONDecodeError:
                messagebox.showerror("Lỗi", "Tham số không hợp lệ")

        def delete_transformation():
            idx = self.selected_ops_listbox.curselection()
            if not idx:
                messagebox.showwarning("Cảnh báo", "Vui lòng chọn phép biến đổi để xóa")
                return
            idx = idx[0]
            self.temp_transformations.pop(idx)
            self.selected_ops_listbox.delete(idx)

        btn_frame_1 = tk.Frame(self.selection_frame, bg="#ecf0f1")
        btn_frame_1.pack(pady=5)
        self.add_trans_btn = ttk.Button(btn_frame_1, text="Thêm phép biến đổi", command=add_transformation, state="disabled")
        self.add_trans_btn.pack(side=tk.LEFT, padx=5)
        self.del_trans_btn = ttk.Button(btn_frame_1, text="Xóa phép biến đổi", command=delete_transformation, state="disabled")
        self.del_trans_btn.pack(side=tk.LEFT, padx=5)

        def add_to_sequence():
            obj_id = self.object_var.get()
            if not obj_id:
                messagebox.showerror("Lỗi", "Vui lòng chọn object")
                return
            if not self.temp_transformations:
                messagebox.showerror("Lỗi", f"Vui lòng thêm phép biến đổi cho object {obj_id}")
                return
            self.selected_sequences.append((obj_id, self.temp_transformations[:]))
            self.sequence_listbox.insert(tk.END, f"Object {obj_id}: {', '.join([t[0] for t in self.temp_transformations])}")
            self.temp_transformations.clear()
            self.selected_ops_listbox.delete(0, tk.END)

        self.add_seq_btn = ttk.Button(self.selection_frame, text="Thêm vào chuỗi", command=add_to_sequence, state="disabled")
        self.add_seq_btn.pack(pady=5)

        order_frame = tk.LabelFrame(self.control_frame, text="Sắp xếp thứ tự thực hiện", font=("Helvetica", 10, "bold"), padx=10, pady=10, bg="#ecf0f1", fg="#2c3e50")
        order_frame.pack(fill="x", pady=5)

        self.selected_sequences = []
        self.sequence_listbox = tk.Listbox(order_frame, height=5, width=50, font=("Helvetica", 9), bg="#f9f9f9")
        self.sequence_listbox.pack()

        def move_up():
            idx = self.sequence_listbox.curselection()
            if not idx or idx[0] == 0:
                return
            idx = idx[0]
            item = self.selected_sequences.pop(idx)
            self.selected_sequences.insert(idx - 1, item)
            self.sequence_listbox.delete(0, tk.END)
            for obj_id, transformations in self.selected_sequences:
                self.sequence_listbox.insert(tk.END, f"Object {obj_id}: {', '.join([t[0] for t in transformations])}")
            self.sequence_listbox.selection_set(idx - 1)

        def move_down():
            idx = self.sequence_listbox.curselection()
            if not idx or idx[0] == len(self.selected_sequences) - 1:
                return
            idx = idx[0]
            item = self.selected_sequences.pop(idx)
            self.selected_sequences.insert(idx + 1, item)
            self.sequence_listbox.delete(0, tk.END)
            for obj_id, transformations in self.selected_sequences:
                self.sequence_listbox.insert(tk.END, f"Object {obj_id}: {', '.join([t[0] for t in transformations])}")
            self.sequence_listbox.selection_set(idx + 1)

        def delete_sequence():
            idx = self.sequence_listbox.curselection()
            if not idx:
                messagebox.showwarning("Cảnh báo", "Vui lòng chọn chuỗi để xóa")
                return
            idx = idx[0]
            self.selected_sequences.pop(idx)
            self.sequence_listbox.delete(idx)

        btn_frame_2 = tk.Frame(order_frame, bg="#ecf0f1")
        btn_frame_2.pack(pady=5)
        self.move_up_btn = ttk.Button(btn_frame_2, text="Lên", command=move_up, state="disabled")
        self.move_up_btn.pack(side=tk.LEFT, padx=5)
        self.move_down_btn = ttk.Button(btn_frame_2, text="Xuống", command=move_down, state="disabled")
        self.move_down_btn.pack(side=tk.LEFT, padx=5)
        self.del_seq_btn = ttk.Button(btn_frame_2, text="Xóa chuỗi", command=delete_sequence, state="disabled")
        self.del_seq_btn.pack(side=tk.LEFT, padx=5)

        def apply_sequence():
            if not self.selected_sequences:
                messagebox.showerror("Lỗi", "Vui lòng thêm ít nhất một object và phép biến đổi")
                return
            img_name = self.selected_image.get()
            if not img_name:
                messagebox.showerror("Lỗi", "Vui lòng chọn ảnh trước")
                return
            img = self.db.get_image(img_name)
            if not img.objects:
                messagebox.showerror("Lỗi", "Ảnh không có object để biến đổi")
                return
            self.apply_sequence_stages(self.selected_sequences, img)

        self.apply_btn = ttk.Button(self.control_frame, text="Áp dụng", command=apply_sequence, state="disabled")
        self.apply_btn.pack(pady=10)

        # Kiểm tra điều kiện ban đầu
        self.check_initial_conditions()

    def check_initial_conditions(self):
        img_name = self.selected_image.get()
        if not img_name:
            self.disable_controls()
            return
        img = self.db.get_image(img_name)
        if not img.objects:
            self.disable_controls()
            return
        self.enable_controls()
        self.display_selected_image()

    def disable_controls(self):
        self.object_box.configure(state="disabled")
        self.add_trans_btn.configure(state="disabled")
        self.del_trans_btn.configure(state="disabled")
        self.add_seq_btn.configure(state="disabled")
        self.move_up_btn.configure(state="disabled")
        self.move_down_btn.configure(state="disabled")
        self.del_seq_btn.configure(state="disabled")
        self.apply_btn.configure(state="disabled")

    def enable_controls(self):
        self.object_box.configure(state="normal")
        self.add_trans_btn.configure(state="normal")
        self.del_trans_btn.configure(state="normal")
        self.add_seq_btn.configure(state="normal")
        self.move_up_btn.configure(state="normal")
        self.move_down_btn.configure(state="normal")
        self.del_seq_btn.configure(state="normal")
        self.apply_btn.configure(state="normal")

    def display_selected_image(self, event=None):
        name = self.selected_image.get()
        if not name:
            self.canvas.delete("all")
            self.object_box.configure(state="disabled")
            self.object_var.set("")
            self.disable_controls()
            return
        img_meta = self.db.get_image(name)
        image = Image.new("RGB", (img_meta.width, img_meta.height), "white")
        draw = ImageDraw.Draw(image)
        for obj in img_meta.objects:
            draw.rectangle([obj.x1, obj.y1, obj.x2, obj.y2], fill=obj.color, outline="black", width=2)
        draw.rectangle([0, 0, img_meta.width - 1, img_meta.height - 1], outline="black", width=3)
        self.tk_image = ImageTk.PhotoImage(image)
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_image)
        self.canvas.configure(scrollregion=(0, 0, img_meta.width, img_meta.height))

        object_ids = [obj.obj_id for obj in img_meta.objects]
        self.object_box['values'] = object_ids
        self.object_box.configure(state="normal")
        self.object_var.set(object_ids[0] if object_ids else "")  # Đặt giá trị mặc định
        self.enable_controls()

    def apply_sequence_stages(self, sequences, img):
        stage = 0
        # Tạo frame riêng để chứa result_text
        result_frame = tk.Frame(self.main_frame, bg="#f0f4f8")
        result_frame.pack(side=tk.BOTTOM, fill="x", pady=5)
        result_text = tk.Text(result_frame, height=5, width=50, font=("Helvetica", 9), bg="#ecf0f1")
        result_text.pack(pady=5)

        all_steps = []
        for obj_id, transformations in sequences:
            for op_name, params in transformations:
                all_steps.append((obj_id, op_name, params))

        def apply_next_stage(current_stage):
            nonlocal stage
            if current_stage >= len(all_steps):
                messagebox.showinfo("Hoàn tất", "Đã áp dụng tất cả các giai đoạn")
                result_frame.destroy()
                self.display_selected_image()
                return

            obj_id, operator_name, params = all_steps[current_stage]
            operator_instance = self.tlm.TLMsearch(operator_name, params)
            if not operator_instance:
                messagebox.showerror("Lỗi", f"Không tìm thấy toán tử {operator_name} với tham số {params}")
                result_frame.destroy()
                return

            for obj in img.objects:
                if obj.obj_id == obj_id:
                    stage += 1
                    result_text.delete(1.0, tk.END)
                    stage_message = f"Stage {stage}: {operator_name} {params} cho {obj_id}"
                    operator_instance.apply(obj)
                    save_database(self.db, self.db_file)

                    # Tính chi phí
                    try:
                        with open(self.server.path, "r") as f:
                            cost_functions = json.load(f)
                        matching_funcs = [f for f in cost_functions if f["type"] == operator_name]
                        if not matching_funcs:
                            result_text.insert(tk.END, f"{stage_message}\nKhông có hàm chi phí phù hợp.")
                        else:
                            cost_results = []
                            for func in matching_funcs:
                                operator = {"type": func["type"], "params": params}
                                try:
                                    cost = self.server.EvaluateCall(operator)
                                    cost_results.append(f"- {func['name']}: {cost}")
                                except Exception as e:
                                    cost_results.append(f"- {func['name']}: Lỗi ({str(e)})")
                            cost_message = "\n".join(cost_results)
                            result_text.insert(tk.END, f"{stage_message}\nChi phí:\n{cost_message}")
                    except Exception as e:
                        result_text.insert(tk.END, f"{stage_message}\nLỗi khi tính chi phí: {e}")

                    self.display_selected_image()
                    self.parent.after(1000, lambda: apply_next_stage(current_stage + 1))
                    break

        apply_next_stage(0)