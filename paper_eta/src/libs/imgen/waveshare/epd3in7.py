from flask_babel import force_locale, gettext
from PIL import Image, ImageDraw

from .. import _utils
from ..generator import EtaImageGenerator
from ...hketa import Eta


class Epd3in7(EtaImageGenerator):

    width = 280
    height = 480

    _bk = 0x00
    _wh = 0xff

    @property
    def colors(self) -> tuple[str]:
        return ("black",)

    def draw(self, etas, degree=0):
        image = Image.new('1', (self.width, self.height), 255)
        b = ImageDraw.Draw(image)

        row_cnt = self._config['layout']['row']
        row_height = self._config['coords']['row']['height']
        coords = self._config['coords']

        # row frame
        for row in range(1, row_cnt):
            b.line((self._config['coords']['row']['offset'][0],
                    row_height * row, self.height, row_height * row))

        for row, route in enumerate(etas):
            if row_cnt <= row:
                break

            # titles
            if route.logo:
                b.bitmap((coords['route']['logo']['offset'][0],
                          coords['route']['logo']['offset'][1] + (row_height*row)),
                         Image.open(route.logo).convert("1").resize((30, 30)),
                         self._bk)
            b.text((coords['route']['name']['offset'][0],
                    coords['route']['name']['offset'][1] + (row_height*row)),
                   _utils.discard(route.no,
                                  coords['route']['name']['width'],
                                  self.fonts['route']),
                   fill=self._bk, font=self.fonts['route'])
            b.text((coords['route']['dest']['offset'][0],
                    coords['route']['dest']['offset'][1] + (row_height*row)),
                   _utils.discard(route.destination,
                                  coords['route']
                                  ['dest']['width'], self.fonts['stop']),
                   fill=self._bk, font=self.fonts['stop'])
            b.text((coords['route']['stop']['offset'][0],
                    coords['route']['stop']['offset'][1] + (row_height*row)),
                   _utils.discard(f"@{route.stop_name}",
                                  coords['route']['stop']['width'],
                                  self.fonts['stop']),
                   fill=self._bk, font=self.fonts['stop'])

            # error
            if isinstance(route.etas, Eta.Error):
                errmsg = _utils.wrap(route.etas.message,
                                     coords['error']['position']['width'],
                                     coords['error']['position']['height'],
                                     self.fonts['err_txt'])

                offset_x, offset_y = _utils.position(errmsg,
                                                     coords['error']['position']['width'],
                                                     coords['error']['position']['height'],
                                                     self.fonts['err_txt'],
                                                     align='c')
                b.text((coords['error']['position']['offset'][0] + offset_x,
                        coords['error']['position']['offset'][1] + row_height*row + offset_y),
                       text=errmsg, fill=self._bk, font=self.fonts['err_txt'])
                continue

            # eta
            for idx, eta in enumerate(route.etas):
                if (idx >= self._config['layout']['eta']):
                    break
                idx_offset = row_height*row + \
                    coords['eta']['position']['height']*idx

                if eta.is_arriving and eta.remark not in (None, ""):
                    with force_locale(route.locale.iso()):
                        text = gettext(
                            "arr_dep") if eta.is_arriving else eta.remark

                    offset_x, offset_y = _utils.position(
                        text,
                        coords['eta']['position']['width'],
                        coords['eta']['position']['height'],
                        self.fonts['err_txt'],
                        align='c')

                    # display the remark
                    b.text((coords['eta']['position']['offset'][0] + offset_x,
                            coords['eta']['position']['offset'][1] + offset_y + idx_offset),
                           _utils.discard(
                        text, coords['eta']['position']['width'], self.fonts['rmk_txt']),
                        fill=self._bk,
                        font=self.fonts['rmk_txt'])
                else:
                    # minute
                    b.text((coords['eta']['min']['offset'][0], coords['eta']['min']['offset'][1] + idx_offset),
                           text=str(int(
                               (eta.eta - route.timestamp).total_seconds() / 60)),
                           fill=self._bk,
                           font=self.fonts['minute'])
                    b.text((coords['eta']['min_txt']['offset'][0],
                            coords['eta']['min_txt']['offset'][1] + idx_offset),
                           text=self._config['texts']['minute'][route.locale],
                           fill=self._bk, font=self.fonts['min_txt'])
                    # time
                    b.text((coords['eta']['time']['offset'][0],
                            coords['eta']['time']['offset'][1] + idx_offset),
                           text=eta.eta.strftime("%H:%M"), fill=self._bk, font=self.fonts['time'])
        return {'black': image.rotate(degree)}

    def draw_error(self, message: str, degree: float = 0) -> dict[str, Image.Image]:
        image = Image.new('1', (self.width, self.height), 255)
        b = ImageDraw.Draw(image)

        offset_x, offset_y = _utils.position(
            message,
            self.width,
            self.height,
            self.fonts['err_txt'],
            align='c')

        b.text((0 + offset_x, 0 + offset_y),
               _utils.discard(message, self.width, self.fonts['err_txt']),
               fill=self._bk,
               font=self.fonts['err_txt'])

        return {'black': image.rotate(degree)}
