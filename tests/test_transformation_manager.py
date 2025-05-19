import tkinter as tk
from tkinter import ttk
from dataclasses import dataclass
from typing import Tuple
from PIL import Image, ImageDraw, ImageTk

# --- Dữ liệu class ---
@dataclass
class ImageObjectRegion:
    obj_id: str
    x1: int
    y1: int
    x2: int
    y2: int
    color: Tuple[int, int, int]

@dataclass
class ImageMeta:
    name: str
    width: int
    height: int
    objects: list

    def add_object(self, obj: ImageObjectRegion):
        self.objects.append(obj)

class ImageDatabase:
    def __init__(self):
        self.images: dict[str, ImageMeta] = {}

    def add_image(self, image: ImageMeta):
        self.images[image.name] = image

    def get_image(self, name: str) -> ImageMeta:
        return self.images[name]

    def list_images(self):
        return list(self.images.keys())


# --- Tạo database demo ---
db = ImageDatabase()

# Tạo các object
obj1 = ImageObjectRegion("ob1", 100, 200, 200, 400, (0, 0, 255))
obj2 = ImageObjectRegion("ob2", 200, 200, 400, 300, (255, 0, 0))
obj3 = ImageObjectRegion("ob3", 400, 200, 500, 300, (0, 255, 0))

# Tạo image
image1 = ImageMeta("image1", width=600, height=500, objects=[])
image1.add_object(obj1)
image1.add_object(obj2)
image1.add_object(obj3)
db.add_image(image1)

# --- UI hiển thị ---
class ImageViewer(tk.Tk):
    def __init__(self, db: ImageDatabase):
        super().__init__()
        self.title("Image Database Viewer")
        self.db = db
        self.canvas = tk.Canvas(self, width=600, height=500, bg="white")
        self.canvas.pack()

        # Dropdown chọn ảnh
        self.selected_image = tk.StringVar()
        self.image_selector = ttk.Combobox(self, textvariable=self.selected_image)
        self.image_selector['values'] = self.db.list_images()
        self.image_selector.pack()
        self.image_selector.bind("<<ComboboxSelected>>", self.display_selected_image)

        self.tk_image = None  # giữ tham chiếu ảnh để tránh bị thu gom rác

    def display_selected_image(self, event=None):
        name = self.selected_image.get()
        img_meta = self.db.get_image(name)

        # Tạo ảnh nền trắng
        image = Image.new("RGB", (img_meta.width, img_meta.height), "white")
        draw = ImageDraw.Draw(image)

        # Vẽ và fill các object
        for obj in img_meta.objects:
            draw.rectangle([obj.x1, obj.y1, obj.x2, obj.y2], fill=obj.color)

        self.tk_image = ImageTk.PhotoImage(image)
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_image)




# --- Khởi chạy ---
if __name__ == "__main__":
    app = ImageViewer(db)
    app.mainloop()
