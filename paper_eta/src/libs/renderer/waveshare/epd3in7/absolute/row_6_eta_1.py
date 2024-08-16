from typing import Iterable

from PIL import ImageFont

from .... import _utils
from ....generator import FONT_BASE_PATH, Eta, RendererSpec
from .._base import FONT_NOTOSANS, Epd3in8RenderBase

FONT_NOTOSANS = ImageFont.FreeTypeFont(
    str(FONT_BASE_PATH.joinpath("NotoSansTC-Variable.ttf")))
FONT_SIRIN = ImageFont.FreeTypeFont(
    str(FONT_BASE_PATH.joinpath("SirinStencil-Regular.ttf")))

FONT_MSG = _utils.get_variant(FONT_NOTOSANS, 16, "Medium")
FONT_ETA = _utils.get_variant(FONT_SIRIN, 60)
FONT_MIN = _utils.get_variant(FONT_NOTOSANS, 22, "Medium")


class Renderer(Epd3in8RenderBase):

    @classmethod
    def spec(cls):
        return RendererSpec(
            width=cls.height,
            height=cls.width,
            color={
                "black": (0, 0, 0)
            },
            description={
                "en": "Display at most 6 routes and up to 1 ETAs",
                "zh_Hant_HK": "顯示最多六條路線及最多一班班次的到站時間"
            },
            graphics={
                "en": tuple(),
                "zh_Hant_HK": tuple()
            }
        )

    def draw(self, etas: Iterable[Eta], degree: float = 0):
        canvas, draw, row_h = self.six_row(etas)

        for row, route in enumerate(etas):
            if isinstance(route.etas, Eta.Error):
                draw.text_responsive(
                    route.etas.message, (150, row*row_h), (130, row_h), FONT_MSG, "wrap-ellipsis", "c")
                continue

            for eta in route.etas[:1]:
                xy = (150, row_h*row)

                if eta.is_arriving:
                    draw.text_responsive(
                        self.text_arr(route.locale), xy, (130, row_h), FONT_MSG, position="c")
                    continue
                if eta.eta is None:
                    draw.text_responsive(
                        eta.remark, xy, (130, row_h), FONT_MSG)
                    continue

                draw.text_responsive(eta.eta.strftime("%H:%M"),
                                     xy,
                                     (130, 55),
                                     FONT_ETA,
                                     "none",
                                     "c")

                draw.line(((150, 55 + row*row_h),
                           (280 + row*row_h, 55 + row*row_h)))
                draw.text_responsive((eta.remark
                                      or eta.extras.get("route_variant", "")),
                                     (xy[0], xy[1] + 55),
                                     (130, 25),
                                     FONT_MSG,
                                     "none",
                                     "c")

        return {"0-0-0": canvas.rotate(degree)}
