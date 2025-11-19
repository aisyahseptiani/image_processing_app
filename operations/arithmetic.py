"""
arithmetic.py
Add, Subtract, Multiply, Divide between two images (same size).
"""
from PIL import Image
import numpy as np


def arithmetic(img1: Image.Image, img2: Image.Image, op: str) -> Image.Image:
    a = np.array(img1.convert('RGB')).astype('float32')
    b = np.array(img2.convert('RGB')).astype('float32')

    if op == 'add':
        r = a + b
    elif op == 'sub':
        r = a - b
    elif op == 'mul':
        r = (a * b) / 255.0
    elif op == 'div':
        b[b == 0] = 1
        r = (a / b) * 255.0
    else:
        return img1

    r = r.clip(0, 255).astype('uint8')
    return Image.fromarray(r)
