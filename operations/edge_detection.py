from PIL import ImageFilter

def edge_simple(img):
    return img.filter(ImageFilter.FIND_EDGES)

def edge_sobel(img):
    sobel_x = img.filter(ImageFilter.Kernel(
        size=(3,3),
        kernel=[-1,0,1, -2,0,2, -1,0,1],
        scale=1
    ))
    sobel_y = img.filter(ImageFilter.Kernel(
        size=(3,3),
        kernel=[-1,-2,-1, 0,0,0, 1,2,1],
        scale=1
    ))
    return sobel_x + sobel_y
