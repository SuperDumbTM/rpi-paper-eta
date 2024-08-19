# pylint: disable=redefined-outer-name

from datetime import datetime
import math
from typing import Literal

from PIL import ImageDraw, ImageFont

T_POS = Literal["n", "ne", "e", "se", "s", "sw", "w", "nw", "c"]


def dt2min(ts: datetime, eta: datetime) -> str:
    """Calculate the difference in minutes between two datetime objects.

    Args:
        ts (datetime): The starting datetime object.
        eta (datetime): The ending datetime object.

    Returns:
        str: A string representation of the difference in minutes between the two datetime objects.
    """
    return str(round((eta - ts).total_seconds() / 60))


def get_variant(font: ImageFont.FreeTypeFont,
                size: int = None,
                name: str = None) -> ImageFont.FreeTypeFont:
    """Generate a variant of the input font with optional size and variation.

    Args:
        font (ImageFont.FreeTypeFont): The original font object.
        size (int, optional): The size of the new font variant. Defaults to None.
        name (str, optional): The variation name for the new font variant. Defaults to None.

    Returns:
        ImageFont.FreeTypeFont: A new font variant based on the input font with optional size and variation.

    Raises:
        ValueError: If the provided variation name is not valid.
    """
    new = font.font_variant(size=(size or font.size))
    if name:
        new.set_variation_by_name(name)
    return new


def text_clip(t: str, length: int, font: ImageFont.FreeTypeFont) -> str:
    """Clips the input text to fit within the specified length based on the provided font.

    Args:
        t (str): The input text to be clipped.
        length (int): The maximum length to clip the text to.
        font (ImageFont.FreeTypeFont): The font used to measure the text length.

    Returns:
        str: The clipped text that fits within the specified length.
    """
    if not t:
        return ""
    if font.getlength(t) <= length:
        return t
    return text_clip(t[:-1], length, font)


def text_ellipsis(t: str, length: int, font: ImageFont.FreeTypeFont) -> str:
    """Generate a text string with ellipsis if the length exceeds the specified limit.

    Args:
        t (str): The input text string.
        length (int): The maximum length allowed for the text.
        font (ImageFont.FreeTypeFont): The font used to measure text length.

    Returns:
        str: The modified text string with ellipsis if the length exceeds the limit.

    Raises:
        ValueError: If the specified length is too small.
    """
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
    """Calculate the offset based on the position relative to the bounding box.

    Args:
        wh_box (tuple[float, float]): The width and height of the bounding box.
        wh (tuple[float, float]): The width and height of the object.
        position (T_POS, optional): The align position relative to the bounding box. Defaults to "c".

    Returns:
        tuple[float, float]: The offset coordinates based on the specified position.

    Raises:
        ValueError: If an invalid position is provided.
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
    """Wrap text to fit within a specified width and height.

    Args:
        draw (ImageDraw.ImageDraw): The ImageDraw object to draw text.
        text (str): The input text to be wrapped.
        wh (tuple[float, float]): The width and height constraints for the wrapped text.
        font (ImageFont.FreeTypeFont): The font used for drawing the text.

    Returns:
        str: The wrapped text that fits within the specified width and height.
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
        """Draw a rectangle with specified width and height.

        Args:
            xy (tuple[float, float]): The coordinates of the top-left corner of the rectangle.
            wh (tuple[float, float]): The width and height of the rectangle.
            fill: The fill color of the rectangle.
            outline: The outline color of the rectangle.
            outline_width (int): The width of the outline.
        """
        self.rectangle((xy, (xy[0] + wh[0], xy[1] + wh[1])),
                       fill,
                       outline,
                       outline_width)

    def cross(self, xy: tuple[float, float], wh: tuple[float, float], fill=None):
        """Draw a cross shape.

        Args:
            xy (tuple[float, float]): The coordinates of the top-left corner of the cross.
            wh (tuple[float, float]): The width and height of the cross.
            fill: The color of the cross.
        """
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
        """Draw responsive text.

        Args:
            text (str): The text to be drawn.
            xy (tuple[float, float]): The coordinates of the top-left corner of the text.
            wh (tuple[float, float]): The width and height of the text bounding box.
            font (ImageFont.FreeTypeFont): The font to be used for the text.
            overflow (Literal["none", "clip", "ellipsis", "wrap-ellipsis"]): The overflow behavior for the text.
            position (T_POS): The position of the text within the bounding box.
            fill: The color of the text.
            debug (bool): Whether to draw debug rectangles.
        """
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
