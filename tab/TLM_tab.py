import tkinter as tk
from tkinter import ttk, messagebox
import json
from PIL import Image, ImageDraw, ImageTk
from transformation_manager import TransformationLibraryManager, create_default_object_operators, load_transformations_from_json, add_operator_to_json
from object_manager import ImageDatabase, save_database
from typing import get_origin, get_args

class TabTLM:
    def __init__(self, parent, db: ImageDatabase):
        self.parent = parent
        self.db = db
        self.db_file = "image_database.pkl"
        self.tlm = TransformationLibraryManager()
        for op in create_default_object_operators():
            self.tlm.TLMinsert(op)
        self.tk_image = None
        self.setup_ui()

    def setup_ui(self):
        # Frame chính
        main_frame = tk.Frame(self.parent, bg="#f0f4f8")
        main_frame.pack(padx=10, pady=10, fill="both", expand=True)

        # Frame cho canvas
        canvas_frame = tk.LabelFrame(main_frame, text="Xem trước ảnh", font=("Helvetica", 12, "bold"), bg="#f0f4f8", fg="#2c3e50")
        canvas_frame.pack(side=tk.LEFT, padx=10, pady=5, fill="both")

        # Tạo canvas container với thanh cuộn
        canvas_container = tk.Frame(canvas_frame, bg="#f0f4f8")
        canvas_container.pack(padx=10, pady=10)

        self.canvas = tk.Canvas(canvas_container, width=600, height=400, bg="white", highlightthickness=1, highlightbackground="#bdc3c7", scrollregion=(0, 0, 600, 400))
        self.canvas.pack(side=tk.LEFT, fill="both")

        # Thêm thanh cuộn dọc
        v_scrollbar = ttk.Scrollbar(canvas_container, orient="vertical", command=self.canvas.yview)
        v_scrollbar.pack(side=tk.RIGHT, fill="y")
        self.canvas.configure(yscrollcommand=v_scrollbar.set)

        # Thêm thanh cuộn ngang
        h_scrollbar = ttk.Scrollbar(canvas_frame, orient="horizontal", command=self.canvas.xview)
        h_scrollbar.pack(side=tk.BOTTOM, fill="x")
        self.canvas.configure(xscrollcommand=h_scrollbar.set)

        # Frame cho các điều khiển
        control_frame = tk.Frame(main_frame, bg="#f0f4f8")
        control_frame.pack(side=tk.RIGHT, padx=10, pady=5, fill="y")

        # Combobox chọn ảnh
        tk.Label(control_frame, text="Chọn ảnh:", font=("Helvetica", 10), bg="#f0f4f8").pack()
        self.selected_image = tk.StringVar()
        self.image_selector = ttk.Combobox(control_frame, textvariable=self.selected_image, width=25)
        self.image_selector['values'] = self.db.list_images()
        self.image_selector.pack(pady=5)
        self.image_selector.bind("<<ComboboxSelected>>", self.on_image_selected)

        # Combobox chọn object
        tk.Label(control_frame, text="Chọn object:", font=("Helvetica", 10), bg="#f0f4f8").pack()
        self.object_var = tk.StringVar()
        self.object_box = ttk.Combobox(control_frame, textvariable=self.object_var, width=25, state="disabled")
        self.object_box.pack(pady=5)
        self.object_box.bind("<<ComboboxSelected>>", self.on_object_selected)

        # Combobox chọn toán tử
        self.operator_label = tk.Label(control_frame, text="Chọn toán tử:", font=("Helvetica", 10), bg="#f0f4f8")
        self.operator_name = tk.StringVar()
        self.operator_box = ttk.Combobox(control_frame, textvariable=self.operator_name, width=25, state="disabled")
        self.operator_box['values'] = self.tlm.list_operators()

        self.continue_btn = ttk.Button(control_frame, text="Tiếp tục", command=self.choose_option, state="disabled")

    def on_image_selected(self, event=None):
        name = self.selected_image.get()
        if not name:
            self.object_box.configure(state="disabled")
            self.operator_box.configure(state="disabled")
            self.continue_btn.configure(state="disabled")
            self.canvas.delete("all")
            return
        # Hiển thị ảnh
        img_meta = self.db.get_image(name)
        image = Image.new("RGB", (img_meta.width, img_meta.height), "white")
        draw = ImageDraw.Draw(image)
        for obj in img_meta.objects:
            draw.rectangle([obj.x1, obj.y1, obj.x2, obj.y2], fill=obj.color, outline="black", width=2)
        draw.rectangle([0, 0, img_meta.width - 1, img_meta.height - 1], outline="black", width=3)
        self.tk_image = ImageTk.PhotoImage(image)
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_image)
        self.canvas.configure(scrollregion=(0, 0, img_meta.width, img_meta.height))

        # Cập nhật danh sách object
        self.object_box['values'] = [obj.obj_id for obj in img_meta.objects]
        self.object_box.configure(state="normal")
        self.object_var.set("")  # Reset object selection

    def on_object_selected(self, event):
        if self.object_var.get():
            self.operator_label.pack()
            self.operator_box.pack()
            self.operator_box.configure(state="normal")
            self.continue_btn.pack(pady=10)
            self.continue_btn.configure(state="normal")

    def choose_option(self):
        selected_obj = self.object_var.get()
        selected_op = self.operator_name.get()
        if not selected_op or not selected_obj:
            messagebox.showerror("Lỗi", "Phải chọn object và toán tử")
            return

        sub_window = tk.Toplevel(self.parent)
        sub_window.title(f"Tùy chọn cho {selected_op}")
        sub_window.configure(bg="#f0f4f8")
        sub_window.geometry("300x150")
        sub_frame = tk.Frame(sub_window, bg="#f0f4f8")
        sub_frame.pack(padx=20, pady=20, fill="both", expand=True)
        tk.Button(sub_frame, text="Chọn từ file JSON", command=lambda: self.apply_from_json(selected_op, selected_obj, sub_window), font=("Helvetica", 10)).pack(pady=5)
        tk.Button(sub_frame, text="Nhập tham số thủ công", command=lambda: self.manual_param_input(selected_op, selected_obj, sub_window), font=("Helvetica", 10)).pack(pady=5)

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
                    # Apply transformation first
                    self.apply_to_one_object(object_id, inst)
                    # Update image display
                    self.on_image_selected()
                    # Show success message
                    messagebox.showinfo("Thành công", "Đã áp dụng phép biến đổi")
                    # Close windows
                    select_win.destroy()
                    window.destroy()

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

                # Add to JSON (if successful, include in success message)
                json_result = add_operator_to_json(op_name, param_dict)
                # Apply transformation
                self.apply_to_one_object(object_id, operator_instance)
                # Update image display
                self.on_image_selected()
                # Show success message (include JSON result if needed)
                messagebox.showinfo("Thành công", f"Đã áp dụng phép biến đổi.\n{json_result}")
                # Close windows
                input_win.destroy()
                window.destroy()

            except Exception as e:
                messagebox.showerror("Lỗi", f"Tham số không hợp lệ: {e}")

        ttk.Button(frame, text="Áp dụng", command=apply_manual).pack(pady=10)

    def apply_to_one_object(self, object_id: str, operator):
        img_name = self.selected_image.get()
        img = self.db.get_image(img_name)
        for obj in img.objects:
            if obj.obj_id == object_id:
                operator.apply(obj)
                save_database(self.db, self.db_file)
                return