"""
boolean.py
Logical NOT, AND, OR, XOR operations on images.
"""
from PIL import Image
import numpy as np


def logic_not(img: Image.Image) -> Image.Image:
    arr = np.array(img.convert('RGB')).astype('uint8')
    r = 255 - arr
    return Image.fromarray(r)


def logic_op(img1: Image.Image, img2: Image.Image, op: str) -> Image.Image:
    a = np.array(img1.convert('L')) > 128
    b = np.array(img2.convert('L')) > 128

    if op == 'and':
        r = a & b
    elif op == 'or':
        r = a | b
    elif op == 'xor':
        r = a ^ b
    else:
        return img1

    out = (r.astype('uint8') * 255)
    return Image.fromarray(out).convert('RGB')
