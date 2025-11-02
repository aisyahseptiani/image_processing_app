from PIL import ImageFilter

def blur_image(img):
    return img.filter(ImageFilter.BLUR)

def sharpen_image(img):
    return img.filter(ImageFilter.SHARPEN)

def gaussian_blur(img, radius=2):
    return img.filter(ImageFilter.GaussianBlur(radius))

def median_filter(img, size=3):
    return img.filter(ImageFilter.MedianFilter(size))
