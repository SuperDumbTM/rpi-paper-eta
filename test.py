from pathlib import Path
import PIL.Image
import timeit

image = PIL.Image.open(Path(".").joinpath(
    "paper_eta", "storage", "screen_dumps", "hti", "black.png")).convert("L")


def fn(image):
    pixel = image.load()
    for x in range(image.size[0]):
        for y in range(image.size[1]):
            if pixel[x, y] != 255:
                image.putpixel((x, y), 0)


def fn2(image):
    pixel = image.load()
    image.putdata([0 if pixel[x, y] != 255 else 255 for y in range(
        image.size[1]) for x in range(image.size[0])])


print(sum(timeit.repeat("fn(image)",
      globals=globals(), number=1, repeat=50))/50)
print(sum(timeit.repeat("fn2(image)",
      globals=globals(), number=1, repeat=50))/50)
