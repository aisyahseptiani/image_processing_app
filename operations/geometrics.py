"""
geometrics.py
Rotation, translation, zooming, flipping, cropping.
"""
from PIL import Image
import numpy as np


def rotate(img: Image.Image, angle: float) -> Image.Image:
    return img.rotate(angle, expand=True)


def translate(img: Image.Image, dx: int, dy: int) -> Image.Image:
    w, h = img.size
    new_w = w + abs(dx)
    new_h = h + abs(dy)
    new_img = Image.new('RGB', (new_w, new_h), (0, 0, 0))
    ox = max(dx, 0)
    oy = max(dy, 0)
    new_img.paste(img, (ox, oy))
    return new_img


def zoom(img: Image.Image, factor: float) -> Image.Image:
    w, h = img.size
    return img.resize((int(w * factor), int(h * factor)), Image.LANCZOS)


def flip(img: Image.Image, horizontal: bool = True) -> Image.Image:
    if horizontal:
        return img.transpose(Image.FLIP_LEFT_RIGHT)
    return img.transpose(Image.FLIP_TOP_BOTTOM)


def crop(img: Image.Image, box) -> Image.Image:
    return img.crop(box)
