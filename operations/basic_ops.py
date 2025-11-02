from PIL import Image, ImageOps, ImageEnhance

def to_grayscale(img):
    return img.convert("L").convert("RGB")

def invert_image(img):
    return ImageOps.invert(img)

def adjust_brightness(img, factor):
    enhancer = ImageEnhance.Brightness(img)
    return enhancer.enhance(factor)

def adjust_contrast(img, factor):
    enhancer = ImageEnhance.Contrast(img)
    return enhancer.enhance(factor)
