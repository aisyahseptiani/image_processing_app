"""
filtering.py
Spatial and frequency-domain filtering.
Implements Gaussian and Median smoothing, and FFT-based ILPF, BLPF, IHPF, BHPF.
"""
from PIL import Image, ImageFilter
import numpy as np


def smoothing(img: Image.Image, typ: str) -> Image.Image:
    if typ == 'gaussian':
        return img.filter(ImageFilter.GaussianBlur(radius=2))
    if typ == 'median':
        return img.filter(ImageFilter.MedianFilter(size=3))
    return img


def _fft2_gray(img: Image.Image):
    g = np.array(img.convert('L')).astype('float32')
    f = np.fft.fft2(g)
    fshift = np.fft.fftshift(f)
    return g, f, fshift


def _ifft2_to_img(fshift):
    ishift = np.fft.ifftshift(fshift)
    inv = np.fft.ifft2(ishift)
    inv = np.abs(inv)
    inv = (inv - inv.min()) / (inv.max() - inv.min() + 1e-9) * 255
    return Image.fromarray(inv.astype('uint8')).convert('RGB')


def _ideal_lowpass(shape, D0):
    P, Q = shape
    u = np.arange(P)
    v = np.arange(Q)
    U, V = np.meshgrid(u, v, indexing='ij')
    D = np.sqrt((U - P/2)**2 + (V - Q/2)**2)
    return (D <= D0).astype('float32')


def _ideal_highpass(shape, D0):
    return 1 - _ideal_lowpass(shape, D0)


def _butterworth_lowpass(shape, D0, n=2):
    P, Q = shape
    u = np.arange(P)
    v = np.arange(Q)
    U, V = np.meshgrid(u, v, indexing='ij')
    D = np.sqrt((U - P/2)**2 + (V - Q/2)**2)
    return 1 / (1 + (D / (D0 + 1e-9))**(2*n))


def _butterworth_highpass(shape, D0, n=2):
    return 1 - _butterworth_lowpass(shape, D0, n)


def frequency_filter(img: Image.Image, typ: str, D0: int):
    """Apply ILPF, BLPF, IHPF, BHPF via FFT on luminance."""
    g, f, fshift = _fft2_gray(img)
    shape = fshift.shape

    if typ == 'ilpf':
        H = _ideal_lowpass(shape, D0)
    elif typ == 'blpf':
        H = _butterworth_lowpass(shape, D0)
    elif typ == 'ihpf':
        H = _ideal_highpass(shape, D0)
    elif typ == 'bhpf':
        H = _butterworth_highpass(shape, D0)
    else:
        return img

    G = fshift * H
    return _ifft2_to_img(G)
