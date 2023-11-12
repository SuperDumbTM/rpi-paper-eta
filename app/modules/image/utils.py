import logging
import math
import threading
from typing import Callable

from PIL import ImageFont

    
def discard(text: str, length: int, font: ImageFont.FreeTypeFont) -> str:
    """discard a string with given maximum length and font

    Args:
        text (str): input text
        length (int): maximum display length in pixel
        font (ImageFont.FreeTypeFont): font used to display the text
        
    Usage:
    ```
        discard("abcdefg", 5, afont) # returns: "ab..."
    ```
    """
    if text is None:
        return ""
    elif font.getlength(text) <= length:
        return text

    for cnt_char in range(len(text), 0, -1):
        if font.getlength(f"{text[:cnt_char]}...") < length:
            return f"{text[:cnt_char]}..."
        
    return text

def wrap(text: str, length: float, height: float, font: ImageFont.FreeTypeFont) -> str:
    """wrap a text to multiple lines with given area,  discard if the area is not
    enough to display all the text

    Args:
        text (str): input text
        length (float): maximum display length in pixel
        height (float): maximum display height in pixel
        font (ImageFont.FreeTypeFont): font used to display the text
        
    Usage:
    ```
        discard("abcdefghijk", 5, 5, afont)
        # returns: "abc\\ndef\\ng..."
    ```
    """
    len_text = int(font.getlength(text))
    len_char = len_text / len(text)
    
    if (length <= len_text):
        char_pre_ln = int(length // len_char)
        
        for cnt_nl in range(math.ceil(len(text) / char_pre_ln) - 1):
            # starting position of current "line" to the modified string
            offset = char_pre_ln * (cnt_nl + 1)
            # insert newline
            text = text[:offset + cnt_nl] + "\n" + text[offset + cnt_nl:]
            # discard remainings if overheight
            if (font.getsize_multiline(text)[1] >= height):
                # discard the last line of the modified string
                # and rejoin them to mulit-line text
                text = "\n".join(text.split('\n')[:-1])
                return discard(
                    text, font.getlength(text) - font.getlength("..."), font)
    return text

def position(
        text: str,
        length: float,
        height: float,
        font: ImageFont.FreeTypeFont,
        offset_x: int = 0,
        offset_y: int = 0,
        align: str = "c"
    ) -> tuple[int, int]:
    """calulate the x, y offset with given alignment

    Args:
        text (str): input text
        length (float): maximum display length in pixel
        height (float): maximum display height in pixel
        font (ImageFont.FreeTypeFont): font used to display the text
        offset_x (int, optional): x offset. Defaults to 0.
        offset_y (int, optional): y offset. Defaults to 0.
        align (str, optional): desire alignment. Defaults to "c".

    Raises:
        ValueError: when the given `align` is not recognized

    Returns:
        tuple[int, int]: start position of x, y (in pixel)
            relative to the given area
    """
    total_width, total_height = font.getsize_multiline(text)
    
    remain_width = max(0, length - total_width) # font.getsize('\n')[0]
    remain_height = max(0, height - total_height)
    if (remain_width <= 0 and remain_height <= 0):
        return (0, 0)

    center_x = int(remain_width / 2)
    center_y = int(remain_height / 2)
    
    match align:
        case "nw" | "NW":
            positions = (0, 0)
        case "n" | "N":
            return (center_x, 0)
        case "ne" | "NE":
            positions = (remain_width, 0)
        case "w" | "W":
            positions = (0, center_y)
        case "c" | "C" | "we" | "WE":
            positions = (center_x, center_y)
        case "e" | "E":
            positions = (remain_width, center_y)
        case "sw" | "SW":
            positions = (0, remain_height)
        case "s" | "S":
            positions = (center_x, remain_height)
        case "se" | "SE":
            positions = (remain_width, remain_height)
        case _:
            raise ValueError('unrecognized alignment')

    return (positions[0] + offset_x, positions[1] + offset_y)

def blockguard(func: Callable, timeout: int,
               daemon: bool = True, _raise: bool = False):
    """a decorator that helps to prevent infinite blocking from executing `func`
    
    NOTE: implemented using `threading` module, be aware of all possible side 
        effects of threaded execution of your function

    Args:
        func (Callable): function to be executed
        timeout (int): time limit for the execution
        daemon (bool): continuity of execution after time-out
        _raise (bool): raise `RuntimeError` when time-out
        
    Raise:
        RuntimeError: funtion execution time-out
        
    """
    def wrap(*args, **kwargs):
        t = threading.Thread(target=func, args=args, kwargs=kwargs)
        t.daemon = daemon # set to True to kill in-progress async tasks
        t.start()
        t.join(timeout)
        if t.is_alive():
            logging.error(
                f"execution of <{func.__name__}> is terminated due to timeout "
                f"({timeout} seconds)")
            if _raise:
                raise RuntimeError(f"execution time-out {timeout}")
        return None
    return wrap
    
    