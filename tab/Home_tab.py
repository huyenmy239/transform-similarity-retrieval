import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageDraw, ImageTk
from object_manager import ImageDatabase, ImageMeta, ImageObjectRegion, save_database
import ast

class TabHome:
    def __init__(self, parent, db: ImageDatabase):
        self.parent = parent
        self.db = db
        self.db_file = "image_database.pkl"
        self.tk_image = None
        self.setup_ui()

    def setup_ui(self):
        # Frame chính
        main_frame = tk.Frame(self.parent, bg="#f0f4f8")
        main_frame.pack(padx=10, pady=10, fill="both", expand=True)

        # Frame cho canvas với kích thước cố định và thanh cuộn
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

        tk.Label(control_frame, text="Chọn ảnh:", font=("Helvetica", 10), bg="#f0f4f8").pack()
        self.selected_image = tk.StringVar()
        self.image_selector = ttk.Combobox(control_frame, textvariable=self.selected_image, width=20)
        self.image_selector['values'] = self.db.list_images()
        self.image_selector.pack(pady=5)
        self.image_selector.bind("<<ComboboxSelected>>", self.display_selected_image)

        ttk.Button(control_frame, text="Thêm ảnh mới", command=self.add_image_window, width=20).pack(pady=5)
        ttk.Button(control_frame, text="Chỉnh sửa object", command=self.edit_objects_window, width=20).pack(pady=5)

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
        # Cập nhật scrollregion để phù hợp với kích thước ảnh
        self.canvas.configure(scrollregion=(0, 0, max(img_meta.width, 600), max(img_meta.height, 400)))
        

    def add_image_window(self):
        window = tk.Toplevel(self.parent)
        window.title("Thêm ảnh mới")
        window.configure(bg="#f0f4f8")
        window.geometry("300x200")

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
                save_database(self.db, self.db_file)
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
            messagebox.showerror("Lỗi", "Vui lòng chọn ảnh trước")
            return
        img_meta = self.db.get_image(name)
        window = tk.Toplevel(self.parent)
        window.title("Chỉnh sửa các object")
        window.configure(bg="#f0f4f8")
        window.geometry("450x600")

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
                save_database(self.db, self.db_file)
                self.display_selected_image()
                window.destroy()
            except Exception as e:
                messagebox.showerror("Lỗi", str(e))

        ttk.Button(scrollable_frame, text="Lưu", command=save).pack(pady=10)