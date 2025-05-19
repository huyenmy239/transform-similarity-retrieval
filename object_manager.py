# object_manager.py
from dataclasses import dataclass
from typing import Tuple, List, Dict
import pickle
import os


@dataclass
class ImageObjectRegion:
    # obj_id: str
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
    objects: List[ImageObjectRegion]

    def add_object(self, obj: ImageObjectRegion):
        self.objects.append(obj)


class ImageDatabase:
    def __init__(self):
        self.images: Dict[str, ImageMeta] = {}

    def add_image(self, image: ImageMeta):
        self.images[image.name] = image

    def get_image(self, name: str) -> ImageMeta:
        return self.images[name]

    def list_images(self):
        return list(self.images.keys())

    def delete_image(self, name: str):
        if name in self.images:
            del self.images[name]


# --- Lưu và tải ---
def save_database(db: ImageDatabase, filename="image_database.pkl"):
    with open(filename, "wb") as f:
        pickle.dump(db, f)


def load_database(filename="image_database.pkl") -> ImageDatabase:
    with open(filename, "rb") as f:
        return pickle.load(f)


def load_or_create_database(filename="image_database.pkl") -> ImageDatabase:
    return load_database(filename) if os.path.exists(filename) else ImageDatabase()
