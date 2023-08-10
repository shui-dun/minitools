from multiprocessing import Pool
from PIL import Image, ImageFont
from handright import Template, handwrite
import os

if __name__ == '__main__':
    size = 120
    with open('input.txt', encoding='utf8') as f:
        text = f.read()
    template = Template(
        background=Image.open(r'resource/bg.png'),
        font_size=size,
        font=ImageFont.truetype(r"resource/hxk2.ttf"),
        line_spacing=int(1.5 * size),
        fill=0,
        left_margin=int(0.5 * size),
        top_margin=int(size * 1.2),
        right_margin=int(0.5 * size),
        bottom_margin=int(size * 1.2),
        word_spacing=0,
        line_spacing_sigma=0.06 * size,
        font_size_sigma=0.05 * size,
        word_spacing_sigma=0.03 * size,
        end_chars=',.?!，。？！、‘“；：',
        perturb_x_sigma=0.02 * size,
        perturb_y_sigma=0.02 * size,
        perturb_theta_sigma=0.0005 * size,
    )
    if not os.path.exists('output'):
        os.mkdir('output')
    with Pool() as p:
        images = handwrite(text, template, mapper=p.map)
        for i, im in enumerate(images):
            im.save("output/{}.jpg".format(i))
