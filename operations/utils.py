"""
utils.py
General helper utilities.
"""
from PIL import Image


def ensure_rgb(img: Image.Image) -> Image.Image:
    return img.convert('RGB')
