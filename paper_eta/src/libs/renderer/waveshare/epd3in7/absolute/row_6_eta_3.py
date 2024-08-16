from typing import Iterable

from PIL import ImageFont

from .... import _utils
from ....generator import FONT_BASE_PATH, Eta, RendererSpec
from .._base import FONT_NOTOSANS, Epd3in8RenderBase

FONT_NOTOSANS = ImageFont.FreeTypeFont(
    str(FONT_BASE_PATH.joinpath("NotoSansTC-Variable.ttf")))
FONT_SIRIN = ImageFont.FreeTypeFont(
    str(FONT_BASE_PATH.joinpath("SirinStencil-Regular.ttf")))

FONT_ERR = _utils.get_variant(FONT_NOTOSANS, 16, "Medium")
FONT_ERMK = _utils.get_variant(FONT_NOTOSANS, 14, "Regular")
FONT_ETA = _utils.get_variant(FONT_SIRIN, 28)


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
                "en": "Display at most 6 routes and up to 3 ETAs",
                "zh_Hant_HK": "顯示最多六條路線及最多三班班次的到站時間"
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
                    route.etas.message, (150, row*row_h), (130, row_h), FONT_ERR, "wrap-ellipsis", "c")
                continue

            for ieta, eta in enumerate(route.etas[:3]):
                xy = (150, row*row_h + row_h/3 * ieta)

                if eta.is_arriving:
                    draw.text_responsive(
                        self.text_arr(route.locale), xy, (130, row_h/3), FONT_ERMK, position="c")
                    continue
                if eta.eta is None:
                    draw.text_responsive(
                        eta.remark, xy, (130, row_h/3), FONT_ERMK)
                    continue

                draw.text_responsive(eta.eta.strftime("%H:%M"),
                                     xy,
                                     (70, row_h/3),
                                     FONT_ETA,
                                     overflow="none")

                draw.text_responsive((eta.remark
                                      or eta.extras.get("route_variant", "")),
                                     (xy[0] + 70, xy[1]),
                                     (60, row_h/3 - 4),
                                     FONT_ERMK,
                                     overflow="none",
                                     position="sw")

        return {"0-0-0": canvas.rotate(degree)}
