"""
basic_ops.py
Basic operations: negative, colour conversions, thresholding, convolution, FFT spectrum.
All functions accept and return PIL.Image.Image objects.
"""
from PIL import Image, ImageOps
import numpy as np


def invert(img: Image.Image) -> Image.Image:
    """Return negative of image."""
    return ImageOps.invert(img.convert('RGB'))


def convert_color(img: Image.Image, mode: str) -> Image.Image:
    """Convert image to several color spaces or pseudo-colour.

    mode options:
      - 'binary' : convert to 1-bit using Otsu-like simple threshold (128)
      - 'L'      : grayscale
      - 'RGB'    : RGB
      - 'HSV'    : HSV (PIL handles conversion)
      - 'CMY'    : convert RGB -> CMY (as RGB image showing C M Y channels)
      - 'YUV'    : convert RGB -> YUV and return an RGB visualization
      - 'YIQ'    : convert RGB -> YIQ and return an RGB visualization
      - 'pseudo' : apply a simple pseudo-color map to grayscale
    """
    mode = mode.lower()
    if mode == 'binary':
        gray = img.convert('L')
        arr = np.array(gray)
        bw = (arr > 128).astype('uint8') * 255
        return Image.fromarray(bw).convert('RGB')
    if mode == 'l':
        return img.convert('L').convert('RGB')
    if mode == 'rgb':
        return img.convert('RGB')
    if mode == 'hsv':
        # PIL can convert to HSV; return as RGB visualization by converting back
        return img.convert('RGB').convert('HSV').convert('RGB')

    # operate on numpy RGB
    arr = np.array(img.convert('RGB')).astype('float32') / 255.0
    r = arr[..., 0]
    g = arr[..., 1]
    b = arr[..., 2]

    if mode == 'cmy':
        # CMY = 1 - RGB
        c = 1.0 - r
        m = 1.0 - g
        y = 1.0 - b
        out = np.stack((c, m, y), axis=-1)
        out = (out * 255.0).clip(0,255).astype('uint8')
        return Image.fromarray(out)

    if mode == 'yuv':
        # using YUV (BT.601-like)
        y = 0.299*r + 0.587*g + 0.114*b
        u = -0.14713*r - 0.28886*g + 0.436*b
        v = 0.615*r - 0.51499*g - 0.10001*b
        # normalize for display
        Y = (y - y.min()) / (y.max() - y.min() + 1e-9)
        U = (u - u.min()) / (u.max() - u.min() + 1e-9)
        V = (v - v.min()) / (v.max() - v.min() + 1e-9)
        out = np.stack((Y, U, V), axis=-1)
        out = (out * 255.0).clip(0,255).astype('uint8')
        return Image.fromarray(out)

    if mode == 'yiq':
        Y = 0.299*r + 0.587*g + 0.114*b
        I = 0.596*r - 0.274*g - 0.322*b
        Q = 0.211*r - 0.523*g + 0.312*b
        Yv = (Y - Y.min()) / (Y.max() - Y.min() + 1e-9)
        Iv = (I - I.min()) / (I.max() - I.min() + 1e-9)
        Qv = (Q - Q.min()) / (Q.max() - Q.min() + 1e-9)
        out = np.stack((Yv, Iv, Qv), axis=-1)
        out = (out*255.0).clip(0,255).astype('uint8')
        return Image.fromarray(out)

    if mode == 'pseudo':
        # simple pseudo color: map grayscale to a colormap (jet-like)
        gray = img.convert('L')
        a = np.array(gray).astype('float32') / 255.0
        # create simple colormap
        def jet(x):
            r = np.clip(1.5 - np.abs(4.0*x - 3.0), 0, 1)
            g = np.clip(1.5 - np.abs(4.0*x - 2.0), 0, 1)
            b = np.clip(1.5 - np.abs(4.0*x - 1.0), 0, 1)
            return np.stack((r,g,b), axis=-1)
        col = jet(a[..., None])
        out = (col * 255.0).astype('uint8')
        return Image.fromarray(out)

    # fallback
    return img.convert('RGB')


def threshold(img: Image.Image, t: int=128) -> Image.Image:
    """Apply global threshold on luminance."""
    gray = img.convert('L')
    arr = np.array(gray)
    bw = (arr > int(t)).astype('uint8') * 255
    return Image.fromarray(bw).convert('RGB')


def convolution(img: Image.Image, kernel) -> Image.Image:
    """Apply 3x3 convolution kernel. `kernel` can be nested list or numpy array."""
    kernel = np.array(kernel, dtype='float32')
    if kernel.shape != (3,3):
        raise ValueError('Kernel must be 3x3')
    arr = np.array(img.convert('RGB')).astype('float32')
    h,w = arr.shape[:2]
    pad = np.pad(arr, ((1,1),(1,1),(0,0)), mode='edge')
    out = np.zeros_like(arr)
    for y in range(h):
        for x in range(w):
            region = pad[y:y+3, x:x+3, :]
            # broadcast kernel over channels
            val = (region * kernel[..., None]).sum(axis=(0,1))
            out[y,x] = val
    out = np.clip(out, 0, 255).astype('uint8')
    return Image.fromarray(out)


def fft_spectrum(img: Image.Image) -> Image.Image:
    """Return magnitude spectrum visualization (log) as RGB image."""
    gray = img.convert('L')
    a = np.array(gray).astype('float32')
    f = np.fft.fft2(a)
    fshift = np.fft.fftshift(f)
    magnitude = np.log1p(np.abs(fshift))
    mag_norm = (magnitude - magnitude.min()) / (magnitude.max() - magnitude.min() + 1e-9)
    mag_img = (mag_norm * 255.0).astype('uint8')
    return Image.fromarray(mag_img).convert('RGB')
