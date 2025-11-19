"""
enhancement.py
Image enhancement operations: brightness, contrast, histogram equalization,
highpass filtering (spatial), highboost filtering.
"""
from PIL import Image, ImageEnhance
import numpy as np


def brightness(img: Image.Image, factor: float) -> Image.Image:
    enhancer = ImageEnhance.Brightness(img)
    return enhancer.enhance(factor)


def contrast(img: Image.Image, factor: float) -> Image.Image:
    enhancer = ImageEnhance.Contrast(img)
    return enhancer.enhance(factor)


def hist_eq(img: Image.Image) -> Image.Image:
    gray = img.convert('L')
    arr = np.array(gray)
    hist, _ = np.histogram(arr.flatten(), 256, [0, 256])
    cdf = hist.cumsum()
    cdf_mask = np.ma.masked_equal(cdf, 0)
    cdf_mask = (cdf_mask - cdf_mask.min()) * 255 / (cdf_mask.max() - cdf_mask.min())
    cdf = np.ma.filled(cdf_mask, 0).astype('uint8')
    eq = cdf[arr]
    eq_img = Image.fromarray(eq)
    return Image.merge('RGB', (eq_img, eq_img, eq_img))


def highpass(img: Image.Image) -> Image.Image:
    kernel = np.array([[-1, -1, -1],
                       [-1,  8, -1],
                       [-1, -1, -1]], dtype='float32')
    arr = np.array(img.convert('RGB')).astype('float32')
    h, w = arr.shape[:2]
    pad = np.pad(arr, ((1,1),(1,1),(0,0)), mode='edge')
    out = np.zeros_like(arr)
    for y in range(h):
        for x in range(w):
            region = pad[y:y+3, x:x+3, :]
            out[y, x] = (region * kernel[..., None]).sum(axis=(0,1))
    out = np.clip(out, 0, 255).astype('uint8')
    return Image.fromarray(out)


def highboost(img: Image.Image, A: float=2.0) -> Image.Image:
    arr = np.array(img.convert('RGB')).astype('float32')
    blur = np.array(img.filter(ImageEnhance.Sharpness(img).enhance(0)).convert('RGB')).astype('float32')
    mask = arr - blur
    out = arr + (A - 1) * mask
    out = np.clip(out, 0, 255).astype('uint8')
    return Image.fromarray(out)
