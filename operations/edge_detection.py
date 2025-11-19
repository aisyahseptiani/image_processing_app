"""
edge_detection.py
Sobel, Prewitt, Roberts, Laplacian, LoG, Canny.
Pure NumPy implementations.
"""
from PIL import Image
import numpy as np


def _conv2d(img, kernel):
    kh, kw = kernel.shape
    ih, iw = img.shape
    pad_h, pad_w = kh//2, kw//2
    padded = np.pad(img, ((pad_h,pad_h),(pad_w,pad_w)), mode='edge')
    out = np.zeros_like(img, dtype='float32')
    for y in range(ih):
        for x in range(iw):
            region = padded[y:y+kh, x:x+kw]
            out[y,x] = np.sum(region * kernel)
    return out


def sobel(img):
    g = np.array(img.convert('L')).astype('float32')
    gx = np.array([[-1,0,1],[-2,0,2],[-1,0,1]], dtype='float32')
    gy = np.array([[1,2,1],[0,0,0],[-1,-2,-1]], dtype='float32')
    sx = _conv2d(g, gx)
    sy = _conv2d(g, gy)
    mag = np.hypot(sx, sy)
    mag = (mag / (mag.max()+1e-9)) * 255
    return Image.fromarray(mag.astype('uint8')).convert('RGB')


def prewitt(img):
    g = np.array(img.convert('L')).astype('float32')
    gx = np.array([[-1,0,1],[-1,0,1],[-1,0,1]], dtype='float32')
    gy = np.array([[1,1,1],[0,0,0],[-1,-1,-1]], dtype='float32')
    sx = _conv2d(g, gx)
    sy = _conv2d(g, gy)
    mag = np.hypot(sx, sy)
    mag = (mag / (mag.max()+1e-9)) * 255
    return Image.fromarray(mag.astype('uint8')).convert('RGB')


def roberts(img):
    g = np.array(img.convert('L')).astype('float32')
    k1 = np.array([[1,0],[0,-1]], dtype='float32')
    k2 = np.array([[0,1],[-1,0]], dtype='float32')
    r1 = _conv2d(g, k1)
    r2 = _conv2d(g, k2)
    mag = np.sqrt(r1*r1 + r2*r2)
    mag = (mag / (mag.max()+1e-9)) * 255
    return Image.fromarray(mag.astype('uint8')).convert('RGB')


def laplacian(img):
    g = np.array(img.convert('L')).astype('float32')
    k = np.array([[-1,-1,-1],[-1,8,-1],[-1,-1,-1]], dtype='float32')
    out = _conv2d(g, k)
    out = (out - out.min()) / (out.max()-out.min()+1e-9) * 255
    return Image.fromarray(out.astype('uint8')).convert('RGB')


def log(img):
    g = np.array(img.convert('L')).astype('float32')
    # LoG kernel 5x5
    log_k = np.array([
        [0, 0,-1, 0, 0],
        [0,-1,-2,-1, 0],
        [-1,-2,16,-2,-1],
        [0,-1,-2,-1, 0],
        [0, 0,-1, 0, 0]
    ], dtype='float32')
    out = _conv2d(g, log_k)
    out = (out - out.min()) / (out.max()-out.min()+1e-9) * 255
    return Image.fromarray(out.astype('uint8')).convert('RGB')


# ================= CANNY ==================
def _gaussian_blur(img):
    k = np.array([[2, 4, 5, 4, 2],
                  [4, 9,12, 9, 4],
                  [5,12,15,12, 5],
                  [4, 9,12, 9, 4],
                  [2, 4, 5, 4, 2]], dtype='float32')
    k /= k.sum()
    return _conv2d(img, k)


def canny(img, low=50, high=150):
    g = np.array(img.convert('L')).astype('float32')
    # 1. smooth
    sm = _gaussian_blur(g)

    # 2. gradients
    gx = np.array([[-1,0,1],[-2,0,2],[-1,0,1]], dtype='float32')
    gy = np.array([[1,2,1],[0,0,0],[-1,-2,-1]], dtype='float32')
    sx = _conv2d(sm, gx)
    sy = _conv2d(sm, gy)

    mag = np.hypot(sx, sy)
    ang = np.rad2deg(np.arctan2(sy, sx)) % 180

    # 3. non-max suppression
    nms = np.zeros_like(mag)
    for y in range(1, mag.shape[0]-1):
        for x in range(1, mag.shape[1]-1):
            direction = ang[y,x]
            m = mag[y,x]
            if (0 <= direction < 22.5) or (157.5 <= direction <= 180):
                if m >= mag[y, x-1] and m >= mag[y, x+1]:
                    nms[y,x] = m
            elif 22.5 <= direction < 67.5:
                if m >= mag[y-1, x+1] and m >= mag[y+1, x-1]:
                    nms[y,x] = m
            elif 67.5 <= direction < 112.5:
                if m >= mag[y-1, x] and m >= mag[y+1, x]:
                    nms[y,x] = m
            else:
                if m >= mag[y-1, x-1] and m >= mag[y+1, x+1]:
                    nms[y,x] = m

    # 4. double threshold
    strong = (nms >= high)
    weak = (nms >= low) & ~strong
    res = np.zeros_like(nms, dtype='uint8')
    res[strong] = 255
    res[weak] = 50

    # 5. hysteresis
    for y in range(1, res.shape[0]-1):
        for x in range(1, res.shape[1]-1):
            if res[y,x] == 50:
                if np.any(res[y-1:y+2, x-1:x+2] == 255):
                    res[y,x] = 255
                else:
                    res[y,x] = 0

    return Image.fromarray(res).convert('RGB')
