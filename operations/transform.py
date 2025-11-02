def rotate_image(img, degree):
    return img.rotate(degree, expand=True)

def resize_image(img, w, h):
    return img.resize((w, h))
