"""
noise.py
Gaussian, Uniform, Salt & Pepper, Rayleigh, Erlang, Exponential noise.
"""
from PIL import Image
import numpy as np


def add_noise(img: Image.Image, typ: str, **kwargs) -> Image.Image:
    arr = np.array(img.convert('RGB')).astype('float32')

    if typ == 'gaussian':
        sigma = float(kwargs.get('sigma', 20.0))
        noise = np.random.normal(0, sigma, arr.shape)
        out = arr + noise

    elif typ == 'uniform':
        low = float(kwargs.get('low', -20))
        high = float(kwargs.get('high', 20))
        noise = np.random.uniform(low, high, arr.shape)
        out = arr + noise

    elif typ == 's&p':
        amount = float(kwargs.get('amount', 0.05))
        out = arr.copy()
        num = int(amount * arr.shape[0] * arr.shape[1])
        # salt
        ys = np.random.randint(0, arr.shape[0], num)
        xs = np.random.randint(0, arr.shape[1], num)
        out[ys, xs] = 255
        # pepper
        ys = np.random.randint(0, arr.shape[0], num)
        xs = np.random.randint(0, arr.shape[1], num)
        out[ys, xs] = 0

    elif typ == 'rayleigh':
        scale = float(kwargs.get('scale', 10.0))
        noise = np.random.rayleigh(scale, arr.shape)
        out = arr + noise

    elif typ == 'erlang':
        k = int(kwargs.get('k', 3))
        lam = float(kwargs.get('lam', 0.5))
        noise = np.random.gamma(k, 1/lam, arr.shape)
        out = arr + noise

    elif typ == 'exponential':
        lam = float(kwargs.get('lam', 0.5))
        noise = np.random.exponential(1/lam, arr.shape)
        out = arr + noise

    else:
        return img

    out = out.clip(0,255).astype('uint8')
    return Image.fromarray(out)
