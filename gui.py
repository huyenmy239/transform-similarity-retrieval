import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from PIL import Image, ImageDraw, ImageTk
import ast, json
from object_manager import ImageDatabase, ImageObjectRegion, ImageMeta, load_or_create_database, save_database
from transformation_manager import TransformationLibraryManager, TransformationOperator, create_default_object_operators, load_transformations_from_json, add_operator_to_json
from cost_function_server import CostFunctionServer
from object_converter import ObjectConvertor
from typing import get_origin, get_args

db_file = "image_database.pkl"
db = load_or_create_database(db_file)
data = load_transformations_from_json()

class ObjectEditorGUI(tk.Tk):
    def __init__(self, db: ImageDatabase):
        super().__init__()
        self.title("Object Image Editor")
        self.db = db
        self.configure(bg="#f0f4f8")  # Màu nền nhẹ

        self.tlm = TransformationLibraryManager()
        for op in create_default_object_operators():
            self.tlm.TLMinsert(op)

        # Tùy chỉnh giao diện với ttk.Style
        style = ttk.Style()
        style.configure("TButton", font=("Helvetica", 10), padding=5)
        style.configure("TCombobox", font=("Helvetica", 10))
        style.configure("TLabel", background="#f0f4f8", font=("Helvetica", 10, "bold"))
        style.configure("TFrame", background="#f0f4f8")

        # Frame chính chứa canvas và các nút
        main_frame = tk.Frame(self, bg="#f0f4f8")
        main_frame.pack(padx=10, pady=10, fill="both", expand=True)

        # Frame cho canvas
        canvas_frame = tk.LabelFrame(main_frame, text="Xem trước ảnh", font=("Helvetica", 12, "bold"), bg="#f0f4f8", fg="#2c3e50")
        canvas_frame.pack(side=tk.LEFT, padx=10, pady=5, fill="both", expand=True)

        self.canvas = tk.Canvas(canvas_frame, width=600, height=500, bg="white", highlightthickness=1, highlightbackground="#bdc3c7")
        self.canvas.pack(padx=10, pady=10)

        # Frame cho các nút điều khiển
        control_frame = tk.Frame(main_frame, bg="#f0f4f8")
        control_frame.pack(side=tk.RIGHT, padx=10, pady=5, fill="y")

        # Tiêu đề cho phần điều khiển
        tk.Label(control_frame, text="Điều khiển", font=("Helvetica", 12, "bold"), bg="#f0f4f8", fg="#2c3e50").pack(pady=(0, 10))

        # Combobox chọn ảnh
        tk.Label(control_frame, text="Chọn ảnh:", font=("Helvetica", 10), bg="#f0f4f8").pack()
        self.selected_image = tk.StringVar()
        self.image_selector = ttk.Combobox(control_frame, textvariable=self.selected_image, width=20)
        self.image_selector['values'] = self.db.list_images()
        self.image_selector.pack(pady=5)
        self.image_selector.bind("<<ComboboxSelected>>", self.display_selected_image)

        # Các nút điều khiển
        buttons = [
            ("Thêm ảnh mới", self.add_image_window),
            ("Chỉnh sửa ảnh", self.edit_objects_window),
            ("Biến đổi object", self.open_transformation_window),
            ("Convertor", self.open_convertor_window),
            ("Tạo chuỗi biến đổi", self.open_sequence_window)
        ]

        for text, command in buttons:
            ttk.Button(control_frame, text=text, command=command, width=20).pack(pady=5)

        self.tk_image = None

    def display_selected_image(self, event=None):
        name = self.selected_image.get()
        if not name:
            return
        img_meta = self.db.get_image(name)
        image = Image.new("RGB", (img_meta.width, img_meta.height), "white")
        draw = ImageDraw.Draw(image)
        for obj in img_meta.objects:
            draw.rectangle([obj.x1, obj.y1, obj.x2, obj.y2], fill=obj.color, outline="black", width=2)
        draw.rectangle([0, 0, img_meta.width - 1, img_meta.height - 1], outline="black", width=3)
        self.tk_image = ImageTk.PhotoImage(image)
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_image)

    def add_image_window(self):
        window = tk.Toplevel(self)
        window.title("Thêm ảnh mới")
        window.configure(bg="#f0f4f8")
        window.geometry("300x200")  # Kích thước cố định cho cửa sổ

        fields = {}
        frame = tk.Frame(window, bg="#f0f4f8")
        frame.pack(padx=20, pady=20, fill="both")

        for label in ["Tên ảnh", "Chiều rộng", "Chiều cao"]:
            row = tk.Frame(frame, bg="#f0f4f8")
            row.pack(fill="x", pady=5)
            tk.Label(row, text=label, width=12, font=("Helvetica", 10), bg="#f0f4f8").pack(side=tk.LEFT)
            entry = tk.Entry(row, font=("Helvetica", 10))
            entry.pack(side=tk.LEFT, fill="x", expand=True)
            fields[label] = entry

        def create():
            try:
                name = fields["Tên ảnh"].get()
                width = int(fields["Chiều rộng"].get())
                height = int(fields["Chiều cao"].get())
                meta = ImageMeta(name, width, height, [])
                self.db.add_image(meta)
                save_database(self.db, db_file)
                self.image_selector['values'] = self.db.list_images()
                self.selected_image.set(name)
                self.display_selected_image()
                window.destroy()
            except Exception as e:
                messagebox.showerror("Lỗi", str(e))

        ttk.Button(frame, text="Tạo ảnh", command=create).pack(pady=10)

    def edit_objects_window(self):
        name = self.selected_image.get()
        if not name:
            return
        img_meta = self.db.get_image(name)
        window = tk.Toplevel(self)
        window.title("Chỉnh sửa các object")
        window.configure(bg="#f0f4f8")
        window.geometry("450x600")  # Tăng kích thước để hiển thị tốt hơn

        entries = []
        container = tk.Frame(window, bg="#f0f4f8")
        container.pack(padx=10, pady=10, fill="both", expand=True)

        canvas = tk.Canvas(container, bg="#f0f4f8", highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg="#f0f4f8")

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill="both", expand=True)
        scrollbar.pack(side=tk.RIGHT, fill="y")

        def add_form(obj=None):
            frame = tk.LabelFrame(scrollable_frame, text=f"Object {len(entries) + 1}", font=("Helvetica", 10, "bold"), padx=5, pady=5, bg="#ecf0f1", fg="#2c3e50")
            frame.pack(fill="x", padx=5, pady=5, anchor="w")

            def row(label, default=""):
                f = tk.Frame(frame, bg="#ecf0f1")
                f.pack(fill="x", pady=2)
                tk.Label(f, text=label, width=12, font=("Helvetica", 9), bg="#ecf0f1").pack(side=tk.LEFT)
                e = tk.Entry(f, font=("Helvetica", 9), width=20)
                e.insert(0, str(default))
                e.pack(side=tk.LEFT, fill="x", expand=True)
                return e

            e = {
                "id": row("Tên object", obj.obj_id if obj else ""),
                "x1": row("x1", obj.x1 if obj else 0),
                "y1": row("y1", obj.y1 if obj else 0),
                "x2": row("x2", obj.x2 if obj else 100),
                "y2": row("y2", obj.y2 if obj else 100),
                "color": row("Màu RGB", obj.color if obj else "(255,0,0)")
            }
            ttk.Button(frame, text="Xóa", command=lambda: (entries.remove(e), frame.destroy())).pack(pady=2, side=tk.RIGHT)
            entries.append(e)

        for obj in img_meta.objects:
            add_form(obj)

        ttk.Button(scrollable_frame, text="+ Thêm object", command=lambda: add_form()).pack(pady=5)

        def save():
            try:
                img_meta.objects = []
                for e in entries:
                    color = ast.literal_eval(e["color"].get())
                    obj = ImageObjectRegion(
                        obj_id=e["id"].get(),
                        x1=int(e["x1"].get()),
                        y1=int(e["y1"].get()),
                        x2=int(e["x2"].get()),
                        y2=int(e["y2"].get()),
                        color=color
                    )
                    img_meta.add_object(obj)
                save_database(self.db, db_file)
                self.display_selected_image()
                window.destroy()
            except Exception as e:
                messagebox.showerror("Lỗi", str(e))

        ttk.Button(scrollable_frame, text="Lưu", command=save).pack(pady=10)

    def open_transformation_window(self):
        trans_window = tk.Toplevel(self)
        trans_window.title("Chọn phép biến đổi")
        trans_window.configure(bg="#f0f4f8")
        trans_window.geometry("350x200")

        frame = tk.Frame(trans_window, bg="#f0f4f8")
        frame.pack(padx=20, pady=20, fill="both", expand=True)

        tk.Label(frame, text="Chọn object:", font=("Helvetica", 10), bg="#f0f4f8").pack()
        object_var = tk.StringVar()
        object_box = ttk.Combobox(frame, textvariable=object_var, width=25)
        
        img_name = self.selected_image.get()
        if not img_name:
            messagebox.showerror("Lỗi", "Chưa chọn ảnh nào")
            return
        img = self.db.get_image(img_name)
        object_box['values'] = [obj.obj_id for obj in img.objects]
        object_box.pack(pady=5)

        def on_object_selected(event):
            operator_label.pack()
            operator_box.pack()
            continue_btn.pack(pady=10)

        object_box.bind("<<ComboboxSelected>>", on_object_selected)

        operator_label = tk.Label(frame, text="Chọn toán tử:", font=("Helvetica", 10), bg="#f0f4f8")
        operator_name = tk.StringVar()
        operator_box = ttk.Combobox(frame, textvariable=operator_name, width=25)
        operator_box['values'] = self.tlm.list_operators()

        def choose_option():
            selected_obj = object_var.get()
            selected_op = operator_name.get()
            if not selected_op or not selected_obj:
                messagebox.showerror("Lỗi", "Phải chọn object và toán tử")
                return

            sub_window = tk.Toplevel(trans_window)
            sub_window.title(f"Tùy chọn cho {selected_op}")
            sub_window.configure(bg="#f0f4f8")
            sub_window.geometry("300x150")
            sub_frame = tk.Frame(sub_window, bg="#f0f4f8")
            sub_frame.pack(padx=20, pady=20, fill="both", expand=True)
            tk.Button(sub_frame, text="Chọn từ file JSON", command=lambda: self.apply_from_json(selected_op, selected_obj, sub_window), font=("Helvetica", 10)).pack(pady=5)
            tk.Button(sub_frame, text="Nhập tham số thủ công", command=lambda: self.manual_param_input(selected_op, selected_obj, sub_window), font=("Helvetica", 10)).pack(pady=5)

        continue_btn = ttk.Button(frame, text="Tiếp tục", command=choose_option)

    def apply_from_json(self, op_name, object_id, window):
        data = load_transformations_from_json()
        
        options = [op for op in data["operators"] if op["name"] == op_name]

        if not options:
            messagebox.showinfo("Thông báo", "Không có tham số nào cho toán tử này trong file JSON")
            return

        select_win = tk.Toplevel(window)
        select_win.title("Chọn tham số")
        select_win.configure(bg="#f0f4f8")
        select_win.geometry("400x300")

        frame = tk.Frame(select_win, bg="#f0f4f8")
        frame.pack(padx=10, pady=10, fill="both", expand=True)

        listbox = tk.Listbox(frame, width=50, height=10, font=("Helvetica", 9), bg="#ecf0f1")
        for i, op in enumerate(options):
            listbox.insert(i, json.dumps(op["parameters"]))
        listbox.pack(pady=5)

        def on_select():
            index = listbox.curselection()
            if index:
                selected_params = options[index[0]]["parameters"]
                inst = self.tlm.TLMsearch(op_name, selected_params)
                if inst:
                    self.apply_to_one_object(object_id, inst)
                    messagebox.showinfo("Xong", "Đã áp dụng biến đổi")
                    self.display_selected_image()
                    select_win.destroy()

        tk.Button(frame, text="Áp dụng", command=on_select, font=("Helvetica", 10), bg="#3498db", fg="white").pack(pady=5)

    def manual_param_input(self, op_name, object_id, window):
        operator = self.tlm.TLMsearch(op_name)
        if not operator:
            messagebox.showerror("Lỗi", f"Không tìm thấy toán tử: {op_name}")
            return

        input_win = tk.Toplevel(window)
        input_win.title("Nhập tham số")
        input_win.configure(bg="#f0f4f8")
        input_win.geometry("350x300")

        frame = tk.Frame(input_win, bg="#f0f4f8")
        frame.pack(padx=20, pady=20, fill="both", expand=True)

        entries = {}
        for key, typ in operator.parameters.items():
            row = tk.Frame(frame, bg="#f0f4f8")
            row.pack(fill="x", pady=5)
            tk.Label(row, text=key, width=15, font=("Helvetica", 10), bg="#f0f4f8").pack(side=tk.LEFT)
            entry = tk.Entry(row, font=("Helvetica", 10))
            entry.pack(side=tk.LEFT, fill="x", expand=True)
            entries[key] = (entry, typ)

        def apply_manual():
            try:
                param_dict = {}
                for key, (entry, typ) in entries.items():
                    val = entry.get()
                    origin = get_origin(typ)
                    if origin == tuple:
                        args = get_args(typ)
                        parsed_val = tuple(args[0](x.strip()) for x in val.strip("()").split(","))
                    else:
                        parsed_val = typ(val)
                    param_dict[key] = parsed_val

                operator_instance = self.tlm.TLMsearch(op_name, param_dict)
                if not operator_instance:
                    messagebox.showerror("Lỗi", f"Không tìm thấy toán tử hoặc tham số không hợp lệ: {op_name}")
                    return
                    
                messagebox.showinfo("", add_operator_to_json(op_name, param_dict))
                self.apply_to_one_object(object_id, operator_instance)
                self.display_selected_image()
                messagebox.showinfo("Thành công", "Đã áp dụng phép biến đổi")
                input_win.destroy()

            except Exception as e:
                messagebox.showerror("Lỗi", f"Tham số không hợp lệ: {e}")

        ttk.Button(frame, text="Áp dụng", command=apply_manual).pack(pady=10)

    def apply_to_one_object(self, object_id: str, operator: TransformationOperator):
        img_name = self.selected_image.get()
        img = self.db.get_image(img_name)
        for obj in img.objects:
            if obj.obj_id == object_id:
                operator.apply(obj)
                save_database(self.db, db_file)
                return

    def apply_to_all_objects(self, inst):
        image = self.db.get_image(self.selected_image.get())
        for obj in image.objects:
            inst.apply(obj)
        self.display_selected_image()

    def open_convertor_window(self):
        window = tk.Toplevel(self)
        window.title("Convertor: Chuyển đổi ảnh")
        window.configure(bg="#f0f4f8")
        window.geometry("400x400")

        frame = tk.Frame(window, bg="#f0f4f8")
        frame.pack(padx=20, pady=20, fill="both", expand=True)

        tk.Label(frame, text="Chọn ảnh 1:", font=("Helvetica", 10), bg="#f0f4f8").pack()
        image1_var = tk.StringVar()
        image1_box = ttk.Combobox(frame, textvariable=image1_var, width=25)
        image1_box['values'] = self.db.list_images()
        image1_box.pack(pady=5)

        tk.Label(frame, text="Chọn ảnh 2:", font=("Helvetica", 10), bg="#f0f4f8").pack()
        image2_var = tk.StringVar()
        image2_box = ttk.Combobox(frame, textvariable=image2_var, width=25)
        image2_box['values'] = self.db.list_images()
        image2_box.pack(pady=5)

        result_text = tk.Text(frame, height=10, width=40, font=("Helvetica", 9), bg="#ecf0f1")
        result_text.pack(pady=10)

        def update_image2_options(event):
            selected_image1 = image1_var.get()
            all_images = self.db.list_images()
            updated_options = [img for img in all_images if img != selected_image1]
            image2_box['values'] = updated_options
            if image2_var.get() == selected_image1:
                image2_var.set("")

        image1_box.bind("<<ComboboxSelected>>", update_image2_options)

        def run_convertor():
            image1_name = image1_var.get()
            image2_name = image2_var.get()
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
                elif result == []:  # Trường hợp hai object giống nhau
                    objects_info.append(f"Object {i+1} ({obj1.obj_id} -> {obj2.obj_id}):\n  Không cần biến đổi.")
                else:
                    steps = "\n".join(f"  {step.operator.name} {step.params}" for step in result)
                    objects_info.append(f"Object {i+1} ({obj1.obj_id} -> {obj2.obj_id}):\n{steps}")

            result_text.delete(1.0, tk.END)
            result_text.insert(tk.END, "\n".join(objects_info))

        ttk.Button(frame, text="Chạy Convertor", command=run_convertor).pack(pady=10)

    def open_sequence_window(self):
        window = tk.Toplevel(self)
        window.title("Tạo chuỗi biến đổi")
        window.configure(bg="#f0f4f8")
        window.geometry("500x600")

        img_name = self.selected_image.get()
        if not img_name:
            messagebox.showerror("Lỗi", "Vui lòng chọn ảnh trước")
            window.destroy()
            return
        img = self.db.get_image(img_name)
        objects = img.objects
        if not objects:
            messagebox.showerror("Lỗi", "Ảnh không có object để biến đổi")
            window.destroy()
            return

        transformations = load_transformations_from_json()
        operator_options = {op["name"]: [json.dumps(params) for params in [entry["parameters"] for entry in transformations["operators"] if entry["name"] == op["name"]]] for op in transformations["operators"]}

        selected_sequences = []
        object_ids = [obj.obj_id for obj in objects]

        selection_frame = tk.LabelFrame(window, text="Chọn object và phép biến đổi", font=("Helvetica", 10, "bold"), padx=10, pady=10, bg="#ecf0f1", fg="#2c3e50")
        selection_frame.pack(fill="x", padx=10, pady=5)

        tk.Label(selection_frame, text="Chọn object:", font=("Helvetica", 10), bg="#ecf0f1").pack()
        object_var = tk.StringVar(value=object_ids[0] if object_ids else "")
        object_box = ttk.Combobox(selection_frame, textvariable=object_var, values=object_ids, width=30)
        object_box.pack(pady=5)

        operators_frame = tk.LabelFrame(selection_frame, text="Chọn phép biến đổi", font=("Helvetica", 10, "bold"), padx=5, pady=5, bg="#ecf0f1", fg="#2c3e50")
        operators_frame.pack(fill="x", pady=5)

        operators = list(operator_options.keys())
        operator_var = tk.StringVar(value=operators[0] if operators else "")
        operator_box = ttk.Combobox(operators_frame, textvariable=operator_var, values=operators, width=15)
        operator_box.pack(side=tk.LEFT, padx=5)

        params_var = tk.StringVar(value=operator_options[operators[0]][0] if operators else "")
        params_box = ttk.Combobox(operators_frame, textvariable=params_var, values=operator_options.get(operator_var.get(), []), width=30)
        params_box.pack(side=tk.LEFT, padx=5)

        def update_params(*args):
            new_operator = operator_var.get()
            params_box['values'] = operator_options.get(new_operator, [])
            params_box.set(operator_options.get(new_operator, [""])[0] if operator_options.get(new_operator) else "")

        operator_var.trace('w', update_params)

        selected_ops_frame = tk.LabelFrame(selection_frame, text="Các phép biến đổi đã chọn", font=("Helvetica", 10, "bold"), padx=5, pady=5, bg="#ecf0f1", fg="#2c3e50")
        selected_ops_frame.pack(fill="x", pady=5)
        selected_ops_listbox = tk.Listbox(selected_ops_frame, height=5, width=50, font=("Helvetica", 9), bg="#f9f9f9")
        selected_ops_listbox.pack()

        temp_transformations = []

        def add_transformation():
            operator = operator_var.get()
            params_str = params_var.get()
            if not operator or not params_str:
                messagebox.showerror("Lỗi", "Vui lòng chọn toán tử và tham số")
                return
            try:
                params = json.loads(params_str)
                temp_transformations.append((operator, params))
                selected_ops_listbox.insert(tk.END, f"{operator} {params}")
            except json.JSONDecodeError:
                messagebox.showerror("Lỗi", "Tham số không hợp lệ")

        def delete_transformation():
            idx = selected_ops_listbox.curselection()
            if not idx:
                messagebox.showwarning("Cảnh báo", "Vui lòng chọn phép biến đổi để xóa")
                return
            idx = idx[0]
            temp_transformations.pop(idx)
            selected_ops_listbox.delete(idx)

        btn_frame_1 = tk.Frame(selection_frame, bg="#ecf0f1")
        btn_frame_1.pack(pady=5)
        ttk.Button(btn_frame_1, text="Thêm phép biến đổi", command=add_transformation).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame_1, text="Xóa phép biến đổi", command=delete_transformation).pack(side=tk.LEFT, padx=5)

        def add_to_sequence():
            obj_id = object_var.get()
            if not temp_transformations:
                messagebox.showerror("Lỗi", f"Vui lòng thêm phép biến đổi cho object {obj_id}")
                return
            selected_sequences.append((obj_id, temp_transformations[:]))
            sequence_listbox.insert(tk.END, f"Object {obj_id}: {', '.join([t[0] for t in temp_transformations])}")
            temp_transformations.clear()
            selected_ops_listbox.delete(0, tk.END)

        ttk.Button(selection_frame, text="Thêm vào chuỗi", command=add_to_sequence).pack(pady=5)

        order_frame = tk.LabelFrame(window, text="Sắp xếp thứ tự thực hiện", font=("Helvetica", 10, "bold"), padx=10, pady=10, bg="#ecf0f1", fg="#2c3e50")
        order_frame.pack(fill="x", padx=10, pady=5)

        sequence_listbox = tk.Listbox(order_frame, height=5, width=50, font=("Helvetica", 9), bg="#f9f9f9")
        sequence_listbox.pack()

        def move_up():
            idx = sequence_listbox.curselection()
            if not idx or idx[0] == 0:
                return
            idx = idx[0]
            item = selected_sequences.pop(idx)
            selected_sequences.insert(idx - 1, item)
            sequence_listbox.delete(0, tk.END)
            for obj_id, transformations in selected_sequences:
                sequence_listbox.insert(tk.END, f"Object {obj_id}: {', '.join([t[0] for t in transformations])}")
            sequence_listbox.selection_set(idx - 1)

        def move_down():
            idx = sequence_listbox.curselection()
            if not idx or idx[0] == len(selected_sequences) - 1:
                return
            idx = idx[0]
            item = selected_sequences.pop(idx)
            selected_sequences.insert(idx + 1, item)
            sequence_listbox.delete(0, tk.END)
            for obj_id, transformations in selected_sequences:
                sequence_listbox.insert(tk.END, f"Object {obj_id}: {', '.join([t[0] for t in transformations])}")
            sequence_listbox.selection_set(idx + 1)

        def delete_sequence():
            idx = sequence_listbox.curselection()
            if not idx:
                messagebox.showwarning("Cảnh báo", "Vui lòng chọn chuỗi để xóa")
                return
            idx = idx[0]
            selected_sequences.pop(idx)
            sequence_listbox.delete(idx)

        btn_frame_2 = tk.Frame(order_frame, bg="#ecf0f1")
        btn_frame_2.pack(pady=5)
        ttk.Button(btn_frame_2, text="Lên", command=move_up).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame_2, text="Xuống", command=move_down).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame_2, text="Xóa chuỗi", command=delete_sequence).pack(side=tk.LEFT, padx=5)

        def apply_sequence():
            if not selected_sequences:
                messagebox.showerror("Lỗi", "Vui lòng thêm ít nhất một object và phép biến đổi")
                return
            self.apply_sequence_stages(selected_sequences, img)

        ttk.Button(window, text="Áp dụng", command=apply_sequence).pack(pady=10)

    def apply_sequence_stages(self, sequences, img):
        stage = 0
        result_text = tk.Text(self, height=5, width=50, font=("Helvetica", 9), bg="#ecf0f1")
        result_text.pack(pady=5)

        all_steps = []
        for obj_id, transformations in sequences:
            for op_name, params in transformations:
                all_steps.append((obj_id, op_name, params))

        def apply_next_stage(current_stage):
            nonlocal stage
            if current_stage >= len(all_steps):
                messagebox.showinfo("Hoàn tất", "Đã áp dụng tất cả các giai đoạn")
                result_text.destroy()
                self.display_selected_image()
                return

            obj_id, operator_name, params = all_steps[current_stage]
            operator_instance = self.tlm.TLMsearch(operator_name, params)
            if not operator_instance:
                messagebox.showerror("Lỗi", f"Không tìm thấy toán tử {operator_name} với tham số {params}")
                return

            for obj in img.objects:
                if obj.obj_id == obj_id:
                    stage += 1
                    result_text.delete(1.0, tk.END)
                    result_text.insert(tk.END, f"Stage {stage}: {operator_name} {params} cho {obj_id}")
                    operator_instance.apply(obj)
                    save_database(self.db, db_file)
                    self.display_selected_image()
                    self.after(1000, lambda: apply_next_stage(current_stage + 1))
                    break

        apply_next_stage(0)

    def open_operator_window(self, target_obj):
        op_win = tk.Toplevel(self)
        op_win.title("Chọn Toán Tử")
        op_win.configure(bg="#f0f4f8")
        op_win.geometry("300x300")

        frame = tk.Frame(op_win, bg="#f0f4f8")
        frame.pack(padx=20, pady=20, fill="both", expand=True)

        tk.Label(frame, text="Chọn Toán Tử:", font=("Helvetica", 10), bg="#f0f4f8").pack()
        op_listbox = tk.Listbox(frame, height=8, width=30, font=("Helvetica", 9), bg="#ecf0f1")
        for name in self.tlm.list_operators():
            op_listbox.insert(tk.END, name)
        op_listbox.pack(pady=5)

        def on_operator_select():
            idx = op_listbox.curselection()
            if not idx:
                return
            op_name = op_listbox.get(idx[0])
            op_def = self.tlm.TLMsearch(op_name)
            if not op_def:
                return

            params = {}
            for key, typ in op_def.parameters.items():
                raw_val = simpledialog.askstring("Tham số", f"{key} ({typ}):")
                try:
                    origin = get_origin(typ)
                    if origin is tuple:
                        parsed_val = ast.literal_eval(raw_val)
                        expected_types = get_args(typ)
                        if not isinstance(parsed_val, tuple):
                            raise ValueError(f"{key} phải là tuple.")
                        if len(parsed_val) != len(expected_types):
                            raise ValueError(f"{key} phải có {len(expected_types)} phần tử.")
                        for i, (v, t) in enumerate(zip(parsed_val, expected_types)):
                            if not isinstance(v, t):
                                raise ValueError(f"Phần tử {i} trong {key} phải là {t.__name__}")
                        params[key] = parsed_val
                    else:
                        params[key] = typ(raw_val)
                except Exception as e:
                    messagebox.showerror("Lỗi", f"Lỗi nhập tham số cho '{key}': {e}")
                    return

            try:
                inst = self.tlm.TLMsearch(op_name, params)
                inst.apply(target_obj)
                save_database(self.db, db_file)
                self.display_selected_image()
                messagebox.showinfo("OK", f"Đã áp dụng {op_name} cho {target_obj.obj_id}")
                op_win.destroy()
            except Exception as e:
                messagebox.showerror("Lỗi", f"Lỗi khi áp dụng toán tử: {e}")

        ttk.Button(frame, text="Áp dụng Toán Tử", command=on_operator_select).pack(pady=10)

if __name__ == "__main__":
    app = ObjectEditorGUI(db)
    app.mainloop()