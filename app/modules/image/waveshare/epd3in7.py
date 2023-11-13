from pathlib import Path
import sys

from PIL import Image, ImageDraw


try:
    sys.path.append(str(Path(__file__).parent.parent))
    from eta_image import EtaImageGenerator
    import utils
    import models
except ImportError:
    from ..eta_image import EtaImageGenerator
    from .. import utils, models


class Epd3in7EtaImage(EtaImageGenerator):

    _bk = 0x00
    _wh = 0xff

    @property
    def colors(self) -> tuple[str]:
        return ("black",)

    @property
    def width(self):
        return 280

    @property
    def height(self):
        return 480

    @staticmethod
    def name() -> str:
        return "full"

    @classmethod
    def description(cls) -> str:
        return cls.layout_data()[cls.name()]['description']

    def draw(self, etas: list[models.Etas | models.ErrorEta], degree: float = 0) -> dict[str, Image.Image]:
        image = Image.new('1', (self.width, self.height), 255)
        b = ImageDraw.Draw(image)

        row_cnt = self._config['layout']['row']
        row_height = self._config['coords']['row']['height']
        coords = self._config['coords']

        # row frame
        for row in range(100):
            b.line((self._config['coords']['row']['offset'][0],
                    row_height * row, self.height, row_height * row))

        for row, eta in enumerate(etas):
            if row_cnt <= row:
                break

            # titles
            # b.bitmap((coords['route']['logo']['offset'][0],
            #           coords['route']['logo']['offset'][1] + (row_height*row)),
            #          Image.open(rtdet.logo()).convert("1").resize((30, 30)),
            #          self._black)
            b.text((coords['route']['name']['offset'][0],
                    coords['route']['name']['offset'][1] + (row_height*row)),
                   utils.discard(eta.route,
                                 coords['route']['name']['width'],
                                 self.fonts['route']),
                   fill=self._bk, font=self.fonts['route'])
            b.text((coords['route']['dest']['offset'][0],
                    coords['route']['dest']['offset'][1] + (row_height*row)),
                   utils.discard(eta.destination,
                                 coords['route']
                                 ['dest']['width'], self.fonts['stop']),
                   fill=self._bk, font=self.fonts['stop'])
            b.text((coords['route']['stop']['offset'][0],
                    coords['route']['stop']['offset'][1] + (row_height*row)),
                   utils.discard(f"@{eta.stop_name}",
                                 coords['route']['stop']['width'],
                                 self.fonts['stop']),
                   fill=self._bk, font=self.fonts['stop'])

            # time
            for idx, time in enumerate(eta.etas):
                if (idx >= self._config['layout']['eta']):
                    break
                idx_offset = row_height*row + \
                    coords['eta']['position']['height']*idx

                # error
                if isinstance(time, models.ErrorEta):
                    continue
                # eta
                if time.is_arriving:
                    offset_x, offset_y = utils.position(
                        time.remark,
                        coords['eta']['position']['width'],
                        coords['eta']['position']['height'],
                        self.fonts['err_txt'],
                        align='c')

                    b.text((coords['eta']['position']['offset'][0] + offset_x,
                            coords['eta']['position']['offset'][1] + offset_y + idx_offset),
                           utils.discard(
                        time.remark, coords['eta']['position']['width'], self.fonts['rmk_txt']),
                        fill=self._bk,
                        font=self.fonts['rmk_txt'])
                else:
                    b.text((coords['eta']['min']['offset'][0],
                            coords['eta']['min']['offset'][1] + idx_offset),
                           text=str(time.eta_minute), fill=self._bk, font=self.fonts['minute'])
                    b.text((coords['eta']['min_txt']['offset'][0],
                            coords['eta']['min_txt']['offset'][1] + idx_offset),
                           text="分",
                           fill=self._bk, font=self.fonts['min_txt'])
                    b.text((coords['eta']['time']['offset'][0],
                            coords['eta']['time']['offset'][1] + idx_offset),
                           text=time.eta.strftime("%H:%M"), fill=self._bk, font=self.fonts['time'])
        return {'black': image.rotate(degree)}

    # def __init__(self, layout_name: str, etaconf: list[RouteEntry], eta_factory: EtaFactory):
    #     super().__init__(layout_name, etaconf, eta_factory)
    #     self.lyo = self.layout_data()[self.name()]['layouts'][layout_name]
    #     self._fn = FontFactory.create(self.lyo['font']['style'])

    # def draw(self, degree: int = 0):
    #     image = Image.new('1', (self.width, self.height), 255)
    #     drawer = ImageDraw.Draw(image)

    #     layout: dict[int] = self.lyo['layouts']
    #     rh = layout['row']['height']  # row height

    #     # fonts
    #     f_rt = self._fn.get_route(self.lyo['font']['size']['route'])
    #     f_stop = self._fn.get_text(self.lyo['font']['size']['stop'])
    #     f_min = self._fn.get_minute(self.lyo['font']['size']['minute'])
    #     f_mintxt = self._fn.get_minute(self.lyo['font']['size']['mintxt'])
    #     f_time = self._fn.get_time(self.lyo['font']['size']['time'])
    #     f_rmk = self._fn.get_remark(self.lyo['font']['size']['rmktxt'])
    #     f_err = self._fn.get_remark(self.lyo['font']['size']['errtxt'])

    #     # row frame
    #     for row in range(self.lyo['counts']['row']):
    #         drawer.line((layout['row']['offset'][0], rh * row,
    #                     self.height, rh * row))

    #     for row, entry in enumerate(self.etaconf):
    #         if self.lyo['counts']['row'] <= row:
    #             break

    #         try:
    #             eta = self.etafactory.create_eta(entry)
    #             rtdet = eta.details
    #             rtdet.route_exists(True)  # check routes existence

        # # titles
        # drawer.bitmap((layout['route']['logo']['offset'][0],
        #                layout['route']['logo']['offset'][1] + (rh*row)),
        #               Image.open(rtdet.logo()).convert(
        #                   "1").resize((30, 30)),
        #               self._black)
        # drawer.text((layout['route']['name']['offset'][0],
        #              layout['route']['name']['offset'][1] + (rh*row)),
        #             utils.discard(rtdet.route_name(),
        #                        layout['route']['name']['width'], f_rt),
        #             fill=self._black, font=f_rt)
        # drawer.text((layout['route']['dest']['offset'][0],
        #              layout['route']['dest']['offset'][1] + (rh*row)),
        #             utils.discard(rtdet.destination(),
        #                        layout['route']['dest']['width'], f_stop),
        #             fill=self._black, font=f_stop)
        # drawer.text((layout['route']['stop']['offset'][0],
        #              layout['route']['stop']['offset'][1] + (rh*row)),
        #             utils.discard(
        #                 f"@{rtdet.stop_name()}", layout['route']['stop']['width'], f_stop),
        #             fill=self._black, font=f_stop)

        # layout outline
        # drawer.line(((170, 0, 170, self.height)), self._black, width=1)
        # drawer.line(((35, 0, 35, self.height)), self._black, width=1)
        # drawer.line(((0, row*40, self.width, row*40)), self._black, width=1)

        # # time
        # for idx, time in enumerate(eta.etas()):
        #     if (idx >= self.lyo['counts']['eta']):
        #         break
        #     idx_offset = rh*row + layout['eta']['row']['height']*idx
        #     if time['minute'] is None:
        #         offset_x, offset_y = utils.position(
        #             time['remark'], layout['eta']['row']['width'],
        #             layout['eta']['row']['height'], f_err, align='c')

        #         drawer.text((layout['eta']['row']['offset'][0] + offset_x,
        #                      layout['eta']['row']['offset'][1] + offset_y + idx_offset),
        #                     utils.discard(
        #                         time['remark'], layout['eta']['row']['width'], f_rmk),
        #                     fill=self._black, font=f_rmk)
        #     else:
        #         drawer.text((layout['eta']['min']['offset'][0],
        #                      layout['eta']['min']['offset'][1] + idx_offset),
        #                     text=str(time['minute']), fill=self._black, font=f_min)
        #         drawer.text((layout['eta']['min_txt']['offset'][0],
        #                      layout['eta']['min_txt']['offset'][1] + idx_offset),
        #                     text=self.lyo['text']['minute'][entry.lang],
        #                     fill=self._black, font=f_mintxt)
        #         drawer.text((layout['eta']['time']['offset'][0],
        #                      layout['eta']['time']['offset'][1] + idx_offset),
        #                     text=time['time'], fill=self._black, font=f_time)
    #         except HketaException as e:
    #             errmsg = utils.wrap(
    #                 e.get_msg(entry.lang), layout['eta']['block']['width'],
    #                 layout['eta']['block']['height'], f_err)

    #             offset_x, offset_y = utils.position(
    #                 errmsg, layout['eta']['block']['width'],
    #                 layout['eta']['block']['height'], f_err, align='c')

    #             drawer.text(
    #                 (layout['eta']['block']['offset'][0] + offset_x,
    #                  layout['eta']['block']['offset'][1] + rh*row + offset_y),
    #                 text=errmsg, fill=self._black, font=f_err)
    #         except Exception as e:
    #             logging.error(f"error occurs: {e.__class__.__name__}, {e}")
    #             logging.debug(e, exc_info=True)

    #     return {'black': image.rotate(degree)}


class Epd3in7TimeOnlyEtaImage(Epd3in7EtaImage):

    @property
    def colors(self) -> tuple[str]:
        return ("black",)

    @staticmethod
    def name() -> str:
        return "timeonly"

    # def __init__(self, layout_name: str, etaconf: list[RouteEntry], eta_factory: EtaFactory):
    #     super().__init__(layout_name, etaconf, eta_factory)

    # def draw(self, degree: int = 0):
    #     logging.info("generating ETA info image(s)")

    #     image = Image.new('1', (self.width, self.height), 255)
    #     drawer = ImageDraw.Draw(image)

    #     layout: dict[int] = self.lyo['layouts']
    #     rh = layout['row']['height']

    #     # fonts
    #     f_rt = self._fn.get_route(self.lyo['font']['size']['route'])
    #     f_stop = self._fn.get_text(self.lyo['font']['size']['stop'])
    #     f_time = self._fn.get_time(self.lyo['font']['size']['time'])
    #     f_rmk = self._fn.get_remark(self.lyo['font']['size']['rmktxt'])
    #     f_err = self._fn.get_remark(self.lyo['font']['size']['errtxt'])

    #     # row frame
    #     for row in range(self.lyo['counts']['row']):
    #         drawer.line((layout['row']['offset'][0], rh * row,
    #                     self.height, rh * row))

    #     for row, entry in enumerate(self.etaconf):
    #         if self.lyo['counts']['row'] <= row:
    #             break

    #         try:
    #             eta = self.etafactory.create_eta(entry)
    #             rtdet = eta.details
    #             rtdet.route_exists(True)  # check routes existence

    #             # titles
    #             drawer.bitmap((layout['route']['logo']['offset'][0],
    #                            layout['route']['logo']['offset'][1] + (rh*row)),
    #                           Image.open(rtdet.logo()).convert(
    #                               "1").resize((30, 30)),
    #                           self._black)
    #             drawer.text((layout['route']['name']['offset'][0],
    #                          layout['route']['name']['offset'][1] + (rh*row)),
    #                         utils.discard(rtdet.route_name(),
    #                                    layout['route']['name']['width'], f_rt),
    #                         fill=self._black, font=f_rt)
    #             drawer.text((layout['route']['dest']['offset'][0],
    #                          layout['route']['dest']['offset'][1] + (rh*row)),
    #                         utils.discard(rtdet.destination(),
    #                                    layout['route']['dest']['width'], f_stop),
    #                         fill=self._black, font=f_stop)
    #             drawer.text((layout['route']['stop']['offset'][0],
    #                          layout['route']['stop']['offset'][1] + (rh*row)),
    #                         utils.discard(
    #                             f"@{rtdet.stop_name()}", layout['route']['stop']['width'], f_stop),
    #                         fill=self._black, font=f_stop)
    #             # time
    #             for idx, time in enumerate(eta.etas()):
    #                 if (idx >= self.lyo['counts']['eta']):
    #                     break
    #                 idx_offset = rh*row + layout['eta']['row']['height']*idx
    #                 idx_offset = rh*row + layout['eta']['row']['height']*idx
    #                 if time['minute'] is None:
    #                     offset_x, offset_y = utils.position(
    #                         time['remark'], layout['eta']['row']['width'],
    #                         layout['eta']['row']['height'], f_err, align='c')

    #                     drawer.text((layout['eta']['row']['offset'][0] + offset_x,
    #                                  layout['eta']['row']['offset'][1] + offset_y + idx_offset),
    #                                 utils.discard(
    #                                     time['remark'], layout['eta']['row']['width'], f_rmk),
    #                                 fill=self._black, font=f_rmk)
    #                 else:
    #                     offset_x, offset_y = utils.position(
    #                         time['time'], layout['eta']['row']['width'],
    #                         layout['eta']['row']['height'], f_time, align='c', offset_y=-3)

    #                     drawer.text((layout['eta']['row']['offset'][0] + offset_x,
    #                                  layout['eta']['row']['offset'][1] + idx_offset + offset_y),
    #                                 text=time['time'], fill=self._black, font=f_time)
    #         except HketaException as e:
    #             errmsg = utils.wrap(
    #                 e.get_msg(entry.lang), layout['eta']['block']['width'],
    #                 layout['eta']['block']['height'], f_err)

    #             offset_x, offset_y = utils.position(
    #                 errmsg, layout['eta']['block']['width'],
    #                 layout['eta']['block']['height'], f_err, align='c')

    #             drawer.text(
    #                 (layout['eta']['block']['offset'][0] + offset_x,
    #                  layout['eta']['block']['offset'][1] + rh*row + offset_y),
    #                 text=errmsg, fill=self._black, font=f_err)
    #         except Exception as e:
    #             logging.error(f"error occurs: {e.__class__.__name__}, {e}")
    #             logging.debug(e, exc_info=True)

    #     return {'black': image.rotate(degree)}


if __name__ == "__main__":
    import enums
    print(Epd3in7EtaImage.layouts(enums.EtaMode.MIXED))
