from PIL import Image, ImageDraw
import matplotlib.pyplot as plt
from object_manager import ImageObjectRegion


def display_object(obj: ImageObjectRegion, title: str = ""):
    # Tạo ảnh trắng kích thước đủ lớn để hiển thị vật thể
    img = Image.new("RGB", (100, 100), (255, 255, 255))
    draw = ImageDraw.Draw(img)

    color = obj.color if obj.color else (0, 0, 0)  # Mặc định màu đen nếu chưa có màu
    draw.rectangle([obj.x1, obj.y1, obj.x2, obj.y2], fill=color, outline=(0, 0, 0))

    plt.imshow(img)
    plt.title(title)
    plt.axis("off")
    plt.show()
