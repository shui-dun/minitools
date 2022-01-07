import numpy as np
from PIL import Image
from PIL import ImageEnhance
from daltonize import daltonize as dz


def colorblind_img(img, type):
    rgb_arr = np.array(img)
    cb_arr = dz.daltonize(rgb_arr, color_deficit=type).astype('uint8')
    cb_img = Image.fromarray(cb_arr)
    return cb_img


def enhance(img):
    return ImageEnhance.Contrast(img).enhance(1.5)


if __name__ == '__main__':
    img = Image.open('origin.png')
    img.show()
    img = colorblind_img(img, 'd')
    # img = colorblind_img(img, 'p')
    img = enhance(img)
    img.show()
