# from paper_eta.src.libs.renderer.waveshare.epd3in7.mixed import row_6_eta_1
# from paper_eta.src.libs import renderer
# from paper_eta.src.libs.hketa.test import TESTS_TC

# row_6_eta_1.Renderer().draw(TESTS_TC)["black"].save("./test.png")

import timeit
import PIL.Image


red = PIL.Image.open("./test_red.png").convert("1")
black = PIL.Image.open("./test_black.png").convert("1")


def test(red, black):
    spec = {
        'red': (255, 0, 0),
        'black': (0, 0, 0),
    }
    merged = PIL.Image.new("RGB", (280, 480), color=(255, 255, 255))
    for color, image in {'red': red, 'black': black}.items():
        pixels = image.load()

        for x in range(image.size[0]):
            for y in range(image.size[1]):
                if merged.getpixel((x, y)) != (255, 255, 255):
                    continue
                if pixels[x, y] == 0:
                    merged.putpixel((x, y), spec[color])
