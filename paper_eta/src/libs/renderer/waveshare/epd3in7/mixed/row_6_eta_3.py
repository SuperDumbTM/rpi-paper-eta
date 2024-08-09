from typing import Iterable

from PIL import Image, ImageDraw, ImageFont

from .... import _utils
from ....generator import FONT_BASE_PATH, Eta, ImageRenderer, RendererSpec

WIDTH = 480
HEIGHT = 280
ROW_HEIGHT = 80

BLACK = 0x00
WHITE = 0xFF

FONT_NOTOSANS = ImageFont.FreeTypeFont(str(FONT_BASE_PATH.joinpath(
    "NotoSansTC-VariableFont_wght.ttf")))
FONT_SIRIN = ImageFont.FreeTypeFont(str(FONT_BASE_PATH.joinpath(
    "SirinStencil-Regular.ttf")))

FONT_NAME = _utils.get_variant(FONT_NOTOSANS, 28, "Bold")
FONT_STOP = _utils.get_variant(FONT_NOTOSANS, 16, "Bold")
FONT_ERR = _utils.get_variant(FONT_NOTOSANS, 16, "Medium")
FONT_RMKE = _utils.get_variant(FONT_NOTOSANS, 16, "Regular")
FONT_MIN = _utils.get_variant(FONT_SIRIN, 32)


class Renderer(ImageRenderer):

    @classmethod
    def spec(cls):
        return RendererSpec(
            width=WIDTH,
            height=HEIGHT,
            color={
                "black": (0, 0, 0)
            },
            description={
                "en": "Display at most 6 routes and up to 3 ETAs",
                "zh_Hant_HK": "顯示最多六條路線及最近三班班次的到站時間"
            },
        )

    def draw(self, etas: Iterable[Eta], degree: float = 0):
        canvas = Image.new('1', (HEIGHT, WIDTH), 255)
        draw = ImageDraw.Draw(canvas)

        for row in range(1, 6):
            draw.line(((0, row * ROW_HEIGHT), (WIDTH, row * ROW_HEIGHT)))

        for row, route in enumerate(etas):
            draw.bitmap((0, row*ROW_HEIGHT),
                        Image.open(route.logo).convert("1").resize((35, 35)))
            _utils.rectangle_wh(draw, (0, row*ROW_HEIGHT), (35, 35))

            _utils.flex_text(
                draw, route.no, (38, row*ROW_HEIGHT), (112, 35), FONT_NAME, debug=1)
            _utils.flex_text(
                draw, route.destination, (0, 35 + row*ROW_HEIGHT), (150, 22.5), FONT_STOP)
            _utils.flex_text(
                draw, f"@{route.stop_name}", (0, 57.5 + row*ROW_HEIGHT), (150, 22.5), FONT_STOP)

            if isinstance(route.etas, Eta.Error):
                errmsg = _utils.wrap(
                    draw, route.etas.message, (130, 80), FONT_ERR)
                _utils.flex_text(
                    draw, errmsg, (150, row*ROW_HEIGHT), (130, 80), FONT_ERR, position="c")
                continue

            for ieta, eta in enumerate(route.etas):
                xy = (150, row*ROW_HEIGHT + ROW_HEIGHT/3 * ieta)

                if eta.is_arriving:
                    _utils.flex_text(
                        draw, "即將抵達／已離開", xy, (130, 80/3), FONT_RMKE, position="c")
                    continue
                if eta.eta is None:
                    _utils.flex_text(
                        draw, eta.remark, xy, (130, 80/3), FONT_RMKE)
                    continue
                _utils.flex_text(
                    draw,
                    str(int((eta.eta - route.timestamp).total_seconds() / 60)),
                    xy,
                    (40, 80/3),
                    FONT_MIN)
                _utils.flex_text(
                    draw, "分", (xy[0] + 40, xy[1]), (20, 80/3), FONT_RMKE, overflow="none", position="s")
                _utils.flex_text(
                    draw, eta.eta.strftime("%H:%M"), (xy[0] + 60, xy[1]), (70, 80/3), FONT_MIN, overflow="none")

        return {"black": canvas}

    def draw_error(self, message: str, degree: float = 0):
        pass
