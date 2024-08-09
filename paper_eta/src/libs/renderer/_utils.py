# pylint: disable=redefined-outer-name

import math
from typing import Literal

from PIL import ImageDraw, ImageFont

T_POS = Literal["n", "ne", "e", "se", "s", "sw", "w", "nw", "c"]


def get_variant(font: ImageFont.FreeTypeFont,
                size: int = None,
                name: str = None) -> ImageFont.FreeTypeFont:
    new = font.font_variant(size=(size or font.size))
    if name:
        try:
            new.set_variation_by_name(name)
        except ValueError:
            print("Available variation name: " +
                  ", ".join(map(str, new.get_variation_names())))
            raise
    return new


def text_clip(t: str, length: int, font: ImageFont.FreeTypeFont) -> str:
    if not t:
        return ""
    if font.getlength(t) <= length:
        return t
    return text_clip(t[:-1], length, font)


def text_ellipsis(t: str, length: int, font: ImageFont.FreeTypeFont) -> str:
    if font.getlength("...") > length:
        raise ValueError("length too small")
    if not t:
        return ""
    if font.getlength(t) <= length:
        return t
    return text_ellipsis(f"{t.rstrip('...')[:-1]}...", length, font)


def offset(
    wh_box: tuple[float, float],
    wh: tuple[float, float],
    position: T_POS = "c"
) -> tuple[float, float]:
    """calulate the x, y offset with given alignment

    Args:
        text (str): input text
        width (float): maximum display length in pixel
        height (float): maximum display height in pixel
        font (ImageFont.FreeTypeFont): font used to display the text
        position (str, optional): desire positioning. Defaults to "c".

    Raises:
        ValueError: the given `position` is not a valid

    Returns:
        tuple[float, float]: start position of x, y (in pixel)
            relative to the given area
    """
    over_width = max(0, wh[0] - wh_box[0])
    over_height = max(0, wh[1] - wh_box[1])

    if (over_width <= 0 and over_height <= 0):
        return (0, 0)

    match position:
        case "nw" | "NW":
            return (0, 0)
        case "n" | "N":
            return (over_width/2, 0)
        case "ne" | "NE":
            return (over_width, 0)
        case "w" | "W":
            return (0, over_height/2)
        case "c" | "C":
            return (over_width/2, over_height/2)
        case "e" | "E":
            return (over_width, over_height/2)
        case "sw" | "SW":
            return (0, over_height)
        case "s" | "S":
            return (over_width/2, over_height)
        case "se" | "SE":
            return (over_width, over_height)
        case _:
            raise ValueError('Invalid position.')


def wrap(draw: ImageDraw.ImageDraw,
         text: str,
         wh: tuple[float, float],
         font: ImageFont.FreeTypeFont) -> str:
    """Wrap a text to multiple lines with given area,  discard if the area is not
    enough to display all the text
    ```
    """
    if len(text) <= 0:
        return text

    len_text = int(font.getlength(text))
    len_char = len_text / len(text)

    if (wh[0] <= len_text):
        char_pre_ln = int(wh[0] // len_char)

        for cnt_nl in range(math.ceil(len(text) / char_pre_ln) - 1):
            # starting position of current "line" to the modified string
            offset = char_pre_ln * (cnt_nl + 1)

            # insert newline
            text = text[:offset + cnt_nl] + "\n" + text[offset + cnt_nl:]

            # discard remainings if overheight
            boxsize = draw.multiline_textbbox((0, 0), text, font=font)
            if (boxsize[3] - boxsize[1] >= wh[1]):
                # discard the last line of the modified string
                # and rejoin them to mulit-line text
                text = "\n".join(text.split('\n')[:-1])
                return text_ellipsis(
                    text, font.getlength(text) - font.getlength("..."), font)
    return text


class EtaImageDraw(ImageDraw.ImageDraw):

    def rectangle_wh(self,
                     xy: tuple[float, float],
                     wh: tuple[float, float],
                     fill=None,
                     outline=None,
                     outline_width=1) -> None:
        self.rectangle((xy, (xy[0] + wh[0], xy[1] + wh[1])),
                       fill,
                       outline,
                       outline_width)

    def cross(self, xy: tuple[float, float], wh: tuple[float, float], fill=None):
        self.line((xy[0], xy[1] + wh[1]/2, xy[0] + wh[0], xy[1] + wh[1]/2),
                  fill=fill)
        self.line((xy[0] + wh[0]/2, xy[1], xy[0] + wh[0]/2, xy[1] + wh[1]),
                  fill=fill)

    def text_responsive(
        self,
        text: str,
        xy: tuple[float, float],
        wh: tuple[float, float],
        font: ImageFont.FreeTypeFont,
        overflow: Literal["none", "clip", "ellipsis",
                          "wrap-ellipsis"] = "ellipsis",
        position: T_POS = "w",
        fill=None,
        debug: bool = False
    ) -> None:
        if overflow == "clip":
            text = text_clip(text, wh[0], font)
        if overflow == "ellipsis":
            text = text_ellipsis(text, wh[0], font)
        if overflow == "wrap-ellipsis":
            text = wrap(self, text, wh, font)

        mltb = self.multiline_textbbox((0, 0), text, font)
        offset_x, offset_y = offset(
            (mltb[2] - mltb[0], mltb[3] - mltb[1]), wh, position)

        # reset the pixel shift due to font size variation
        offset_x += xy[0] - mltb[0]
        offset_y += xy[1] - mltb[1]
        self.text((offset_x, offset_y), text, fill, font)

        if debug:
            self.rectangle((mltb[0] + offset_x, mltb[1] + offset_y,
                            mltb[2] + offset_x, mltb[3] + offset_y))
            self.rectangle_wh(xy, wh)
            self.cross(xy, wh)
